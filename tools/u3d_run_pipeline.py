#!/usr/bin/env python3
"""Run U3D source-images/source-configs pipeline in one command.

Pipeline stages:
1) export images
2) extract sequential level map
3) export level configs
4) group images by mode
5) split atlases to sprite slices (remove base atlas)
6) export avatar/material/group map
7) import (none / dry-run / apply)
8) verify sourceImages structure and split coverage
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple


@dataclass
class StepResult:
    name: str
    command: List[str]
    returncode: int


def _resolve(path_text: str) -> Path:
    return Path(path_text).expanduser().resolve()


def _default_source_root(project_root: Path) -> Path:
    # New layout: myprojects/<project>/webprojects
    if project_root.name == "webprojects":
        return (project_root.parent / "sourceImages").resolve()
    return (project_root.parent.parent / "sourceImages" / project_root.name).resolve()


def _default_source_config_root(project_root: Path) -> Path:
    # New layout: myprojects/<project>/webprojects
    if project_root.name == "webprojects":
        return (project_root.parent / "sourceConfigs").resolve()
    return (project_root.parent.parent / "sourceConfigs" / project_root.name).resolve()


def _run_step(name: str, command: Sequence[str], cwd: Path) -> StepResult:
    cmd = list(command)
    print(f"[pipeline] step={name}", flush=True)
    print("[pipeline] cmd=" + " ".join(cmd), flush=True)
    completed = subprocess.run(cmd, cwd=str(cwd), check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            f"Step failed: {name} (exit={completed.returncode})"
        )
    return StepResult(name=name, command=cmd, returncode=completed.returncode)


def _load_json(path: Path) -> Dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _verify_top_level_dirs(source_root: Path) -> List[str]:
    images_dir = source_root / "images"
    if not images_dir.is_dir():
        return ["images dir not found"]
    bad: List[str] = []
    for item in sorted(images_dir.iterdir()):
        if not item.is_dir():
            continue
        name = item.name
        if name == "Others":
            continue
        if name.startswith("Main_Level_"):
            continue
        if name.startswith("Story_"):
            continue
        bad.append(name)
    return bad


def _verify_config_top_level_dirs(source_config_root: Path) -> List[str]:
    configs_dir = source_config_root / "configs"
    if not configs_dir.is_dir():
        return ["configs dir not found"]
    bad: List[str] = []
    for item in sorted(configs_dir.iterdir()):
        if not item.is_dir():
            continue
        name = item.name
        if name == "Others":
            continue
        if name.startswith("Main_Level_"):
            continue
        if name.startswith("Story_"):
            continue
        bad.append(name)
    return bad


def _verify_no_base_for_split_entries(source_root: Path, mapping_doc: Dict) -> Tuple[int, int]:
    entries = mapping_doc.get("entries", [])
    split_entries = 0
    residual_base = 0
    for entry in entries:
        if entry.get("kind") != "Texture2D":
            continue
        export_path = entry.get("exportPath")
        if not isinstance(export_path, str) or not export_path:
            continue
        slices = entry.get("spriteAtlasSlices")
        if not isinstance(slices, list) or not slices:
            continue
        split_entries += 1
        if (source_root / export_path).is_file():
            residual_base += 1
    return split_entries, residual_base


def _load_split_module(split_script_path: Path):
    spec = importlib.util.spec_from_file_location("u3d_split_script", split_script_path)
    if not spec or not spec.loader:
        raise RuntimeError(f"failed to load split script: {split_script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


def _iter_unique_bundle_rel_paths(mapping_doc: Dict) -> Iterable[str]:
    seen = set()
    for entry in mapping_doc.get("entries", []):
        if entry.get("kind") != "Texture2D":
            continue
        bundle_rel = entry.get("bundleRelPath")
        if not isinstance(bundle_rel, str) or not bundle_rel:
            continue
        if bundle_rel in seen:
            continue
        seen.add(bundle_rel)
        yield bundle_rel


def _verify_all_atlas_split(
    project_root: Path,
    source_root: Path,
    mapping_doc: Dict,
    split_script_path: Path,
) -> Tuple[int, int, List[str]]:
    entries = mapping_doc.get("entries", [])
    by_key: Dict[Tuple[str, int], Dict] = {}
    for entry in entries:
        if entry.get("kind") != "Texture2D":
            continue
        bundle_rel = entry.get("bundleRelPath")
        path_id = entry.get("pathId")
        if not isinstance(bundle_rel, str):
            continue
        if not isinstance(path_id, int):
            continue
        by_key[(bundle_rel, path_id)] = entry

    module = _load_split_module(split_script_path)
    atlas_total = 0
    atlas_unsplit = 0
    examples: List[str] = []

    for bundle_rel in sorted(_iter_unique_bundle_rel_paths(mapping_doc)):
        bundle_path = project_root / bundle_rel
        if not bundle_path.is_file():
            continue
        slices_by_tex = module._collect_bundle_atlas_slices(bundle_path)
        for tex_path_id, tex_slices in slices_by_tex.items():
            if len(tex_slices) < 1:
                continue
            atlas_total += 1
            entry = by_key.get((bundle_rel, int(tex_path_id)))
            if not entry:
                atlas_unsplit += 1
                if len(examples) < 20:
                    examples.append(f"{bundle_rel}#{tex_path_id} (missing mapping)")
                continue
            split_slices = entry.get("spriteAtlasSlices")
            if not isinstance(split_slices, list) or len(split_slices) < 1:
                atlas_unsplit += 1
                if len(examples) < 20:
                    export_path = entry.get("exportPath")
                    examples.append(f"{bundle_rel}#{tex_path_id} ({export_path})")
                continue
            export_path = entry.get("exportPath")
            if isinstance(export_path, str) and (source_root / export_path).is_file():
                atlas_unsplit += 1
                if len(examples) < 20:
                    examples.append(f"{bundle_rel}#{tex_path_id} (base still exists)")
    return atlas_total, atlas_unsplit, examples


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one-click U3D pipeline: images+configs export/map/group/split/import/verify."
    )
    parser.add_argument(
        "--project-root",
        required=True,
        help="Project root, e.g. webprojects/drgm_ljpx2_lt",
    )
    parser.add_argument(
        "--source-root",
        default="",
        help=(
            "sourceImages project directory. Default: "
            "new layout => <project-root-parent>/sourceImages, "
            "legacy => sourceImages/<project-name>"
        ),
    )
    parser.add_argument(
        "--source-config-root",
        default="",
        help=(
            "sourceConfigs project directory. Default: "
            "new layout => <project-root-parent>/sourceConfigs, "
            "legacy => sourceConfigs/<project-name>"
        ),
    )
    parser.add_argument(
        "--asset-dir",
        default="StreamingAssets/WebGL/ljpx2_lt",
        help="Asset bundle directory relative to project-root.",
    )
    parser.add_argument(
        "--webdata-dir",
        default="Build",
        help="WebGL data directory relative to project-root.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean source-root and source-config-root before export stages.",
    )
    parser.add_argument(
        "--import-mode",
        choices=("none", "dry-run", "apply"),
        default="dry-run",
        help="Import stage mode. dry-run is the safe default.",
    )
    parser.add_argument(
        "--allow-size-mismatch",
        action="store_true",
        help="Pass through to import stage.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Skip export stage.",
    )
    parser.add_argument(
        "--skip-map",
        action="store_true",
        help="Skip sequential-map stage.",
    )
    parser.add_argument(
        "--skip-group",
        action="store_true",
        help="Skip group-by-mode stage.",
    )
    parser.add_argument(
        "--skip-config-export",
        action="store_true",
        help="Skip level-config export stage.",
    )
    parser.add_argument(
        "--skip-split",
        action="store_true",
        help="Skip split-atlas stage.",
    )
    parser.add_argument(
        "--skip-avatar-map",
        action="store_true",
        help="Skip avatar/material mapping export stage.",
    )
    parser.add_argument(
        "--ct-term-map",
        default="",
        help='Optional JSON path: {"<ct>":"中文文案"} for avatar-map commonTypeTerm.',
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip verify stage.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python executable path. Default: current interpreter.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = Path.cwd().resolve()
    project_root = _resolve(args.project_root)
    source_root = _resolve(args.source_root) if args.source_root else _default_source_root(project_root)
    source_config_root = (
        _resolve(args.source_config_root)
        if args.source_config_root
        else _default_source_config_root(project_root)
    )
    python_bin = args.python

    if not project_root.is_dir():
        raise SystemExit(f"project-root not found: {project_root}")
    tools_dir = workspace / "tools"
    if not tools_dir.is_dir():
        raise SystemExit(f"tools directory not found: {tools_dir}")

    export_script = tools_dir / "u3d_export_source_images.py"
    config_export_script = tools_dir / "u3d_export_level_configs.py"
    map_script = tools_dir / "u3d_extract_sequential_level_map.py"
    group_script = tools_dir / "u3d_group_images_by_mode.py"
    split_script = tools_dir / "u3d_split_root_spriteatlas_images.py"
    avatar_map_script = tools_dir / "u3d_export_avatar_material_map.py"
    import_script = tools_dir / "u3d_import_source_images.py"

    for script in (
        export_script,
        config_export_script,
        map_script,
        group_script,
        split_script,
        avatar_map_script,
        import_script,
    ):
        if not script.is_file():
            raise SystemExit(f"script not found: {script}")

    step_results: List[StepResult] = []
    if not args.skip_export:
        cmd = [
            python_bin,
            "-u",
            str(export_script),
            "--project-root",
            str(project_root),
            "--asset-dir",
            args.asset_dir,
            "--webdata-dir",
            args.webdata_dir,
            "--output-root",
            str(source_root),
        ]
        if args.clean:
            cmd.append("--clean")
        step_results.append(_run_step("export", cmd, workspace))

    if not args.skip_map:
        map_output = source_root / "sequential_level_data_map.json"
        cmd = [
            python_bin,
            "-u",
            str(map_script),
            "--asset-dir",
            str((project_root / args.asset_dir).resolve()),
            "--output",
            str(map_output),
        ]
        step_results.append(_run_step("map", cmd, workspace))

    if not args.skip_config_export:
        cmd = [
            python_bin,
            "-u",
            str(config_export_script),
            "--project-root",
            str(project_root),
            "--asset-dir",
            args.asset_dir,
            "--output-root",
            str(source_config_root),
        ]
        if args.clean:
            cmd.append("--clean")
        step_results.append(_run_step("config-export", cmd, workspace))

    if not args.skip_group:
        cmd = [
            python_bin,
            "-u",
            str(group_script),
            "--source-root",
            str(source_root),
        ]
        step_results.append(_run_step("group", cmd, workspace))

    if not args.skip_split:
        cmd = [
            python_bin,
            "-u",
            str(split_script),
            "--project-root",
            str(project_root),
            "--source-root",
            str(source_root),
        ]
        step_results.append(_run_step("split", cmd, workspace))

    if not args.skip_avatar_map:
        avatar_map_output = source_config_root / "level_avatar_material_mapping.json"
        cmd = [
            python_bin,
            "-u",
            str(avatar_map_script),
            "--source-config-root",
            str(source_config_root),
            "--source-image-root",
            str(source_root),
            "--output",
            str(avatar_map_output),
        ]
        if args.ct_term_map:
            cmd.extend(["--ct-term-map", args.ct_term_map])
        step_results.append(_run_step("avatar-map", cmd, workspace))

    if args.import_mode != "none":
        cmd = [
            python_bin,
            "-u",
            str(import_script),
            "--project-root",
            str(project_root),
            "--source-root",
            str(source_root),
        ]
        if args.allow_size_mismatch:
            cmd.append("--allow-size-mismatch")
        if args.import_mode == "dry-run":
            cmd.append("--dry-run")
        step_results.append(_run_step(f"import:{args.import_mode}", cmd, workspace))

    verify_summary: Dict[str, object] = {}
    if not args.skip_verify:
        mapping_path = source_root / "image_mapping.json"
        if not mapping_path.is_file():
            raise RuntimeError(f"verify failed: mapping not found: {mapping_path}")
        mapping_doc = _load_json(mapping_path)
        config_mapping_path = source_config_root / "config_mapping.json"
        if not config_mapping_path.is_file():
            raise RuntimeError(f"verify failed: config mapping not found: {config_mapping_path}")
        config_mapping_doc = _load_json(config_mapping_path)
        avatar_mapping_path = source_config_root / "level_avatar_material_mapping.json"
        if not avatar_mapping_path.is_file():
            raise RuntimeError(f"verify failed: avatar mapping not found: {avatar_mapping_path}")
        avatar_mapping_doc = _load_json(avatar_mapping_path)

        bad_dirs = _verify_top_level_dirs(source_root)
        bad_config_dirs = _verify_config_top_level_dirs(source_config_root)
        split_entries, residual_base = _verify_no_base_for_split_entries(source_root, mapping_doc)
        atlas_total, atlas_unsplit, atlas_examples = _verify_all_atlas_split(
            project_root=project_root,
            source_root=source_root,
            mapping_doc=mapping_doc,
            split_script_path=split_script,
        )
        config_exported_count = int((config_mapping_doc.get("summary") or {}).get("exportedCount", 0))
        avatar_level_count = int((avatar_mapping_doc.get("summary") or {}).get("levelCount", 0))

        verify_summary = {
            "badDirs": bad_dirs,
            "badConfigDirs": bad_config_dirs,
            "splitEntries": split_entries,
            "residualBaseFiles": residual_base,
            "atlasTotal": atlas_total,
            "atlasUnsplit": atlas_unsplit,
            "atlasUnsplitExamples": atlas_examples,
            "configExportedCount": config_exported_count,
            "avatarLevelCount": avatar_level_count,
        }
        print("[pipeline] verify summary=" + json.dumps(verify_summary, ensure_ascii=False))

        if bad_dirs:
            raise RuntimeError(f"verify failed: unexpected top-level dirs: {bad_dirs}")
        if bad_config_dirs:
            raise RuntimeError(
                f"verify failed: unexpected config top-level dirs: {bad_config_dirs}"
            )
        if residual_base > 0:
            raise RuntimeError(f"verify failed: residual base atlases: {residual_base}")
        if atlas_unsplit > 0:
            raise RuntimeError(
                f"verify failed: atlas not split: {atlas_unsplit}, examples={atlas_examples[:5]}"
            )
        if config_exported_count <= 0:
            raise RuntimeError("verify failed: no config entries exported")
        if avatar_level_count <= 0:
            raise RuntimeError("verify failed: no avatar map levels exported")

    print("[pipeline] done")
    print(f"[pipeline] project_root={project_root}")
    print(f"[pipeline] source_root={source_root}")
    print(f"[pipeline] source_config_root={source_config_root}")
    print("[pipeline] steps=" + ",".join(item.name for item in step_results))
    if verify_summary:
        print("[pipeline] verify=pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

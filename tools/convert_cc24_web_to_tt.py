#!/usr/bin/env python3
"""
Convert a Cocos Creator 2.4 web build into a TikTok mini-game package
by following the base2.4 -> bytedance-mini-game-cc2.4 mapping.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def fail(msg: str) -> None:
    print(f"[ERR] {msg}", file=sys.stderr)
    raise SystemExit(1)


def parse_index_html(index_html: Path) -> Tuple[str, str]:
    text = index_html.read_text(encoding="utf-8", errors="ignore")

    settings_match = re.search(
        r'<script\s+src="([^"]*src/settings[^"]*\.js(?:\?[^"]*)?)"',
        text,
        flags=re.IGNORECASE,
    )
    main_match = re.search(
        r'<script\s+src="([^"]*main[^"]*\.js(?:\?[^"]*)?)"',
        text,
        flags=re.IGNORECASE,
    )
    if not settings_match:
        fail(f"cannot find settings script tag in {index_html}")
    if not main_match:
        fail(f"cannot find main script tag in {index_html}")

    settings_rel = settings_match.group(1).split("?", 1)[0].lstrip("./")
    main_rel = main_match.group(1).split("?", 1)[0].lstrip("./")
    return settings_rel, main_rel


def load_settings_via_node(settings_js: Path) -> Dict:
    node_code = r"""
const fs = require('fs');
const vm = require('vm');
const p = process.argv[1];
const code = fs.readFileSync(p, 'utf8');
const ctx = {
  window: {},
  console: { log(){}, warn(){}, error(){} }
};
ctx.global = ctx;
ctx.self = ctx;
ctx.globalThis = ctx;
vm.createContext(ctx);
vm.runInContext(code, ctx, { timeout: 3000 });
process.stdout.write(JSON.stringify(ctx.window._CCSettings || null));
"""
    try:
        res = subprocess.run(
            ["node", "-e", node_code, str(settings_js)],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        fail("node is required but not found in PATH")
    except subprocess.CalledProcessError as exc:
        fail(f"failed to evaluate settings: {exc.stderr.strip()}")

    out = res.stdout.strip()
    if not out or out == "null":
        fail(f"failed to extract window._CCSettings from {settings_js}")
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        fail(f"invalid settings JSON from node: {exc}")
    if not isinstance(data, dict):
        fail("settings payload is not an object")
    return data


def write_settings_js(settings: Dict, dst: Path) -> None:
    settings = dict(settings)
    settings["platform"] = "bytedance"
    settings.setdefault("server", "")
    payload = json.dumps(settings, ensure_ascii=False, separators=(",", ":"))
    dst.write_text(f"window._CCSettings={payload};", encoding="utf-8")


def has_encrypted_assets(assets_dir: Path) -> bool:
    if not assets_dir.exists():
        return False
    # Detect old encrypted payload signature used by this project.
    for p in assets_dir.rglob("*"):
        if not p.is_file():
            continue
        suffix = p.suffix.lower()
        if suffix not in {".png", ".json", ".txt", ".plist", ".bin"}:
            continue
        try:
            head = p.read_bytes()[:8]
        except OSError:
            continue
        if head.startswith(b"netease"):
            return True
    return False


def rename_bundle_indexes(assets_dir: Path) -> List[Tuple[str, str]]:
    renamed: List[Tuple[str, str]] = []
    for bundle_dir in sorted(p for p in assets_dir.iterdir() if p.is_dir()):
        hashed = sorted(bundle_dir.glob("index.*.js"))
        canonical = bundle_dir / "index.js"
        if canonical.exists():
            continue
        if len(hashed) == 1:
            src = hashed[0]
            rel_src = src.relative_to(assets_dir.parent).as_posix()
            rel_dst = canonical.relative_to(assets_dir.parent).as_posix()
            src.rename(canonical)
            renamed.append((rel_src, rel_dst))
        elif len(hashed) > 1:
            fail(f"multiple hashed index files in {bundle_dir}")
    return renamed


def add_module_alias(module_map: Dict[str, str], key: str, target: str) -> None:
    module_map[key] = target
    if key.startswith("./"):
        no_dot = key[2:]
        module_map.setdefault(no_dot, target)
    else:
        module_map.setdefault("./" + key, target)

    if key.endswith(".js"):
        no_ext = key[:-3]
        module_map.setdefault(no_ext, target)
        module_map.setdefault("./" + no_ext.lstrip("./"), target)


def build_cc_require(assets_dir: Path, renamed: List[Tuple[str, str]], dst: Path) -> None:
    module_map: Dict[str, str] = {}

    for bundle_dir in sorted(p for p in assets_dir.iterdir() if p.is_dir()):
        canonical = bundle_dir / "index.js"
        if not canonical.exists():
            continue
        rel = canonical.relative_to(assets_dir.parent).as_posix()
        add_module_alias(module_map, rel, rel)

    # Keep compatibility with hashed names from source web build.
    for old_rel, new_rel in renamed:
        add_module_alias(module_map, old_rel, new_rel)

    lines = ["let moduleMap = {"]
    for key in sorted(module_map):
        target = module_map[key]
        lines.append(
            f"'{key}': function () {{ return require('{target}'); }},"
        )
    lines.append("// tail")
    lines.append("};")
    lines.append("")
    lines.append("window.__cocos_require__ = function (moduleName) {")
    lines.append("  if (!moduleName) {")
    lines.append("    throw new Error('cannot find module: empty');")
    lines.append("  }")
    lines.append("")
    lines.append("  let name = moduleName;")
    lines.append("  let loader = moduleMap[name];")
    lines.append("")
    lines.append("  if (!loader && name.startsWith('./')) {")
    lines.append("    loader = moduleMap[name.slice(2)];")
    lines.append("  }")
    lines.append("")
    lines.append("  if (!loader && !name.endsWith('.js')) {")
    lines.append("    loader = moduleMap[name + '.js'] || moduleMap['./' + name + '.js'];")
    lines.append("  }")
    lines.append("")
    lines.append("  if (!loader && name.endsWith('.js')) {")
    lines.append("    const noExt = name.slice(0, -3);")
    lines.append("    loader = moduleMap[noExt] || moduleMap['./' + noExt];")
    lines.append("  }")
    lines.append("")
    lines.append("  if (!loader) {")
    lines.append("    const candidates = [moduleName];")
    lines.append("    let lastError = null;")
    lines.append("    if (!moduleName.startsWith('./')) {")
    lines.append("      candidates.push('./' + moduleName);")
    lines.append("    }")
    lines.append("    for (let i = 0; i < candidates.length; i++) {")
    lines.append("      try {")
    lines.append("        return require(candidates[i]);")
    lines.append("      } catch (nativeRequireError) {")
    lines.append("        lastError = nativeRequireError;")
    lines.append("      }")
    lines.append("    }")
    lines.append("    if (lastError) {")
    lines.append("      throw lastError;")
    lines.append("    }")
    lines.append("    throw new Error('cannot find module ' + moduleName);")
    lines.append("  }")
    lines.append("")
    lines.append("  return loader();")
    lines.append("};")
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")


def patch_main(main_js: Path, use_png_hook: bool) -> None:
    text = main_js.read_text(encoding="utf-8", errors="ignore")
    patched = re.sub(r"src/settings[^'\"/\\]*\.js", "src/settings.js", text)
    # Switch png downloader hook by resource mode:
    # - encrypted assets: keep custom downloader (.png -> abf)
    # - plain assets: use default engine downloader ({})
    if use_png_hook and "function abf(" in patched:
        if "{'.png':abf}" not in patched:
            patched = patched.replace(
                "a1_0x3992(0x26)]({});var _0x2a9893",
                "a1_0x3992(0x26)]({'.png':abf});var _0x2a9893",
                1,
            )
            patched = patched.replace("register({});", "register({'.png':abf});", 1)
    else:
        patched = patched.replace(
            "a1_0x3992(0x26)]({'.png':abf});var _0x2a9893",
            "a1_0x3992(0x26)]({});var _0x2a9893",
            1,
        )
        patched = patched.replace("register({'.png':abf});", "register({});", 1)
    main_js.write_text(patched, encoding="utf-8")


def patch_game_js(game_js: Path) -> None:
    text = game_js.read_text(encoding="utf-8", errors="ignore")
    main_marker = "require('./main'); // TODO: move to common"
    if main_marker in text and "[TT_DIAG] force window.jsb=false" not in text:
        text = text.replace(
            main_marker,
            "\n".join(
                [
                    "if (typeof tt !== 'undefined' && window.jsb) {",
                    "  console.warn('[TT_DIAG] force window.jsb=false before require main');",
                    "  try { window.jsb = false; } catch (e) {}",
                    "}",
                    "",
                    main_marker,
                ]
            ),
            1,
        )
    diag_anchor = "if (cc.sys.platform !== cc.sys.BYTEDANCE_GAME_SUB) {"
    if diag_anchor in text and "[TT_DIAG] patch assetManager hooks" not in text:
        text = text.replace(
            diag_anchor,
            "\n".join(
                [
                    "console.log('[TT_DIAG] patch assetManager hooks');",
                    "try {",
                    "  if (cc && cc.assetManager) {",
                    "    const __origLoadScript = cc.assetManager.loadScript && cc.assetManager.loadScript.bind(cc.assetManager);",
                    "    if (__origLoadScript) {",
                    "      cc.assetManager.loadScript = function (list, cb) {",
                    "        const len = Array.isArray(list) ? list.length : -1;",
                    "        console.log('[TT_DIAG] loadScript len=' + len);",
                    "        if (Array.isArray(list) && list.length === 0) {",
                    "          setTimeout(function () {",
                    "            console.log('[TT_DIAG] loadScript empty -> cb begin');",
                    "            try {",
                    "              cb && cb(null);",
                    "              console.log('[TT_DIAG] loadScript empty -> cb done');",
                    "            } catch (e) {",
                    "              console.error('[TT_FATAL] loadScript empty cb throw', e && (e.stack || e.message || e));",
                    "              throw e;",
                    "            }",
                    "          }, 0);",
                    "          return;",
                    "        }",
                    "        return __origLoadScript(list, function (err) {",
                    "          if (err) console.error('[TT_FATAL] loadScript', err && (err.stack || err.message || err));",
                    "          console.log('[TT_DIAG] loadScript cb begin err=' + String(!!err));",
                    "          try {",
                    "            cb && cb(err);",
                    "            console.log('[TT_DIAG] loadScript cb done');",
                    "          } catch (e) {",
                    "            console.error('[TT_FATAL] loadScript cb throw', e && (e.stack || e.message || e));",
                    "            throw e;",
                    "          }",
                    "        });",
                    "      };",
                    "    }",
                    "",
                    "    const __origLoadBundle = cc.assetManager.loadBundle && cc.assetManager.loadBundle.bind(cc.assetManager);",
                    "    if (__origLoadBundle) {",
                    "      cc.assetManager.loadBundle = function (name, opts, cb) {",
                    "        let _opts = opts;",
                    "        let _cb = cb;",
                    "        if (typeof _opts === 'function') { _cb = _opts; _opts = undefined; }",
                    "        console.log('[TT_DIAG] loadBundle start ' + name);",
                    "        return __origLoadBundle(name, _opts, function (err, bundle) {",
                    "          if (err) console.error('[TT_FATAL] loadBundle ' + name, err && (err.stack || err.message || err));",
                    "          else console.log('[TT_DIAG] loadBundle ok ' + name);",
                    "          _cb && _cb(err, bundle);",
                    "        });",
                    "      };",
                    "    }",
                    "  }",
                    "",
                    "  if (cc && cc.game && cc.game.run) {",
                    "    const __origGameRun = cc.game.run.bind(cc.game);",
                    "    cc.game.run = function (opt, onStart) {",
                    "      console.log('[TT_DIAG] cc.game.run called');",
                    "      const wrapped = function () {",
                    "        console.log('[TT_DIAG] onStart called');",
                    "        return onStart && onStart();",
                    "      };",
                    "      return __origGameRun(opt, wrapped);",
                    "    };",
                    "  }",
                    "",
                    "  if (cc && cc.game && cc.game.prepare) {",
                    "    const __origPrepare = cc.game.prepare.bind(cc.game);",
                    "    cc.game.prepare = function (cb) {",
                    "      console.log('[TT_DIAG] cc.game.prepare called');",
                    "      return __origPrepare(function () {",
                    "        console.log('[TT_DIAG] cc.game.prepare callback');",
                    "        return cb && cb();",
                    "      });",
                    "    };",
                    "  }",
                    "",
                    "  if (cc && cc.game && cc.game._prepareFinished) {",
                    "    const __origPrepareFinished = cc.game._prepareFinished.bind(cc.game);",
                    "    cc.game._prepareFinished = function (cb) {",
                    "      console.log('[TT_DIAG] _prepareFinished called');",
                    "      return __origPrepareFinished(function () {",
                    "        console.log('[TT_DIAG] _prepareFinished callback');",
                    "        return cb && cb();",
                    "      });",
                    "    };",
                    "  }",
                    "",
                    "  if (cc && cc.game && cc.game._initEngine) {",
                    "    const __origInitEngine = cc.game._initEngine.bind(cc.game);",
                    "    cc.game._initEngine = function () {",
                    "      console.log('[TT_DIAG] _initEngine called');",
                    "      return __origInitEngine.apply(this, arguments);",
                    "    };",
                    "  }",
                    "",
                    "  if (cc && cc.game && cc.game._initRenderer) {",
                    "    const __origInitRenderer = cc.game._initRenderer.bind(cc.game);",
                    "    cc.game._initRenderer = function () {",
                    "      console.log('[TT_DIAG] _initRenderer called');",
                    "      return __origInitRenderer.apply(this, arguments);",
                    "    };",
                    "  }",
                    "",
                    "  if (cc && cc.assetManager && cc.assetManager.builtins) {",
                    "    const b = cc.assetManager.builtins;",
                    "    if (b.init) {",
                    "      const __origBuiltinsInit = b.init.bind(b);",
                    "      b.init = function (cb) {",
                    "        console.log('[TT_DIAG] builtins.init called');",
                    "        return __origBuiltinsInit(function () {",
                    "          console.log('[TT_DIAG] builtins.init callback');",
                    "          return cb && cb();",
                    "        });",
                    "      };",
                    "    }",
                    "    if (b._loadBuiltins) {",
                    "      const __origLoadBuiltins = b._loadBuiltins.bind(b);",
                    "      b._loadBuiltins = function (name, type, cb) {",
                    "        console.log('[TT_DIAG] builtins._loadBuiltins start ' + name);",
                    "        return __origLoadBuiltins(name, type, function (err) {",
                    "          if (err) console.error('[TT_FATAL] builtins._loadBuiltins ' + name, err && (err.stack || err.message || err));",
                    "          else console.log('[TT_DIAG] builtins._loadBuiltins ok ' + name);",
                    "          return cb && cb(err);",
                    "        });",
                    "      };",
                    "    }",
                    "  }",
                    "",
                    "  if (cc && cc.errorID) {",
                    "    const __origErrorID = cc.errorID.bind(cc);",
                    "    cc.errorID = function () {",
                    "      try { console.error.apply(console, ['[TT_CC_ERROR_ID]'].concat([].slice.call(arguments))); } catch (_) {}",
                    "      return __origErrorID.apply(this, arguments);",
                    "    };",
                    "  }",
                    "  if (cc && cc.warnID) {",
                    "    const __origWarnID = cc.warnID.bind(cc);",
                    "    cc.warnID = function () {",
                    "      try { console.warn.apply(console, ['[TT_CC_WARN_ID]'].concat([].slice.call(arguments))); } catch (_) {}",
                    "      return __origWarnID.apply(this, arguments);",
                    "    };",
                    "  }",
                    "",
                    "  if (cc && cc.director && cc.director.loadScene) {",
                    "    const __origLoadScene = cc.director.loadScene.bind(cc.director);",
                    "    cc.director.loadScene = function (sceneName, onLaunched, onUnloaded) {",
                    "      console.log('[TT_DIAG] loadScene start ' + sceneName);",
                    "      return __origLoadScene(sceneName, onLaunched, function () {",
                    "        console.log('[TT_DIAG] loadScene complete ' + sceneName);",
                    "        return onUnloaded && onUnloaded.apply(this, arguments);",
                    "      });",
                    "    };",
                    "  }",
                    "} catch (e) {",
                    "  console.error('[TT_FATAL] patch hooks', e && (e.stack || e.message || e));",
                    "}",
                    "",
                    diag_anchor,
                ]
            ),
            1,
        )
    marker = "window.boot();"
    if marker in text and "[TT_DIAG] before window.boot" not in text:
        text = text.replace(
            marker,
            "\n".join(
                [
                    "console.log('[TT_DIAG] before window.boot jsb=' + String(!!window.jsb));",
                    "try {",
                    "  window.boot();",
                    "  console.log('[TT_DIAG] after window.boot invoke');",
                    "} catch (e) {",
                    "  console.error('[TT_FATAL] window.boot()', e && (e.stack || e.message || e));",
                    "  throw e;",
                    "}",
                ]
            ),
            1,
        )
    game_js.write_text(text, encoding="utf-8")


def clean_legacy_files(dst: Path) -> None:
    for p in [
        dst / "web-adapter.js",
        dst / "tt-dom-shim.js",
    ]:
        if p.exists():
            p.unlink()

    for p in dst.glob("main.*.js"):
        if p.name != "main.js":
            p.unlink()
    for p in (dst / "src").glob("settings.*.js"):
        if p.name != "settings.js":
            p.unlink()

    for p in dst.rglob(".DS_Store"):
        if p.is_file():
            p.unlink()


def update_project_config(project_config: Path, project_name: str) -> None:
    if not project_config.exists():
        return
    try:
        data = json.loads(project_config.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return
    if isinstance(data, dict):
        data["projectname"] = project_name
        project_config.write_text(
            json.dumps(data, ensure_ascii=False, indent=4) + "\n",
            encoding="utf-8",
        )


def convert(source: Path, template: Path, dest: Path) -> None:
    if not source.exists():
        fail(f"source not found: {source}")
    if not template.exists():
        fail(f"template not found: {template}")
    if not (source / "index.html").exists():
        fail(f"missing source index.html: {source / 'index.html'}")
    if not (source / "assets").exists():
        fail(f"missing source assets directory: {source / 'assets'}")

    settings_rel, main_rel = parse_index_html(source / "index.html")
    src_settings_path = source / settings_rel
    src_main_path = source / main_rel
    if not src_settings_path.exists():
        fail(f"settings script not found: {src_settings_path}")
    if not src_main_path.exists():
        fail(f"main script not found: {src_main_path}")

    tmp_dest = dest.with_name(dest.name + ".tmp")
    if tmp_dest.exists():
        shutil.rmtree(tmp_dest)

    shutil.copytree(template, tmp_dest)

    # Replace assets with source assets.
    shutil.rmtree(tmp_dest / "assets")
    shutil.copytree(source / "assets", tmp_dest / "assets")

    # Keep source src folder for optional plugin scripts.
    if (tmp_dest / "src").exists():
        shutil.rmtree(tmp_dest / "src")
    shutil.copytree(source / "src", tmp_dest / "src")

    # Main from source web build.
    shutil.copy2(src_main_path, tmp_dest / "main.js")

    # Keep template engine (TT-adapted).
    # Do not overwrite with source web engine for this conversion mode.

    # Prefer source physics file if present.
    physics_candidates = sorted(source.glob("physics-min*.js"))
    if physics_candidates:
        shutil.copy2(physics_candidates[0], tmp_dest / "physics-min.js")

    # Settings normalization.
    settings_obj = load_settings_via_node(src_settings_path)
    write_settings_js(settings_obj, tmp_dest / "src" / "settings.js")

    use_png_hook = has_encrypted_assets(source / "assets")
    patch_main(tmp_dest / "main.js", use_png_hook)
    patch_game_js(tmp_dest / "game.js")
    renamed = rename_bundle_indexes(tmp_dest / "assets")
    build_cc_require(tmp_dest / "assets", renamed, tmp_dest / "ccRequire.js")
    clean_legacy_files(tmp_dest)
    update_project_config(tmp_dest / "project.config.json", source.name)

    if dest.exists():
        shutil.rmtree(dest)
    tmp_dest.rename(dest)

    print(f"[OK] source   : {source}")
    print(f"[OK] template : {template}")
    print(f"[OK] output   : {dest}")
    print(f"[OK] bundles  : {len(list((dest / 'assets').glob('*/index.js')))}")
    print(f"[OK] renamed  : {len(renamed)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Cocos Creator 2.4 web build to TikTok mini-game package."
    )
    parser.add_argument("--source", required=True, help="source web build directory")
    parser.add_argument("--template", required=True, help="TT template directory")
    parser.add_argument("--dest", required=True, help="destination directory")
    args = parser.parse_args()

    convert(Path(args.source), Path(args.template), Path(args.dest))


if __name__ == "__main__":
    main()

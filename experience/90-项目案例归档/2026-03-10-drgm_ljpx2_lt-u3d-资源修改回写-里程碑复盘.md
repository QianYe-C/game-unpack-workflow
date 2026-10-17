# 2026-03-10 DRGM（ljpx2_lt）U3D 资源修改回写里程碑复盘

## 里程碑结论
- 已完成：`sourceImages` 导出、分组、修改、回写全链路打通。
- 已完成：按配置表映射关卡资源（非文件名猜测）。
- 已完成：回写后自动同步 `PackageManifest` CRC，解决 `CRC Mismatch`。
- 已完成：本地启动验证通过，未再出现资源 CRC 报错。
- 已完成：修复“分图文件名与图片内容错位”的核心映射问题。

## 本次产出与脚本
- 说明：以下路径为本项目示例，重点是方法，不是目录名本身。
- 项目目录（示例）：`/Users/jiaojian/Documents/localweb/myprojects/drgm_ljpx2_lt/webprojects`
- 贴图目录（示例）：`/Users/jiaojian/Documents/localweb/myprojects/drgm_ljpx2_lt/sourceImages`
- 关键脚本：
  - `tools/u3d_export_source_images.py`
  - `tools/u3d_group_images_by_mode.py`
  - `tools/u3d_import_source_images.py`
  - `tools/u3d_manifest_crc.py`（新增）
  - `tools/u3d_sync_manifest_crc.py`（新增）

## 关键经验

### 1) 关卡映射必须来自资源配置，不要靠文件名
- 主线映射来源：`Game.Gameplay.Level.Addressable.Data.SequentialLevelDataBase`。
- 故事模式映射来源：`PackageManifest` 中 story 相关 level asset 顺序。
- 结论：关卡顺序与包关系应以配置资产为准，文件名只做辅助手段。

### 1.1) 本次核心卡点：图片名字和内容对不上（已定位根因）
- 现象：
  - NH1 等关卡中，分图文件名对应的角色与游戏内看到的角色不一致。
  - 进一步导致按分类目录重组看起来错误（如某目录混入其他类型角色）。
- 根因：
  - 导出时错误假设 `SpriteAtlas.m_PackedSpriteNamesToIndex` 与 `m_RenderDataMap` 同索引一一对应。
  - 实际上两者顺序可能不同；索引硬配会让 `spriteName -> textureRect` 错位。
  - 另外，Sprite 元数据可能来自共享包，像素来自关卡 Atlas 包，单包内难以还原完整关系。
- 修复：
  - 改为基于 `Sprite.m_RenderDataKey` 做映射，建立：
    - `atlasTag + spriteName -> renderKey`
    - `atlasTag + renderKey -> spriteName`
  - 用 `renderKey` 找到准确 `renderData(textureRect)` 后再裁图，消除名称错配。
  - 导出层统一用稳定标识：`imageKey = bundleHash#atlasIndex`。
- 验证：
  - 全量导出与重组后，关卡链路校验通过（配置 -> imageKey -> 分图）。
  - 不再出现“名字正确但图错”的批量问题。

### 2) 图片分组结构要服务“可编辑 + 可回写”
- 当前落地结构：
  - `Main_Level_N/`：主线关卡资源
  - `Story_N/`：故事模式资源
  - `Others/`：仅 Level 相关但不归入主线/故事的资源
  - 其他非 Level 图片保持在 `images/` 根目录
- 映射关系单独存文件（`image_mapping.json`、`mode_folder_mapping.json`），避免目录结构和写回逻辑耦合。

### 3) 回写必须做增量，不要全量重打
- 以 `sha256` 对比识别“被修改图片”。
- 只更新对应 `Texture2D(pathId)`，减少风险和耗时。
- 尺寸校验默认开启；尺寸不一致直接阻断（除非显式放行）。

### 4) CRC Mismatch 的根因与固定解法
- 现象：`Asset Bundle: CRC Mismatch. Provided xxxx, calculated yyyy`。
- 根因：`.unity3d` 被改后，`PackageManifest_*.bytes` 里的该 bundle CRC 仍是旧值。
- 解法：回写后自动同步 manifest CRC（仅同步本次改动涉及的 bundle hash）。
- 本次已将此步骤接入 `u3d_import_source_images.py`，默认自动执行。

## 标准操作命令（可复用）

### A. 回写前确认（dry-run）
```bash
python3 tools/u3d_import_source_images.py \
  --project-root webprojects/drgm_ljpx2_lt \
  --source-root sourceImages/drgm_ljpx2_lt \
  --dry-run
```

### B. 正式回写（自动同步 manifest CRC）
```bash
python3 tools/u3d_import_source_images.py \
  --project-root webprojects/drgm_ljpx2_lt \
  --source-root sourceImages/drgm_ljpx2_lt
```

### C. 单包 CRC 精准修复（应急）
```bash
python3 tools/u3d_sync_manifest_crc.py \
  --project-root webprojects/drgm_ljpx2_lt \
  --bundle-hash <32位hash>
```

## 验收标准
- 回写报告 `import_report.json` 中：
  - `changedTextures > 0`
  - `manifestCrcSync.errorCount == 0`
- 本地运行时：
  - 控制台无 `CRC Mismatch` 报错
  - 进入目标关卡无新增资源校验失败

## 风险与约束
- 不建议“全量”重算并写回所有 manifest CRC，风险高且会扩大改动面。
- 建议只同步“本次改动涉及的 bundle hash”。
- 若修改图片尺寸，可能触发运行时布局/UV/图集边界问题；默认保持尺寸一致。

## 当前项目入口（2026-03-11）
- 导出入口：`myprojects/drgm_ljpx2_lt/export.py`
- 回写入口：`myprojects/drgm_ljpx2_lt/writeback.py`
- 目标：只保留“导出 / 写回”两脚本入口，其他为内部实现细节。

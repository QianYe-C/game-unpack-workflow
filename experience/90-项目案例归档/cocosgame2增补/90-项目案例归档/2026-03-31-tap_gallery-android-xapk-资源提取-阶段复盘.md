> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-03-31-tap_gallery-android-xapk-资源提取-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-03-31 Tap Gallery Android XAPK 资源提取阶段复盘

## 阶段结论
- 已完成 `Tap Gallery_ Tap Game_0.21.0_APKPure.xapk.zip` 解包。
- 已完成 `Sprite` / `Texture2D` 导出，共导出图片对象 `2580` 个。
- 已完成 `Assets/Configs/*` 配置导出，共导出配置 `962` 份。
- 已完成关卡配置索引整理：
  - `LevelData`：`678` 份
  - `MonthLevelsData`：`4` 份
  - `LevelCollection`：`6` 份

## 项目目录
- 项目目录：`myprojects/tap_gallery`
- 原始包：`myprojects/apk/Tap Gallery_ Tap Game_0.21.0_APKPure.xapk.zip`
- 输入中间层：`myprojects/tap_gallery/input`
- 图片输出：`myprojects/tap_gallery/sourceImages`
- 配置输出：`myprojects/tap_gallery/sourceConfigs`

## 包体结构结论
- 这是标准 Android `split APK` / `XAPK` 结构：
  - `com.tap.gallery.apk`
  - `config.arm64_v8a.apk`
  - `UnityDataAssetPack.apk`
- 真正的 Unity 资源主体不在 `base.apk`，而在 `UnityDataAssetPack.apk`：
  - `assets/aa/Android/*.bundle`
  - `assets/aa/catalog.json`
  - `assets/aa/settings.json`
- `base.apk` 里的 `assets/bin/Data/data.unity3d` 主要是脚本与少量公共资源；关卡配置主体仍在 Addressables bundle。

## 关键经验

### 1. Android 版不能套 WebGL `PackageManifest` 思路
- 本包没有 WebGL 项目的 `StreamingAssets/WebGL/.../PackageManifest_*.bytes` 链路。
- 关卡与配置要直接从 Android Addressables bundle 里提取。
- 核心 bundle：
  - `maingamebundle_assets_all_*.bundle`
  - `monthlevelsdata_assets_all_*.bundle`
  - `configs_assets_all_*.bundle`

### 2. 关卡配置可直接从 `MonoBehaviour.typetree` 转 JSON
- `LevelData`、`MonthLevelsData`、`LevelCollection` 都能直接 `read_typetree()`。
- 导出时要裁掉 `serializationData.SerializedBytes` 这类超长二进制字段，只保留长度摘要，否则 JSON 噪声很大。
- `LevelData` 里的 `_mainSprite`、`_collectionsSprite` 等 `PPtr` 可解析到同 bundle 内的 `Sprite`，可进一步回链到导出的 PNG。

### 3. 贴图导出要同时支持 `Texture2D` 和 `Sprite`
- 只导 `Texture2D` 会漏掉大量可直接使用的切图。
- `Sprite.image` 可以直接拿到裁好的 PNG，适合关卡与活动图使用。
- 最终按：
  - `sourceImages/texture2d/`
  - `sourceImages/sprite/`
  分类落盘。

### 4. 遍历 `env.container` 时要跳过空 `PPtr`
- `scenes_scenes_all_*.bundle` 中存在空引用。
- 直接访问 `obj.type.name` 可能抛出：
  - `PPtr can't deref with m_PathID == 0!`
- 需要对 `obj.type` / `obj.path_id` 包一层 `try/except`，跳过空引用再继续遍历。

## 当前产物
- 脚本入口：`myprojects/tap_gallery/extract.py`
- 关卡索引：
  - `myprojects/tap_gallery/sourceConfigs/level_index.json`
  - `myprojects/tap_gallery/sourceConfigs/month_index.json`
  - `myprojects/tap_gallery/sourceConfigs/collection_index.json`
- 提取摘要：
  - `myprojects/tap_gallery/sourceConfigs/meta/extract_summary.json`
  - `myprojects/tap_gallery/logs/extract_summary_*.json`

## 复用命令
```bash
.venv/bin/python myprojects/tap_gallery/extract.py
```

## 风险与遗留
- 当前导出的是“可读配置 + PNG 贴图”工作区，不包含回写链路。
- 部分公共资源在 `data.unity3d` / `datapack.unity3d` 中无容器路径，只能按对象名与 `pathId` 导出。
- 若后续需要“关卡 -> 完整资源清单”强映射，还可继续基于 `level_index.json` 做二次整理。

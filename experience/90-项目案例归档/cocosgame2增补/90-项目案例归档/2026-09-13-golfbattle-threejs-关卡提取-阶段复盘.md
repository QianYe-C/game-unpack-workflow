> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-13-golfbattle-threejs-关卡提取-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-09-13 Golf Battle Three.js 关卡提取阶段复盘

## 目标
处理 `golfbattle` XAPK，取出全部关卡配置，并按 goingball/clientThreeJS 的资源协议在 `/Users/jiaojian/Documents/golf` 建立 Three.js 工程。

## 阻塞
APK 只有 77MB，本地 AssetBundle 仅 Forest 环境 + 教程关。其余主题标记为 `External`，不在包内。

## 根因
关卡表在 `sharedassets1` 的 `GameConfiguration` TextAsset，不在 IL2CPP 字符串里。几何按环境 scene + 球洞 scene 分 bundle，运行时从 `v1-cdn.golfbattle.miniclippt.com` 拉，postfix `gfx-4`，`latest.txt` 为 `233`。

## 动作
1. 按工作流建六大目录并解 XAPK。
2. Cpp2IL 导出 `HoleConfig` / `EnvironmentConfig` 字段。
3. UnityPy 导出 TextAsset，解析 224 条 holes + 9 条 env。
4. 导出 Forest 359 节点、教程关 191 节点、83 mesh。
5. 在 `/Users/jiaojian/Documents/golf` 建 Vite/Three/Rapier 工程与四份文档。

## 验证证据
- `sourceConfigs/hole-catalog.json`：holes=224，themes forest 40 / rocky 34 / snow 34 / jungle 31 / cliffs 31 / sakura 29 / lavaland 25。
- `sourceImages/three-assets/manifest.json`：meshes 83，prefabs 2。
- CDN `latest.txt` 与 S3 `golf-battle-live-configuration/v1/latest.txt` 均为 `233`。

## 遗留风险
- 远程 bundle 路径仍 403，不能把缺失当成关卡不存在。
- 教程关出生点/洞口/手感未对照原版。
- 进洞目前是距离阈值，不是完整 Magnet 触发链。

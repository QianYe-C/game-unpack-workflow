> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-loading启动场景与远程包预加载-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-09-28 Idlecat loading 启动场景与远程包预加载

## 目标

把原本承载完整游戏的 `loading.scene` 拆成轻量启动场景：启动阶段只显示“猫咪移动中..”和一只移动的小猫，游戏内容在资源包可用后进入 `game.scene`。其余鱼、枪、宠物和字体资源保留为可选包，后续接正式 CDN 时不需要再次改启动链。

## 实施

- 通过 Cocos MCP 将原重场景移动为 `assets/game.scene`，保留原 UUID 与节点资源；没有直接编辑 scene 序列化文件。
- 通过 Cocos MCP 新建 `assets/loading.scene`，只包含相机、纯色清屏、`LoadingCat`、系统字体 `LoadingText` 和 `BootLoader`。背景图和自定义字体没有放入启动场景。
- `NativeBootLoader.ts` 在构建运行时加载 `fish-module`、`gun-module`、`input-fonts`、`pet-module` 的 bundle；默认只加载 bundle 并继续进入游戏，避免首屏扫描全部资源。
- `?preload=1` 或节点上的 `preloadAssets=true` 才会逐包执行 `preloadDir`，并把预加载进度写到状态文字。可选包失败只记录警告，不阻塞进入游戏。
- 构建配置的起始场景为 `loading.scene`，场景清单同时包含 loading 与 game；`director.loadScene('game')` 负责完成切换。

## 验证

`cocos_scene validate_scene` 返回 `brokenCount=0`、`isValid=true`。调试 CLI 构建 `temp/douyin-cli/20260928-183714-cli.log` 成功，产物 236,397,844 字节，`invalidScriptErrors=[]`。随后用隔离的远程候选配置构建 `temp/douyin-cli/20260928-183759-remote-cli.log`：本地启动包估算 12,160,267 字节，远程包 218,660,397 字节，7 个 bundle 进入 `remote/`，无远程可执行文件，PNG/音频/字体/BIN 字节集合与调试基线一致。证据见工程内 loading-bootstrap-20260928.json（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/idlecat/idlecat/docs/evidence/loading-bootstrap-20260928.json`）。

## 边界

当前 `server` 仍为空，正式 CDN 上传、远程 HTTPS、真实抖音 SDK 和真机冷启动按需求延后；这轮只把资源包边界和启动逻辑预留好。默认启动只依赖一张小猫图和系统字体，完整包仍会随当前调试构建输出，接 CDN 后再切换 `mainBundleIsRemote`/bundle 远程配置。

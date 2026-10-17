# Bundle 远程化与迁移说明

## 使用说明（示例与通用边界）
- 文中 `retorm/`、Bundle 名称列表、查询参数均为示例。
- 实际项目可替换为自身目录名、包名与参数键。
- 重点是“运行时可配置远程源 + 本地回落 + 启动核心保留本地”的迁移思路。

## 目标

- 将业务 Bundle 调整为远程加载。
- 将远程 Bundle 统一迁移到本地 `retorm/` 目录。
- 保留启动核心 Bundle 在本地 `assets/`，保证首屏可启动。

## 已完成修改

### 1) 运行时远程配置接入

修改文件：`game.js`

- 增加默认远程 Bundle 列表（业务包）。
- 增加远程目录常量：`retorm`。
- 支持读取远程配置来源（按优先级）：
  1. 启动参数 `query`：`remoteServer` / `bundleServer` / `server`，`remoteBundles` / `bundles`
  2. 全局变量：`window.__REMOTE_BUNDLE_SERVER__` / `window.__REMOTE_BUNDLES__`
  3. 本地存储：`tt.getStorageSync('remoteServer'|'bundleServer')`、`tt.getStorageSync('remoteBundles'|'bundles')`
- 自动规范化远程地址：
  - 保证末尾 `/`
  - 保证末尾包含 `retorm/`
- 无远程地址时默认回落到本地：`retorm/`

### 2) Cocos 设置改为运行时注入

修改文件：`src/settings.b6e15.js`

- `remoteBundles: window.__REMOTE_BUNDLES__ || []`
- `server: window.__REMOTE_BUNDLE_SERVER__ || ""`

## Bundle 迁移结果

### 迁移到 `retorm/` 的 32 个 Bundle

`config`, `game`, `home`, `res`, `res_AngryBirds`, `res_ENightmare`, `res_GoldMiner`, `res_Jocker`, `res_Line`, `res_LuckyTD`, `res_Mine`, `res_MPBall2`, `res_MultiplayerPinball`, `res_PinballWar`, `res_Publlic`, `res_Report`, `res_RussianBlock`, `res_TT`, `res_ZCrossFire`, `res_ZombiesDieFirst`, `cfg_Cave1`, `cfg_Cave2`, `cfg_FindStage`, `cfg_Level1`, `cfg_Level2`, `cfg_Level3`, `cfg_Level4`, `cfg_Level5`, `cfg_Level6`, `cfg_Level7`, `cfg_NewStage`, `cfg_Train`

### `assets/` 当前保留（启动核心）

- `internal/`
- `load/`
- `main/`
- `resources/`

## 使用方式

### 本地 `retorm`（默认）

- 不传 `remoteServer` 时，自动走 `retorm/`。

### 外部 CDN

- 示例：`?remoteServer=https://cdn.example.com/&remoteBundles=game,home,res_ZombiesDieFirst,cfg_Train`
- 运行时会自动拼接到：`https://cdn.example.com/retorm/`

## 验收建议

1. 清缓存后冷启动，确认首屏正常。
2. 进入任一玩法（如 `res_ZombiesDieFirst`），确认远程 Bundle 拉取成功。
3. 检查控制台无 `config.*.json` / `import/*` / `native/*` 404。

> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-03-05-doomsdayroom_web-mobile1-tt-pack-size-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# doomsdayroom_web-mobile1 TT 包体瘦身阶段复盘

- 日期：2026-03-05
- 项目：`doomsdayroom_web-mobile1`
- 阶段：`TT 首包/总包体积门禁`
- 目标目录：`output/doomsdayroom_web-mobile1/tt`

## 1. 阶段目标与门禁
- 首包（不含分包）小于 4MB。
- 本地包总量（首包 + 分包）小于 30MB。
- 启动路径仅保证进入 `load` 场景，业务重资源走远程 CDN。

## 2. 阻塞现象与根因
- 原始结构中 `assets` 全量在本地（约 199MB），首包和总包均超限。
- `main` bundle 在主包内（约 2.8MB），导致首包无法压到 4MB 以下。
- `main.js` 为定制混淆版本，`assetManager.init` 未注入 `subpackages`，导致仅改目录不生效。

## 3. 最小修复动作
1. 分包化：
- `assets/main` -> `subpackages/main`（`index.js` 改名 `game.js`）
- `assets/home` -> `subpackages/home`（`index.js` 改名 `game.js`）
2. 远程化：
- 其余 30 个业务 bundle 迁移到 `output/doomsdayroom_web-mobile1/tt-cdn/retorm/`。
3. 配置同步：
- `game.json` 增加 `main/home` 分包声明。
- `src/settings.js` 设置 `subpackages`、`remoteBundles`、默认 `server`。
- `main.js` 补充 `assetManager.init` 的 `subpackages` 参数。
- `game.js` 增加运行时 CDN 覆盖能力（query/global/storage），默认本地 `http://127.0.0.1:8080/retorm/`。

## 4. 打通证据（门禁结果）
- 首包：`3.26 MB`（`first_package_bytes=3415874`）
- 本地总量（首包+分包）：`20.99 MB`（`total_local_bytes=22005471`）
- 远程目录体积：`179 MB`（`output/doomsdayroom_web-mobile1/tt-cdn`）

结论：
- 首包门禁（<4MB）通过。
- 本地总量门禁（<30MB）通过。
- 业务重资源已转远程目录，满足“首包仅启动 + 分包保留部分 + 其余走 CDN”。

## 5. 遗留风险与下一步
- 远程资源需在真机/开发者工具验证跨域、超时与降级行为。
- 正式上线前将默认 `server` 替换为真实 CDN 地址。
- 若后续仍需压缩“本地总量”，可继续把 `home` 从分包切换为远程 bundle。

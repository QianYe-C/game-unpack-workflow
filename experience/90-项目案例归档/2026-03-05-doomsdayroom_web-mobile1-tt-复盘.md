# doomsdayroom_web-mobile1 -> TT 分包改造总复盘

- 复盘日期：2026-03-05
- 项目：`doomsdayroom_web-mobile1`
- 目标平台：`TT`
- 输出目录：`output/doomsdayroom_web-mobile1/tt`

## 1. 输入与判型
- 输入 URL：`https://yzcdn.yuanzililiang.cn/DoomsdayRoom/Web/web-mobile1/`
- 判型结论：Cocos Creator 2.4 Web
- 使用模板：`templates/bytedance-mini-game-cc2.4`

## 2. 改造目标
- 首包（不含分包）控制在 4MB 内，仅保证启动到 `load` 场景。
- 本地总量（首包 + 分包）控制在 30MB 内。
- 部分资源保留分包，其余业务重资源走远程 CDN。

## 3. 核心问题与根因
- 问题 A：原始包体过大，首包/总包均超限。
  - 根因：`assets` 全量本地、`main` 在主包、运行时未正确注入分包配置。
- 问题 B：`tt.loadSubpackage ok` 后卡在 `loadBundle start home`，并出现 `remote/res/import` 批量超时。
  - 根因：网络链路问题（VPN/代理干扰），不是分包配置和资源缺失。

## 4. 最小改造动作
1. 分包化：
- `assets/main` -> `subpackages/main`（`index.js` 改为 `game.js`）
- `assets/home` -> `subpackages/home`（`index.js` 改为 `game.js`）
2. 远程化：
- 其余业务 bundle 迁移到 `output/doomsdayroom_web-mobile1/tt-cdn/remote`（兼容 `retorm` 软链）。
3. 配置与启动链路：
- 同步 `game.json` / `src/settings.js` / `game.js` 的 `subpackages`、`remoteBundles`、`server`。
- 分包加载回归模板链路：使用 `tt.loadSubpackage`，不强制本地 `require` 分包脚本。
4. 下载稳态增强（诊断与容错）：
- 增加分包与 bundle 关键日志。
- 增加下载超时、重试与并发调优。
5. 环境修复：
- 关闭 VPN/代理后重试。

## 5. 验证结果
- 包体门禁：
  - 首包：`3.26 MB`（< 4MB，通过）
  - 本地总量：`20.99 MB`（< 30MB，通过）
- 运行门禁：
  - 分包可成功加载（`tt.loadSubpackage ok`）。
  - 关闭 VPN/代理后，`home` 后续远程资源可正常拉取，卡点解除。

## 6. 关键经验
- 分包问题和远程下载问题必须拆开诊断，不能混为一个结论。
- “浏览器可访问”不等于“小游戏网络栈稳定可达”。
- 排障以“双端对账”为准：客户端报错 + 服务端是否收到同批请求。
- 若客户端大量超时但服务端无对应请求，优先排查 VPN/代理/网络策略。

## 7. 遗留风险与后续
1. 局域网 HTTP 仅适合本地调试，仍受网络环境影响。
2. 联调/提测切到公网 HTTPS CDN，避免策略差异。
3. 清理调试期临时日志，保留最小稳定参数并做弱网回归。

## 8. 关联阶段文档
- `experience/2026-03-05-doomsdayroom_web-mobile1-tt-pack-size-阶段复盘.md`
- `experience/2026-03-05-doomsdayroom_web-mobile1-tt-remote-download-阶段复盘.md`

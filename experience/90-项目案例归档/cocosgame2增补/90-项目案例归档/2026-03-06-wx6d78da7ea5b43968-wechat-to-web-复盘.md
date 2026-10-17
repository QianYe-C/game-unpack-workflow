> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-03-06-wx6d78da7ea5b43968-wechat-to-web-复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# wx6d78da7ea5b43968 微信小游戏包 -> Web 工程复盘

## 1. 目标与结论
- 目标：将 `input/wx6d78da7ea5b43968` 还原为可本地运行的 Cocos Web 工程。
- 结果：已在 `webprojects/wx6d78da7ea5b43968_restore` 跑通，Playwright 验证进入场景 `008_gc`，无 page error / console error。

## 2. 输入判型
- 引擎：`Cocos Creator 2.4.15`
- 包结构：主包 + 子包（`subpackages/loading`、`subpackages/scripts`）+ 远程 bundle 资源。
- 关键约束：微信包不是完整 web 构建产物，需补齐 web 运行期要求的目录/文件命名。

## 3. 关键问题与根因
1. `assets/internal/index.<ver>.js` / `assets/main/index.<ver>.js` 404  
   根因：仅有 `index.js`，缺少版本化入口文件名（`index.<ver>.js`）。
2. `require is not defined`（bundle `index*.js`）  
   根因：微信包产物中包含顶层 `require("@babel/runtime/...")`，浏览器直接脚本模式无 CommonJS `require`。
3. 看起来一直停在 Cocos loading  
   根因：场景实际已加载，但启动链路未按 web 模板处理 splash 隐藏逻辑，视觉上像“没进游戏”。
4. 资源偶发异常  
   根因：本地静态服务缓存导致旧资源命中，出现“修了但仍报旧错”。

## 4. 本次有效改造动作
1. 从小游戏包还原 web 目录
- 抽取主包/子包模块，映射到 web 目录：
  - `subpackages/loading/game.js -> assets/loading/index.js`
  - `subpackages/scripts/game.js -> assets/scripts/index.js`
- 还原 `main.*.js`、`src/settings.*.js`、`assets/*/index.js`。

2. 补齐版本化 bundle 入口
- 根据 `settings.bundleVers` 为每个 bundle 生成/对齐 `assets/<bundle>/index.<ver>.js`。
- 同步修正缺失 bundle 映射（本次移除不存在的 `008_1_roomGame` 条目）。

3. 全量补齐远程资源到本地
- `config` 抓取结果：`41/41` 成功（`_work/fetch_remote_configs.report.json`）。
- import/native 预抓结果：`4034/4034` 成功，`remote_missing=0`（`_work/prefetch.remote_bundles.report.json`）。
- 运行本地化模式：`remoteBundles=[]`、`subpackages=[]`、`server=''`（走本地 assets）。

4. 修复浏览器运行时模块问题
- 将 bundle 中顶层 Babel helper 的 `require(...)` 依赖改为内联 helper（`Array.includes`、`Object.values`、`typeof` 等），避免浏览器脚本模式报错。

5. 对齐 web 模板启动时序
- 在 `main.dd6da.js` 补齐模板式 `setLoadingDisplay()`。
- 使用 `cc.director.once(cc.Director.EVENT_AFTER_SCENE_LAUNCH, ...)` 在首场景启动后关闭 splash、恢复 canvas 可见。

6. 固化本地服务方式
- 使用 `http-server` 启动并禁缓存：
  - `http-server . -p 8080 -a 127.0.0.1 -c-1`

## 5. 验收证据
- Playwright 报告：`webprojects/wx6d78da7ea5b43968_restore/_work/playwright-headed-report.json`
  - `reachedInGame=true`
  - `reachedScene=008_gc`
  - `pageErrors=[]`
  - `consoleErrors=[]`

## 6. 可复用经验（微信包转 Web）
1. 先判定“是否真卡住”  
- 先看场景日志（`LoadScene/Success to load scene`）再看画面；可能是 splash 没关，不是场景没进。
2. 先修版本化入口，再查资源  
- `index.<ver>.js` 404 会直接阻断 bundle 加载，比单个资源缺失更优先。
3. 小程序模块产物不等于浏览器模块产物  
- 出现 `require is not defined` 时，优先检查 bundle 顶层 helper 注入方式。
4. 本地联调必须禁缓存  
- 避免静态服务缓存导致“假回归”。
5. 验收要双轨  
- `控制台无阻断错误` + `画面已进入目标场景`，两者都要满足。

## 7. 流程固化（后续默认）
- 输入默认形态：`input/<wxid>/`，目录内可能包含多个 `.wxapkg`。
- 固定先执行离线批量解包工具，再进入“转 webproject”：
  - `tools/wxapkg_batch_unpack.js`
- 不再依赖在线下载临时解包器，避免环境漂移。
- Windows 与 macOS/Linux 统一同一套脚本，仅命令入口不同（`node` / `.cmd` 包装）。

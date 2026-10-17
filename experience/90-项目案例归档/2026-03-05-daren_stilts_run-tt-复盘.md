# daren_stilts_run -> TT（Unity WebGL）阶段复盘

## 1. 背景
- 项目：`daren_stilts_run`
- 目标：先保证 TT 包可启动，再逐步优化包体与稳定性。
- 关键报错：`read may cause OOM (66549485 B)`，触发点为本地 `readFile` 读取 `data-package/*.br`。

## 2. 关键结论
- 本地大 `.br` 读取可能被 TT 平台 OOM 防护拦截，报错发生在解压前。
- 远程可达不等于稳定进入游戏；“下载成功”后仍可能卡在解压/内存阶段。
- `TT_STAGE` 事件顺序不保证严格递增（Data/WASM 并行），出现 `0 -> 3 -> 1` 可接受。
- 真正异常判据：`[TT_REMOTE] ... handoff` 后长期没有 `TT_STAGE 5:readAssets` / `6:prepareGame`。

## 3. 当前实现（已冻结）
- 文件：`output/daren_stilts_run/tt/game.js`
- 已做：
  - 统一 `webgl.framework.js` 导出到 `unityNamespace.UnityModule`（修复模块类型不匹配）。
  - 拦截 data `.br` 的 `readFile`，改为 `tt.request(arraybuffer)` 远程读取（300s 超时）。
  - 远程读取成功后按 TT 回调契约回传（`success + complete`，`errMsg: readFile:ok`）。
  - 读取失败回退本地 `readFile`。
  - data/wasm/StreamingAssets 分包加载走 bypass（`tt.loadSubpackage` 直 success）。
  - 增加 `TT_REMOTE` / `TT_STAGE` 诊断日志。

## 4. CDN 与联调经验
- 联调地址（示例）：`http://192.168.110.45:8080/remote/...`
- 本地静态服务可用不代表手机链路稳定；VPN/代理会显著影响超时表现。
- 需要用服务端访问日志确认“请求是否到达”，不要只看客户端报错。

## 5. 后续路线（优先级）
1. 稳定性优先：保持当前实现，持续回归不同网络环境。
2. 若仍偶发卡在 handoff 后：评估“远程未压缩 data”方案，绕开 `.br` 解压峰值。
3. 长期方案：回 Unity 源工程做资源级拆分与远程化（Addressables/AssetBundle）。

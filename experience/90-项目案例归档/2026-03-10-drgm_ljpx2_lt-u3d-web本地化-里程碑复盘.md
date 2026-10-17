# 2026-03-10 DRGM（ljpx2_lt）U3D Web 本地化里程碑复盘

## 里程碑结论
- 已完成：线上 URL 工程可在本地 Web 工程运行。
- 已完成：资源从“逐个 404 修复”升级为“全量预下载”流程。
- 已完成：`/mini-data/sys/nowTime` 改为本地时间响应。
- 已完成：去除移动端启动提示 `WebGL builds are not supported on mobile devices.`。

## 本次关键改动
- 项目目录：`/Users/jiaojian/Documents/localweb/webprojects/drgm_ljpx2_lt`
- 关键文件：
  - `index.html`
  - `prefetch_all_bundles.sh`
  - `StreamingAssets/WebGL/ljpx2_lt/all_hashes_from_manifest.txt`

### 1) 启动与接口本地化
- 在 `index.html` 中拦截 `/mini-data/sys/nowTime`（XHR + fetch）。
- 本地返回 JSON（`Date.now()`），避免依赖失效的密钥/时间服务。

### 2) 资源 404 的工程化处理
- 识别到资源系统为 YooAsset（manifest 头：`OOY 1.5.2`）。
- 从 `PackageManifest_ljpx2_lt_1772087400.bytes` 提取全量 hash（1474 个）。
- 新增脚本 `prefetch_all_bundles.sh`：
  - 自动生成 hash 清单；
  - 检测本地已存在资源；
  - 并发下载缺失 `hash.unity3d`；
  - 失败自动重试；
  - 最终输出完整性结果。
- 执行后本地校验：`missing=0`，`*.unity3d = 1474`。

### 3) WebGL 默认移动端提示去除
- 删除 `index.html` 移动分支中的 `unityShowBanner('WebGL builds are not supported on mobile devices.')` 调用。
- 保留移动端 viewport 与 canvas 样式逻辑，不影响主流程。

## 经验与方法
- 不要逐个修资源 404，优先做“全量清单 -> 批量补齐”。
- 有 manifest 时，最稳是离线提取并落库（hash 清单文件化）。
- 接口替换尽量在入口统一拦截（XHR + fetch），避免散改业务代码。
- 本地路径结构必须和线上保持一致，切关时最容易暴露路径问题。
- 并发下载需要重试机制；公网源站会出现偶发 SSL 超时。

## 后续建议
- 将远程 fallback 改为可配置开关（开发开、发布关）。
- 把 `prefetch_all_bundles.sh` 接入一键启动流程（先校验后启动 httpserver）。
- 新版本发包时，固定执行：更新 manifest -> 预下载 -> 完整性校验 -> 启动回归。

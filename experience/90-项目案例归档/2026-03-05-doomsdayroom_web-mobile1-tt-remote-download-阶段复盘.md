# 2026-03-05 doomsdayroom_web-mobile1 TT 远程下载链路阶段复盘

## 阶段目标与门禁条件
- 目标：首包仅保留 load 场景，home 与其依赖可通过分包 + 远程资源正常加载。
- 门禁：日志可走过 `loadBundle start home`，且不再被批量 `remote/res/import/*.json` 超时阻断。

## 阻塞现象与根因
- 现象：`tt.loadSubpackage home` 已成功，但随后停在 `loadBundle start home`，并循环出现一批 `remote/res/import` 请求超时。
- 关键排查：对照本地静态服务日志，客户端报超时时服务端并未稳定收到同批请求。
- 根因：网络链路问题（VPN/代理干扰），不是分包配置和资源文件缺失。

## 最小修复动作
- 保持分包按模板链路执行：走 `tt.loadSubpackage`，不再强制本地 `require` 分包脚本。
- 增加运行时诊断：分包开始/成功/失败、`loadBundle` 超时悬挂提示。
- 下载侧稳态补丁：提升下载超时、增加重试、调整并发为更保守值。
- 环境侧修复：关闭 VPN/代理后重试。

## 打通证据
- 出现 `tt.loadSubpackage ok home`。
- 关闭 VPN/代理后，远程加载恢复，卡点消失。
- 服务端日志可与客户端请求对上（至少可见对应 `remote/res/import` 请求）。

## 当前遗留风险与下一阶段计划
- 风险：局域网 HTTP 作为临时 CDN，仍受网络环境和代理策略影响。
- 计划：
  1. 联调与提测切换到公网 HTTPS CDN。
  2. 收敛调试日志，保留必要稳定性参数。
  3. 做一轮弱网回归，确认首包/分包/远程三段链路稳定。

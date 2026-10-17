> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-time-provider-bridge.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 时间校时提供器桥接

日期：2026-09-28

任务系统在检测到设备跳变或应用恢复后，原先只能发出 `time-check-requested`，没有统一消费入口。本轮新增 `NativeTimeBridge` 并在 `GameEconomy` 注册监听：只有平台明确注册的 provider 才能返回 UTC；没有 provider 时不发起隐式请求、不用设备时间替代，也不通过 GM 参数伪造成功。

提供器回调带取消句柄和代际门禁，覆盖同步完成、异步取消、无效时间、提供器替换和销毁时清理。同步完成发生在返回取消句柄前时，不会残留失效句柄阻塞下一次校时。

验证：`verify_time_transport.mjs`、`verify_time_rules.mjs`、`verify_mission_transaction.mjs`、`verify_mission_gameplay_events.mjs`、`verify_mission_ui_rules.mjs` 和资产范围 TypeScript 检查均通过；CLI `20260928-164837` 成功，脚本错误为 0。

限制：真实抖音 SDK/服务仍需在宿主侧调用 `registerNativeTimeProvider`，本轮没有伪造网络成功。真实广告、支付、CDN 分包和真机回归仍未完成。

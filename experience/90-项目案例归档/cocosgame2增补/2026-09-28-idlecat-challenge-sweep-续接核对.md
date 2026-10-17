> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-challenge-sweep-续接核对.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 挑战扫荡续接核对

日期：2026-09-28

## 结论

挑战付费扫荡实现已存在，不再是“缺失 sweepRefresh 分支”的待办。扫荡规则、三只活动猫战力、30+90/自动120奖励、逐关推进、写盘失败回滚、广告回调令牌、刷新恢复以及普通胜利与扫荡互斥均通过现有回归。

## 验证

- `node tools/migration/verify_speedrun_sweep.mjs`
- `node tools/migration/verify_speedrun_sweep_transaction.mjs`
- `node tools/migration/verify_speedrun_victory_transaction.mjs`

三项均通过；事务测试覆盖重复点击、过期回调、取消/重试、存档失败和待结算恢复。

## 发现与边界

挑战字体的两项 UV 验证当前不能直接作为产品失败结论。旧原版快照来自 2026-09-26，现行 Noto Sans SC 资产布局来自 2026-09-27，两个动态字体图集的字符坐标不同，因此现有快照与当前资产不能做逐 UV 比较。没有修改运行时代码或字体资产，下一步应在同一字体资产版本下重新采集原版快照，再继续像素级文字验收。

真实广告/支付 SDK、正式 CDN 分包、真机冷启动和全量跨模块视觉仍按总状态文档列为未完成。

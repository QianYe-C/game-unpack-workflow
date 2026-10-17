> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-challenge-font-atlas-核对.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 挑战字体动态图集核对（2026-09-28）

## 结论

原版挑战面板的中文轮廓、纯中文和 Mplus 数字并非共用一个运行时字体对象。Frida 只读采集确认三组 font pointer 与图集尺寸分别为 2048×2048（padding 12）、2048×2048（padding 9）和 1024×1024（padding 25）。同一字形在不同运行时重排后绝对 UV 会变化，因此不能把当前工程 atlas 的 UV 与旧快照逐点相等当成视觉验收条件。

当前工程的挑战开始与失败/结算核心文字已按原版位置、字形区域宽高、padding/字体指标回归，误差在门槛内通过；没有修改产品字体图集或运行时代码。

## 验证

- `node tools/migration/verify_challenge_start_typography.mjs`：5 个核心标签通过，最大位置误差约 `0.0000816`。
- `node tools/migration/verify_challenge_typography.mjs`：5 个失败/结算标签通过，最大位置误差约 `0.0000855`。
- `verify_speedrun_sweep.mjs`、`verify_time_transport.mjs`、`verify_mission_transaction.mjs` 同轮回归通过。
- 证据：atlas-pointer-audit.json（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/idlecat/idlecat/docs/evidence/challenge-typography-20260928/atlas-pointer-audit.json`）。

## 边界

`atlasComparable=false` 是有意的验收结果：运行时动态图集的绝对位置不跨实例比较。若要做最终像素验收，需要在同一平台、同一字体 provider 和同一渲染链下重新截图；这不应通过手工改 UV 解决。真实抖音 provider、真机和最终像素回归仍待平台接入。

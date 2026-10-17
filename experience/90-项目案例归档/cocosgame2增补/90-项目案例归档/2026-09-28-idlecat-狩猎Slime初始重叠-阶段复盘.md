> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-狩猎Slime初始重叠-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-09-28 Idlecat 狩猎 Slime 初始重叠阶段复盘

## 目标

还原 Slime 粒子出生时与地面或墙体重叠的法线、穿透推出和剩余时间步积分，同时不让普通粒子每帧付出第二次物理查询。

## 动作

在 `NativeTreeDeathParticles` 中保留公开 `sweepSphereClosest` 作为第一道查询。只有返回 `distance===0` 时，才通过 Creator 3.8.8 的内部 `sweepSingle` 以 `POSITION|NORMAL|MTD` 取得穿透深度和几何法线；查询不可用时回退原分支。重叠分支使用原版反弹后速度、穿透推出和完整剩余步积分，零法向速度不做除法。该逻辑只对已测 `Slime`/`measuredMotion` 生效，不修改全局 PhysicsSystem。

## 验证

真实 Creator PhysX WASM 回放 60 个狩猎重叠样本，其中 10 个零法向墙面样本：最大位置误差 `7.3349256e-6`，速度误差 `3.1966491e-7`。普通飞行和正向接触没有额外 MTD 查询；运行时报告见 overlap-runtime-verification.json（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/idlecat/idlecat/docs/evidence/hunt-slime-physics-20260928/overlap-runtime-verification.json`）。自由运动/出生/斜面/低速回归和脚本检查继续通过。

## 边界

样本覆盖单盒体地面、墙体和已采集的 Slime 参数，不代表棱角、复合碰撞体、网格、Unity 随机流、最终像素或真机帧耗已经完成；这些继续作为狩猎模块后续门禁。

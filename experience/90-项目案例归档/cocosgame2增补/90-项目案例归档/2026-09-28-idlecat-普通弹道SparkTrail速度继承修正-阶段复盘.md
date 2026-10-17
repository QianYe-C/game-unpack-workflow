> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-普通弹道SparkTrail速度继承修正-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 普通弹道 SparkTrail 速度继承修正

日期：2026-09-28

## 目标

调查普通弹道“碎粒子偏多/拖尾形态不一致”的静态参数差异，保持原版水滴主体和 SparkTrail 的层级、距离发射和随机行为边界。

## 根因

`assets/source-data/world/NormalBulletParticle.json` 的 SparkTrail 渲染器速度继承为 `0.05`，Cocos 预制体曾保存为 `0.2`。这会放大拉伸拖尾中的速度贡献，使粒子尾部视觉比原版更长、更碎。形状映射不是问题：Unity Sphere=0 已正确映射为 Cocos Sphere=3，体积发射、半径和继承速度范围也一致。

## 动作

通过已有 `NativeBgm.patchNormalRendererExplicit` 编辑器方法，经 Cocos MCP `cocos_scene.execute_method` 保存 `db://assets/prefabs/world/0_Normal.prefab`，将 SparkTrail `velocityScale` 恢复到 `0.05`。同时把构建器的验证条件扩展为检查 SparkTrail 的 renderMode、velocityScale、lengthScale，防止后续重建回归。没有直接写 prefab，也没有启动编辑器预览。

## 验证证据

- SparkTrail 23 项静态对照（历史引用，项目文件未随包提供：`../../../../idlecat/idlecat/docs/evidence/normal-bullet-glow-20260928/sparktrail-audit.json`）
- 修正说明与命令记录（历史引用，项目文件未随包提供：`../../../../idlecat/idlecat/docs/evidence/normal-bullet-glow-20260928/resolution.md`）
- Cocos `cocos_prefab validate`：4 节点、135 组件、无问题；
- Cocos `cocos_scene validate_scene`：0 断裂引用；
- TypeScript 检查通过；
- `python3 tools/build/build_douyin.py` 成功，产物 291,501,846 bytes。

## 遗留风险

静态参数通过不等于随机流、逐帧发射计数和最终像素完全一致；下一步应在非编辑器构建中做同输入的逐帧 A/B。原始包体预算仍需继续分包，不能把本次修正当作包体问题的解决。

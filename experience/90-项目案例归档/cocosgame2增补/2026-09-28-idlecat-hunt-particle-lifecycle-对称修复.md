> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-hunt-particle-lifecycle-对称修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 狩猎/矿山全局粒子生命周期对称修复（2026-09-28）

原版证据显示：地图关闭后全局粒子发射器仍保持 active，存活粒子继续自然衰减约 1.283 秒；移植版的绘制桥在 UI 提交时会调用 ParticleSystem 的 `_detachFromScene`，原实现没有在绘制节点禁用时恢复模型，可能让切出地图后的全局模拟冻结。

本轮只改 `assets/scripts/NativeParticleDrawSlot.ts`：记录 UI 提交造成的 detach，在绘制槽 disable、enable 和 destroy 边界检测模型是否脱离场景并调用原生 `_attachToScene`。没有复制粒子池、没有逐帧扫描隐藏对象、没有手工重复 simulate，模拟仍由原 ParticleSystem 单实例负责。

验证通过：

- `verify_particle_draw_slot.mjs`：编辑器路径保持 inert；单模型提交保持；disable/enable 两次 attach 对称性通过。
- `verify_hunt_particle_depth.mjs`：深度排序 534 个原生坐标，中心最大误差 `0.0000042915`，隐藏池读取 0。
- `verify_hunt_particle_lifecycle.py`：原版跨地图存活/自然衰减证据仍通过；它不冒充移植版像素验收。
- `verify_mine_particle_collisions.mjs` 与 TypeScript 检查通过。
- Cocos MCP 刷新脚本资源后，CLI 构建成功：`20260928-170619-cli.log`，脚本错误 0，产物 236,381,278 字节；产物 PNG 70–90 质量压缩仍生效。

边界：尚未启动编辑器预览，也没有同输入 MuMu/浏览器跨模式残留粒子的像素采样，因此这项修复完成的是生命周期契约；最终视觉、真实 SDK/CDN/真机仍待后续平台阶段。

> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-27-idlecat-raid-runtime-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 突袭运行阶段复盘

## 2026-09-27 14:28 突袭实际回合打通

- 已在独立profile=raid、state=keep档跑满60秒：Lv.9、奖励225，结算无浏览器错误；点击确定后正常返回主线地图和升级栏。
- 原版Reward_Panel_Reload(2b57578)的两项成绩共用Lv.{0}。此前错误填入Score/整段中文触发Mplus缺字，已修正；HUD HighScore_Reload(2b56570)独立显示本周最佳。原始字符串GOT/ScriptString证据 temp/raid-label-formats.json。HUD局部<size=45>仍待精确几何支持。
- 12个fill的原始颜色通过MCP应用到scene/prefab与MaskGraphic。临时InstallRaidVisuals/InstallRaidModule组件和assets脚本均已通过MCP清理，tools/editor保留。
- CLI 20260927-142747 success=true、sourceUnchanged=true、22.48秒。源摘要59e4fb52dd0fa5ca036eaddefbb48506c162de905c6436a22300f4c893ff3f3b；1228文件输出镜像一致。证据 docs/evidence/raid-runtime-20260927.json，源日志 logs/raid-runtime-20260927-142747。
- MuMu最终视觉仍受Mac锁屏限制，不能称完整1:1。原始PortalDust(1253/67073)和GibletExplodeDirt(22246/71656)已读取完整粒子模块到temp/raid-fx-raw.json：前者循环30/s、圆形63；后者50粒一次、Donut形状、碰撞。Raid_Boss.Die_Reload并不直接调用粒子播放，不能凭节点名猜测每条血都播放。真实触发/形状/碰撞需继续对照后接入，避免又增加错误碎粒子。
- 无构建进程、无临时安装组件。总目标active，真实SDK、混合字号、原特效和原版/抖音视觉回归仍未完成。

验收：使用独立profile=raid&state=keep&unlock=all&ui=raid，首次重置加raidreset=1；正式验收保留档时移除此项。用户主档不受影响。

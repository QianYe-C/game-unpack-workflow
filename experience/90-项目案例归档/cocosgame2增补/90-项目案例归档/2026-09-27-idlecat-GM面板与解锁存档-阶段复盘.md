> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-27-idlecat-GM面板与解锁存档-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# GM面板与解锁存档阶段复盘

重组日期：2026-09-27。

目标：修复空 GM，给出持续验收入口、资源和真实解锁进度。
阻塞与根因：导入的Cheat_Panel缺背景sprite，原调试表单无行为；原GM只改变当前关卡，最高关卡未同步，存档门槛仍可能锁住。
动作：通过MCP序列化scene/prefab的23按钮面板，沿用正式控制器路由；补资源、解锁、关闭与错误反馈；同步最高关卡并避免回写降低；无编辑器Run/Preview/GUI Build。
证据：主工程docs/evidence/gm-panel-20260927.json、verify_gm_panel.mjs、verify_mission_gameplay_events.mjs、任务事务测试、tsc；浏览器GM及武器路由通过。CLI122018成功，sourceUnchanged=true；归档包SHA f4d8714adc2b7c482dd1846dbfc0832a88f152605377966baf03599aceb387a6。
风险：GM入口显示不代表每个模块已经1:1完成；本次没有重复抖音模拟器验收，任务模块字体视觉/SDK/校时还待续。
复用方法：同时审计可见节点、按钮事件、存档门槛与旧控制器持有状态，分别做视觉点击和保存重载验证。

## 2026-09-27 用户精简要求覆盖初版
GM只保留货币增加、挑战和主线进度，6按钮3输入框。EditBox需绑定backgroundImage，文本节点锚点(0,1)，不能只给同节点Sprite赋图，否则EditBox初始化覆盖背景、文字错位。挑战字段SpeedRun_Stage_Now须加入保存白名单；三项操作先保存再改运行状态，主线修改保留最高记录且刷新地图。URL采用state=keep，避免显式固定参数覆盖GM编辑。浏览器验证钻石100000→100001、挑战保存2后恢复1；最新123557 CLI通过。证据gm-panel-simple-20260927.json。

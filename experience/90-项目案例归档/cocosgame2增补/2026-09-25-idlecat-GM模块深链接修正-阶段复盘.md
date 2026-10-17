> 归档来源：`cocosgame2/experience/2026-09-25-idlecat-GM模块深链接修正-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。


# GM 模块深链接修正

`NativeGMController` 的 URL 路由最初把 SafeArea 根误当成内容面板，鱼、宠物、冒险链接只显示首页。复核正式 `loading.scene` 后，改为保留 SafeArea 根、激活其已有首个内容子节点，并补齐设置/武器等真实节点名。编辑器重载刷新脚本缓存后，`?gm=1&unlock=all&ui=setting|gun|fish|pet|adventure` 均能从冷启动打开对应原生界面，未创建运行时节点。证据：`idlecat/docs/evidence/gm-route-modules-20260925.json`。

> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-adventure-map-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat Adventure 地图项遮罩修复

Adventure 地图弹窗的六个原版隐藏 Mask（`15457/4032/4033/4034/4035/1038`）在移植资源中仍带 SpriteStencil。通过 Cocos MCP 同步 `Adventure_manager.prefab` 与 `loading.scene`，全部恢复为 Mask type 0 并移除 Sprite；Mask 的 Graphics 由引擎用于矩形裁切，不绘制原图。Adventure 规则、事务、奖励动画和场景断链验证通过，未启动编辑器预览。

> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-contents-raid-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat Raid 共享 Contents Viewport 遮罩修复

Raid 原版 `Viewport__u634` 的 `m_ShowMaskGraphic=0` 在移植中仍有 SpriteStencil。通过 Cocos MCP 同步 `Contents_UI.prefab` 与 `loading.scene`，改为 Mask type 0 并移除 Sprite；其余可见 Raid fill/mask 保持不变。Raid 模式、规则、事务和场景断链验证通过，CLI 构建成功，未启动编辑器预览。

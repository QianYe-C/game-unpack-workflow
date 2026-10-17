> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-contents-hunt-boss-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat Hunt/Boss 共享 Contents Viewport 遮罩修复

Hunt 的 `Viewport__u832` 与 Boss 的 `Viewport__u752` 在共享 `Contents_UI` 中残留 SpriteStencil/NativeSlicedFill，但原版对应 `m_ShowMaskGraphic=0`。通过 Cocos MCP 同步 prefab 与 `loading.scene`：Mask 改为 type 0，移除 Sprite/NativeSlicedFill；可见内容遮罩未改。

Hunt、Boss、Raid 规则/模式/事务回归通过，场景断链0，CLI 构建成功，未启动编辑器预览。

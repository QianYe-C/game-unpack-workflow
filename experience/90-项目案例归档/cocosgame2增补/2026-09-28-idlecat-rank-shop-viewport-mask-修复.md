> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-rank-shop-viewport-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 排行榜/商店隐藏 Viewport 遮罩修复

原版 `m_ShowMaskGraphic=0` 的排行榜 `Viewport__u774`、商店周常 `Viewport__u110` 在移植中残留 SpriteStencil/NativeSlicedFill；商店另一个 `Viewport__u6482` 还缺少 Mask。通过 Cocos MCP 同步对应 prefab 与 `loading.scene`：隐藏 viewport 统一使用 Mask type 0、移除 Sprite/NativeSlicedFill，6482 补回 Mask。可见内容列表、武器列表和业务逻辑未改。

排行榜规则、商店规则/交付/交易/武器挂载以及场景断链验证通过；CLI 构建成功，未启动编辑器预览。

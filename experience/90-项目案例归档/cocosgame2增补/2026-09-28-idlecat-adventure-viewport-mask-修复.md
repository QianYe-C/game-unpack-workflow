> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-adventure-viewport-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat Adventure 隐藏 Viewport 遮罩修复

Adventure 的遗物列表 `Viewport__u136` 与原版隐藏 Mask 语义不一致，移植资源残留 SpriteStencil 和 NativeSlicedFill。通过 Cocos MCP 同步 prefab 与 loading.scene：Mask 改为 `GRAPHICS_RECT(0)`，移除 Sprite/NativeSlicedFill；可见遗物卡和奖励逻辑未改。Adventure 规则、耐久提交和奖励动画测试通过，场景断链0。CLI 构建和浏览器同输入视觉回归仍需后续收口，未启动编辑器预览。

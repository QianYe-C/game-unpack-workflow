> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-skin-viewport-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 皮肤列表 Viewport 遮罩修复

## 现象
皮肤列表的 `Viewport__u19` 保留了 SpriteStencil 与 NativeSlicedFill，和原版只负责裁切的 viewport 语义不一致。资源门禁因此检测到隐藏 viewport 仍有可见 Sprite，可能造成滚动列表边界出现额外底色或遮挡。

## 处理
通过 Cocos MCP 同步修改 `Skin_manager.prefab` 和 `loading.scene`：将 Mask 改为 `GRAPHICS_RECT(0)`，移除 Sprite 和仅服务于该可见填充的 NativeSlicedFill。25 张皮肤卡、资源引用、按钮事件和其它可见遮罩未改动。

## 验证
`verify_skin_module.mjs` 111 项通过；随后需完成 CLI 构建和浏览器同输入回归。未启动编辑器预览。

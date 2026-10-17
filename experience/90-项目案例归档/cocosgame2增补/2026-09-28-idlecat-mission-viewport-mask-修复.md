> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-mission-viewport-mask-修复.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 任务隐藏 Viewport 遮罩修复

## 现象
任务面板的两个原版隐藏 viewport 在移植资源中出现了裁切渲染器漂移：一个仍保留 Sprite + SpriteStencil，另一个缺少 Mask 但保留可见 Sprite/NativeSlicedFill。这会让滚动列表边界、文本和奖励层出现异常叠加。

## 处理
通过 Cocos MCP 修改 `Mission_maanger.prefab` 与 `loading.scene`，将 `Viewport__u1389`、`Viewport__u1915` 恢复为原版隐藏 viewport 语义：Mask type=GRAPHICS_RECT(0)，移除 Sprite；第二个节点同时移除仅用于可见填充的 NativeSlicedFill。可见任务填充遮罩、hatch 子节点、奖励图标和原始粒子参数未改动。没有直接编辑 scene/prefab，也没有启动编辑器预览。

## 验证
`verify_mission_assets.mjs`、任务 culling、gameplay events、rules、transaction、ui rules 均通过；Cocos 场景断链验证 `brokenCount=0`。下一步构建后仍需浏览器同输入视觉回归；真实抖音 provider、真机和最终像素验收不在本次证据范围。

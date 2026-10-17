> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-Cocos线性渲染目标验证-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Cocos 线性渲染目标验证

## 目标

为还原原版粒子在 sRGB 目标上的 Linear 透明混合，确认 Cocos Creator 3.8.8 是否能创建保留 `SRGB8_A8` 的世界渲染目标，并且不破坏现有相机和遮挡链。

## 根因

Cocos 的 `RenderTexture._initWindow` 会把传入 `RenderPassInfo` 的颜色附件格式改为 `root.device.swapchainFormat`。在当前 WebGL2 交换链中该格式是 `RGBA8`，所以单纯 `RenderTexture.reset({ passInfo: SRGB8_A8 })` 实际仍是普通 RGBA8，不能提供原版的硬件线性混合。

## 动作

建立只读、隔离的 Cocos GFX 浏览器探针，不加载游戏场景、不运行编辑器预览、不修改 Prefab/Scene/Meta/存档。通过公开的 `RenderTexture.window` 取得窗口，在同一窗口上重新初始化 `SRGB8_A8` RenderPass，并检查缩放后的底层颜色纹理格式。

## 证据

探针输出记录：默认初始化为 `RGBA8`；显式 RenderWindow 初始化后为 `SRGB8_A8`；resize 后仍为 `SRGB8_A8`；清理无错误。原版六张受控像素图仍是判断粒子混合的依据，本探针只证明目标格式能力，未将独立三角形绘制冒充游戏像素通过。

证据：`idlecat/docs/evidence/cocos-linear-target-20260928/verification.md`。

## 当前结论

后续世界相机接入必须使用显式 RenderWindow 初始化或等价引擎适配层，不能调用普通 RenderTexture reset 代替。接入前仍需对主世界相机、特效相机、UI 相机、呈现四边形、清屏/遮挡、尺寸变化和总帧耗时做实际验证；因此本阶段没有改生产相机目标，也没有宣称视觉完成。

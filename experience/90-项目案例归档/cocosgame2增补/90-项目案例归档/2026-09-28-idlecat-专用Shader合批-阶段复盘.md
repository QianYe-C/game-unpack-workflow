> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-专用Shader合批-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# idlecat 专用 Shader 合批阶段复盘

用户要求 Draw Call 降至 50 以内，保留原版效果与排序。本轮围绕实际运行批次实现，不用隐藏战斗效果达到数字。

## 方法

1. UI 使用 8 纹理槽专用 Shader，将图片、原 SDF 字体、填充公式和矩形裁切参数写入顶点。原 assembler 继续产出几何；不重排提交顺序。
2. 粒子在实际 WebPipeline 队列构建后合并实例流，保留 billboard/stretched billboard 公式、颜色原始位、发射器缩放、原始排序。RGBA8 不透明目标用预乘混合统一 alpha/additive；未知路径回退。
3. 9 处经过源纹理/几何验证的冗余模板改为等价 Shader 裁切；任务屏幕外条目按原视口自身矩形剔除，原圆角/条纹仍保留。

## 容易踩的坑

- `Pass.getHandle()` 缺失时返回 0，不能只判断 undefined。
- 纹理槽 0 是有效槽；误写 <=0 会重复占槽并导致拆批。
- Canvas.onEnable 早于子 Mask.onLoad，过早关闭会被 Mask 重建；等 activeInHierarchy 后在绘制前处理。
- 扩展顶点格式需要独立足够大的顶点 arena，否则 512 KB 默认缓冲导致碎片。
- 3.8.8 当前项目为 WebPipeline，旧 ForwardPipeline renderQueue 钩子不会触发。
- `Material.overridePipelineStates` 不支持资产；必须使用 `renderer.MaterialInstance`。cc 顶层没有可直接构造的 MaterialInstance 导出。
- `getBoundingBoxToWorld()` 包含子节点，不可用作 ScrollView 视口边界；使用其自身 UITransform。
- 统计覆盖连续 840 帧与密集射击，不能用单张静止截图。日志跨刷新保留，必须核对时间。

## 验证与边界

2048 组真实 GPU 混合对照无像素误差；顶点、索引、槽复用、实例数、边界裁切、回收测试和离线 TypeScript 检查通过。任务横纵滚动、领奖重排、关闭重开已验证。小武器装备/库存区域逐像素相同；完整武器存在少量栅格舍入差异，未夸大为全图完全相同。

最终数值、CLI 源指纹、平台结果与归档位置见主工程 `doc/专用Shader合批与50DC验收.md`。本阶段不代表全项目移植完成，也不能替代包体/纹理内存、分包或真实平台服务验收。

最终连续840帧：浏览器密集战斗14–40、武器17–29、鱼15–41、宠物16–28、任务37–42、挑战15–36；抖音主线15–27、长屏任务45–50。CLI20260928-015725，源SHA80bf50d559ac51a58d0429233f30922c282c32ee10e0f72c19e5c5237b055a5d；归档logs/unified-batching-20260928-015725。长屏任务余量小，真机与其他状态不作全覆盖保证。

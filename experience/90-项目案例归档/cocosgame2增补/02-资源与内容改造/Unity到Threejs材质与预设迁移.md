> 归档来源：`cocosgame2/experience/02-资源与内容改造/Unity到Threejs材质与预设迁移.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Unity 到 Three.js 的材质与预设迁移

新增日期：2026-09-28，来源：3dchar 阶段复盘。

预设索引应按 Unity Transform 原始子节点顺序解析；文件名排序会破坏配装。每个 renderer 的逆绑定矩阵必须独立保留，特别是握持装备。GPU skinIndex 类型必须与 shader 的属性类型匹配。

视觉迁移先取证颜色空间、材质关键字、灯光与实际运行时 SH，不通过名称推断金属度。Gamma 工程不能直接套用现代线性 PBR + ACES。环境 cubemap 应保留原预滤波 mip 与 HDR 解码，而非重新生成普通 mip。透明材质需要同时核对 culling、ZWrite、premultiplied diffuse 和高光 alpha 规则。

自定义网页 shader 无法通过标准 GLB 自动传递给外部查看器，应明确这项交付边界。异步截图/导出需要在请求时冻结配置名称，防止快速切换导致证据错标。

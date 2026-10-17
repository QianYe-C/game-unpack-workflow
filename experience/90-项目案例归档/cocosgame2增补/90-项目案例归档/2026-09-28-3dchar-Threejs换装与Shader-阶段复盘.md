> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-3dchar-Threejs换装与Shader-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 3dchar Three.js 换装与 Shader 阶段复盘

日期：2026-09-28

目标：资源分类、原生 H5 换装、保留 Demo 所有预设，并解决 shader 外观偏差。

根因与处理：

1. Unity 子节点顺序就是预设索引，不能按名字重排。解析原始 PresetData 得到 10 套，按原编号导出，1046 个选项对应 1172 个网格。
2. 武器蒙皮的 renderer transform 并非单位矩阵。保留每个网格自己的 inverse bind，并以共享 24 节点驱动；1172 网格绑定姿态抽样最大位置误差约 0.000117。
3. WebGL2 Uint32 skinIndex 触发整数属性接口，与浮点 vec4 不匹配。运行时转换 Uint16，模型恢复显示。
4. 原版是 Gamma URP/Lit；直接使用 Three 标准 PBR、额外灯、ACES 导致泛白。读取 PlayerSettings、原 shader，并在原版 Forward draw 捕获真实 uniform：白色环境 SH、0.2 主光、HDR decode [5,1,0,1]。移植 BRDF、Gamma 输出、反射 mip、透明混合与 culling。不要根据 Metalness 材质名推断金属度，其值实际为 0。
5. 截图接口不可用，通过应用自身 PNG 导出获得渲染证据。异步 toBlob 必须冻结捕获时的预设名，否则快速切换会误标图片。

验证：8 项自动测试通过；全部十套预设浏览器切换并保存 PNG，无 shader 错误；GLB 导出包含 37 动作，校验文件头、关节/逆绑定数量及动画目标。生产构建成功。日志在 myprojects/3dchar/logs，源工程在 webprojects/threejs。

遗留边界：阴影算法/镜头尚非逐像素对齐；动画未复刻 Mecanim foot IK；GLB 标准 PBR 在其他查看器中不等于网页自定义 URP。截图证据为应用画布导出，不是完整浏览器界面截图。

清单复核补充：2026-09-28 对照用户商品清单，1134 FBX总数与分项展开1130并不相符。Demo按类别多出共42网格为1172；按原名字逐一核对无转换缺项，但合并编号的武器/背饰/手部/头部子类尚未独立对应。用户列36动作，实际37含额外Cheer。贴图实际256²。官方50示例仅有10配置，不可将Demo转换完成表述为完整商品资源已交付。详见项目 sourceConfigs/官方清单核对.md。

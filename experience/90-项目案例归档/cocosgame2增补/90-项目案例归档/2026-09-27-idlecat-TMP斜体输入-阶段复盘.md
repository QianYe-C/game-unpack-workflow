> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-27-idlecat-TMP斜体输入-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat TMP 斜体输入修复

2026-09-27，知识归档日期同日。

目标：还原兑换码与昵称弹窗的原斜体占位文字和输入区padding。

根因：NativeTmpGeometry采用自定义顶点，Label.isItalic本身不会经过Cocos内置斜体处理；原输入文本开启extra padding，几何实际限制为材质GradientScale=10，旧移植只用基础padding。

依据：原TextMeshProUGUI.GenerateTextMesh 0x549eff8、斜体段0x54a21ec..0x54a22d4；原运行时44个顶点、italicAngle35/capLine67/faceScale0.8。参照官方uGUI TMP公式并以当前游戏ARM64及采样结果核对。新增可选斜体参数不改变普通文本路径，多行剪切按各行基线计算。

动作：NativeTmpLayout/NativeTmpGeometry增加斜体参数；InstallInputTypography通过MCP修改Setting、Rank_manager与loading.scene，设置额外padding10。补原兑换入口BounceBtn的0.9/0.1缩放。临时组件和assets脚本已清理。工具保留在tools/editor，未手写序列化文件。

验证：兑换码28顶点最大误差0.0000772、昵称16顶点0.0000656；零角度与原普通文字一致，多行基线不影响剪切。普通中文/自动字号/多行图标回归和tsc通过。两个弹窗浏览器截图与无新增error记录见docs/evidence/redeem-20260927。只用CLI构建，没有编辑器运行。

遗留：输入跨字体和Emoji回退尚未完整实现。临时改写昵称Text、ForceMeshUpdate并在finally恢复的原生采样证明中文及Ω来自JP (Outline)，Emoji来自TMP Sprite，未分配字符为U+25A1；没有写存档或调用改名业务。当前兑换码问号保护只防止缺字崩溃，不是视觉还原。排行榜动态名称也需要覆盖。后续应按原字体/材质分段排版，保留原输入字符串和业务长度规则。

2026-09-27 TMP斜体阶段：CLI20260927-183734通过，20.19秒、sourceUnchanged=true；源SHA256 77a4749d248af0a3a90ca250aaf41cd3c9f3f89c4c1db93848d2a31c1b25d1af。兑换码/昵称44个原生顶点误差<0.00008，浏览器弹窗检查通过。无运行中构建、无临时安装组件，总目标active。下一条可执行动作：实现原JP备用字体与Emoji分段渲染，覆盖昵称输入和排行榜动态名称；原生证据docs/evidence/redeem-20260927/native-input-fallback.json。地图原接缝保持，未改变资源。

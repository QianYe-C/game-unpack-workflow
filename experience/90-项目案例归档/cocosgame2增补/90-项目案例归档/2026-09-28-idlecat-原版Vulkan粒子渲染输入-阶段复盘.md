> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-原版Vulkan粒子渲染输入-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 原版 Vulkan 粒子渲染输入阶段复盘

2026-09-28 建立与重组。

目标：继续核对原版矿山图集取帧与最终混合，避免以CPU曲线通过替代像素一致。

阻塞与根因：MuMu实际走Vulkan21，公开GLES函数虽存在却无调用；原Shader平台18为SMOL-V，文本提取为空不代表没有代码。

动作：直接getter确认Vulkan/Linear；13/17/19一次性副本捕获78/102/114索引及同一候选pipeline，原对象与存档不写入，副本全部销毁。固定上游解码器提交，恢复36个SPIR-V程序并关联原子程序表/关键词；8个非程序化实例变体直接传递UV/颜色，4个程序化实例变体单列条件分支。

验证：两份可重复验证器通过，运行资产SHA仍匹配CLI130848。无编辑器内运行，无新增游戏构建，无运行时负担。证据见myprojects/idlecat/logs/particle-vulkan-input-20260928，详细文档在工程doc/原版Vulkan粒子渲染输入核对.md。

遗留：mapped-memory搜索没有得到已验证顶点，不能称UV完成；候选pipeline还未映射到live shader二进制。Linear真实混合、CPU UV、最终像素/真机及平台服务仍待完成。下一动作是实际顶点上传地址/格式和原frame UV，不根据经验盲加翻转或gamma。

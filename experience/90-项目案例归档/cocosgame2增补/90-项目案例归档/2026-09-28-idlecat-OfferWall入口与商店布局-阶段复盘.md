> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-OfferWall入口与商店布局-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat OfferWall入口与商店布局

目标：恢复原入口曝光条件与原始商店布局。

阻塞与根因：原入口按钮未绑定；商店每秒刷新强制隐藏免费奖励区；免费奖励区遗漏原VerticalLayoutGroup与ContentSizeFitter。编辑器热重载期间临时节点失效，后续场景renderer退出造成MCP超时。

动作：448组原生getter采样并恢复现场；按SDK/存档/关卡/活动条件刷新原节点；MCP绑定4份prefab和场景，补左上对齐/间距10的原布局；删除强制隐藏占位逻辑。编辑器确认renderer disposed后按既有授权重启，等待脚本注册再挂载，未执行编辑器预览。

证据：483项原生/TS/商店集成检查，MCP引用与原配置布局推导检查，浏览器横幅显示/周期刷新/点击打开，FreeCash与服务器配置宿主回归、运行时TS。CLI083703源不变，无缺失脚本；logs/offerwall-entry-20260928-083703归档，产物逐文件镜像。

遗留：真实SDK、placement加载/关闭/奖励领取与pending恢复及最终原版像素对照未完成；原始包291369610字节仍超预算。整体移植保持active。

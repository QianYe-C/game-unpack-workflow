> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-FreeCash面板与服务边界-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# FreeCash 面板与服务边界阶段复盘

重组日期：2026-09-28。

目标：原生中文样式、作者化Prefab及原曝光和奖励行为一致。动作：MCP绑定6Prefab与场景；复用原字体补字，互斥横幅、持久化权益及可替换SDK接口。阻塞：真实SDK与远端配置尚未接入，不能以GM奖励替代账号关联。

实际浏览器发现检查关联等待不结束：Creator同一callback的schedule只更新interval，scheduleOnce回调尾部会cancel，自注册不能实现循环。改为等待期间schedule，结束统一unschedule。纯规则和mock调度通过不能替代引擎实际生命周期验收。另有截图与输入坐标偏移，以短时捕获节点Touch落点校准，诊断清理后再次实测。

验证：1081原生曝光、73权益检查，控制器真实TS配mock服务/存储、Prefab读回、离线tsc和浏览器原错误提示/超时恢复/关闭重开通过。CLI074723成功源不变、无缺失脚本。证据：myprojects/idlecat/logs/freecash-prefab-20260928-074723。

遗留：真实SDK、配置缓存/曝光日志、同画幅逐像素/抖音真机、291MB标准包体未过发布门禁。总移植目标未完成。

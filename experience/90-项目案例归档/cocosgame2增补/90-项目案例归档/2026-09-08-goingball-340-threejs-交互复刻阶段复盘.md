> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-08-goingball-340-threejs-交互复刻阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Going Balls 3.40 → Three.js 交互复刻阶段复盘

日期：2026-09-08。阶段记录，整游 1:1 与微信/抖音小游戏验收尚未完成。

## 项目与输入

- 原始材料及逆向脚本：`/Users/jiaojian/Documents/cocosgame/myprojects/goingball`。
- 客户端：`/Users/jiaojian/Documents/goingball/clientThreeJS`，Three.js / TypeScript / Vite，Rapier 固定步进，主线程默认、Worker 可选。
- 新版 Going Balls 3.40 / versionCode 287 / Unity 6000.0.73f1；旧版 3.24 独立保留。
- 用户安装 MuMu 后，拉取 ARM64 split；与 ARMv7 输入包相同路径 assets 内容一致，资源导出可共用，原生地址必须分别解析。
- 全量提取 1,304 prefab、763 个关卡对象、203 个球部件、338 个 Resources prefab；56 个导出例外有记录，无 prefab / 脚本解析异常。

## 关键发现

1. **看见路面不等于加载了碰撞。** Unity 保存时关闭的 collider 会在 Level.SetEnablePhysics、PushObject.ResetAll 中启用；起点平台还由 FinishGate 动态补建。仅按 prefab 的 m_Enabled / m_IsKinematic 会导致穿模或箱子无法碰撞。
2. **颜色不一致先查 shader 公式。** 原版 Gamma 分支 SH 环境光经过 Gamma 变换；Custom/DiffuseColored 在受光项之外再加 albedo。此前遗漏两项让木板和蓝平台偏暗，不能靠全局曝光掩盖。
3. **同手势比较必须明确消费边界。** 首滑是独立 PushSphereForward(400)；普通滑动有标准化限幅和 tanf 衰减。Worker 合并多个固定子步时，触摸增量只消费一次，持续键盘值逐步施加。
4. **物理与渲染原因分开验证。** Rapier FIX_INTERNAL_EDGES 修正共享三角边导致的平地弹起；相机开局插值速率也会造成球体看似突然跳动。
5. **源资源里存在旧流程。** 3.40 StateGame 获得额外球走 SphereManager/VisualSphereLifeController；SpawnpointCollectable 虽然存在，不能据类名就认定当前在用。
6. **收集不是立即隐藏。** 金币先移到玩家相机坐标系上方再吸入，总计 0.666 s，加速转动并缩小；额外小球用真实 3D 模型飞入生命槽，逻辑加命和 HUD 填槽分开。
7. **复活要失效旧状态。** 新生命测试暴露复活后旧掉落姿态重复消费的问题；通过 generation 失效旧 Worker 消息，并同步刷新/清空主线程状态，避免一帧多次扣命。
8. **逆向工具本身也需验证。** 修复了 VA→ELF 文件偏移和 Disarm ADRP 地址误读，使用 Capstone 对原始字节独立验证；方法委托要先解全局指针再读元数据。

## 渲染与性能实现

静态几何按材质和 48 单位空间单元合批，金币保留实例矩阵，动态箱/检查点/门不烘焙进静态网格。加载当前关和一个下一关可见预览；依据原版 fog end=200 限制渲染距离。初版双关 102 calls，经实例化与剔除，第一关预览基线约 61 calls / 26.2k 三角形；后续额外球与收集效果数值以客户端最新证据为准。

金币闪光复用一个 11 粒子实例池，过渡球共享源几何与缓存材质。加载时预编译效果 shader，避免首个收集事件触发编译卡顿。完整派生资产约 799.5 MB，当前只做浏览器按依赖加载，小游戏分包/CDN 尚未实现。

## 实测与证据

- 用户视觉反馈推动材质、镜头、SWIPE 世界空间、金币旋转、检查点、预加载、起点门和收集动画逐项修正。
- 主线程/Worker 已有前进、实际箱体接触位移、检查点、金币、生命和复活测试；最新结果见客户端 `docs/evidence/pickup-tests.log`。
- MuMu 原版第二关录像 `docs/evidence/native-pickups.mp4`，可见金币 +10 与额外球飞入第二槽。
- 原版无注入只读内存采样约 600 s，35,246 条样本，进程存活。原版 PSS 与浏览器 JS heap 不是同一口径，不能据两者算内存优势。
- 更早的注入采样期间有 libpairipcore 崩溃，因果未完全确认；默认采样工具已换为只读方式。

## 未完成范围

完整关卡选择/bonus/无缝接管、全部机关与空中/滑面物理、原版结算/抽奖/商店/存档、音效、完整粒子和 UI 3D 生命槽，以及微信/抖音开发者工具和真机。当前文件不是整游完成声明。

持续记录入口：[客户端文档](../README.md)、进度（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/goingball/clientThreeJS/docs/PROGRESS.md`）、收集效果分析（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/goingball/clientThreeJS/docs/PICKUP_PARITY.md`）。


## 全关卡与机关基础里程碑（18:00）

关卡文件全部在本地，763 个 Level prefab 包含 500 个分段，不能当作 763 个连续关号。只读读取原版 IL2CPP 静态字典，恢复五张 90 项组合表，主线走 v01；同时接入 bonus、140 关后的循环和 Setup 1/2 互斥方案。第 21/22/30 关 MuMu 截图与客户端组合对应。主线 1…248 实际组件矩阵通过共享选关器生成，便于直接跳到真实启用的机制。

补显式导出 unity default resources，解决惰性解析漏掉的圆柱/球等碰撞网格。15,970 个引用文件无缺失，仍有两个动态字体贴图引用例外。素材约 802.3 MB，本地完整性不代表小游戏包体已合规。

MovingPlatform、Hammer、Propeller 的固定时钟与 kinematic 接触、运行时叶片克隆和 Trampoline 的速度设置/层过滤已经接入；21 项主线程/Worker 回归通过，构建通过。完整原版动态对照、其他施力机关、关节、生成器、传送门仍在继续。

用户购买免广后，存档恢复改为仅恢复旧档的进度字段，保留当前购买/VIP/皇冠球及库存。第 53 关已录制 20 秒真实弹板玩法；可见弹板、腾空、跌落和检查点复活，尚未完成同皮肤的客户端轨迹匹配。

计划与证据入口：局内计划（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/goingball/clientThreeJS/docs/IN_LEVEL_PLAN.md`）、关卡组合（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/goingball/clientThreeJS/docs/LEVEL_PROGRESSION.md`）、主线机制样本（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/goingball/clientThreeJS/docs/MAIN_LEVEL_MECHANISMS.md`）、跳关工作流（历史引用，项目文件未随包提供：`/Users/jiaojian/Documents/goingball/clientThreeJS/docs/MUMU_SAVE_WORKFLOW.md`）。

铰链补充：HingePlatform 的刚体/关节在 OnLevelReset 添加，平台和螺母在 Init 保持世界变换重挂，旧父节点销毁。客户端已恢复并通过真实撞击/支点回归；完整 23 项通过，MuMu 第 10 关录像已取得。动态角度曲线、重置及 BalancePlatform 其他分支仍待完成。详见客户端 docs/HINGE_PLATFORM.md。

平衡平台补充：BalancePlatform 的自动分支按局部 X 轴运动；非自动分支由 OnLevelReset 解冻，不能仅根据 prefab 或 OnLevelEnablePhysics 的 kinematic=true 判为静态。已恢复 ±角度限位、真实碰撞计数、约十个固定步延迟回正、角度平方目标速度和力上限 20。49 个原始非自动实例均使用单箱体和手动 COM=0，已处理对应质量/惯性；Rapier 与 PhysX 的响应标定仍待完成。MuMu 第 57 关关号已确认，探索视频未抵达平台，不能替代接触验证。详见客户端 docs/BALANCE_PLATFORM.md 和 evidence/physical-balance-tests.log。

临时地板阶段：按 ARM64 恢复玩家/幽灵接触、延迟关闭碰撞、延后隐藏及复活恢复。应读取主题 terrainTemporary 四槽，不能使用 prefab 的 Legacy 占位材质；AdvancedDissolve 遮罩和阈值已定位，shader 未完成。31 项回归通过，MuMu 第 58 关探索并未证明消融时序对齐。SkullBridge 的 TryToHitPlank 是 stub，但 UpdateSkullRays 仍直接调用 Hit，必须沿实际调用链分析。详细工作流/证据见客户端 docs/TEMPORARY_TERRAIN.md。

消融 shader 续接：已从 APK GLES 程序 94/95 提取裁切/底色/边缘发光逻辑，保留 source uniforms 与采样。每块临时地板独立 uniform，共享纹理与两类 shader cache，GPU 像素裁切/实例独立性和主线程/Worker 物理 4 项通过。17 主题中部分材料原本无消融，不对其强加新 shader。完整光照匹配、MuMu 板内停留时序、小游戏 GPU 编译/性能未完成。详细证据见 clientThreeJS/docs/TEMPORARY_TERRAIN.md。

骷髅桥分析阶段：UpdateSkullRays 的实际命中按容器局部位置索引选板，不能用函数名推断为 Raycast。缩窄动画 duration=0.333 与再次接受命中的 interval=1 秒不同；需同步 Transform、BoxCollider 和纹理 ST。独立时钟 3 项测试通过，但关卡尚未集成。当前本地 prefab 无 head 实例，继续追查场景/动态资源；不可将此局部资源结论写成原版没有头部。详见 clientThreeJS/docs/SKULL_BRIDGE.md。

骷髅桥运行时阶段：初始化、触发、位置选板、缩窄 BoxCollider 和模型/UV/tint 已连通；中心与边缘真实接触 main/worker 通过，稳定源码完整 37 项通过。首轮边开发边回归触发 HMR，导致页面状态/执行上下文丢失，失败单独归档并在冻结源码后重跑，不能通过自动重试掩盖。原版 RNG、困难入口、头部来源、Update/LateUpdate 帧边界仍待验证。最新证据见 clientThreeJS/docs/SKULL_BRIDGE.md。

### 困难支路与清单闭包

关卡资源全部落地后仍要追踪运行时加载链：Going Balls 困难路段由 LevelManager 按全局关号 >=71、入口候选和加载结果附加。普通组合表扫描会漏掉固定 hardstart 与九个 hardlevel 中的机关/宝箱。ISIL 漏掉门槛跳转且全局地址不可靠，须用 ARM64 与只读运行时字符串交叉核验。RNG 在起始段初始化后才选困难段，不能忽略中途随机消费。流程文档：clientThreeJS/docs/HARD_SECTIONS.md。付费后跳关继续只改进度，禁止恢复整个旧存档。

### 支路集成必须做完整场景接触回归

只读 MuMu 运行时 73/74 的困难段为 2/9，initSeed 0，支持 InitState 后第一整数 Range 的恢复算法。客户端按父关入口→hardstart→hardlevel 装配，原有实例 ID 足以隔离，无需改写资源 ID。

隔离板测试通过不代表整关能触发：首次实际 73 关测试在 Y≈-50 被旧“检查点高度-18”误杀。修复为最近支撑高度参考后，主线程/Worker 全场景接触和渲染尺寸同步通过；18 米临时阈值仍需原版状态机替换。完整 40 项回归通过，宝箱和实际沿路通关尚未验收。失败记录与临时适配边界必须一起保留，不能改测试绕过后宣称原版行为完成。

### 宝箱回调与 metadata 陷阱

困难宝箱会回检查点并销毁支路，不可复用普通通关。未初始化的 MethodInfo 槽读到 0x6000485f/61，必须按原始 metadata 定义索引解析，不是代码指针；导出的 method-map 数组顺序也不等于 metadata 索引。提取脚本现支持 Type::Method，重载按 VA 独立命名避免覆盖。奖励测试仅证明计算契约，背包/镜头/返程/释放仍需真实接入和原版验证。

### 退场不能只隐藏模型

困难宝箱返程的物理释放需清理动态创建的关节固定锚点、机制时钟和 collision 映射。第 73 关退场实际移除 158 刚体（包含锚点）/149 碰撞体/12 关节，main/worker 行为一致；generation 使旧快照不再恢复对象。渲染合批和粒子直接挂到场景 root，后续必须记录实例所有权与金币批次引用，不能 remove(shell) 后就报告整段内存回收。证据与接续设计见 RUNTIME_RETIREMENT.md。


### 渲染实例退场与验证

渲染实例所有权与退场已实现：清理独占合批资源、粒子、源节点/对象索引及机制引用，压缩跨实例金币批次并保留共享 Assets。main/worker 专项 2 项通过；最终全套 46 项通过（2.6 min），构建通过（4.05 s）。构造场景 GPU geometry 146→81、calls 272→138、粒子 6→3、共享纹理保持 30。证据见 RUNTIME_RETIREMENT.md。宝箱目标/动画/入账/返程调用未接入，共享缓存淘汰和小游戏长期内存待验，总目标 active。

工作流补充：渲染资源必须按实例记录所有权，不能仅移除 shell；独占资源释放与共享缓存淘汰分开处理。粒子 GPU 指标先预热再采基线，冻结源码后执行完整回归，避免热更新污染结果。购买状态继续由进度专用跳关工具保护。


- 2026-09-08（宝箱目标）：按原生 OnLevelEnablePhysics 启用 authored-disabled SphereCollider，登记目标/触发器/箱体引用，退场清理目标；CoinChest 子树不再静态合批，保留 3 个可动画网格。九种 hardlevel 的真实 enter、持续重叠不重复、关闭/恢复、退场和 renderOnly 隔离在 main/worker 中通过。专项 2 项通过（6.4 s），最终全套 48 项通过（2.6 min），构建通过（4.04 s）；日志 all-chest-target-tests.log/build-chest-target.log。
- 2026-09-08（宝箱动画源）：只读导出 Chest_open 控制器、Cap_open/Cap_closed_idle 原始 AnimationClip 及 streamed 系数，确认 IsOpen bool、零时长状态转换和 0→65→55→62→60 回弹关键值。Animator 配置此前只在源导出中，未进入运行包；补记依赖审计缺口。下一步运行时动画打包/播放、粒子、库存入账、7 秒镜头及回溯。main 仍未消费目标事件，MuMu 实际领取和小游戏性能尚待验证，总目标保持 active。

工作流补充：对每种运行时组件同时审计资源字段与生命周期方法。序列化 disabled 不等于运行时没有碰撞；依赖审计必须解析 Animator 的 controller/clip，不可只覆盖材质、网格和粒子。源系数、控制器状态与脚本时序共同决定动画，避免仅凭截图估计开箱动作。


- 2026-09-08（箱盖源动画）：package-chest-animation 覆盖两个控制器/12 个资源，内置与 bundle 开闭片段 raw SHA 一致且控制器状态一致；打包前预检未知依赖，纳入总打包脚本。ChestAnimation 逐段计算原 streamed cubic、镜像本地旋转，支持开闭、暂停、重复 true 不重启和退场；播放结束停止重复更新。
- 2026-09-08（验证）：动画/目标/退场 5 项通过（15.8 s），最终完整 49 项通过（2.6 min），构建通过（3.53 s）。源箱体闭合、1/6 秒回弹与 2 秒稳定截图落盘并检查，开盖节点/方向正确；独立机位灯光不作为 MuMu 原版视觉验收。首次测试 -0/+0 严格相等失败单独保留，改为数值比较。
- 2026-09-08（后续缺口）：宝箱光线/金币粒子尚未实现非零时间 burst 和 stretched billboard；main 未消费宝箱目标并调用动画/奖励/回溯。新增全量动画依赖审计：宝箱 12 项覆盖，另有 49 Animator +4 Animation（含皮肤和 UI）未覆盖；逐路径清单已保存。持续保留 MuMu 同步实测、全机制移植及小游戏实机性能门禁，目标 active。

工作流：动画先追完整 Animator→controller→clip 链，源副本用字节哈希及控制器状态校验等价；恢复 streamed 多项式后用真实网格截图检查节点/坐标。资源预检应在写入前完成，文件存在性审计不能代替动画依赖审计。


- 2026-09-08（粒子爆发/atlas）：补非零时刻 burst 与帧内出生年龄，clear/隐藏/dispose 取消队列；按 source maxNumParticles 预留 burst 缓冲，宝箱 26 槽不再截断 16 个粒子。GPU 每实例 UV 矩形播放源 4×1 生命周期动画，实际一 draw。粒子形状/方向/旋转/完整拉伸仍待补，未连接宝箱 Play/领取流程。
- 2026-09-08（验证）：粒子/拾取/退场专项 7 项通过（25.1 s）；调整最终容量并补重叠上限断言后，完整 50 项通过（2.7 min），构建通过（4.24 s）。初轮源码 HMR 导致 Worker 执行上下文被销毁，失败记录单独保留，不作为运行时失败或通过。最新证据 all-particle-burst-tests.log、build-particle-burst.log。
- 2026-09-08（源审计和续接）：12 个宝箱、24 个发射器原始配置/材质/TRS 全量落盘；Unity 6.0 文档确认 Length Scale 依速度方向拉伸，Velocity Scale=0 不代表不对齐方向。下一步 sphere/cone 源发射、旋转、速度朝向拉伸与 0.1 秒 Play，然后宝箱奖励/结束镜头/回溯。保留 MuMu 同步验证及小游戏性能验收，总目标 active。

工作流补充：不能用连续 rate×lifetime 估算有 burst 的粒子容量；校验跨帧发射时同时检查粒子数量和出生年龄。atlas 帧、旋转和拉伸方向分别验证，不能只靠静态截图或材质名称确认整体粒子效果。


- 2026-09-08（宝箱源粒子）：新增 playSource 保留源节点 TRS，球形体积/锥形底面发射与速度方向、光线随机角及旋转、按世界速度方向拉伸；开盖 0.1 秒后启动两发射器，约 0.15 秒出现 16 个粒子，关闭取消/清理，重开恢复。实例退场释放独占特效且清理状态映射。
- 2026-09-08（验证）：专项 5 项通过（14.4 s）；补连续发射帧内出生时间后最终完整 51 项通过（2.7 min），构建通过（4.24 s），见 all-chest-particles-tests.log/build-chest-particles.log。新截图可见箱内光线，单粒子发射器渲染一 draw；桌面样本不作小游戏性能验收。
- 2026-09-08（差异与接续）：源审计发现光线 SizeModule.separateAxes=true、金币 pivot=(0,-0.5,0)，还需补齐并校准 shader/tint、随机序列和非均匀缩放。main 未消费目标事件，库存奖励/结束镜头/回溯未串联，MuMu 实际领取与同时序视觉仍待验证；完整目标 active。

工作流：同一特效需联合核对发射源 TRS、模块曲线、renderer 模式/pivot 和材质程序。截图能证明可见效果但不能证明参数全部对齐；发现未覆盖字段继续列入待办，不以测试通过代替原版对照。


- 2026-09-08（粒子参数校准）：接入光线 X/Y 独立尺寸和 coin pivot，修正拉伸绕序、源双面渲染；从 APK 提取两种加法 shader 与 pass state，区分 Mobile 顶点 clamp、Legacy 2*tint/alpha clamp、Legacy RGB-only 与 Mobile RGBA 混合。保持单 draw，支持贴图 ST。
- 2026-09-08（验证）：最终 9 项粒子/宝箱/拾取/退场专项通过（30.0 s），构建通过（4.06 s）；GPU pivot 质心移动 8 像素，测试 Legacy/Mobile 输出 alpha 为 64/128。初轮 HDR/RGBA8 预期错误归档，Three 默认 alpha 差异已修正。未把上轮 51 项重复记为新整套 52 项。
- 2026-09-08（续接）：箱盖及粒子基础可由 setChestOpen 驱动，main 仍未消费目标、发奖或返程。下一步连接库存奖励/结束镜头/转场回溯/退场，MuMu 同时序校准及小游戏性能仍待验证。源随机、非均匀缩放、soft-particle/fog 质量设置未验，总目标 active。

工作流：shader 验证同时提取程序和 pass state；相同“Additive”名称不保证 alpha 行为一致。GPU 用可控纹理/颜色检验数值与位置，默认引擎混合状态须与源状态核对。RGBA8 钳制可能使 HDR 测试预期错误，不能因测试失败直接改材质。


## 2026-09-08 库存价格与钱包基础

从 3.40 ARM64 的 Economy.CheckSpheresProgression、GetAllInventoryValue(false)、GetSphereModel/GetSpherePrice(index) 与 UserInventory.ResetSpheresToDefault 追踪价格来源。只读 native-levels sphere-prices 读取 EconomySettings 静态字段 +0x110/+0x118 的模型/价格列表，输出 49 个唯一模型；新增类型名、长度和数值校验。首次误判为 SharedData 被校验拒绝，修正为 EconomySettings 后读取成功。证据 evidence/native-sphere-prices.json；package-sphere-prices.py 校验、哈希并打包为 assets/sphere-prices.json，已接入总打包与资源清点。该表是当前 3.40 运行配置的观测，不保证未来远程配置不变。旧 TextAsset 库存/经济配置属于历史 schema，未用作本次价格依据。

库存价值按 progression index 对拥有模型求价，不能把模型 enum 直接当价格索引；不含钱包、当前选中皮肤和重复拥有项。Worlds 奖励以及追加模型 42/40 价格为零。只读 MuMu 当前拥有 [1,40,42,29]、选中 29，库存价值为 0；未修改免广/VIP 或其他购买字段。原版默认拥有 progression 首项 1；客户端仍保留既有初始钱包 10，不把它宣称为新验证的原版默认值。

新增 inventory-value.ts 和 Inventory：统一持有余额、拥有球与局内已领取目标集合。claimChest 先验证奖励计算，再入账并登记目标，同一局重复目标不重复发奖；beginRun 清理本局领取集合。普通拾取仍先累计 runCoins，通关后入同一钱包，切关保留钱包与库存。启动时先读价格表再允许加载关卡，避免异步初始化期间进入未就绪钱包。当前仅会话内存状态，尚无持久化、购买同步或皮肤解锁界面；debug 选球不授予拥有权。

验证：最终 inventory-value、inventory、chest-reward 和 pickups 共 10 项通过（20.9 s），包含 main/worker 实际拾取→通关入账→切到第 2 关保留余额；构建通过（4.11 s）。日志 evidence/inventory-final-tests.log、evidence/build-inventory.log。本轮没有重跑整套测试。

尚未接通：main 的宝箱目标事件尚未调用 claimChest，7 秒结束镜头、1 秒转场、检查点回溯与支路退场仍待实现；不能据此把宝箱领取标记完成。下一步把这些生命周期连接，并用 MuMu 实际领取录像核验。完整局内机制、小游戏适配及实机性能目标继续 active。


## 2026-09-08 跨关源逻辑更正

新建 CROSS_LEVEL_FLOW.md，保存 11 个 ARM64 方法机器码/反汇编/哈希和常量。MuMu 只读运行内存验证 isPremium 恒 false，当前包普通关间距离为 9，不因免广购买直接改为 29；未修改购买或存档。虚方法槽确认终点自动制动目标为下一关 GetStartSpawnPoint，经其场景变换后传入 StopSphere(true)。源每固定步位置插值因子为 0.02；完整速度/角速度和碰撞顺序待迁移。点击继续才推进关号/LoadLevels，修正此前“自由连续接管”的笼统计划。

当前 main 仍 distanceTo(finish)<3、冻结固定步并显示结算；没有制动到下一出生点。本轮为证据和计划更正，非运行时修复。接续优先源门传感器→共享 Simulation 制动→落点支撑/镜头→继续转场与资源退场，再用 MuMu 同时序核验；全部原定局内/小游戏性能任务保留，目标 active。


## 2026-09-08 当前结束门传感器接入

GateBarrier 从源 FinishGate.triggerCollider 解析实例作用域 triggerTag，缺失引用显式报错。源结束门 BoxCollider 已由场景编译器加载，本轮复用其事件，没有添加距离代理或重复 collider。main 使用当前 gates.end.triggerTag 的 entered 事件结算，移除 distanceTo(finish)<3。起点门和其他实例不会误触发。

tests/finish-gate.spec.ts 使用真实第 1 关 main/worker，验证旧半径范围内的终点前方 2.6、侧面 2.85 均不触发，门上方和起点门不触发，进入结束门内部才完成且入账不重复。与首关持续滚动、钱包/切关回归共 7 项通过（32.8 s）；构建通过（4.33 s）。证据 evidence/finish-gate-tests.log、build-finish-gate.log。本轮未重跑全套。

初轮测试在 Worker reset 清空快照后读取 tick，导致等待 NaN 超时；修正为 reset 前记录 tick 后回归通过，原日志 finish-gate-initial-tests.log 保留。初次构建发现回调内可变 gates 的 TypeScript 空值保护不足，已补可选访问，日志 build-finish-gate-initial.log 保留。未改动 Worker reset 的正确快照失效逻辑。

尚未完成：触发门后当前仍即时进入旧结算 UI、停止固定步，未执行源 AutoBrake 至下一关出生点。下一步保持结束阶段固定步更新，在共用 Simulation 中落实制动位置/速度/角速度，并处理目标支撑、镜头和继续回调。源 MuMu 同时序与小游戏性能验收继续待办；总目标 active。


## 2026-09-08 AutoBrake 共用模拟基础

新增 runtime/auto-brake.ts：snap=true 的逐固定步位置插值、水平速度衰减（保留垂直速度）、源缓存角速度归一化及位移对应的滚动速度、距离平方停止阈值。角速度因子 100 从 PhysicalSphere 构造函数 +0x170 写入恢复，机器码/反汇编加入 cross-level-source 的 SHA 清单；浮点乘法保留“归一化→乘本步距离→乘 100”的源顺序。sample 计算请求位姿，observe 判定停止，目标复制且校验有限值。

Simulation.beginAutoBrake、Physics.beginAutoBrake 和 Worker autoBrake 命令共用计算；命令携带 generation，reset/init/dispose 清理制动状态。激活制动时屏蔽新的用户驱动/launch，暂停零步不移动，批量步进逐固定步计算。状态快照新增 active/target；无逐物体 RPC。

当前适配动态球时使用 Rapier.setTranslation 请求位置，保留刚体类型、重力与碰撞求解，不把球随意改成 kinematic。Rapier 官方说明直接设置位置属于 teleport，kinematic 应使用 setNextKinematicTranslation；因此这个适配的扫掠、插值和接触时序尚不能视为 PhysX MovePosition 已对齐。来源：[Rapier rigid body position](https://rapier.rs/docs/user_guides/javascript/rigid_body_position/)。当前测试使用零重力空场隔离数学行为，不冒充完整终点道路接触验证。

首轮 7 项通过（30.2 s），之后补浮点运算顺序再做最终回归，结果见本节末。测试涵盖真实 main/worker 的 20 个单步与一次 20 步一致、零步暂停、忽略驱动、在途 step 后 reset 清除制动，以及既有门触发与首关滚动。

main 尚未调用 beginAutoBrake：终点仍走旧结算 UI/冻结固定步。下一步必须一起接入下一关出生点/落点支撑、保持完成阶段物理更新、结束镜头和继续回调；还需 MuMu 逐帧对照位置/角速度/重力与碰撞，确认当前动态位置适配是否应替换。源 snap=false、kinematic 球和特殊球 actuator 不在本轮覆盖。未宣称完整跨关或小游戏性能验收完成，目标 active。


- 2026-09-08（自动制动基础）：共用 AutoBrake 固定步计算及 Simulation/Physics/Worker 命令已加入，包含源角速度因子 100、目标校验、快照状态和 reset/generation 取消。main 尚未调用，落点支撑与结束阶段更新待接入。动态位置适配的 PhysX 接触时序未验证，不记为跨关完成，详见 CROSS_LEVEL_FLOW.md。
- 最终自动制动/门事件/首关滚动 7 项通过（29.6 s），构建通过（3.94 s）；证据 evidence/auto-brake-final-tests.log、build-auto-brake-final.log。未重跑全套；零重力隔离测试不替代真实道路与 MuMu 同时序验收。总目标 active。


## 2026-09-08 终点到下一出生点运行接入

main 的当前结束门 enter 事件现在调用 Physics.beginAutoBrake(nextLevel.spawn)，进入 finishing 阶段；won 仍表示本关已结算，但 finishing 时保持固定步与球渲染更新，屏蔽用户驱动和新的拾取/死亡结算。球达到制动停止阈值后才显示现有 LEVEL COMPLETE 对话框。这个 UI 显示时机属于当前接入方式，原版 MediatorGameFinish、CameraMode=15 与相应结束 UI 尚未恢复，不能据此宣布整个完成流程 1:1。

beginAutoBrake 同一命令可携带落点支撑：从已摆放下一关的 PhysicsScene 选取固定、非传感器 shapes，保留原始网格/BoxCollider、变换、材质和 enabled 状态，在制动开始时加入 Simulation；没有创建替代平板。当前加入的是下一关全部静态实体碰撞，尚未空间裁剪；动态/kinematic 机关和传感器未激活。若后续某关出生区依赖运动物体，还需按该关源生命周期接管，不能把这项当作所有关卡完整接管。

Simulation 校验支撑 body 身份、排除动态/kinematic 和 sensor，并防重复添加；main 记录同一局支撑已加入，调试重进门不重复创建。load 重建清理支撑/finishing；已通关时调用 respawn 改为重载本关，避免把制动结束状态留在检查点复活。debug.placeBall 清理 finishing；暂停仍停固定步。静态碰撞随当前 Physics.dispose 释放，尚未实现原版继续流程的驻留复用。

真实第 1→2 关和第 5→6 关 main/worker 接触源结束门后，球从终点位置移动到下一出生点；第一组目标约 (-0.000123,-3.500000,155)，结果 z=154.990143；第二组目标约 (26.999842,0,125.145767)，结果 z=125.135902，垂直误差约 0.000066。源固定步制动约 325 步，Worker 观测批次边界可差一步；最终位置吻合，没有掉落。测试进一步点击真实下一关按钮，确认关号变化及 won/finishing/autoBrake 清理。

tests/finish-arrival.spec.ts 四个真实场景用例，配合自动制动、终点边界和钱包回归，最终 12 项通过（49.5 s），构建通过（4.69 s）。证据 evidence/finish-arrival-final-tests.log、build-finish-arrival-final.log；本轮未重跑全套。截图 finish-arrival-{1,5}-{main,worker}.png 已落盘，第 1 关截图已查看：仍为现有结算遮罩，不能作为原版结束镜头验收。没有用零重力测试结果替代这次真实道路结果。

接续：恢复 CameraMode=15、MediatorGameFinish 与继续转场；MuMu 同样输入核验制动轨迹、角速度、碰撞与结束时序；覆盖 bonus/组合/全部关卡出生区，落实驻留资源接管/空间裁剪并测内存与加载尖峰。PhysX MovePosition 对 Rapier 动态位置适配仍待原版实测。宝箱回溯、剩余局内机关、全主题/皮肤及微信/抖音实机目标均保留，目标 active。


## 2026-09-08 CameraMode 15 结束门镜头

解析 CameraOperator.ChangeMode 的跳表（0xcfb298，索引 15，基址 0x22f82b8），实际分支为 0x22f8698，选择 GateFinishCameraPoseProvider 并 SyncWithGamePoseProvider，继承当前属性。不是 GameFinishCameraPoseProvider（mode 18）。源目标为 GyroTarget 中 StopSphere 保存的下一关出生 OrientedPoint.TransformPoint(0,0,-10)。main 按下一关摆放矩阵与合成出生锚点计算该目标，进入终点时 beginFinish，保留当前镜头姿态。

源目的属性：distance=CAMERA_DISTANCE+3，angleVertical=CAMERA_ANGLE_VERTICAL+5，angleHorizontal=0，verticalOffset=CAMERA_VERTICAL_OFFSET+sin(Time.time)*0.2；targetPosition 按 clamp01(dt) 从当前目标插值。四个属性速率 [distance,yaw,pitch,offset]=[1,3,1,1]，distance 插值权重上限 0.2，yaw 每帧变化上限 5°，pitch 限制 [0,89]。原代码及常量存于 evidence/finish-camera-source，包含源机器码/反汇编和逐文件 SHA256。

新增只读 native-levels camera-constants，MuMu PID 4802 检查 GameConfig 实际 isPVPGame=false、distance=5、pitch=26、offset=-0.5，证据 native-finish-camera-constants.json。故当前主线结束门目标为距离 8、俯角 31°。PVP getter 是 7/30，当前客户端未覆盖 PVP 镜头，不能将主线固定参数推广到该模式。未修改存档/购买。

GameCamera 增加结束门分支，保留进入时 target/yaw/pitch/distance/offset，暂停零 dt 不改变位姿，reset 清理结束状态。tests/finish-camera.spec.ts 检查首帧 .1 秒 yaw=8.4、pitch=21.1、distance=5.3、offset=-.05，继承/拷贝目标、收敛、角速度上限与重置；实际第 1/5 关 main/worker 仍达到下一出生点并完成继续。最终专项 7 项通过（42.6 s），构建通过（4.14 s），日志 finish-camera-tests.log/build-finish-camera.log。没有重跑完整测试套件。

截图已更新并另存 finish-camera-{1,5}-{main,worker}.png；已检查第 1 关，镜头拉远/抬高后可见更长道路，现有结算遮罩仍覆盖球附近。它不能作为原版完成 UI 的验收图。当前继承的普通 GameCamera/GyroTarget 过滤仍有既存差异、Time.time 与浏览器时间相位尚未对齐，源后续 mode 18/结束 UI/转场时序及 MuMu 同操作录像对照仍待完成。总目标 active，全部剩余局内机制和小游戏性能门禁保留。


## 2026-09-08 MuMu 实际通关与结算回调证据

以既有只修改 progress 的 mumu-save 工具将 73→1，保留购买、球29和库存。进关画面显示两把钥匙、100金币及VIP剩余时间；五次相同竖直 swipe（1440×2560，720/1800→720/900，350ms，间隔2秒）完成原版首关，输入时间戳保存在 native-finish-gestures.json。screenrecord 720×1280 录像 native-finish-1.mp4、ffprobe 信息 native-finish-video-info.json 与每2秒一帧接触表 native-finish-contact.jpg 已落盘并检查。

这次拾取第三把钥匙后进入 12 格 MatchThree 奖励界面，并非普通完成界面。接触表约14秒仍在门前，约16秒球已前移，约18秒进入匹配界面；这是粗采样观察，不作为逐帧/精确坐标验收。本轮没有点击奖励格或继续领取，不能据此推出普通 ScreenFinish 的按钮/发奖时序。第一关皇冠球参数亦不等同客户端默认铁球的同条件性能基准。

ARM64 MediatorGameFinish.Init 调用 Economy.PauseRun，OnEconomyRunPaused 禁用输入、通知结束声音后通过 DOVirtual.DelayedCall 等待约1.8秒（常量0xcf9b08=1.7999999523162842，ignoreTimeScale=true）。此次方法实际执行后，只读解析已初始化的回调槽：0x4b852d8→0x2217424 ContinueFinish，0x4b852e8→0x22174b4 OnEconomyRunFinished；证据 native-finish-callbacks.json。ContinueFinish 调用 Economy.FinishRun，后者委托 GameTimer.StopTimer。需要继续追踪 GameTimer 的回调时序，不能把1.8秒直接当作门触发到所有完成UI出现的精确总延迟。

OnEconomyRunFinished 将拥有钥匙与本局钥匙相加后限制到0…3；isPremium=false 分支在总数3时 ShowMatchThree，否则 ShowFinishScreen。当前包 isPremium 恒false不等同免广/VIP购买，不能因为用户购买免广就跳过匹配奖励分支。源还设置 collectedCoinCount×10 的基础奖励，零枚时回退10、rewardMultiplier=2；实际入账/领取路径、不同 GameType、奖励翻倍仍待完整解析，不在本轮更改钱包以免重复结算。

新增 native-levels finish-callbacks 只读命令，NDK 编译及 MuMu 实测通过；全部 MediatorGameFinish 方法与 Economy PauseRun/FinishRun 的机器码/反汇编/SHA 清单保存于 evidence/finish-mediator-source。游戏运行时代码未修改，因此没有把前轮7项测试/构建记作本轮新验证。

采集后用本次备份恢复进度到73（restore仅覆盖关卡/attempts/falls，不回滚购买和当前库存），读回校验通过；native-finish-restored-home.png 已检查，LEVEL73、皇冠球及VIP仍在。原始跳转/恢复记录分别 native-finish-jump-1.json、native-finish-restore-73.json。

计划修正：现有 completeFinish 仍等制动active=false才暂停并弹临时窗口，这与原版回调驱动流程不一致。下一步先恢复 PauseRun/StopTimer→普通完成或三钥匙分支→后续镜头/ScreenFinish与继续；保持制动与结算展示独立，核对暂停是否该影响动画/非缩放时间，再替换临时窗口。未把本次匹配画面当作普通结算样式。局内全部机制、宝箱回溯和小游戏适配/真机性能范围继续保留，目标active。


## 2026-09-08 结算时钟与制动解耦

补齐 GameTimer.StopTimer/Update/DoStopTimer/LateUpdate 的源审计：StopTimer 保存 Action 并设置 +0x49 标志；Update 清标志后 DoStopTimer，计时器即使已经停止也调用 Action。LateUpdate 处理的是 StartTimer，不是停止回调。因此 PauseRun 和 FinishRun 通过 Update 回调推进，不等待 AutoBrake 的停止距离。原始方法及 SHA 已加入 finish-mediator-source。

新增 FinishClock：pause-request→delay（未缩放1.8秒）→stop-request→done，start 不重复启动，load/debug reset 取消。main 每可见帧使用未被物理 dt 上限截断的 elapsed 更新时钟；以随后 update 消费请求模拟源队列阶段。Unity MonoBehaviour/DOTween 具体执行排序仍可能相差一帧，不能声称按原版逐帧完全一致；后台挂起与恢复策略也尚未平台验证。

终点 enter 启动时钟，球制动仍独立更新。临时完成界面由时钟到达触发，不再等待 autoBrake.active=false；显示完成界面时不暂停物理/结束镜头，制动完成仅清 finishing。普通暂停窗口依然使用 paused。finishScreenShown 供验证；load 和 debug reset 清时钟/遮罩。暂时保留现有完成界面与继续动作，本轮没有把三钥匙匹配奖励、原 ScreenFinish 动画/领取/按钮延迟或后续镜头模式冒充完成。

测试新增 source-clock 的队列阶段、未缩放延迟、重复 start、取消和只回调一次；四个真实第1/5关 main/worker arrival 测试新增断言：finishScreenShown 时 finishing 仍为true、paused=false，之后球仍抵达下一关出生点。最终测试与构建结果另记本节末。

原版完整结算还涉及库存钥匙分流、基础奖励/翻倍领取、继续转场及 GameFinish 镜头，当前钱包仍沿用先前通关入账方式，需后续按完整交易路径修正。保持 MuMu 同操作录像比对、所有局内机制及微信/抖音实机性能验收待办，目标active。

最终结算时钟/真实跨关/终点事件/钱包共10项通过（46.5 s），构建通过（3.92 s）。日志 evidence/finish-clock-tests.log、build-finish-clock.log；本轮未重跑全套。界面按时钟出现且未冻结制动的 main/worker 断言通过；完整原版 UI、匹配奖励及平台验收仍待完成。


- 2026-09-08（结算UI源清单）：audit-finish-ui.py 从1985节点 UI_CanvasScreens 中提取五种 ScreenFinish，节点数142/95/21/95/17，直接 sprite/字体无缺文件，四种依赖外部共享金币粒子。源布局、绑定、active/CanvasGroup/过渡配置及包SHA全部落盘；直接绑定解析和节点唯一性检查通过。
- FINISH_UI_INVENTORY.md 记录独立资源清单、共享依赖与移植顺序。尚需确认 ARM64 UI+0x308 的实际变体，不能用32位恢复字段偏移直接推断；运行界面仍是临时弹窗，本轮未修改游戏代码/重跑游戏测试。MuMu普通结算对照、所有剩余机关和小游戏实机门禁保留，目标active。


## 2026-09-08 主线变体运行字段确认与独立打包

native-levels 新增 ui-finish-fields：只读扫描已初始化 metadata 槽，校验 namespace=Gyro/type=UI，按 FieldInfo.parent 检查字段表归属后导出 screenFinish* 名称/偏移，不调用 Unity、不写运行内存。MuMu PID17413 找到 UI 元数据槽0x4b8aff0，screenFinishTabs offset=776（0x308），SBL=784（0x310），Boarding=792，Challenge=800。证据 native-ui-finish-fields.json。这直接闭合 MediatorGameFinish.ShowFinishScreen 读取 UI+0x308 → screenFinishTabs → UIPropsCanvasScreens.screenFinishTabs → 组件63d32d2d_47097/根63d32d2d_8534 的选择链，不再依赖32位偏移推算。

新增 package-finish-ui.py，严格检查运行字段证据后生成 public/assets/finish-ui-layout.json（kind=finish-ui-layout-v1）。主面板142节点、外部共享节点2个、定位父级3个、19个sprite/2字体引用，296320字节。父级保留Canvas/CanvasScaler/CanvasGroup及RectTransform/TRS，过滤其他窗口控制器；parent 从原包索引转为稳定 parentId，校验全部父引用闭合。主子树源组件、RectTransform/active/文本/图片等仍完整保留；共享节点单独标识，不伪装为面板自有对象。该文件是UI布局schema，不是可直接传给LevelScene的PrefabPack。

总资源打包脚本已挂接此步骤，inventory-levels 加入显式依赖。重新执行 audit-finish-ui 和 inventory-levels，当前15972个引用文件/781767489字节，无缺文件；之前两个非局内字体贴图未解析ID仍如实保留，不因本次面板完整就宣称全项目依赖已完结。面板 sprite/字体文件检查、父引用闭合和绑定选择断言均通过。审计 selectionVerified 已依据运行证据更新。

当前 main 仍未加载此布局文件，通用结算窗口未替换，本轮不会声称新增UI视觉效果或运行性能收益。下一步按这份明确选择的布局实现 RectTransform→屏幕定位、源淡入及按钮生命周期，处理共享金币粒子和运行脚本改写；再与MuMu普通结算录像对照。完整剩余局内机制、宝箱回溯、小游戏适配/真机性能目标不变，目标active。本轮为只读原生验证与资源打包，未重跑无关的游戏全套测试。


### 结算源UI布局转换

根 Canvas 序列化尺寸/scale为零不能直接作为运行布局使用，须按 CanvasScaler 与真实视口重建；child anchoredPosition 是轴心对锚点参考的偏移，不等同源 localPosition。已落实纯布局矩阵并验证源8°标题、拉伸遮罩、非中心轴心与跨屏比例。4项专项及构建通过，日志在 clientThreeJS/docs/evidence/ui-layout-final-tests.log、build-ui-layout-final.log。源运行脚本对显隐/布局的改写及实际渲染仍待接入，不能以几何测试代替MuMu视觉验收。


### 源UI sprite渲染与图集污染定位

仅导出sprite裁切PNG会丢失原始矩形、padding和九宫格边框；改用实际SpriteAtlas条目时还必须读取packingRotation及每个Image的m_UseSpriteMesh。首轮独立样例漏传后者导致紧密图集邻图污染；全源101个Image测试检出，补回源顶点/三角形后截图污染消除。disk的64像素纹理边框32+32使中间UV为零宽，绘制时仍须保留中间拉伸面。提取、SHA记录和打包在clientThreeJS/scripts，最终9项专项通过、构建通过；ui-image-source-render.png只是独立样例，完整UI/自定义星星shader和原生逐帧对照仍待验证。13张全分辨率UI纹理共4.43MB文件/23.46MB基级RGBA估算，不是平台性能验收。


### UI星星shader迁移

原材质保留_SrcBlend=1/_DstBlend=0，但实际shader pass固定SrcAlpha/OneMinusSrcAlpha，包括Alpha通道；必须审计shader而非只读残留材质字段。源GLES实现双纹理RGBA插值与Image/Material双乘色，_MainTex及ST无参与。已提取shader2–5/SHA/状态与纹理，GPU用已知色验证alpha=.5得到目标alpha=.25，真实灰星至金星截图通过样例检查；UI图片/布局/星星10项专项及构建通过，完整结算与平台验收仍待完成。证据在clientThreeJS/docs/evidence/ui-star-shader和ui-star-interpolation.png。


### UI层级状态与绘制作用域

独立导出面板后不能按JSON对象排序当作绘制顺序，应从RectTransform.m_Children重建保留节点的兄弟次序；CanvasGroup ignoreParentGroups不解除父级inactive。uiHierarchy保留源数据并以显式覆盖处理运行状态，生成5个源Mask的begin/end作用域，3项专项及构建通过。GPU stencil/Text/源Show生命周期仍待接入，命令平衡不等于遮罩视觉验收。证据：clientThreeJS/docs/evidence/ui-hierarchy-tests.log。


### GPU stencil迁移

源Mask需要begin写位、子级测试、pop恢复，showMaskGraphic=false只关闭颜色；透明孔需AlphaClip避免写入遮罩。按源位规则实现后，以GPU像素测试验证嵌套交集及退出恢复，额外旧位探针验证根层真正清零，不能只检查无遮罩兄弟（它关闭测试即使脏位也会正常显示）。10项专项/构建通过，根层补测通过；共享纹理身份及释放计数验证通过。源5个Mask的完整面板呈现、Text和原版实机对照仍待完成。


### UI文字特效与布局边界

源Text共22节点，字号/溢出/BestFit并不统一；应先保留配置和字体SHA。Outline四方向副本后再Shadow会作用于整个结果，共10份，UseGraphicAlpha按Color32乘积截断，不能直接用CSS描边代替。已生成索引顶点效果并在本地Fredoka固定字号样例验证一次draw、释放归零，10项专项及构建通过；字号自适应/换行/基线和字体引擎抗锯齿差异仍需对齐，样例不算TextGenerator复刻完成。


### Unity Font归一化与生成输入

源Font的m_FontSize不能统一按1处理：Fredoka为1、LegacyRuntime为13。提取原Font后验证嵌入TTF字节一致，并独立解析head/hhea交叉验证ascent/descent/lineGap，可发现错误归一化。Text源码配置+100是UpperLeft、8000是MiddleRight，不能全部居中。源22个生成设置与字体度量9项专项/构建通过；TextGenerator的BestFit/advance/kerning/换行仍未实现，输入设置测试不代替原版排版验证。证据ui-font-source.json、ui-text-settings-final-tests.log。


## 2026-09-08 原版 TextGenerator 缓存与源节点匹配

上一目标轮仅回答定位问题，属于无实现进展；本轮重新检查工作树、工作流与缓存后，补齐可复现的文字证据匹配。没有修改原版存档、购买或运行内存。

scripts/native-text.c 为被动 ARM64 内存读取器，/proc/PID/mem 只以 O_RDONLY 打开，不调用 Unity。已保存 evidence/native-text-cache.json：3.40、PID 17413、253 个候选。klass 由元数据槽 0x4bfe068 验证 TextGenerator；读取 m_LastSettings(+0x20，96 字节)、m_Verts(+0x88)；UIVertex stride=108，position+0、UV0+44。对象/列表和顶点二次读取一致后才输出。仅采集可打印 ASCII 1–80 字符、4–512 顶点，非全量文字普查。稳定缓存也可能是隐藏或尚未回收对象，不能据此证明当前可见节点归属。

8 个原生方法的 .bin、带调用注释反汇编和 SHA 已归档 evidence/ui-text-native-source/manifest.json，包括 Text.GetGenerationSettings/OnPopulateMesh、TextGenerator.PopulateAlways/Populate_Internal_Injected。源 ELF SHA 一并保存；托管包装最终进入引擎 icall，不能把托管参数恢复当成完成了字体布局。

新增 scripts/match-native-text.py，运行 python3 scripts/match-native-text.py 生成 evidence/native-text-matches.json，校验源布局哈希，逐项匹配文字、请求字号、BestFit 开关及范围、anchor、lineSpacing、pivot、overflow、固定 Rect 尺寸。22 个源 Text 中 17 个存在“已采集字段相符”的候选；4 个无匹配：50×50 的 2x、+100、+120、+1:30；拉伸 AD 需求解父布局，本离线报告不猜其尺寸。报告保留同文字拒绝原因，缓存索引和几何 SHA，输出除以 scale 后且未执行 PixelAdjustPoint/Outline/Shadow 的局部边界。

纠正部分缓存抽查的结论：COMPLETED! 不仅有 560×64/请求字号22 的其他候选，还存在 index158、560×80/请求字号63/BestFit10–80 的源参数匹配记录，40顶点。脚本匹配后发现这一事实；第一次测试因误断言无匹配失败，保留 native-text-settings-tests.log，修正为只接受匹配候选并排除两份不同参数记录。不可把请求字号63直接当作引擎最终 BestFit 字号。

tests/ui-text-settings.spec.ts 用独立原版缓存校验当前 uiLayout + uiTextSettings 对上述17节点的输出，视口1440×2560，scale约1.91904044，覆盖所有现有采集字段。最终3项通过(463ms)，evidence/native-text-settings-final-tests.log；构建通过约4.2s，build-native-text-settings.log，既有大包警告仍在。

证据边界：未采集 font 身份、style/color/richText 等全部字段，不能称完整 generation settings 相等；17个节点也不代表17个独立活跃实例。同样未验证最终 BestFit、基线、换行、字距、动态 atlas 和像素取整。缓存只作开发证据，未放入 public/assets、未做字符串硬编码查表。下一步恢复可复用的字体布局/字形图集与完整 UI 提交路径，用这些原版几何做误差对照，再接入主游戏。主游戏结算仍旧弹框，不宣称视觉1:1或小游戏验收完成。总目标 active。


## 2026-09-08 UI 渲染层串联与 GPU 所有权验证

上轮为进展：已有独立原版字形缓存匹配和测试。本轮重新检查 ui-layout/ui-hierarchy/ui-image/ui-stencil 以及 Three 本地清屏实现，新增 src/runtime/ui-layer.ts，将源布局、组件绘制顺序、CanvasGroup alpha 和 mask begin/end 提交串联。GraphicFactory 必须返回每个请求的 Image/Text，不能静默略过；返回时移交独占 geometry/material，纹理仍由外部共享缓存持有。TextGenerator 尚未实现，生产调用若缺少 Text 工厂应报错。

UILayer.rebuild 按源节点/组件复用基础几何（Mask begin/end 共用），每个命令独立 stencil 材质与 renderOrder；构建全部成功后才替换旧层。构建失败释放已取得的新几何和材质，旧画面保持。源基础材质在克隆后释放；共享 Texture 由 uiStencilMaterial 保留身份。dispose 幂等。render 使用调用者当前 framebuffer，保留已有颜色/深度，只在需要 mask 时清 stencil，检查目标确有 stencil；临时关闭 autoClear 并在 finally 恢复。渲染层拥有本次 UI pass 的 stencil 内容，调用者必须在依赖场景 stencil 的 pass 之后提交 UI。当前不负责事件分发、MonoBehaviour、RectMask2D 或每帧动画更新；rebuild 用于结构/状态变更，不能逐帧重建所有 UI。

新增 tests/ui-layer.spec.ts：真实 GPU 验证绿色已有背景保留、蓝色子图形被源 Mask 限制、后绘红色兄弟覆盖、CanvasGroup .5 混合、无 stencil 目标拒绝、失败重建保留前帧、反复重建驻留几何稳定、重复 dispose、所有已创建 geometry/base material 各释放一次、外部共享纹理不被提前释放。源结算包147节点的图片层用真实纹理运行，Text在测试副本中明确禁用，不是替代字体。普通源状态61命令/61 draw calls；强制激活保留分支以覆盖全部源 Mask 时105 calls；关闭根后0命令。重复打开后全部释放，renderer.info.memory 中 geometry/texture归零。

图片层截图 evidence/ui-layer-source-images.png 已检查：徽章、标题条、星星和按钮资源提交可见；文字缺失是明确的测试条件，另外一些白底/占位图形状态仍未核验，不能凭截图假定它们已对齐原版。并未把源静态序列化 active 状态当作源控制器初始化后的完整结算画面。

最终 ui-layer/ui-hierarchy/ui-stencil 共6项通过(3.5s)，日志 evidence/ui-layer-final-tests.log；构建通过，build-ui-layer-final.log。尚无整套 UI batching，61 calls 是隔离图片层实测而非小游戏达标结果。后续在不跨越 mask 边界、不打乱透明绘制顺序的前提下合并连续兼容图形；文字图集、插值动画和主游戏完整结算 UI 接入仍待完成。主游戏继续使用旧结算弹框，未宣称1:1或微信/抖音真机验收。总目标active。


## 2026-09-08 UI 相邻图形合批：源图片层 61→39 calls

上一轮完成 UILayer 串联与 GPU 所有权验证，属于有效进展。本轮重新读取当前代码，将前述61 calls的具体性能问题落到实现与像素证据。

新增 src/runtime/ui-batch.ts，UILayer 默认启用，new UILayer(false) 提供验证对照。只处理标记 default-v1 的默认 UI shader，相邻命令的纹理身份、shader/defines、混合/深度/stencil/颜色写入等状态必须兼容；Mask begin/end 是硬边界，绝不按纹理排序或跨越其他图形。UIStar 插值材质不参与此合批。局部顶点按对应源矩阵变到屏幕坐标，原三角形顺序保留，逐图形 tint/CanvasGroup alpha 与已有 uiColor 相乘后写入 Float32 RGBA，统一 tint 为白色。支持源 indexed/non-indexed geometry；局部 shader 效果、形变、非完整 drawRange 或 geometry groups 不在支持范围，保留单独提交。

合批不修改输入网格。新几何/材质由渲染层接管，未再引用的旧几何和命令材质立即释放，Mask共用几何仍保留。纹理继续使用原对象。drawCount仍表示源逻辑命令数，submissionCount表示实际提交网格数；没有把命令减少误计为源节点减少。UI变更时重建，render不逐帧合批。未来要修改已烘焙颜色/位置需更新合批缓冲或重建，不能只更新已释放的原材质。

验证在同一浏览器GPU、750×1334视口、同样源图和清屏状态执行未合批/合批对照：普通结算图片层61命令，61→39 calls，减少22/约36.1%；4,002,000个RGBA通道逐值比较，maxChannelError=0、differentChannels=0。强制开启保留分支的覆盖态由上轮105 calls降至58 calls（本次该覆盖态验证可提交和释放，未做其独立全图像素比较）。关闭根为0命令，重复重建驻留几何稳定，最终geometry/textures归零。

新增 ui-batch.spec.ts 专门覆盖重叠透明排序、Uint8归一化逐顶点RGBA、同纹理中间隔了另一纹理不可跨越、Mask入栈/出栈边界和mask内合批。8→6 calls，整图像素maxError=0，输入矩阵/tint保持不变，共享纹理身份保持，最终资源归零。与 ui-layer、ui-stencil 合计4项通过(5.2s)，evidence/ui-batch-final-tests.log；构建通过，build-ui-batch.log。source图片层测试同步使用未合批作独立基准，截图仍为 ui-layer-source-images.png。

限制：这些是本地浏览器隔离UI图片层数据，不是整个游戏draw call或微信/抖音真机结果；没有证明重建CPU时间/内存峰值改善，也未完成动态图集或跨纹理合批。文字排版、源结算控制器状态/动画及主游戏接入仍待办。主游戏旧结算弹框保持，未宣称1:1或平台验收。总目标active。


## 2026-09-08 原版单行文字度量规则：41条候选顶点精确复现

上一轮完成UI相邻合批及像素验证，属于进展。本轮重新读取字体导出、缓存和原生Text.GetGenerationSettings证据，以实际嵌入TTF开展排版度量对照；不使用浏览器默认文字尺寸猜测。

新增 scripts/probe-native-glyphs.py，用 /Users/jiaojian/Documents/cocosgame/.venv/bin/python 运行；证据 native-glyph-probe.json/log。Pillow11.3.0、FreeType2.13.3，ImageFont.Layout.BASIC、逐字符 hinted advance，tight raster ink bounds。校验字体TTF以及输入source/cache/match哈希；不修改原版内存、存档或主游戏。搜索字号与0/1/2像素边距时，仅允许整条标签共用一个平移，不能为各字符单独拟合位置。

17个源节点对应41条候选关联（其中25个不同cacheIndex，不能说41个独立活跃节点），全部以1像素边距取得零字形边界/字距误差。全部是当前Fredoka样本，不覆盖LegacyRuntime。进一步加入 singleLinePrediction：完全不读取缓存顶点选择字号或平移，仅使用源参数、字体度量和字符测量，预测每个quad的4个顶点XY。41条关联均maxVertexError=0。

与这些样本一致的单行规则：
- 光栅像素字号 floor(requestedSize×scale)。启用BestFit时，从max到min按整数请求字号搜索，使用取整后像素字号的hinted advance和字体lineSpacing×pixelSize判断是否在extent×scale内。不是简单 floor(rectHeight/lineSpacing)。CLAIM x2最终匹配请求50/像素95，不能因源高度60而误选49；自由搜索里49向上取整也同像素，但独立单行规则选50。
- 字符advance逐个累加，tight ink quad四边各加1像素；空格只推进advance，不生quad。在这些样本中不需要GPOS/浏览器kerning。
- 水平原点 floor(extentWidth×scale×(anchorX−pivotX)−advance×anchorX)。已验证MiddleCenter与MiddleRight，pivot均(.5,.5)。不泛化为所有9种对齐。
- 中线基线分别对半行高与ascent取最近整数再相减：round(lineHeightPixels/2)−round(ascentPixels)，不是先相减再round。样本没有恰好半整数，尚不能区分tie-to-even和tie-away。
- 例如COMPLETED!自动字号66、126px、平移(-412,-47)；66显示字号33、63px、平移(-35,-23)；8000固定57、109px、平移(-77,-40)。这些值只作为证据，不写成生产字符串查表。

验证为TTF→度量→所有quad顶点与独立MuMu缓存逐值比较，41条全部通过；probe产物保留拟合与独立预测两个结果以避免用已拟合位置自证。没有游戏代码改动，无需重跑游戏构建/物理测试。不能把几何吻合宣称字形纹理像素完全吻合：本次没有读取Unity字体atlas位图，也未验证浏览器Canvas能生成相同hinted字形。源包装方法仍不能证明引擎内部完整实现。

下一步：将验证过的单行计算落为可复用的TS布局模块，字体后端提供像素字号的glyph metrics/atlas，禁止使用缓存标签硬编码查表；评估可在浏览器及微信/抖音运行的同等字体光栅路径，并量化缓存/atlas内存。随后接入UILayer Text工厂、Outline/Shadow与源结算控制器。换行、富文本、最小字号仍溢出、其他锚点、像素取整tie、多视口和活跃实例归属仍待验证。主游戏结算UI未替换，未宣称1:1/小游戏验收，目标active。


## 2026-09-08 TS单行布局内核落地，544个原版顶点通过

上一轮通过FreeType探针获取单行规则，本轮属于实现推进。新增 src/runtime/ui-text-line.ts，输入 uiTextSettings 的设置、源UIFontDefinition与独立 UIGlyphMeasure 接口，输出请求字号/像素字号、advance、origin、pixel quads和unitsPerPixel。接口提供每字符每像素字号的hinted整数advance与baseline-relative、Y-up tight ink bounds；空格用null ink。未依赖Python、DOM或Canvas，未写入任何标签→布局查表，便于后续替换跨平台字体后端。

实现BestFit从max向min搜索，像素字号floor(size×scale)，以hinted advance和源lineSpacing判断是否容纳；每个像素字号/重复字符在本次调用内复用测量。字形四边1px边距，水平floor对齐，中线高度/ascent分别取最近整数。输出为TextGenerator缓存层的pixel geometry，未执行后续PixelAdjustPoint与Outline/Shadow。半整数暂取ties-to-even，尚无原版tie样本证实。支持经过样本验证的MiddleCenter/MiddleRight、中心pivot、普通ASCII单行；换行/富文本/其他锚点/字体样式、fixed字号需要换行截断、BestFit最小仍容不下、零fixed请求字号明确报错，不能默认为完整TextGenerator。

新增 scripts/export-ui-glyph-fixture.py，从原版嵌入TTF独立测量字形，生成 docs/evidence/ui-line-glyph-fixtures.json：1字体、2287条glyph metrics、93273字节，记录TTF/输入哈希与Pillow/FreeType版本。只在测试证据目录，未放入public/assets。该fixture不包含字符串布局、选中字号或平移；TS需要实际执行搜索、累加advance与定位。生产字体光栅后端仍待实现。

tests/ui-text-line.spec.ts 通过 uiLayout(1440×2560)→uiTextSettings→uiTextLine，对独立MuMu缓存的17节点/41候选关联、544个quad顶点XYZ逐值比较，全部精确相等；25个不同缓存索引，非41个独立活跃实例。明确校验CLAIM x2自动字号50/pixel95，COMPLETED!字号66/origin(-412,-47)。同时验证不支持的路径不能静默生成错误文字。与文字设置/字体度量合计5项通过，证据 ui-text-line-final-tests.log；构建通过，build-ui-text-line-final.log。此前日志保留，不重复游戏物理全套。

下一步仍是实际字形光栅与atlas后端：需要与原版 hinted 度量一致，并验证字形位图/UV、不同像素比、纹理缓存与释放；再将quads接入UILayer Text工厂和源结算控制器。当前未接主游戏，仍是旧结算弹框，不能把TS几何对照通过称为完整视觉1:1。微信/抖音字体加载及真机性能尚未验收。总目标active。


## 2026-09-08 浏览器FreeType WASM后端与有界度量缓存

上一轮已落地TS单行内核，本轮将独立字体测量接口接到实际浏览器光栅后端，属于实现进展。参考FreeType官方接口文档（https://freetype.org/freetype2/docs/reference/ft2-face_creation.html ，https://freetype.org/freetype2/docs/reference/ft2-glyph_retrieval.html），使用FT_New_Memory_Face、FT_Set_Pixel_Sizes、FT_Load_Char(RENDER|TARGET_NORMAL)；字体bytes必须在FT_Done_Face前保持有效。浏览器路径没有共享同一face跨线程。

新增 scripts/ui-freetype.c 和 build-ui-freetype.py，Emscripten本地5.0.7编译其锁定VER-2-13-3端口（与Pillow验证FreeType2.13.3相同）。编译脚本核对端口版本，记录工具版本、命令、端口/包装源码和输出SHA。无文件系统、web/worker环境、64KiB栈，初始4MiB线性内存，可增长上限32MiB。输出 public/assets/ui-font-engine/freetype.wasm 571582字节、freetype.js 11997字节；同时附FreeType FTL、zlib、Emscripten许可证及NOTICE，清单脚本要求这7文件存在。首次Homebrew SDK/许可证定位失败已修正，失败日志保留，最终构建证据ui-freetype-build.json与ui-freetype-build-final.log。

src/runtime/ui-freetype.ts实现按需加载的共享WASM实例、owned font face/原TTF内存/输出缓冲、LRU度量缓存和独立rasterize。默认度量上限1024条，可配置；BestFit measure只留advance/ink，不留每次尝试字号的位图副本。rasterize返回由调用者持有的紧裁剪单通道alpha；字形位图负pitch、空格无ink、缺字、无效字体/尺寸、已释放font均明确处理。WASM调用后重新取heap视图以适应内存增长。关闭字体按face→缓冲/原字节顺序释放，dispose幂等。引擎dispose关闭持有字体；WASM实例线性内存仍随实例引用保留，并非立即归还OS。

export-ui-glyph-fixture.py补充可复现的70份独立Pillow灰度位图SHA（Fredoka C/O/L/E等、数字、上下延字形和空格，5种像素字号）。tests/ui-freetype.spec.ts实际在浏览器加载WASM：2287条度量与独立TTF fixture相同，70位图SHA相同；实际font.measure接入uiTextLine后，原版544个缓存顶点仍逐值一致。后者为原版几何证据，前者的位图仅与独立Pillow相同，尚未读取Unity atlas位图，不可宣称原版文字像素验收。

最终本机样本：加载/实例化约6.9ms（可能已有缓存，非冷启动保证），遍历2287度量98.5ms；128条LRU上限保持，active分配55520字节，关闭/无效字体打开失败/连续10次打开光栅关闭后均回到144字节基线；线性内存始终4194304字节。只说明此测试中的分配回收，非全进程内存、GPU内存或真机性能。3项测试通过848ms，ui-freetype-final-tests.log；构建通过3.9s，build-ui-freetype-final.log；资源清单重建missingFiles=[]，仍有原先2个未解析资源ID，不作为完整行为通过。

工作流：修改C或升级编译器/FreeType时先 python3 scripts/build-ui-freetype.py，审查版本/SHA与许可证；运行浏览器度量/位图/原版顶点测试，再 inventory-levels.py 与常规build。不要把仅修改纹理资源当作无需核验字体后端更新。

下一步实现glyph atlas与Text mesh工厂，接入UILayer/Outline/Shadow以及源结算控制器。当前后端未接主游戏；微信/抖音仍需要验证其WASM加载/实例化适配、字体缓存与小游戏真机性能。构建ENVIRONMENT含worker不等于已实现字体Worker队列，本轮未实测Worker。换行、富文本、其他对齐和源atlas位图仍待办，目标active。


## 2026-09-08 GPU字形图集与Text网格工厂落地

上一轮已有真实FreeType浏览器后端，本轮将其连接GPU字形图集、单行布局、Outline/Shadow和UILayer，属于实现推进。新增 ui-glyph-atlas.ts 与 ui-text-mesh.ts；ui-image默认shader增加UI_GLYPH_ALPHA路径，从R8纹理红通道取alpha，保持vertex Color32颜色、组alpha、stencil与既有相邻合批接口。

UIGlyphAtlas每字体一张固定页，默认1024×1024，单通道R8/无mipmap/LinearFilter/unpackAlignment1，CPU像素存储1MiB，基础纹理数据量1MiB（不包括驱动分配/对象开销，并非实测进程GPU字节）。字形tight alpha四边留1像素透明边，shelf分配，top顶点用v0对应数据首行，防止上下翻转。UV在生命周期内稳定，重复get不重复上传标记。单字形超页或总容量满均明确失败，保留已有条目/位置/纹理版本；不会扩容或逐出仍被mesh引用的glyph。调用者必须先释放UI mesh再释放/替换atlas。atlas拥有CPU/GPU纹理，font由调用者持有；dispose幂等并断开纹理image.data对原CPU缓冲引用。

uiTextMesh使用uiTextSettings→uiTextLine→atlas生成真实quad UV，pixel坐标转local units，按源组件次序应用uiEffects，再用uiColor属性接入默认UI材质。返回mesh独占geometry/material，atlas纹理共享。自定义Text材质、尚未支持的排版模式仍明确拒绝；最后的Canvas PixelAdjustPoint取整仍未补齐。没有按标签硬编码字体结果。

新增ui-glyph-atlas.spec.ts：GPU读取实际C字形每个像素与独立raster alpha对照，方向/透明padding误差0；重复缓存不增加texture version；超大字形与填满页面均失败且不破坏旧条目；最终renderer几何/纹理数和atlas CPU数据均归零。源图片层保留已验证的17文字节点范围，其中当前静态active状态实际绘出12文字，5未覆盖Text在fixture副本中显式禁用；这不是主游戏跳过文字的逻辑。真实字体+描边/阴影+图片，raw73→batched52 calls，750×1334全图RGBA像素差0；38个缓存glyph，1MiB页用高91像素。重复重建条目数与驻留几何稳定，释放全部资源归零。

截图 evidence/ui-source-text-atlas.png 已检查，标题、徽章数字、CLAIM x2、NO THANKS等实际可见；仍是序列化静态UI状态，含888等模板内容和白底/占位图形，尚未接源控制器动画与实际结算数值。不能把此截图当作MuMu结算最终画面对齐。像素差0指合批前后，不是与原版屏幕差0。

最终ui-glyph-atlas/ui-batch/ui-freetype共4项通过4.3s，证据ui-glyph-atlas-final-tests.log；构建通过，build-ui-glyph-atlas-final.log。默认一次图集更新上传整页，实际动画期/频繁新字号的上传开销仍需测量，不能按静态复用测试推断性能达标。目标设备maxTextureSize、R8路径与小游戏WASM适配待真机验证。

下一步补齐其余5文字节点的源布局和PixelAdjustPoint，恢复源结算控制器初始可见性/实际数值/奖励动画，再把完整工厂接入主游戏。主游戏仍旧结算弹框；尚未宣称完整1:1或微信/抖音验收。总目标active。


## 2026-09-08 preferred尺寸、横向布局组与UpperLeft金币文字

上一轮图集已打通，本轮查明5个被排除Text中的+100并非只缺少一种对齐：源节点63d32d2d_7295附有ContentSizeFitter双轴Preferred(2)，父级coins是HorizontalLayoutGroup。静态sizeDelta173×0必须经自动布局求值。整个包有5个横向组，默认active层级运行4个，全激活覆盖态5个；不能把组总数当成当前有效数。先前测试误断言默认5已纠正并保留失败日志。

新增ui-auto-layout.ts，处理当前包使用的无control/forceExpand/useScale横向组和Preferred fitters。复制RectTransform为运行快照，不修改序列化包；先求Text preferred尺寸，再按父到子顺序处理组，依源m_Children、active和ignoreLayout筛子节点，处理padding（含-8负top）、spacing、childAlignment和reverseArrangement，按源top-left驱动anchor/anchoredPosition。默认宽高由子自身sizeDelta保持；主轴溢出时从padding起排，不擅自居中；非当前包使用的弹性布局/min-fit明确拒绝。通用Unity完整layout priority/flexible negotiation仍未实现。调用方将driven nodes交给UILayer，目前在源UI测试工厂使用，并未接入main。

算法对照Unity官方源文件：
https://raw.githubusercontent.com/Unity-Technologies/uGUI/main/com.unity.ugui/Runtime/UGUI/UI/Core/Layout/HorizontalOrVerticalLayoutGroup.cs
https://raw.githubusercontent.com/Unity-Technologies/uGUI/main/com.unity.ugui/Runtime/UGUI/UI/Core/Layout/ContentSizeFitter.cs
同时从3.40 ARM64提取4方法存入evidence/ui-auto-layout-native-source（附SHA和原ELF SHA）：ContentSizeFitter.HandleSelfFittingAlongAxis 0x48d3a5c、HorizontalOrVerticalLayoutGroup.SetChildrenAlongAxis 0x48d5450、Text.get_preferredWidth 0x48e9634、get_preferredHeight 0x48e9708。后者明确调用TextGenerator.GetPreferredHeight并除pixelsPerUnit；官方main代码不是该二进制的精确源码版本，不把静态对照扩大为源布局逐节点运行验收。

ui-text-line新增uiTextPreferred固定普通字号路径，hinted advance之和/scale与round(font lineHeight)/scale。新增UpperLeft垂直原点ceil(rectTopPixels)减单独round(ascent)，仍只覆盖y pivot=.5；横向pivot使用现有坐标公式推广，+120源pivot.x=1，不可强制改成.5。对其未取得同实例缓存，推广属于实现推论，不称新增原版逐字验收。

真实FreeType、1440×2560视口：+100 preferred=(171.43984375,96.40234375)，MuMu缓存index156=(171.43985,96.4023438)，差仅记录float精度；预测origin(-165,-56)，16个顶点XYZ完全相等。缓存可能仍来自隐藏实例，未证明owner。旧17节点41候选544顶点继续通过。UpperLeft零高静态rect不再被拿去直接生成文字。

源UI fixture新增2x(70px固定且双轴overflow)、+100、+120三节点，现仅排除LegacyRuntime粗体的+1:30和AD两节点。默认状态实际可见15 Text；与图片一起raw76→batched55 calls，全图RGBA差0，47glyph占一张1MiB R8页，usedHeight110，重复重建稳定且最后资源归零。截图ui-source-auto-layout.png已检查：金币数/币图标和倍率条正确执行组内排布；按钮仍同时显示模板CLAIM/8000等重叠状态，须接源控制器切换，不能据此当作最终原版界面。

最终ui-auto-layout/ui-text-line/ui-glyph-atlas共6项通过3.7s，evidence/ui-auto-layout-verified-tests.log；构建通过4.1s，build-ui-auto-layout.log。失败日志ui-auto-layout-tests.log及ui-auto-layout-final-tests.log保留，分别暴露inactive组计数和右pivot处理缺口后已修正。

下一步补LegacyRuntime粗体路径和源结算控制器初始显示状态/数值/动画，再接完整UI到主游戏。PixelAdjustPoint、换行/富文本、native所有实例布局与微信/抖音真机验收仍待办。主游戏旧结算UI未替换，目标active。


## 2026-09-08 ScreenFinish领取内容互斥分支

上一轮自动布局有实质进展。本轮从当前包的ScreenFinish组件引用追踪控制器；类在global namespace，不是Gyro.ScreenFinish，首次按后者提取为空后改为精确全局类。已提取17方法的ARM64机器码/调用注释和SHA，归档evidence/screen-finish-native-source/manifest.json，原ELF SHA沿用已验证来源。归档并不代表17方法都已迁移。

Show(0x209b858)在0x209bb10开始按rewardMultiplier→bonusBoxes→wheel的优先级选择；相关分支分别在0x209bb74/0x209bc58隐藏buttonClaimLabel对象，显示buttonClaimCoins对象。普通分支0x209bccc→0x209bcf4显示label并隐藏coins。直接GameObject.SetActive操作有明确证据，不再保留二者静态同时active的状态。optional buttonClaimCoins为空时源分支不更改这两对象。wheel中的isPremium分支保留于原生代码，但已验证发行版getter恒false；不得因用户购买免广把它视为true。

新增src/runtime/finish-claim-view.ts，仅将上述直接SetActive分支映射为UIOverride：通过ScreenFinish组件与RectTransform/组件ID绑定，优先级和空引用分支保持，源节点不变。mode由调用方/源flags提供，模块不替代Mediator决定奖励模式，不执行倍率、开箱或转盘。未迁移Show整体时间线、UIItem.Show/Hide过渡、延迟继续按钮、奖励递增、退款/广告/库存分支，名称和文档明确限定为claim view。

其他本轮观察：Init(0x209b320)保存rewardContainer原anchoredPosition并隐藏starsContainer；SetDetails(0x209be78)写rewardCoins和rewardLabel后调用ForceRebuildLayoutImmediate，进一步支持上一轮补自动布局的必要性。SetRefillOfferDetails(0x209c174)按amount>0开关refillOffer，有正数时更新sphere sprite及文本。Show先显示Claim、隐藏Continue并创建延迟回调，还根据局部小游戏分支控制其他区域。Mediator后续可再更改这些状态，不能把单个Init/Show截面直接当最终可见状态。它们仍需继续追踪、实现和MuMu时间序列验证。

fixture将claim overrides同时交给uiAutoLayout和UILayer，普通模式不再把CLAIM和8000叠在一起。finish-claim-view测试覆盖普通/倍率/boxes/wheel以及多flag时的优先级，检查源数据不变和继承后的实际Text active。与glyph atlas共3项通过3.3s，finish-claim-view-final-tests.log；构建通过build-finish-claim-view.log。当前14个可见Text+图片raw74→54 calls、全图合批像素差0，45glyph稳定且最终资源释放归零。截图ui-source-claim-visibility.png已检查，领取重叠消失；其他模板状态/白色占位图形仍存在，不能称控制器完整接管或原版视觉验收。

下一步继续Mediator的奖励分支选择、Show/Update时间线和按钮真实状态，再补LegacyRuntime粗体两节点、PixelAdjustPoint并接main。主游戏仍使用旧结算UI，微信/抖音真机待验收，总目标active。


## 2026-09-08 继续按钮延迟证据与资源包配置

上一轮关于跨关落点的回答只核对并说明既有状态，按目标审计记为无新增进展；本轮继续可执行工作，无外部阻塞。完成此前未归档的FinishContinueClock证据链并将配置进入可部署资源包，未缩减整体移植目标。

只读native-levels finish-continue-delay在MuMu PID17413读取GameConfig静态区+0x34两次并检查稳定，native-finish-continue-delay.json记录Gyro.GameConfig.NOTHANKSDELAY=2秒；没有修改游戏内存、购买或存档。额外核查Gyro.GameConfig::.cctor 0x22f6924，0x22f6980写入0x40000000，0x22f6998存入+0x34，与float32的2一致。DG.Tweening.DOVirtual::DelayedCall 0x2492ea4将参数传给SetUpdate(Normal,independentUpdate)，ScreenFinish.Show传true。两个方法的机器码、调用注释与SHA并入screen-finish-native-source，现19方法；本轮重新校验原ELF SHA和全部归档SHA。此前尝试枚举FieldInfo/延迟回调指针失败，最终改用已有klass校验和已证明静态偏移；不能声称本轮完成延迟回调指针的运行解析。

FinishContinueClock负责Show创建延迟、advance接收未缩放秒数、到期一次发出显示请求。Hide/HideButtonContinue取消；直接ShowButtonContinue不取消原待执行句柄。此请求对应UIItem.Show(false)的开始，不代表alpha立即为1。当前模块显式拒绝重复Show，尚未适配源重叠Tween句柄路径。计时采用JS double及1e-12到期容差，不是完整DOTween float32与Unity帧排序仿真，120次1/60只验证逻辑时钟，不代表原版同帧验收；未连接实际暂停/恢复生命周期。

package-finish-ui.py校验3.40运行证据的类型、字段、偏移和值，导出timing.continueDelaySeconds=2、continueDelayIndependentUpdate=true及运行JSON/原生manifest SHA。重新打包成功，finish-ui-layout.json为313578字节，保留142主节点、2共享、3父级、19sprite和2字体。这样正式控制器可从同一资源包取参数，无需引用docs或另写魔法秒数。源Sprite/字体提取校验依然通过。inventory-levels重新运行缺文件为0，2个既存未解析资源ID仍保留；此清单不证明运行行为完整。

专项最终3项通过352ms（finish-continue-clock-final-tests.log），构建通过约4.1秒（build-finish-continue-clock-final.log），大bundle告警仍在。测试读取正式打包参数，覆盖到期一次、取消/重开，以及直接显示与取消的区别。早先2项日志保留，不冒充本轮结果。此次未修改主场景渲染，不生成伪视觉验收图，也未重跑无关全套。

剩余：UIItem淡入/隐藏过渡、完整ScreenFinish/Mediator奖励状态与发奖、LegacyRuntime粗体/PixelAdjustPoint、主游戏接入与原版继续转场、MuMu同操作逐帧对照。主游戏仍为临时结算框。全部局内机关、资源驻留优化及微信/抖音实机性能门禁继续待完成，目标active。


## 2026-09-08 源透明度过渡与命名纠正

上一目标轮完成继续按钮时钟与打包证据，本轮分类为接续实质进展。核查源类型后纠正此前文档中UIWidget名称：真实基类是Gyro.UIItem，UISHTAlpha/UIShowHideTransition位于全局命名空间。UIItem.Init调用GetComponent填入shTransition，所以prefab该字段为null不能直接当成没有过渡；继续按钮同节点有UISHTAlpha及CanvasGroup。

只读提取UIItem及两种transition类，35方法的机器码/注释、ELF SHA、逐文件SHA存入evidence/ui-alpha-native-source。提取了UIButton方法但未将未审计的按钮事件视作已验证。本轮依据为静态ARM64和源序列化配置，没有新增MuMu动态帧采样。

UIShowHideTransition.Show 0x20d46a8先Kill(false)旧Tween；若transitionValue低于地址0xcf9cd8中的float32 9.999999747378752e-05，先设为这个值；目标1，duration=(1-current)*showDuration，配置showDelay与showEase。Hide 0x20d4914目标0、duration=current*hideDuration，无showDelay。SetTransitionValue 0x20d37d4按value>0设置GameObject.active，并保存数值；UISHTAlpha的override随后设置CanvasGroup.alpha，没有在该层改interactable/blocksRaycasts。源Ease枚举Linear=1。继续按钮63d32d2d_6370配置show/hide均0.5秒、linear、showDelay0；根面板0.1秒、关卡条0.2秒，不能用统一CSS时长替代。

新增ui-alpha-transition.ts提供线性透明度内核和UIOverride，覆盖激活阈值、剩余距离时长、反向时取消旧Tween、直接SetTransitionValue不取消、StopTween冻结当前值和active跟随透明度。直接接入现有uiHierarchy进行源继续按钮状态验证：在0.25秒约alpha=.5001，反向0.125秒约.2501，结束active=false；不擅自增加淡入完成前禁用交互。仅支持当前源面板的Linear和0…1范围，其他Ease显式报错。

时钟边界：Show/Hide源码没有像ScreenFinish.DelayedCall那样显式SetUpdate(ignoreTimeScale)，因此模块接收调用者提供的tweenSeconds，不能直接把2秒按钮时钟的未缩放时间规则套给透明度；DOTween全局默认/游戏时间缩放仍需核查。当前实现是JS逻辑插值，不宣称与原版float32/启动延迟/更新顺序逐帧等价。Started/Finished委托调度、UIItem.isVisible防重入（Show已可见直接返回、Hide已隐藏返回）、即时Show不StopTween而即时Hide先StopTween的差异仍由后续owner层实现。没有将此模块当完整UIItem替代品。

专项2项通过360ms，日志ui-alpha-transition-tests.log；构建通过3.93秒，build-ui-alpha-transition.log，大包警告保留。没有修改主场景或生成新视觉验收截图；本轮只验证透明度状态计算与CanvasGroup继承。归档SHA再次校验通过。

下一步按已取证UIItem语义补owner与事件生命周期，再接ScreenFinish控制器/实际奖励数值与主游戏；继续推进原版转场、MuMu同输入对照、其余机关和微信/抖音实机性能验收。总目标active，不宣称UI或局内完整复刻。


## 2026-09-08 继续按钮控制器与源面板状态合成

上一目标轮增加透明度内核和原生证据，为实质进展。本轮检查当前源UIItem.Show/Hide、ScreenFinish.ShowButtonContinue/HideButtonContinue/Hide后，将两秒时钟与透明度内核串成FinishContinueView；不使用静态截图代替控制器。

按ScreenFinish组件ID解析buttonContinue引用，绑定实际UIButton节点63d32d2d_6370；按UIItem.Init同对象GetComponent语义查找UISHTAlpha，即使源shTransition=null仍能工作。要求唯一Alpha及CanvasGroup，缺引用显式报错；复制配置、不改原节点。open启动新等待并执行按钮Hide(true)；两秒到期执行Show(false)。showContinue可提前显示且保留延迟；到期时isVisible守卫使已显示按钮不重启淡入。hideContinue取消等待后按instant执行隐藏；当isVisible已false时，重复Hide(true)仍直接返回，不能强制清零已有淡出。close只取消结算延迟，不主动改子按钮alpha或杀掉其透明度Tween，父窗口的隐藏由外层控制。

显式区分advanceDelay(unscaledSeconds)和advanceTransition(tweenSeconds)，尚未推断DOTween全局时间域/具体帧执行顺序。此类只覆盖原继续按钮，不是通用UIItem：没有提供高亮动画、Started/Finished委托、点击处理、普通结算发奖或父窗口生命周期。重复ScreenFinish.open继续显式拒绝，源重复Show产生重叠句柄路径尚未支持。主游戏仍未替换临时结算框。

新3项测试使用实际源面板检查绑定、子节点active/alpha继承、两时钟分离、提前显示到期不重启、重复Hide守卫、关闭与重新打开；联合时钟/透明度共8项通过406ms，finish-continue-view-tests.log。源GPU fixture进一步接控制器，测试等待、半透明、完全显示三个状态：calls分别53/54/54，合批相对未合批全图RGBA差均0。半程alpha=.5000999999974738，渲染文字淡入截图ui-source-continue-half.png已查看；仍含888模板关号、静态奖励区域和既有白色占位元素，不作为原版完整结算UI验收。

源图片+Text默认状态仍raw74→54 calls，45字形1MiB R8页稳定；controller不新增纹理/图集；最终geometry/textures/atlasCPU归零。源面板测试与controller共5项通过4.9秒（finish-continue-view-render-tests.log），构建通过（build-finish-continue-view.log），大包警告仍保留。这些GPU验证不等于微信/抖音实机性能结果；fixture每个采样重建UI仅用于像素比较，不是已优化的主游戏每帧更新方案。

下一步仍需主线ScreenFinish状态/数值/奖励分支、窗口动画与事件、动态UI不重复重建方案、剩余字体能力，再接入main并做MuMu普通结算录像对照。继续转场、全部剩余局内机制和小游戏平台性能门禁保留，总目标active。


## 2026-09-08 结算数字格式的运行取证

此前读取SetDetails/SetRefillOfferDetails及PID仅核查既有状态，尚未产出实现；本轮继续取得新运行证据并落地文字写入。native-levels新增finish-label-formats，MuMu PID17413只读：SetDetails槽0x4b79c08为"{0}"，fallback槽0x4b7c100为"CLAIM x{0}"。因此源模板+100的加号不是SetDetails保留的格式，实际coins40应写40。首次补球槽0x4b7c108读取失败exit11，部分JSON保存为native-finish-label-formats-attempt.txt；读者增加可读性检查后输出refill:null，成功结果native-finish-label-formats.json，不将未解析当空字符串或已确认格式。未写游戏内存/存档/购买。

新增finish-detail-text按ScreenFinish组件引用写rewardLabel及可空buttonClaimLabel，优先调用方提供的本地化claim格式，否则采用原版fallback。保持Int32输入，不做金币乘10/最低奖励/钱包发放，避免与Mediator职责混淆；返回组件数据副本、不改源节点。仅支持已确认{0}替换，复杂.NET格式显式拒绝；调用者须随后执行源auto-layout以对应ForceRebuildLayoutImmediate。level group显示、补球sprite/文本与主游戏接入仍未完成，正式资源包尚未加入这份新格式证据。

2项专项通过305ms（finish-detail-text-tests.log）。初次构建因测试JSON异构组件联合类型失败，保留build-finish-detail-text.log；修正测试集合类型后build-finish-detail-text-final.log构建成功。此轮未改主游戏渲染、不宣称视觉更新；下一步将实际值与布局/源面板合成，继续解析补球及Mediator奖励分支。其余局内机制与小游戏真机性能门禁完整保留，总目标active。


## 2026-09-08 正式金币格式打包与实际值渲染

上一轮运行字符串取证与文字写入为实质进展。本轮package-finish-ui加入labelFormats及native-finish-label-formats.json的SHA，严格校验3.40 reward={0}、claimFallback=CLAIM x{0}；未解析refill不作为可用格式导出。重新执行源贴图/字体提取和面板打包成功。测试从正式包取格式，不再仅靠docs JSON传参。

源GPU fixture在claim状态处理后执行finishDetailText(coins=40,multiplier=2)，随后uiAutoLayout和网格构建，模拟源SetDetails文字写入→ForceRebuildLayoutImmediate顺序。实际FreeType测得40宽96、123456宽265，assert后者更宽，截图ui-source-runtime-reward.png已检查：40替代+100、金币随组重排。六位数只验证布局尺寸，没有声称该数值在原版奖励中可取得。未验收原版同实例40的原生顶点或逐帧数值动画。

默认文字+图片raw74→54 calls，合批RGBA最大差0，44glyph固定1MiB图集，重建稳定且最终geometry/textures/atlasCPU归零；继续按钮隐藏/半透明/全显示53/54/54 calls，差0。新截图ui-source-runtime-reward-half.png保留淡入状态，原始模板截图不覆盖。界面仍有888关号、未接控制器的星级/倍率/补球区域和白色占位图形，不能称完整结算验收。此次未改main。

文字与图集专项4项通过4.5秒，finish-label-package-tests.log；构建通过build-finish-label-package.log。inventory-finish-label-package.log已重新检查，无缺文件，2个既存未解析ID保留。下一步仍需完整ScreenFinish/Mediator状态、补球格式和sprite、窗口事件、字体缺口和main接入，之后MuMu同操作核验。全部局内机制及微信/抖音实机性能门禁继续保留，总目标active。


## 2026-09-08 补球字符串静态解析闭环

上一轮正式格式打包/实际数字渲染为实质进展。本轮新增extract-finish-label-formats.py，读取原3.40 ARM64 ELF的SHT_RELA，验证R_AARCH64_RELATIVE(0x403)，再从映射地址读取metadata usage。验证kind=5、低位标记和metadata31字符串表边界，索引=(encoded&0x1fffffff)>>1；UTF8解码。来源算法对照本地Cpp2IL LibCpp2IL/MetadataUsage.cs及Il2CppStringLiteral.cs，不依赖猜测或截图文字。

refill槽0x4b7c108→重定位0x4cf3f10→encoded0xa0000a9b→literal1357，精确值+{0}。reward槽0x4b79c08→literal24788为{0}，claimFallback槽0x4b7c100→literal4522为CLAIM x{0}，两项与此前MuMu运行证据交叉校验通过。原运行文件refill:null保留，不伪装为本轮已运行初始化读取。三个值及中间链、ELF/metadata SHA保存finish-label-formats-static.json。该证据解决补球格式未知，不证明补球发放路径或动画。

package-finish-ui现在自动执行解析，将refill及静态证据SHA写入正式面板包；每次打包均校验运行已知两个值和静态元数据。资源打包成功，2项文字配置专项通过，refill-format-tests.log；构建通过build-refill-format.log。未修改主游戏或新增渲染效果，本轮无需截图。补球标签写入/sphere sprite选择、控制器显示、发奖流程仍待接入，全部其余机制和小游戏验收范围保留，目标active。


## 2026-09-08 补球区域状态与数据绑定

上一轮补球格式静态取证为实质进展。本轮依据已归档ScreenFinish.SetRefillOfferDetails增加finish-refill-view：amount>0显示refillOffer，写SphereSprites解析结果到refillOfferSphere.m_Sprite，+{0}写入refillOfferLabel；amount<=0只隐藏区域、不解析sprite/不改旧文字。按源组件与RectTransform引用解析，使用副本和active overrides，不改原包。参数为Int32；本模块不发球、不改库存、不假定球模型编号等于sprite数组下标。

2项测试覆盖0/-1早退、子节点继承隐藏、正数+3及模型29传给解析器、数据不变；解析器测试返回现有sprite，只证明调用/写入绑定，不冒充模型29图标正确性。finish-refill-view-tests.log及build-finish-refill-view.log通过。主场景和GPU fixture尚未接这部分，因此无新视觉验收截图。

同时提取SphereSprites全类原生方法，归档sphere-sprites-native-source/manifest.json与各文件SHA。GetSphereSpriteIndex 0x208a4b8线性查找静态spheresSpritesProgression，找不到LogError并返回0；GetSprite 0x208a620在instance存在时按该索引读取spritesSpheres，否则LogError返回null。映射表和数组的具体数据尚未导出/关联，后续必须补齐，不能把传入callback当已完成源映射。当前finishRefillView允许null sprite以保留源返回路径。

下一步补球模型顺序表与sprite资源依赖后，将补球状态、实际金币、按钮及父窗口合成完整ScreenFinish；仍需Mediator奖励选择/发放、字体缺口、main接入与MuMu同操作验证。所有剩余局内机制与微信/抖音实机性能门禁不变，目标active。


## 2026-09-08 球模型图标映射导出

上一轮补球view为实质进展。本轮native-levels新增sphere-sprite-order，通过klass校验SphereSprites后读取static+0数组，要求与源cctor的0x4a=74长度一致，两次复制比较稳定；MuMu PID17413只读成功，native-sphere-sprite-order.json存74模型。未修改内存、存档或购买。

主UI包63d32d2d_3068的SphereSprites.spritesSpheres有74项，多人HUD包63d32d2d_8484只有21项；本轮选择完整主UI列表，与静态顺序位置配对，非根据模型编号推图标。模型6位于index2、模型3位于index6，模型29在index28。新增package-sphere-sprites.py校验74唯一模型、数组长度和所有catalog sprite文件存在，生成public/assets/sphere-sprites.json附源包/运行证据SHA。总打包和inventory入口已挂接，资源清单重跑。尚未验证当前live instance究竟引用哪个UI prefab，主线选择基于源主UI归属及完整长度，不把它表述成live实例字段读取。

sphere-sprites.ts按源GetSphereSpriteIndex线性匹配，未知模型通知调用方并回退首sprite；空表显式报错。2项测试检查顺序、非顺序模型和未知回退，sphere-sprites-tests.log通过；构建build-sphere-sprites.log通过。测试所有表项循环仅是打包/查询一致性，不等于74张图标逐个原版视觉验收。

本轮映射资源已在客户端，未将所有新增sprite补入独立finish-ui的texture/atlas几何集合，也未接main；接补球view前须处理这些绘制依赖、核对显示图标和资源驻留。下步继续接正确图标到源面板，并完成ScreenFinish/Mediator主游戏流程、MuMu对照。其余全部机关及微信/抖音实机性能门禁保持，目标active。


## 2026-09-08 补球图标裁切依赖与GPU合成

上一轮映射导出为实质进展。本轮extract-finish-sprites扩大源提取范围至主UI SphereSprites的74个sprite，保留源SpriteAtlas映射、packingRotation、边框/裁切padding/纹理尺寸；与面板共92个sprite。package-finish-ui自动生成模型映射，并内嵌sphereSprites及文件SHA，添加所有相关sprite和texture定义，源纹理SHA校验通过。正式面板345746字节，纹理依赖共15个文件，PNG文件总计4674408字节（不是GPU内存）。

源GPU fixture用模型29与数量3调用finishRefillView→sphereSprite→uiAutoLayout→uiImageMesh，图像ui-source-refill-crown.png已查看：+3与皇冠VIP球图标出现，裁切未见白底或错误方向。此前ui-source-runtime-reward.png被当前fixture更新，新文件名另存本轮证据；旧文档中的历史截图路径不再代表当时原样。主游戏仍未接该面板；此图仅为源UI合成，不能称原版奖励场景对照。

补球/映射/源GPU联合6项通过4.6秒，refill-sprites-render-tests.log；构建build-refill-sprites.log通过。raw74→54 calls全图合批RGBA差0，44字形固定1MiB，结束几何/纹理/atlasCPU归零。继续三态53/54/54 calls差0。现fixture加载包中全部纹理，仅验证功能及释放；真实运行应按当前图标和显示节点加载依赖，不能把新增74图标全加载当内存优化已完成。资源清单重新检查，仍2个既存未解析ID，inventory-refill-sprites.log。

下一步完成当前图标按需加载、实际窗口与奖励状态、字体剩余能力和main接入；随后MuMu普通结算同输入对照。全部剩余局内机关、继续流程及小游戏真机drawcall/内存/加载门禁继续保留，总目标active。


## 2026-09-09 UI纹理按当前绘制树选择

上一轮补球依赖与GPU合成为实质进展。本轮新增ui-texture-dependencies，复用uiHierarchy当前active/override绘制树，按Image sprite绑定收集纹理，包含mask写入/退出对应Image，去重；源UI Sprite Interpolate显式收集_Tex0/_Tex1，缺sprite/texture或未知材质在加载前报错。字体/动态glyph atlas由独立生命周期管理。alpha=0但active仍true的图元不擅自剔除，避免破坏后续淡入。

源GPU fixture改用依赖集合加载：当前模型29补球+3状态13/15纹理；文字+图片74→54 calls，合批RGBA差0，继续隐藏/半透明/全显示53/54/54 calls差0；44glyph固定1MiB，重复重建稳定且资源最终归零。ui-demand-textures-tests.log 2项通过4.2秒；ui-demand-textures-unit.log 2项通过282ms，覆盖隐藏树不加载、星星双纹理、去重和缺失依赖报错。build-ui-demand-textures.log构建通过。本轮没有以两张纹理文件数推算OS/GPU实测内存节省。

该模块返回当前依赖ID，不执行网络加载/缓存引用计数/实例释放；调用者在激活原先隐藏Image、更换球图标或材质前必须重新选择并加载差集。本轮主游戏尚未接完整结算，因此这些效果仍是源fixture验证。后续需把生命周期、异步切换失败处理和动态UI更新接到实际窗口，不能只靠fixture重建作为性能方案。原版完整状态、字体缺口、MuMu对照和微信/抖音全部实机门禁继续保留，目标active。


## 2026-09-09 UI纹理所有权与异步关闭

上一轮按绘制树选择依赖为实质进展。本轮新增UITexturePool及lease：按texture ID共享一次加载，每次acquire去重后持有引用；所有依赖成功才返回纹理表。任一失败等待本次已发起请求settled后回滚本次引用，其他lease继续保留原资源；失败条目引用归零后移除，允许重试。release幂等，最后引用释放调用Texture.dispose。关闭pool后禁止acquire，晚到结果立刻dispose且等待中的请求抛出关闭错误。这里没有取消网络/图像解码，挂起请求仍需等待完成，未伪称可中断加载。

该池明确独占loader返回的纹理；不能直接把Assets共享缓存当loader，否则两个所有权系统会互相释放。纹理实例允许同ID多个UI共享，窗口替换时应先acquire新lease并成功重建，再释放旧lease；调用者必须先移除引用纹理的mesh再dispose整个pool。当前没有LRU驻留，最后引用即释放，降低空闲驻留但重复打开可能重新解码，需后续实机数据决定缓存策略。

测试验证替换失败保持旧画面所需资源、成功资源回滚、失败重试、重复释放、并发同ID只调用loader一次、加载途中关闭后晚到纹理只dispose一次。源GPU fixture接入真实TextureLoader与lease，13/15依赖总共13次加载，第二lease复用全部实例；74→54 calls、合批RGBA差0，继续三态差0；最后geometry/textures/atlasCPU归零。联合4项通过4.6秒，ui-texture-pool-render-tests.log；构建通过3.83秒build-ui-texture-pool.log。没有新增UI外观变化，仍是源fixture而非主游戏界面。

未完成：生产窗口状态机/异步替换提交调度、动态文字与alpha的低成本更新、字体缺口、完整ScreenFinish/Mediator和main接入；MuMu普通结算与小游戏真机内存/加载尖峰仍未验证。全部局内机制、跨关流程和平台范围继续保留，目标active。


## 2026-09-09 异步UI窗口渲染提交

上一轮纹理pool为实质进展。本轮新增UIWindowLayer，拥有UILayer、专用纹理pool及当前lease。replace先复制节点/viewport/override快照，按当前绘制依赖异步acquire，revision校验确保旧请求晚到不覆盖新请求；过期失败不触发新窗口报错。只有当前请求成功完成UILayer事务重建后才释放旧lease；重建抛错时释放候选lease，旧几何和旧纹理继续保留。dispose先退役UI网格，再释放lease和pool，使晚到解码资源被收集。definitions/factory引用仍由调用方保持一致，控制器auto-layout在提交前准备。

新测试以单个真实源Image生成实际Three几何，覆盖并发旧请求丢弃、最新请求节点在等待期间修改仍不污染快照、网格失败保持旧draw/纹理状态、关闭中加载不提交且late纹理释放。首次选到隐藏源Image导致测试没有生成图元，失败日志ui-window-layer-tests.log保留；隔离fixture显式激活源节点后通过，不修改正式源数据。另发现空绘制层调用scene.add(...[])警告，UILayer加长度判断消除无效调用。

资源pool/源GPU/窗口联合6项通过5.2秒，ui-window-layer-regression.log；构建通过4.30秒build-ui-window-layer.log。强化快照测试后单独重跑ui-window-layer-snapshot-tests.log通过。原源GPU仍74→54 calls像素差0、资源归零；新owner本身当前是Node侧真实几何与Texture生命周期测试，尚未替换GPU fixture外层管理或接main，不能将既有GPU验证称新owner屏幕集成验收。

这不是源Gyro.UIWindow生命周期的替代：Show/Hide事件、动画、奖励选择/发放、点击路由仍要按原版控制器实现。replace为结构/内容变化而设，structuredClone及重建不可用于每帧alpha动画；低成本动态更新仍待落实。完整结算main接入、MuMu逐帧和微信/抖音实机性能、全部剩余机关与跨关范围保留，目标active。


## 2026-09-09 异步窗口层源面板GPU接入验证

上一轮新增UIWindowLayer为实质进展。本轮将完整源GPU fixture图形工厂改为由纹理表参数构造，并真实创建UIWindowLayer加载/提交源节点，补齐此前仅Node几何测试的边界。它独占新TextureLoader输出，未把旧pool的共享纹理转移给新owner；测试并存参考层和owner用于像素比较，不代表生产双份驻留方案。

首次完整提交owner 13 entries/resident/references、74 draw commands→54 submissions，与既有参考层全图RGBA差0。继续按钮隐藏/半透明/全显示均通过owner.replace真正提交，owner与未合批参考差0，calls53/54/54，累计纹理加载13次不增加。人为注入图形工厂异常后，错误被传回，旧owner画面全图差0，资源统计完全相同。最后owner先dispose再关闭参考层/atlas，两者所有geometry/textures/atlasCPU归零。

最终ui-window-layer-gpu-final-tests.log 2项通过3.3秒；此前集成版本构建build-ui-window-layer-gpu.log通过3.56秒，随后仅增强测试失败注入断言并重跑专项，没有把此前构建时间说成增强后重建。截图沿用源fixture路径，仍是40金币、模型29+3、888模板与未接管奖励区域；本轮没有新视觉设计，不作为原版普通结算验收。

本轮只完成测试面板的窗口owner接入，没有替换main结算UI。接入前仍需源窗口事件/完整奖励状态、两个粗体标签、低成本动态更新。replace的快照与重建用于结构变化，本测试用三个时间采样比对不能证明每帧重建性能合适。MuMu同操作、全机关/跨关和微信/抖音实机性能范围保持，目标active。


## 2026-09-09 源窗口事件顺序

上一轮异步owner GPU验证为实质进展。本轮提取Gyro.UIWindow 12方法至ui-window-events-source，机器码/调用注释/逐文件SHA与原ELF SHA归档。主ScreenFinish序列化registeredWindow=1、type=0、isVisible=1、closeButton=null；不可凭类名把窗口type改为Screen=4。Init先UIItem.Init查同对象transition，再订阅OnShowStarted/OnHideStarted/OnShowFinished；具体委托slot目标尚未运行解析，方法行为已静态取证。

Show 0x23a0d50：registered且instant且先前不可见时，先RegisterOpenedWindow；然后UIItem.Show；instant或无transition时直接OnWindowShown。该shown位于UIItem调用之后，即便重复即时Show被UIItem守卫拦下，窗口仍发shown。非即时有transition时注册发生于OnShowStarted 0x23a104c，该函数还发UIPublicEvents.FireOnUIWindowOpen；OnShowFinished 0x23a0e8c发shown。

Hide 0x23a0ea8：先前可见且registered立即Deregister，再UIItem.Hide；不直接发OnWindowClose。OnHideStarted 0x23a10b4发公共UIWindowClose。CloseWindow 0x23a0d14执行虚Hide(false)后发实例OnWindowClose，不等待淡出完成。公共close和实例closed不是同一回调。未发现这些方法直接修改按钮input lock，不以窗口动画结束推测输入禁用规则。

新增ui-window-events顺序模型返回有序effects，显示可见性和注册条件按原方法；transition回调由未来调用方明确传入，不猜测时间。3专项覆盖动画开始/完成、即时与重复显示、hide注销和close独立回调以及无transition路径，通过331ms（ui-window-events-tests.log）；构建通过4.13秒。模型尚不派发实际委托、不执行UIItem淡入，不支持回调重入时的同步对象状态观测；只是供控制器接入的顺序约束，不能将返回effect列表当完整源MonoBehaviour实现。main未改，无新截图。

下一步将窗口effects、透明度生命周期、按钮时钟与完整ScreenFinish/Mediator串联，补重入/时间域和实际点击回调，继续处理字体/动态更新与主游戏接入。全部局内机制/跨关及MuMu和微信抖音实机范围保持，目标active。


## 2026-09-09 领取与继续按钮分支

上一轮源窗口事件为实质进展。本轮审计已归档ScreenFinish.OnButtonClaim 0x209c2a4、OnButtonContinue 0x209c4f0、DropFinish 0x209c448和InvokeOnClaim 0x209c4d4。lockButtons+0x170为true时两个点击入口直接返回；普通分支直接调用+0x60 OnClaim，倍率分支先UIRewardMultiplier.StopAnimation再调用，二者不设置lock。箱子Stop后设置lock=true，然后OnClaimStart，再独立时间DelayedCall；转盘调用Drop再设置lock=true，无箱子OnClaimStart；发行版isPremium恒false，因此不执行后续premium隐藏Claim按钮分支。Continue不设置锁，仅未锁时调用OnContinue。Show清lock。

从源ELF段读取0xcf9ba8=float32 1.600000023841858（箱子延迟）、0xcf99bc=0.800000011920929（转盘掉落完成后的延迟），证据finish-claim-delays.json含地址/ELF SHA。两DelayedCall bool=true。延迟槽0x4b7c110和Drop槽0x4b7c118的实际回调目标尚未独立运行指针解析，InvokeOnClaim/DropFinish关联依据对应源方法结构，后续需闭合绑定证据，不能声称本轮运行实测奖励时间。

新增FinishClaimActions同步调用hooks，保持倍率→箱子→转盘→普通优先级、设置lock和claimStart的先后、Drop后置lock及使用执行时当前OnClaim回调。delay由调用方实现，不内建猜测渲染帧时间；没有模拟小游戏本体、入账或额外防连点。测试普通/倍率不凭空上锁、箱子阻止重复点击且1.6秒参数、回调更新、Show解锁和转盘掉落后0.8秒及不触发claimStart，3项通过，finish-claim-actions-tests.log；构建build-finish-claim-actions.log通过。未新增真实定时运行或点击UI路由验收。

源没有保存这些领取DelayedCall的handle；本模块不擅加hide取消接口，但跨窗口重开/旧回调归属仍需结合Mediator验证。真正重复入账防护必须按Economy交易流程实现，不能在视图层改源锁行为。main仍沿用旧通关入账路径；新dispatcher尚未接入，未宣称奖励流程已修复。

下一步闭合回调绑定及Mediator领取交易、窗口/小游戏生命周期，再与实际UI层合成并接main；字体/动态更新、所有剩余机关与MuMu/微信抖音实机性能范围完整保留，目标active。


## 2026-09-09 结算与窗口回调绑定闭环

上一轮分支dispatcher为实质进展。本轮重新确认MuMu PID17413存活，native-levels新增finish-ui-callbacks，只读6个元数据槽；可解析的MethodInfo首字落在模块范围才报告codeOffset，未初始化的usage保留值并输出null，不将它当代码地址。NDK编译/推送/运行成功，未调用Unity方法或修改存档、购买。

原运行结果native-finish-ui-callbacks.json：0x4b7c0e8=0x60001a05，0x4b7c110=0x60001a0b，0x4b7c118=0x60001a09，三个仍是MethodDef编码；新verify-finish-ui-callbacks.py按metadata31布局解析（36字节MethodDefinition、88字节TypeDefinition），验证kind3/标记位、表边界、声明类型名/namespace及其methodStart/count归属。方法索引3330→ScreenFinish.ShowButtonContinue，3333→InvokeOnClaim，3332→MiniGameBonusBoxesWheel_OnDropFinish。这闭合2秒显示、箱子1.6秒/转盘后0.8秒领取、转盘Drop的绑定，不再只依赖方法名推断。

另三个已初始化运行槽：0x4b8b688→0x23a104c OnShowStarted、0x4b8b678→0x23a10b4 OnHideStarted、0x4b8b680→0x23a0e8c OnShowFinished，与前轮原生方法地址吻合。6项解释及原metadata/运行JSON SHA存finish-ui-callbacks-verified.json，脚本可重跑，verify-finish-ui-callbacks.log记录全部结果。MethodDef解析规则对照本地Cpp2IL源码，保留静态元数据证据与live代码指针证据的区别。

本轮不改运行游戏TS逻辑，因此没有重跑无关游戏测试/构建，也没有声称实际领取交易、动画时长或普通结算画面已运行验收。前轮dispatcher回调目标推论现已明确；剩余Mediator经济交易与窗口事件实际派发/重入、字体缺口和main接入仍待完成。所有局内机关、跨关与微信/抖音实机性能门禁保留，目标active。


## 2026-09-09 经济交易入口与advanceOnFinish分支

上一轮6个回调绑定取证为实质进展。本轮新增源经济方法和两个闭包类的提取，合并关键Mediator方法至finish-economy-source，共32份bin/注释文件及SHA。初次归档假设旧manifest有methods键失败，改读文件格式并成功归档；未更改运行游戏或库存。

SharedData.get_advanceOnFinish 0x22c9b9c读取UserPrefs.GetBool（字符串slot0x4b882c8，默认false）。它不是isPremium常量，也不是免广/VIP是否购买；当前实际pref值尚未读取，不能据默认值断言用户当前分支。

Continue 0x22177cc先保存GetLives结果。advanceOnFinish=false时调用AddCoins(earnedCoins +0x48)，再AddCoins(matchThreeEarnedCoins +0x78)，随后AddTickets/GetMaxTickets、AddRVTickets、可选MatchThreeUserData.Save；runCollectedKeys>0时只调用一次AddKey，不能照钥匙数循环新增。若matchThreeEarnedSphere非0则AquireSphere，earnedLives>0再AddLives。true时跳过这一批基础发放至0x2217ae4。末段根据consumedKeys调用ConsumeKeys，随后SetLivesOnLevelFinish(进入Continue前保存的生命数)、ProgressLevel、Save(false)、OnContinue并DestroyMediator。尚未展开全部analytics/模式对其前后影响，不将此摘录当完整交易实现。

OnRewardedSuccess_EarningsMultiplier 0x2218d20附近依次读取当前倍率/箱子/转盘结果写rewardMultiplier +0x68，多flag依次覆盖与点击入口else-if优先级不同。计算rewardCoins*multiplier加到earnedCoinsRewarded与earnedCoins，记录额外部分rewardCoins*(multiplier-1)。advanceOnFinish=true时且earnedLives==0、rewardLives>0则先AddLives；multiplier>1才立即AddCoins额外部分，而不是再发完整乘积。false路径让累计值随后由Continue统一发放。ScreenFinish_Continue的闭包只做CoinParticles.Show与金币显示更新/后续回调，不宜仅凭HUD数字改变认定钱包已入账。

Economy.AddCoins 0x21e5e5c仅amount>=1时调用UserInventory.AddCoins，然后Fire_OnCoinsEarned；没有在此方法内部Save。AddLives 0x21e7d28读取库存生命及容量，容量0时置5，将当前+amount上限夹到容量；此方法没有底部0夹限或amount正数检查，调用方正数条件不可遗漏。具体UserInventory字段持久化/余额溢出策略及一次结算防重复仍需继续审计。

客户端main当前结束门inventory.addCoins(runCoins)是旧实现，尚未按上述阶段与pref分流，也没有完整奖励票据/三消库存交易。此轮不直接改钱包，避免只搬半条路径造成丢失或重复；下一步读取pref和继续Economy/Inventory链，再与完整ScreenFinish一并接入。未跑无关测试/构建，未称奖励1:1。全部局内机制、跨关与MuMu/微信抖音实机门禁保留，目标active。


## 2026-09-09 跨关奖励偏好与库存底层核验

前一用户问答只核对并解释既有跨关证据，没有修改权威实现，按目标续跑规则记为无新增实现进展；本轮继续完成偏好取证。此前native advance-on-finish-key读取以exit11失败，未将失败当字符串证据，也没有调用Unity方法强行初始化。新增extract-advance-on-finish-key.py从ARM64 ELF RELATIVE relocation和metadata31 literal解析：slot0x4b882c8→usage0x4d14718→0xa0008cb9→literal18012，字符串为advof。静态证据advance-on-finish-key-static.json包含ELF/metadata SHA。

重新确认MuMu PID17413存活，只读包内PlayerPrefs XML：advof不存在。UserPrefs.GetBool 0x23e5e14先HasKey，有键时GetInt!=0，无键时用调用方默认值；SharedData getter传false。因此本次磁盘存档对应advanceOnFinish=false，Continue时发放基础奖励。证据advance-on-finish-persisted.json含时间、文件SHA及范围说明；未读取尚未保存的内存PlayerPrefs，不把磁盘结果当运行中分支的直接证明。没有修改购买、库存或存档。

Gyro.UserInventory.AddCoins 0x21f8f8c：amount<1直接返回，否则ARM64字段+0x90执行32位add/str，无饱和夹限、无Save或事件；Economy封装另外触发事件。这里只记录机器语义，尚未据此改写客户端完整经济事务。新增两方法bin和反汇编共4文件，finish-economy-source manifest现36文件并校验SHA。

主游戏仍有终点提前inventory.addCoins(runCoins)的旧路径，待与Mediator生命周期、Continue和奖励分支整体接入；不能宣称此次修复了客户端入账。未更改TS运行行为，未重复无关构建/测试。下一步核验advanceOnFinish=true基础发放位置与false累计值初始化，再接完整事务；MuMu同步制动/镜头、真实跨关转场、全部机关和微信抖音性能验收继续保留，目标active。


## 2026-09-09 奖励初始化、普通继续累计与提前推进疑点

上一目标轮完成advof静态解码/存档取证，为实质进展。本轮逐条读取源OnEconomyRunFinished、ScreenFinish_Continue和奖励成功方法，并新增Init、构造器、Economy.ProgressLevel、UserInventory.ProgressOneLevel归档；经济源manifest现44文件，全部SHA核验通过。

Init 0x2216fd8用str xzr +0x40及stur xzr +0x45等重叠写将earnedCoinsRewarded(+0x40)、earnedCoinsCollect(+0x44)、earnedCoins(+0x48)、consumedKeys(+0x4c)清零；runCoins/keys来自参数存+0x58/+0x5c。OnEconomyRunFinished在非快速返回分支设置rewardCoins=Int32(runCollectedCoins*10)，结果为0时回退10，默认multiplier=2；并不直接将rewardCoins写入earnedCoins。

普通ScreenFinish_Continue 0x22192e0使用ld1r和add v0.2s，将rewardCoins同时加到earnedCoinsCollect与earnedCoins。奖励成功入口则将rewardCoins*multiplier同时加到earnedCoinsRewarded与earnedCoins，两个入口不能无条件依次执行，否则会多加一份基础奖励；其各自后续动画回调链需保留。没有以视图数字代替钱包余额。

OnEconomyRunFinished 0x22176e0读取advanceOnFinish：false直接返回；true依次AddCoins(rewardCoins)，consumedKeys为真时ConsumeKeys，否则本局keys>=1时AddKey一次，然后ProgressLevel、Save(false)。这闭合此前只找到奖励额外部分即时发放的缺口。非领取路径的基础金额也不是当前main的runCoins原始数量。

新发现需核验的生命周期疑点：Continue末段0x2217df4仍调用ProgressLevel，未见同一advanceOnFinish条件包围；Economy.ProgressLevel末段无条件调用UserInventory.ProgressOneLevel，后者0x21f9b64明确对+0x100做Int32+1，不是max/幂等操作。不能凭函数名假定重复调用安全，也不能仅凭两段静态调用断言当前原版实际跳两关：需要追踪true时完整回调是否仍进入Continue、是否切换状态/偏好或更新库存对象。当前磁盘偏好false不会在OnEconomyRunFinished走这条提前推进分支，但未保存内存值仍未取证。

本轮没有凭猜测添加幂等包装或直接改main经济路径。下一步闭合普通/奖励动画回调实际进入Continue的关联以及true分支的生命周期，完成后整体接入。源文件提取日志finish-progress-level-extract.log、finish-progress-one-extract.log保留；未改TS，未重复无关构建/测试。全部跨关转场、局内机制与MuMu/微信抖音实机门禁继续待验，目标active。


## 2026-09-09 领取动画回调、ScreenFinishOver及弹珠转接

上一轮结算初始化及非幂等推进取证为实质进展。本轮新增extract-finish-economy-callbacks.py，按ELF relocation和metadata31 MethodDef解析7个slot，验证索引归属/边界，保留SHA和类型索引。普通继续slot0x4b85398/3a0/3a8对应DisplayClass42_0 b__0/b__1/b__2；奖励slot0x4b85378/380/388对应DisplayClass40_0 b__0/b__1/b__2；二者末尾b__2均尾调用ScreenFinishOver 0x2219494，不是互相调用，普通继续累计不会自动再跑一遍奖励入口。0x4b853b0解析为PachinkoContinue，证据finish-economy-callbacks-static.json。这是静态绑定验证，不是live执行日志。

ScreenFinishOver先按boxesActive/wheelActive依次ReleaseSphereView，再Overlay.Hide、结算窗口Hide(false)。然后读取isPremium、GetBoarding1Min；boarding=3时额外读取GetLastUnlockedLevel，level==1或premium为真直接Continue；其他boarding时仅premium为真直接Continue。其余情况将+0xb9清false，并MediatorPachinko.Create(callback)。PachinkoContinue 0x221982c保存回调bool至+0xb9再尾调用Continue。购买免广不能代替此处isPremium；本版已核验的isPremium恒false依旧保留。源归档新增4文件，manifest共48文件SHA全部通过。

新增运行模块finish-over.ts保留释放/隐藏/配置读取顺序、条件读取关号、弹珠初始结果false和异步完成结果写入后继续。通过hooks接真正弹珠生命周期/经济Continue，未猜测添加去重或定时器。3项测试覆盖双球释放、等待弹珠回调才继续、boarding3首关/后续关/premium分支、不活动资源和非3配置不读关号；finish-over-tests.log 3 passed(293ms)，build-finish-over.log构建通过，已有大包警告仍在。

该模块尚未接main，弹珠小游戏本体与完整事务仍待接入，不能称普通结算交互已还原。此前advanceOnFinish=true疑点没有消失：两条领取末尾最终均可到Continue，原生ProgressOneLevel不幂等；仍需结合原版运行配置与状态变化核验，不能静态假设不会双推进。当前磁盘false的证据范围不变。下一步核验弹珠奖励/返回和原版实际配置，并把结算模块与UI/经济整体装配；全局内机制、连续转场、MuMu同输入及微信/抖音性能门禁继续保留，目标active。


## 2026-09-09 弹珠退出资源生命周期与Boarding配置来源

上一轮finish-over模块及3项测试为实质进展。本轮新增pachinko-lifecycle-source归档6个原生方法、12文件及SHA。Create(shared,callback) 0x2234c64传null machine转入另一重载CreateInstance→Init，不能假设所有入口都复用场景内machine。

OnExit 0x2236fc8首先UIPachinko.SetActions全部置null，记录条件analytics后调用BaseMediator.DestroyMediator；它不直接调用继续。OnDestroyMediator 0x2236770依次移除奖励广告、OnPrizeHit、OnTargetReached监听，Hide(false)，ResetSlotsLocation；destroyPachinkoMachine(+0x40)为真才Destroy机器GameObject，之后另一个UI引用对象GameObject无条件Destroy，PachinkoUserData.Save，再将pachinkoUnlockedSphere(+0x6e)传OnContinue，最后BaseMediator.OnDestroyMediator。UI+0xb0对象的具体资源名尚未核实，不擅命名为球；Unity.Object.Destroy实际释放有引擎时序，不能把调用顺序当即时GPU释放证明。

GetBoarding1Min从SupersonicController静态字段+0x60取键、+0x68取默认值，经GetConfigValue(string,int)解析。新增native-levels boarding-config，NDK编译并重新确认MuMu PID17413，读取成功：key=Boarding1Min、defaultValue=0、instance指针存在。证据native-boarding-config.json及attempt完整退出码0；只读原进程，未调用Unity或改存档。

GetConfigValue 0x238020c先以Unity.Object.op_Inequality检查静态instance(+0x98)，无有效对象返回默认；否则拼接前缀与键，有UserPrefs覆盖则GetInt，否则通过SupersonicWisdom API.GetConfigValue。实例指针存在不等于Unity对象有效，也不等于远程值已获得。当前证据只证明默认0，不得用来将finish-over boarding分支写死。下一步取证覆盖前缀/窄范围偏好及API实际配置来源，继续弹珠玩法及完整窗口/经济装配。

本轮新增只读诊断命令和源取证，未改主游戏TS，无需重复上一轮构建/测试。此前advanceOnFinish=true双推进疑点仍待运行状态核验。所有关卡机制、连续转场和微信抖音设备性能验收保留；目标active。


## 2026-09-09 Boarding覆盖键与SDK配置读取边界

上一轮弹珠生命周期与live默认字段取证为实质进展。本轮新增extract-config-prefix.py，静态解析GetConfigValue的字符串slot0x4b7b808→usage0x4d171b8→literal19376，值debug；因此准确覆盖键是debugBoarding1Min。config-prefix-static.json保留ELF及metadata SHA。

重新确认MuMu PID17413存活，只读PlayerPrefs XML并仅输出该键：不存在。boarding-override-persisted.json记录时间及文件SHA。此次XML SHA与上轮不同，因此没有沿用上次文件值；不读取/打印其他库存和购买内容。该结论排除本次磁盘调试覆盖，不排除尚未保存的内存覆盖，更不证明远程配置等于默认0。

源码定位最初按Assembly-CSharp路径查Stage10ApiExtension失败，随后使用原生方法映射提取成功。GetConfigValue(int) 0x3c8bf0c读取API实例+0x18布尔，为false返回传入默认；为true调用get_Container并从container+0x60经接口槽7取配置对象，再经接口槽0传key/default。还未解析此运行配置实例/接口实际类型，因此不从静态分支推断当前Boarding结果。新增SDK方法bin/反汇编，pachinko-lifecycle-source共14文件SHA验证通过。

本轮未改运行TS，未重复构建测试。下一步按实际SDK实例定位配置对象并只读目标键，或在MuMu完成同路径结算验证；主游戏结算/弹珠装配、全关机关与微信抖音性能门禁继续保留，目标active。


## 2026-09-09 SDK运行配置实例与接口目标

上一轮覆盖项排查为实质进展。本轮提取get_Api/get_Container，新增native-levels boarding-sdk只读命令，确认MuMu PID17413并两次编译推送运行成功。运行API存在且+0x18=1；Stage10ApiExtension静态缓存container存在且+0xa8=0。container+0x60实例类型SwStage40ConfigManager。按GetConfigValue原生代码的接口offset表解析接口槽7，live目标0x3b98e54，核对原生SwCoreConfigManager.get_DynamicConfig正是返回实例+0x58。

据该已验证getter读取动态对象，类型SwDynamicConfigManager；按另一接口槽0得到live代码0x3b96e7c，方法映射确认为SwDynamicConfigManagerBase.GetValue(string,int)。证据native-boarding-sdk.json、native-boarding-sdk-dynamic.json及首次attempt日志保留。只读内存、不调用SDK、不修改偏好购买。本轮已经确认实际实例链，不再仅猜测远程配置入口；但尚未读取该方法内部实际键值，因此Boarding1Min的最终数值仍未知。

源归档增加3方法6文件，pachinko-lifecycle-source共20文件SHA核验通过。下一步解析GetValue的字典/覆盖优先级，只取Boarding1Min目标值，再连接原版结算验证。未改运行TS，无重复构建测试。主游戏结算装配、全关机关、MuMu与小游戏真机门禁均保留，目标active。


## 2026-09-09 Boarding1Min动态值只读取证完成

上一轮live配置实例链为实质进展。本轮GetValue 0x3b96e7c→0x3b96e94确认dynamic+0x10字典查key，取tuple对象.ToString后Int32.TryParse，缺键/解析失败返回default；成功返回解析值并写source。源字典TryGetValue 0x30edafc反汇编明确entries+0x18、entry步长32、tuple16字节；取证片段boarding-dictionary-lookup-disassembly.txt含方法后相邻指令，不当整段单一方法。

native-levels增加只扫描Boarding1Min，其他键值不输出。首次手写字符串长度11造成错误零匹配（attempt证据保留，不能使用）；修为strlen/sizeof推导12后正确找到唯一项，类型Int64、source=3。新增Int64读取并以十进制字符串输出，避免JS精度损失。最终MuMu PID17413两次连续读取一致：boardingRawValue="0"，boardingMatches=1。native-boarding-value-final.json为有效最终证据；native-boarding-value.json为识别类型但未输出值的中间结果。

因此已证实当前SDK动态配置确有Boarding1Min=0，并非只沿用默认。其ToString→Int32解析对应0。source枚举3未在本轮映射命名。未保存的内存debugBoarding1Min仍未取证，磁盘此前无覆盖；不把字典结果当实际画面观察。结合发行版isPremium=false与ScreenFinishOver，SDK值0对应创建Pachinko而非直接Continue，实际交互仍需MuMu同路径验收。

源新增4文件，pachinko-lifecycle-source共24文件SHA通过；只读工具NDK编译/多次运行成功，无存档修改或Unity调用。未更改TS，无重复无关构建。下一步实现/装配弹珠阶段并验证原版实际结算，advanceOnFinish=true问题和完整主游戏事务继续待办；全关机制及小游戏设备门禁保留，目标active。


## 2026-09-09 弹珠投球状态与延迟准备模块

上一轮动态Boarding取值为实质进展。本轮提取OnDrop/OnDropLater/NewGame共6源文件，生命周期归档30文件SHA通过。NewGame仅部分读取，本轮未宣称初始化奖励列表/随机分布已完成。

OnDrop 0x22369f0先增加userData.ballsDropped(+0x18)，调用PachinkoBehaviour.DropBalls，再将mediator.ballsToDrop(+0x48)-1，ShowButtons(false,false)，shared userData+0x1a8计数+1。若ballsDropped<ballsToDropMax(+0x54)，创建0.5秒独立时间DelayedCall。静态metadata验证slot0x4b85be0→MethodDef8854 Gyro.MediatorPachinko.OnDropLater；它只在执行时ballsToDrop>=1时PrepareToDrop(1)、ShowButtons(true,false)，不是自动再次DropBalls。没有按剩余数决定是否安排延迟，也没有OnDrop入口的计数保护，UI控制可点击时机。

新增pachinko-drop.ts保留原版顺序、Int32计数、执行时读取剩余数及由调用方提供独立时钟。它不管理物理球、实际UI或源未保存handle的延迟取消；完整Mediator销毁归属仍需装配。两项专项测试验证先记数再投球、半秒后仅准备、上限基于总次数、执行时剩余数判定；pachinko-drop-tests.log 2 passed(404ms)，build-pachinko-drop.log构建通过(8.86s)。主游戏尚未接入此模块，未称弹珠实际可玩。

下一步还原PrepareToDrop/DropBalls的球生成、投放与命中机制以及NewGame配置，并与已移植结算UI/交易整体接入。全部关卡机制、连续转场、MuMu同操作及微信抖音真机性能门禁保留，目标active。


## 2026-09-09 弹珠准备与物理释放源码边界

上一轮投球状态模块与测试为实质进展。本轮新增4个PachinkoBehaviour方法共8源文件，生命周期归档38文件SHA核验。

PrepareToDrop 0x2336df8销毁全部旧ready球GameObject并清列表，按count重复NewBall后UpdateReadyToDropPositions；即使count<=0也清旧ready并更新位置。它不清已释放active列表。NewBall 0x2336fa8实例化ball模板(+0x38)，设父级为Behaviour transform，刚体isKinematic=true并SetActive(true)，没有在此方法加发射力。

DropBalls 0x2337088遍历ready(+0x48)，将每颗刚体isKinematic=false，逐颗读Unity.Time.time写球+0x3c，再加入active(+0x50)，最后清ready并清数组引用。没有显式AddForce、赋初速度或位置跳变；是否完全按重力运动仍需核验prefab刚体/球Update逻辑，不能仅凭这个方法声称物理轨迹已对齐。

UpdateReadyToDropPositions 0x233649c按GetSize、ready数量、字段+0x88/+0xa8和ELF浮点常量排布本地x，y/z取模板localPosition；设置Transform.localPosition后另将world position同步到Rigidbody.position。这一步不能省略，否则渲染球与碰撞体初始位置可能分离。常量与字段名尚待闭合，不凭眼估间距或直接搬主游戏球参数。

本轮仅新增源码依据和设计约束，未改主游戏TS或重复无关构建。下一步提取GetSize/球自身更新与prefab物理参数、解析排布常量，落实ready/active生命周期和布局后接弹珠场景；全局内机制/连续转场/MuMu与微信抖音实机验收仍待完成，目标active。


## 2026-09-09 弹珠附加加速度及ready排布计算

上一轮物理释放取证为实质进展。本轮GetSize确认返回SphereCollider.radius*2，不乘Transform缩放。FixedUpdate 0x23359b0每步AddForce(fakeGravity,+0x30..38,mode5)，源ForceMode枚举明确5=Acceleration。故DropBalls无发射力不代表仅默认重力；必须核验prefab useGravity与fakeGravity并适配质量无关加速度。

OnCollisionEnter先比prevHitCollider(+0x48)，相同且非运动学时线速度乘0.6660000085830688；相同计数增加。否则比较lastHitCollider(+0x40)，相同只增计数，不同清0。计数>=11时执行另一个mode5加速度并清0，该向量取Vector3静态字段乘100，其方向尚未本轮确认。最后更新prev/last并派发OnHitOther。这里只记录源，不将其当物理碰撞时序已验证。

ELF读取readyWidthFactor=-1.0499999523162842、readySpacingFactor=1.0499999523162842及碰撞衰减，pachinko-ball-constants.json含地址/SHA。新增pachinko-ready-layout.ts按原float32操作顺序计算排布，横移中心=horizontalMoveValue*(xLimit-count*diameter*1.05/2)，各球间距diameter*1.05，y/z沿用模板。调用者仍需同步world刚体位置，模块不生成球也不接main。2项测试覆盖单球/多球对称、横移端点与空数组；366ms通过，构建8.14s通过。源新增6文件，生命周期44文件SHA通过。

下一步完成prefab参数与碰撞恢复向量、ready/active实体生命周期，再接弹珠场景；完整结算和全关机制、MuMu同输入与微信抖音实机性能继续待验，目标active。


## 2026-09-09 弹珠预制体物理配置提取

上一轮排布实现及测试为实质进展。本轮新增extract-pachinko-physics.py，分别按PachinkoBehaviour.ballPrefab→PachinkoBall→theRigidbody/theCollider引用闭合，从本地3049机器与8547独立弹珠pack提取；校验类型和三组件所属同一node，并从configs按m_Material读取物理材质。pachinko-prefab-physics.json保存完整组件、位置、layer与每个pack SHA，非人工转录。

两个引用模板基础值一致：radius=0.30000001192092896、mass=1、useGravity=true、linearDrag=0、angularDrag=0.05000000074505806；PachinkoBall.fakeGravity=(0,-20,0)。材质dynamic/staticFriction均0.20000000298023224、bounciness=1、friction/bounceCombine均3。模板m_IsKinematic=false，但NewBall运行时明确改true、DropBalls再false，不能直接把模板布尔当待投状态。模板constraints=0、collisionDetection=0；不会擅用主游戏球radius0.5/mass5/零弹性覆盖。

证据为序列化值，world gravity/Init覆盖仍需单独查证；因此没有直接断言最终加速度=-29.81或实测弹跳轨迹。组合策略枚举3的确切含义需沿源Unity枚举确认后映射Rapier。后续需取板面/钉子材质及层碰撞矩阵、激活模板时序，并测同操作轨迹。脚本成功生成两个记录，未修改TS，无重复构建测试。全范围目标及平台实机门禁保留，目标active。


## 2026-09-09 弹珠模板激活与碰撞体资源清单

上一轮prefab参数取证为实质进展。本轮Awake 0x2335fcc明确先SetActive(false)隐藏ballPrefab，然后分别新建readyToDrop/dropping列表；序列化球节点active=true不能直接实例化成初始场景中的自由动态球。NewBall随后才激活新克隆，需在运行装配时保持该生命周期。

扩展extract-pachinko-physics.py，为两个pack全部Box/Sphere/Capsule/MeshCollider记录组件、层、物理材质和完整父链TRS，校验无父循环，并单独标记序列化继承active，不冒充Awake之后状态。独立8547共23碰撞体（13Box、9Capsule、1模板Sphere），5个trigger；3049机器24个，6个trigger。独立板其余22个均layer23，模板球layer24；板面collider的m_Material为null，不能解读为摩擦0，需要源默认材质配置。pachinko-prefab-physics.json新增boards记录，脚本重跑成功。

本轮无主游戏TS修改，无重复构建。源码归档新增Awake两文件，累计46文件。后续装配应先禁用模板，再按层矩阵创建源形状/触发器；Capsule轴向及组合变换不可替换为猜测Box。运行碰撞、命中与退出接入及所有关卡/小游戏性能门禁继续待办，目标active。


## 2026-09-09 弹珠目标触发器与命中清理顺序

上一轮模板初始化/碰撞清单为实质进展。本轮静态解析slot0x4b89a58对应字面量Targets（pachinko-target-tag.json含ELF/metadata SHA，extract-pachinko-target-tag.py可重跑）。PachinkoBall.OnTriggerEnter 0x2335be4先CompareTag，仅Targets才派发静态OnHitTarget(ball,collider)，随后球SetActive(false)、Destroy(GameObject)。其他trigger直接返回；没有独立isKinematic切换或先销毁再奖励。

PachinkoBehaviour.PachinkoBall_OnHitTarget 0x23371e8取collider GameObject组件（泛型目标类型未本轮解析），PlayHitForBallSpeed(20,true)，从dropping移除球，HapticFeedback.Trigger(3)，然后若OnTargetReached有监听，读取目标组件+0x24索引传回调。声音参数是常量20而非即时球速。目标组件类型与索引资源映射需继续闭合，不能按碰撞体遍历序号替代。

源码归档新增4文件，生命周期50文件SHA通过；本轮无主游戏TS变更，无重复构建。下一步把Targets标签/组件索引与源pack或原始导出关联，再实现落槽奖励；现有碰撞清单仅trigger标记不足以替代标签门禁。全结算装配、全关机制、MuMu同输入及小游戏实机门禁完整保留，目标active。


## 2026-09-09 落槽索引与储蓄金币累计

上一轮目标触发器取证为实质进展。本轮扩展碰撞清单，记录同节点PachinkoElementTarget组件；两个pack各5个目标，索引校验均为0..4且唯一。8547节点8561/8563/8572/8566/8575依次对应0/1/2/3/4；3049节点6049/6047/6039/6043/6035对应0..4（统一前缀63d32d2d_）。源组件type=4，目标MeshRenderer序列化disabled；不可因为渲染器关闭就删掉触发器。证据pachinko-prefab-physics.json及pachinko-target-map-extract.log；Targets原始标签与GetComponent泛型参数仍需闭合，不以组件名代替标签证明。

MediatorPachinko.OnTargetReached 0x223739c的开头先targetsHits[index]加1，再piggyCoins += targetsCoins[index]*新targetsHits[index]，随后PachinkoUserData.Save；即同槽多次命中金额随累计次数增长，不是固定每球加一次槽基础值，更不是直接Economy.AddCoins进主钱包。后续还涉及动画/更多状态，本轮尚未完整移植该方法。源新增2文件，生命周期归档52文件。

本轮清单生成及索引校验通过，未改主游戏TS，无重复构建。下一步核验OnTargetReached后续与目标金币初始配置，再整体落地累计/表现/提取流程；全部关卡机制、主结算装配与小游戏实机性能门禁保留，目标active。


## 2026-09-09 最后落槽与储蓄罐待领奖励生命周期

上一轮落槽索引/累计取证为实质进展。本轮完整续读已归档OnTargetReached后段，新增行为证据：progress=Clamp01(GetTargetsHitsSum()/ballsDropPerGame)，同时更新Behaviour/UI进度、PiggyCoins；CoinParticles从目标索引对应UI起点飞到储蓄罐目标，AnimateCoin(1)。不是飞向主钱包。

当ballsDropped<ballsDropPerGame且dropping为空且ballsToDrop==0时，PrepareToDrop(0)，按另一静态配置显示补球Claim并SetClaimAmount。之后独立判断ballsDropped>=ballsToDropMax且dropping为空才进入最终储蓄罐分支；未达条件另有配置控制的1.5秒独立延迟，具体配置/回调尚需核验，不能统称固定自动退出。

最终分支0x2237910清mediator+0x70..7f作为待领奖励快照，并将当前piggyCoins写+0x70。遍历piggyPrizes：Coins类型1加SharedData.GetRewardCoinsAmount；Tickets类型2每项加20；RVTickets类型3每项加1；Ball类型0在prizeSphere非0且Economy.HasSphere=false时记录sphere。这里主要组装待领奖励，GetCoins/GetRVTickets用于HUD显示，不是Add入账。

随后SetPiggyBreakRewards(coins,tickets,rvTickets,sphere)、ShowBreakPiggy(true)，将userData.ballsDropped=0、gamesPlayed+=1，AllPrizesCollected时allPrizesWonCount+=1，接着NewGame重建下一轮数据并Save，AddAfterFinishMiniGamesPlayed并Economy.Save(false)。所以待领奖励必须由Mediator快照持有，不能领取时重新从已更新的PachinkoUserData计算；不能把“关闭UI时才初始化下一轮”作为替代实现。

上述结论来自已归档源码，未改TS/重跑构建，也未声称完整弹珠已运行。下一步据此实现待领奖励与数据轮次分离，并追踪打碎/领取的实际入账时机。全主结算/关卡机制及MuMu、小游戏真机性能门禁继续待办，目标active。


## 2026-09-09 储蓄罐领取入账与粒子表现分离

上一轮待领快照生命周期核验为实质进展。本轮新增OnBreak、FinishBreakParticles、OnClaimBreak、OnRewardedSuccess_ClaimPiggy共8源文件，累计60文件SHA校验。

OnBreak本体清UI actions、显示Overlay、StartAniHammerHit、Piggy.Explode及StartShowBreakRewardsAni，安排两个DelayedCall；没有在该方法直接Add库存。FinishBreakParticles同样只依据快照正数决定播放coins/tickets/rvTickets粒子，并读取当前Economy余额更新HUD；不能因粒子到达才推断发钱，更不能在该方法重复Add。各粒子目标引用按源字段不同，待实际UI资源绑定。

实际入账入口OnRewardedSuccess_ClaimPiggy：sphere非0时设置pachinkoUnlockedSphere=true并AquireSphere(sphere,false,true,false)；coins>=1调用AddCoins；tickets>=1取得GetMaxTickets后AddTickets；rvTickets>=1调用AddRVTickets；随后Economy.Save(false)。再记录统计/analytics并Fire_OnBreakPiggy，后续有另一静态配置的UI分支未本轮完整追踪。入账依据Mediator+0x70..7f快照，不能重新读取已NewGame的PachinkoUserData。

OnClaimBreak含资格/广告相关流程，本轮虽提取但尚未完整验证免广、奖励票与广告成功如何调用此入口。不能将购买免广等同自动发奖，也不在粒子或OnBreak补发一遍。本轮未改TS，无重复构建。下一步完成点击到领取成功回调的资格链与UI切换，然后接入完整奖励事务；全主结算/弹珠/局内机制及MuMu、微信抖音实机门禁保留，目标active。


## 2026-09-09 储蓄罐奖励票与广告领取路由

上一轮实际发放入口为实质进展。本轮OnClaimBreak源确认先设置placement=0x26(38)，调用SharedData.ConsumeRVTicket(38)。成功则记录使用placement、读取剩余票数，调用UI.ConsumeRVTicket(remaining,callback)，随后BeginRVSkipped；静态slot0x4b85bf8解析为OnRewardedSuccess_ClaimPiggy，必须等UI票动画回调，不能消费票后立即自行发奖再让回调重复发放。该绑定已加入可复跑extract-finish-economy-callbacks.py。

无票时先读slot0x4b7b4f8静态bool（身份未本轮确认，不能叫免广）；true直接BeginRV后进入成功处理。false时CanShowRewarded(38)，不可展示直接返回；可展示则记placement、waitingForPachinkoClaimPiggy(+0x6d)=true，BeginRV再ShowRewarded。广告结果处理以AdViewInfo+0x1c数值分支：10走成功候选，并核对当前placement=38和waiting=true后清waiting，再调用成功入口；9走另一结果分支，具体枚举与失败UI需继续查证，不能把所有关闭回调当奖励成功。

源归档新增结果处理2文件累计62；本轮未改主游戏TS，无重复构建。下一步确认静态bool身份/广告结果枚举及失败UI，再装配资格路由；用户购买免广不被修改，也不作为未经验证的奖励成功捷径。所有主游戏/全关/真机验收范围保留，目标active。


## 2026-09-09 弹珠广告最终结果路由模块

上一轮票/广告分支核验为实质进展。本轮源AdResult枚举闭合：7 RewardedClosed，8 RewardedReceivedReward，9 RewardedFinished_NoReward，10 RewardedFinished_GiveReward。OnRewardedAdResult只处理9/10，其他返回。9且对应placement37/38等待标记为真时清标记、记录结果、OnExit；10先记奖励placement，清等待，再对应ClaimBalls/ClaimPiggy成功入口。补球回调之后继续读取当前placement和piggy等待状态，源为顺序分支，不固定else-if。

新增pachinko-ad-result.ts，保留最终事件门禁、等待状态与回调顺序；不冒充SDK适配或完整广告资格流程。2项专项验证7/8不发奖、10只处理等待中且重复最终事件不再发放、9退出无奖励，以及补球回调修改placement后重新判定。pachinko-ad-result-tests.log 2 passed(290ms)，build-pachinko-ad-result.log通过(3.91s)。两源C#枚举/字段文件已归档SHA。

模块尚未接main，原版静态免广告相关bool及其来源仍待核验，用户购买不改动；完整票动画/奖励事务及实际广告平台回调装配待完成。全关机制和小游戏真机性能范围保留，目标active。


## 2026-09-09 无票直接成功分支是debugYESADS

上一轮广告结果路由实现/验证为实质进展。本轮native-levels新增piggy-direct-claim-flag只读命令，读取slot0x4b7b4f8类名/命名空间及static+0。重新确认MuMu PID17413，NDK编译推送运行成功：Pronetis.AdController、value=0。源AdController.cs明确第一个静态bool为debugYESADS；文件归档SHA，native-piggy-direct-claim-flag.json含时间/PID。

因此OnClaimBreak在ConsumeRVTicket失败后的直接成功分支属于debugYESADS，而非购买免广。当前运行该调试开关false，应继续CanShowRewarded路径；购买是否影响ConsumeRVTicket/CanShowRewarded仍需沿其实现核验，不能从此结论推导用户必须观看广告。未修改购买库存、存档或运行开关。

本轮只读取证，无TS变更或重复构建。接续将明确命名的debugYESADS用于领取路由装配，并继续票消费规则；完整主游戏接入、弹珠玩法和全关/小游戏实机验收继续待完成，目标active。


## 2026-09-09 当前VIP绕过实际扣票的分支确认

上一轮debugYESADS身份核验为实质进展。本轮SharedData.ConsumeRVTicket 0x22c6560确认先检查slot0x4b7cf70/static+8。新native-levels rv-ticket-bypass命令重新确认MuMu PID17413后只读，类Gyro.SharedData、offset8、value1。源字段顺序_instance指针后isActiveVIP（32位偏移4，ARM64偏移8）闭合身份；native-rv-ticket-bypass.json保存时间和结果。

VIP=true时RewardedAdButton.SetRewardedAdTicketAvailable(true)，记录placement的资源日志后return true，不调用Economy.ConsumeRVTicket。非VIP时才调用Economy消费，随后用GetRVTickets()>0刷新可用状态，消费成功再日志/true，失败false。Economy消费还受EconomySettings静态+0xe0开关控制，开启才UserInventory.ConsumeRVTickets(1)，不开启false；底层扣票/Save仍待核验。

因此当前实际VIP状态可通过ConsumeRVTicket成功分支进入UI票动画回调且不扣票，不需要debugYESADS。这与isPremium恒false不矛盾，二者不同；不能把所有购买免广普遍等同VIP，也不能断言该用户必须走广告。之前OnTargetReached/领取后使用相同slot+8的未命名配置，现在应解释为VIP（含1.5秒自动退出分支），需在装配时按当前VIP行为处理。

本轮源增加消费方法/SharedData字段归档，未改购买库存或存档、未改TS。下一步按已验证VIP分支接入领取流程，核对VIP弹珠结束自动退出和奖励快照生命周期；完整主游戏/全关机制及微信抖音真机性能继续待验，目标active。


## 2026-09-09 VIP奖励票消费运行模块

上一轮运行VIP状态及源消费分支核验为实质进展。本轮新增consume-rv-ticket.ts实现SharedData消费层：VIP直接刷新ticketAvailable=true、记录资源类型3并成功，不读取/修改票余额；普通路径调用Economy消费hook，然后基于消费后余额>0刷新可用状态，失败不记录成功，成功记录类型2。底层EconomySettings资格/持久化由库存层负责，不在该模块猜测库存规则。

2项专项测试覆盖VIP零余额查询与零扣减，以及普通成功用扣后余额、失败仍刷新状态且不记消费。consume-rv-ticket-tests.log 2 passed(282ms)，build-consume-rv-ticket.log构建4.06s通过。尚未接主游戏或票动画/广告资格完整流程，不能宣称当前主游戏VIP行为已修复。源类型2/3保留原数值，未擅自映射统计名称。

下一步把该模块接入已核验的领取路由，并完成UI票动画生命周期、完整库存事务和弹珠场景装配；全部局内机制及MuMu/小游戏实机性能范围保留，目标active。


## 2026-09-09 VIP/普通票动画完成时序模块

上一轮消费规则模块为实质进展。本轮UI.ConsumeRVTicket源码确认保存最新callback及remaining>0，Show Overlay、更新票余额显示；isActiveVIP时VIPTicketAni.Show，否则将票显示首子节点world position转screen后RewardedAdTicketAni.SetFromScreenPosition/Show。两者都独立延迟0.8500000238418579（ELF0xcf99fc）。静态slot0x4b8afc8→OnConsumedRVTicket绑定闭合。完成先Hide Overlay，再SetTicketAvailable(保存值)，最后调用当前callback。

新增rv-ticket-animation.ts保持源可重入状态覆盖语义、VIP/普通分支和独立延迟；具体票图形/屏幕坐标动画由hook负责，不宣称已绘制VIP票。尤其VIP零库存时完成会把ticketAvailable置false，按此方法源码保留，不擅自修成true；完整系统其他刷新需后续装配。2项测试覆盖顺序、ELF时长与重复调用的最新回调，339ms通过；构建4.03s通过。4源文件及SHA归档。

该模块未接main，普通/专用票动画本体、领取路由和库存事务尚待整体接入；不能凭单测声称主游戏效果对齐。下一步组合已核验消费与动画流程，继续VIP原版画面验证。全关/小游戏实机门禁保留，目标active。


## 2026-09-09 储蓄罐领取模块组合验证

上一轮票动画时序实现为实质进展。本轮重新读取三个运行模块并新增pachinko-claim.ts，将OnClaimBreak的消费→票动画→领取回调和无票debugYESADS/CanShowRewarded路径接通；与pachinkoAdResult共享placement/waiting状态。票成功先记skipped placement，安排动画后BeginRVSkipped；广告分支先记请求/日志，再waiting=true、BeginRV、ShowRewarded。未添加源未证实的点击锁或跨会话去重。

组合测试使用真实consumeRVTicket/RVTicketAnimation/pachinkoAdResult：VIP不扣票但等待动画，普通票扣一次且广告不可用也可凭票领取；无票不可展示时不发奖，可展示时7/8不发奖，最终10仅处理等待中一次。pachinko-claim-tests.log 2 passed(301ms)，build-pachinko-claim.log3.53s通过。结果hook为测试记数，并非已接生产库存，因此只能证明模块间路由/顺序，不能称真实奖励事务或SDK完成。

主游戏尚未调用该组合，真实VIP票图形、库存发放/保存及弹珠场景装配待完成。接续应加入真实奖励快照事务与场景生命周期，保留当前完整UI/原版同输入和所有关卡/小游戏实机门禁，目标active。


## 2026-09-09 生产Inventory补齐票字段原语

上一轮领取组合验证为实质进展。本轮重新读取生产Inventory，确认仅金币/球所有权且没有票；补入tickets/rvTickets独立余额、addTickets/addRVTickets/consumeRVTickets。按原UserInventory两种票正数才增加，Int32加法；消费amount<1或Int32减后负数返回false且不写，否则写余额true。beginRun只清箱子去重，不清票；现有金币/球行为未改。

源Economy.AddTickets(amount,max)在max>=1且当前+amount>max时把amount替换为max-current，随后仅amount>=1调用库存，但无论正负都Fire_OnTicketsEarned(amount)。该cap/event属于经济层，尚未接入Inventory原语，也不能自动降低已超限库存。初次读取无后缀AddTickets文件失败，改用已提取重载0x21e8a0c成功；四源方法8文件归档SHA。

2项生产Inventory专项覆盖票种独立、余额不足无扣减、跨beginRun保留、输入校验与Int32溢出，300ms通过；构建3.51s通过。票默认0，存档读写/恢复还未接入，现有主游戏也尚未使用新票方法。下一步建立经济层封顶/发奖/保存适配再接领取；全关/原版同输入和小游戏实机门禁保留，目标active。


## 2026-09-09：普通票 Economy 封顶适配实际库存

上一轮为跨关状态核对，未改变实现，按目标检查归类为 no progress；本轮推进代码与验证，无外部阻塞。

新增 src/game/ticket-economy.ts 的 creditTickets，接受实际 Inventory、奖励、上限与事件回调。依据 evidence/pachinko-lifecycle-source/Gyro.Economy__AddTickets__0x21E8A0C.capstone.txt：max>=1 时比较 Int32(current+amount)>max，成立则奖励改为 Int32(max-current)；仅正值调用库存加票，无论正零负都发 OnTicketsEarned。回调发生在库存变更后。max<=0 禁用封顶，不在此层保存。

例如库存18领取5、上限20：入账2，通知2；满20再领取通知0；库存30领取5、上限20：余额保持30，通知-10。不要把负通知误解为扣票，也不要用 Math.min/max 改写而丢失原生 Int32 溢出语义。接口拒绝非 Int32 参数属于 TypeScript 输入边界校验。

验证：tests/ticket-economy.spec.ts 联合 inventory-tickets.spec.ts 共4项通过（297ms），覆盖临界/满额/超额、禁用封顶、非正奖励、事件后读库存、票种独立、原生溢出及非法参数不变更。npm run build通过，保留既有大包警告。日志 evidence/ticket-economy-tests.log、build-ticket-economy.log。

该函数仍未接 main/Pachinko 最终奖励事务，也未完成持久化。下一步必须保持 Mediator 待领快照与 NewGame 后新数据分离，按源顺序接球皮肤、金币、普通票、RV票与一次保存，再整合真实 UI/场景；现有 main 结算提前入账问题仍待修复。没有宣称完整结算、跨关、全关卡或小游戏平台验收完成。


## 2026-09-09：Pachinko 待领奖励入账与 VIP 自动砸猪

上轮票经济层为 progress；本轮新增领取回调组合及原生尾部证据，无阻塞。新增 runtime/pachinko-piggy-reward.ts，按 OnRewardedSuccess_ClaimPiggy 0x2237e5c：隐藏领取/退出按钮、显示砸猪按钮；非零 sphere 先置 unlockedSphere，再 AquireSphere(model,false,true,false)；正金币、普通票（查询上限）、RV票依次入账；Save(false)；记录奖励统计、资源日志、Pachinko action=3、EndRV(placement38,result6)、Fire_OnBreakPiggy。即便奖励均非正且无皮肤也保留 Save。

新的原生证据：Fire_OnBreakPiggy 后才读取 SharedData.isActiveVIP。VIP 清空 UI Actions、立即隐藏砸猪按钮，再 independent DelayedCall(0.8999999761581421, OnBreak)。ELF 0xcf98d4 bytes=6666663f；回调 slot0x4b85b88 静态 MethodDef8862 明确解析到 Gyro.MediatorPachinko.OnBreak，不是退出。证据 pachinko-vip-break-delay.json 与 finish-economy-callbacks-static.json；脚本 extract-pachinko-vip-break-delay.py 可重跑，回调解析脚本同步扩展。与前面的 UI.ConsumeRVTicket 0.8500000238 秒等待分别建模。

新增 UIPachinko.cs 入 source archive，83个文件 SHA256 全量校验通过。该 C# dump 字段是32位偏移，buttonClaimBreak/ExitBreak/Break 对应 0x4c/50/54；原 ARM64 领取指令访问对应0x98/a0/a8，显示/隐藏采用既有 UIItem 虚方法映射。不要混用两种偏移。

集成测试使用真实 PachinkoClaim→RVTicketAnimation→rewardPachinkoPiggy，库存使用生产 Inventory，普通票使用 creditTickets。验证VIP不消费票、票动画前不发奖、入账顺序、保存时余额、普通票消费后回补、封顶实际入账2而资源统计仍记录原奖励20、后续砸猪不再次入账、VIP独立0.9秒延迟、非VIP保留手动砸猪以及非正奖励。与既有领取测试合计4项通过（338ms），构建通过。日志 pachinko-piggy-reward-tests.log、build-pachinko-piggy-reward.log。

边界：测试的图形、皮肤领取、存储和统计均为有序 hooks，不代表已接原生 SDK/真实文件保存/主游戏。recordRewards 的生产适配须写源统计字段与领取标记；endRV 须按源补齐其余固定参数。传入 state 必须是 Mediator 独立待领字段，不得引用 NewGame 已初始化的下一局 UserData；此回调自身不臆造重复领取锁，入口由领取路由/UI 控制。本轮仍未完成 main 装配、Pachinko 真实物理/动画、跨关继续和小游戏真机验收。


## 2026-09-09：砸猪双延迟回调和结束顺序

上一轮领取组合实现为 progress，本轮推进 OnBreak 0x22382a0 时序模块与原生回调解析，无阻塞。新增 runtime/pachinko-break.ts：清空按钮 Actions→显示遮罩→StartAniHammerHit→Explode(0.8500000238)→StartShowBreakRewardsAni(delay2,duration0.3330000043)→安排独立1.899999976秒回调→隐藏砸猪按钮(false)→安排独立5秒回调→LogPachinkoAction(5)。爆开和奖励动画方法内部时钟尚待下钻，独立属性仅确认两次 DOVirtual.DelayedCall，不能泛化为所有动画。

重要新证据：slot0x4b85c08 解析为 MethodDef8863 PlaySoundOnBreak，不是 FinishBreakParticles。该方法0x223847c只调用 HapticFeedback.Trigger(4) 和 UIPublicEvents.FireOnMiniGameFinish；声音是否由事件订阅者播放待核，不能凭方法名自造音效。slot0x4b85c10 解析为 MethodDef8867 <OnBreak>b__38_0 (0x2238a2c)，5秒后按 Overlay.Hide→FinishBreakParticles→BaseMediator.DestroyMediator 顺序执行；不是直接 OnExit。两方法机器码和反汇编已入 pachinko-lifecycle-source manifest。

ELF浮点常量：0xcf99fc=0.8500000238，0xcf9bf4=0.3330000043，0xcf98a4=1.899999976；2与5为原生浮点立即数。证据 pachinko-break-timing.json、finish-economy-callbacks-static.json，回调抽取脚本已扩展并执行。模块使用 Math.fround 保留精度。

专项时钟测试验证缩放游戏时钟暂停时仍可推进两个独立回调、遮罩在等待期保持、1.9秒事件与5秒粒子/销毁的先后顺序。联合领取测试3项通过（306ms），构建通过；日志 pachinko-break-tests.log、build-pachinko-break.log。

仍待接入：模块 effects 为 hooks；真实锤击、猪破碎、奖励展示、FinishBreakParticles 的粒子发射参数/资源、OnDestroyMediator 的保存/回调/释放、主游戏结算装配未完成。FinishBreakParticles 只读取库存余额刷新 UI，不再入账。不能把模块测试当作 MuMu 画面一致性或完整弹珠关卡验收。


## 2026-09-09：猪破碎资源与原生切割/清理机制

上轮时序实现归类 progress。本轮取得此前未闭合的破碎源证据和可重跑资源清单，改变下一步实现选择：不能用普通粒子代替网格切割。

UIPachinkoPiggy.Explode 0x20c4200 先 Kill(false) 旧 tween 并置空，再把 independent DelayedCall(delay) 返回句柄存入+0xf8。<Explode>b__12_0 0x20c42ec 调用 PigPresenter.ExplodePigHardcoded 0x20dd020。OnDisable 0x20c40c8 / StopTween 0x20c40f0 均 Kill(false) 并置空；重入/离场应取消尚未执行的爆开回调，不能套用前面 Mediator 不保存句柄的延迟策略。

ExplodePigHardcoded 使用 TransformDirection/TransformPoint 构造切割输入，包含 Random.value 与两次 Random.onUnitSphere，最后调用 ShatterToolkit.ShatterTool.Split（0x20eedc8）。切割平面构造、generic数据身份、Split算法尚未完整迁移；serialized cuts=2 不能推断最终碎片数，也不能宣称固定预切割模型已等价。预计算/Worker只作为待评估方案，应保留原随机规则和几何结果后测峰值，不提前宣称性能改善。

PostSplit 0x20ddd74：创建 ShardObjects 集合；逐碎块设父节点到 PigPresenter，若有 Rigidbody，在 presenter世界位置+(1,0,-1) 调 AddExplosionForce(force1.5,radius5,upwards3)，加入清理列表。随后逐 InsideCoins 激活对象，在 presenter世界位置施加 force20,radius5,upwards3，加入清理列表，启动 DestroyShards coroutine。具体物理默认 ForceMode 需继续解析被调用重载；没有擅自把该参数映射为 Rapier impulse。

DestroyShards.MoveNext 0x20de184 首次 yield WaitForSeconds(2)，恢复后逐 ShardObjects 调 Object.Destroy；这是缩放时钟等待，与独立爆开延迟不同。此处未清空列表，Unity延迟销毁/父级先销毁/协程停止边界仍待还原。

新增 scripts/extract-pachinko-piggy.py，执行通过，输出 evidence/pachinko-piggy-resources.json。沿 UIPachinkoPiggy→PigPresenter→ExploadablePig/InsideCoins/pigBreakPoints 验证类型和引用，存父链TRS、组件物理参数、本地几何SHA及文件大小。唯一资源pack63d32d2d_3820：5个参考点、11个金币刚体；破碎源 Mesh63d32d2d_2034 为542顶点/525三角形/23644字节。源节点Pig254LowPolyMesh renderer序列化禁用、刚体kinematic=true、Convex MeshCollider开启；不可因renderer禁用而漏掉待激活网格。ShatterTool generation1、generationLimit3、cuts2、fillCut1、cutMaterial63d32d2d_931，另有HierarchyHandler/TargetUvMapper，必须一起评估。

7个方法的机器码与反汇编、2个C#源声明已归档，pachinko-lifecycle-source 共103文件SHA256全量通过（pachinko-piggy-source-verification.log）。本轮为逆向/资源工具变更，未改变运行画面，不额外运行无关游戏测试或构建。仍待网格切割规则、真实碎片物理/清理、动画和main装配，未完成1:1或平台验收。


## 2026-09-09：7个原生切割平面生成

上轮资源/源证据调查为 progress。本轮新增 runtime/pachinko-cut-planes.ts，按 PigPresenter.ExplodePigHardcoded 原生顺序构造7个世界Plane，normal归一化与distance=-dot(normal,point)按Float32操作，阈值ELF0xcf9d08=9.999999747e-6。

经 Vector3..cctor 0x45b4488 与 Vector3.cs 交叉确认 slot0x4b7adc0 static+0x18为up、+0x3c为right、+0x48为forward，不能凭记忆套静态字段排列。坐标拥有者为 PigPresenter.pigTrigger (+0x28)，不是 Presenter自身或ExploadablePig。七平面依次：trigger.TransformDirection(up)穿point0；up穿point1；right穿point1；forward穿point2；right+right*(Random.value*5+5)穿point3；世界Random.onUnitSphere穿point3；第二次世界Random.onUnitSphere穿point4。所有point均为 trigger.TransformPoint(pigBreakPoints[i].localPosition)。第5法线归一化后方向通常不变，但必须消耗Random.value，且保留原操作顺序；末两法线不能额外乘trigger旋转。

ShatterTool.cs确认 Split(Plane[],Action onPreSplit=null,Action onPostSplit=null)；原调用x2=null、x3为后回调。Plane定义构造已迁移，切割执行与后回调绑定尚待完成。

2项测试通过（317ms）：旋转90度+非均匀scale下方向只旋转、点走完整TRS，7平面经过正确世界点、只有5次方向变换，随机value/sphere/sphere调用顺序保留，零法线及缺少参考点输入边界。测试通过Three Object3D作变换适配，未冒充Unity逐位验证。npm run build通过，日志 pachinko-cut-planes-tests.log/build-pachinko-cut-planes.log。107个源文件SHA全量通过，新增Vector3初始化二进制/反汇编和Vector3/ShatterTool声明；规则落入 pachinko-cut-plane-source.json。

当前函数要求调用方提供随机源与trigger变换，未擅自使用Math.random，未接main或真实网格。下一步继续ShatterTool.Split网格裁切/封口/属性插值及原随机生成器与碎片物理；平台drawcall/内存实测仍待最终场景，不能由七平面推断碎片数或峰值。


## 2026-09-09：Shatter局部平面转换与Split执行边界

上轮七平面实现为 progress，本轮新增 localShatterPlanes（runtime/pachinko-cut-planes.ts）并保存3个ShatterTool原生方法及IHull声明，共114源文件SHA256通过（shatter-source-verification.log）。

ConvertPlanesToLocalspace 0x20eefd4 按每个世界Plane生成 localPoint 与 localNormal：先用 -distance*normal 取世界平面上一点，再 ShatterTool.transform.InverseTransformPoint；normal 先 InverseTransformDirection，再逐轴乘 transform.localScale，按Float32计算长度并以1e-5阈值归一化。它不是直接用原参考点，也不是把pigTrigger当目标变换。使用localScale而非lossyScale/父级总scale，不能擅自替换通用逆转置算法。实现提取共享Float32归一化函数，保持既有七平面计算。

专项3项通过（417ms），包含既有世界平面、随机顺序，以及父级scale(7,11,13)+对象scale(2,3,4)/平移情形：点走完整逆矩阵、法线只乘本地scale，空数组不访问变换。构建通过。日志shatter-local-planes-tests.log/build-shatter-local-planes.log。测试为Three适配数学/流程测试，不等于Unity native逐位或MuMu图形匹配。

Split 0x20eedc8 先保存pre/post回调，即使后续早退；有平面且isIntact(+0x40)及有效非空hull后取得mapper，sendPreSplitMessage为真时优先pre回调否则SendMessage；随后ConvertPlanesToLocalspace→CreateNewHulls→CreateNewGameObjects；sendPostSplitMessage为真时优先post回调否则SendMessage；最后Object.Destroy原GameObject并置isIntact=false。内部generic接口目标还需与metadata进一步核实，未直接移植整个Split入口。

CreateNewHulls 0x20ef254外层遍历全部输入points，逐轮读取集合计数，对已有hull调用IHull.Split(localPoint,localNormal,fillCut,uvMapper,colorMapper,out A,out B)，之后检查结果IsEmpty再纳入集合。IHull接口slot0=IsEmpty、slot2=Split可由声明佐证；集合接口slot身份/替换及A/B最终顺序仍待严格解析后实现，不能仅按分支推测写死。封口算法、UV/颜色插值与生成对象尚未完成。

下一步保留ShatterTool具体IHull实现/三角形裁切及封口为必做；目前没有生产网格输出、场景破碎画面或小游戏性能验收。待集成时保留后回调发生在原对象销毁之前的源生命周期。


## 2026-09-09：FastHull顶点分类与属性分配

上轮局部平面转换归类 progress。本轮 ShatterTool.Start 0x20eeb00 明确内部类型0调用FastHull(mesh)，类型1调用LegacyHull(mesh)；与原猪pack internalHullType=0一致。新增FastHull/HullType声明及Start、Split、AssignVertices、IsEmpty、静态构造共5方法原生证据，归档126文件SHA256验证通过（fast-hull-source-verification.log）。

新增 runtime/fast-hull-vertices.ts 的 assignHullVertices：源 positions 为Float32Array，点/法线及逐步差值/乘法/相加按Float32运算；dot(normal,vertex-point)>=0分A，否则B。原指令0x20e0b34 fcmp、0x20e0b38 cset ge；没有epsilon双边归属。旧顶点按原顺序写到对应侧，以side-local索引构建oldToNew，附above Uint8Array。法线/颜色/切线/UV随顶点原值复制，缺失通道不生成，输出不共享输入存储。当前两遍分配用于获得精确大小的输出数组，保持分组和映射结果；未据此宣称耗时或内存优化。

2项专项通过（311ms），覆盖平面上的顶点只归A、两侧顺序和所有属性、输出修改不影响原网格、单精度减法（16777217先舍入）边界、零法线、缺失与非法属性长度。构建通过。日志 fast-hull-vertices-tests.log/build-fast-hull-vertices.log。

FastHull.Split 0x20e0688 先处理近零法线回退up，再创建A/B、AssignVertices、AssignTriangles、条件FillCutEdges、ValidateOutput，最后写结果。封口还依赖可用color/UV mapper，缺mapper时走警告分支；具体近零阈值、警告字串、ValidateOutput细节和所有triangle逻辑尚待迁移。IsEmpty 0x20e0474：isValid为false，或顶点<3，或indices<3时为空；不能只按数组是否非空保留无效碎片。

本轮未接主场景，也未输出封闭碎片。下一步继续AssignTriangles/SplitTriangle交点和属性插值、FillCutEdges封口及ValidateOutput，之后与真实猪mesh组成端到端切割再对照MuMu。原随机源、物理爆炸、平台实测和整个移植目标仍未完成。


## 2026-09-09：三角形路由与跨边交点

上轮顶点分配为 progress。本轮提取 FastHull.AssignTriangles 0x20e0fcc（1652字节）和 SplitTriangle 0x20e28c8（5324字节），原文件与反汇编归档，130源文件SHA256通过。

新增 runtime/fast-hull-triangle.ts。routeHullTriangle：三点同侧则按旧新索引直接保留；混合侧别选孤立顶点top，并将原三顶点循环旋转为top/cw/ccw，不反转绕序。原(0,1,2)孤立0→(0,1,2)，孤立1→(1,2,0)，孤立2→(2,0,1)。top在A时SplitTriangle(topHull=A,bottomHull=B)，在B时交换hull参数，且AssignTriangles交换两交点out地址以维持切口边方向。代码以reverseCutEdge标志交给后续边收集，尚未把此标志当成三角形翻面。

hullTriangleIntersections：numerator=dot(normal,pointOnPlane-top)，分别除以dot(normal,cw-top)、dot(normal,ccw-top)，Float32逐操作并Clamp01，然后top+edgeDelta*t求两交点。保留原0x20e2a20至0x20e2abc的计算/夹值语义，不插入epsilon或修改近零除数。该模块只计算交点及参数，未完成属性插值、新三角形索引追加。

测试覆盖全部8种侧别组合、保持原绕序与A/B封口边方向；几何案例两边t=.5/.25，交点严格落在x=0平面；面在边范围之外时夹到0/1。联合顶点测试共4项通过（305ms），构建通过；日志fast-hull-triangle-tests.log/build-fast-hull-triangle.log。source日志fast-hull-triangle-source-verification.log。

剩余：SplitTriangle对交点normal/color/tangent/uv的精确插值与归一化、两侧新增顶点/三角形顺序、短切口剔除阈值、FillCutEdges、ValidateOutput。当前不是完整裁切器，未产生可渲染碎片或接入main；下一步必须继续这些步骤，再用原猪网格与MuMu验证，不能用专项测试宣称完整破碎或1:1。


## 2026-09-09：交点属性插值及Color32修正

上轮三角形路由/交点实现为 progress。本轮进一步解析SplitTriangle并提取FastHull两个构造函数，134源文件SHA256通过（fast-hull-interpolate-source-verification.log）。FastHull(mesh) 0x20dff78 明确调用 Mesh.get_colors32，因此纠正前轮HullVertexData.colors使用Float32Array的错误：已改成Uint8Array，顶点分配输出也使用字节颜色；此前“全部属性浮点存储”不成立，以本节和当前代码为准。

新增 runtime/fast-hull-interpolate.ts 的 interpolateHullEdge：位置/UV按Float32逐步线性插值；法线xyz插值后按1e-5长度阈值归一化；切线仅xyz插值归一化，w直接取other端（CW交点取CW顶点w，CCW同理），不是插值w也不是取top.w。源cw.w存sp+4、ccw.w存sp+0，之后随各自xyz写回两侧。Color32逐通道插值后fcvtzs截断并写byte；0到255中点为127，不是128，保持源字节精度。缺失属性不生成；相反法线中点为零向量。

测试联合6项通过（339ms），覆盖t=0仍取另一端切线w、颜色127/10截断、法线/切线归一化、UV、相反法线、缺失属性及既有8种侧别/交点/顶点分配。npm run build通过；日志fast-hull-interpolate-tests.log/build-fast-hull-interpolate.log。

源新增三角形顺序已观察：top侧(mappedTop,newCW,newCCW)，bottom侧(mappedCW,mappedCCW,newCCW)与(mappedCW,newCCW,newCW)，两侧各追加独立两交点。下一轮需把当前顶点/路由/交点/属性模块组成真实surface split并用原猪mesh校验；本轮尚未追加索引，也未完成短切口过滤、封口、ValidateOutput或main装配。不能据此宣称完整切割器、画面还原或平台性能通过。


## 2026-09-09：原猪网格surface split组合验证

上轮交点属性实现为 progress。本轮新增 runtime/fast-hull-surface.ts，将assignHullVertices、routeHullTriangle、hullTriangleIntersections、interpolateHullEdge组成真实surface split。两侧各追加独立CW/CCW交点，top侧(mappedTop,newCW,newCCW)，bottom侧(mappedCW,mappedCCW,newCCW)、(mappedCW,newCCW,newCW)；同侧原三角形用oldToNew映射保留。返回完整positions/可选属性/indices及有向cutEdges。

AssignTriangles原ELF0xcf98d0浮点值9.999999439624929e-11：交点差的平方长度小于此值不收切口边；保留非退化边CW→CCW，孤立顶点在B时反向。FastHull.Split近零法线平方阈值使用同常量，低于时回退up。代码使用Math.fround(1e-10)。无caps、无ValidateOutput；本函数明确只完成表面裁切阶段，不能当闭合碎片。

新增2项组合测试。简单跨面三角形核对精确一加二索引顺序、有向切口和面积；真实pack63d32d2d_3820/Mesh63d32d2d_2034经本地HTTP资源服务加载，原542顶点/525三角形，分别在本地x/y/z=0切割。x输出461/104三角形、20切口边；y408/201、42边；z322/309、53边。面积误差分别3.2823e-9、-1.3249e-9、4.5408e-9；所有索引有效、属性长度吻合、位置/法线/UV有限。原表面积2.4600151461。结果见piggy-surface-cuts.json，注意这不是原版七随机平面或MuMu输出的对照。

最终2项通过（341ms），构建通过；日志fast-hull-surface-tests.log/build-fast-hull-surface.log。首次构建发现测试node:fs类型未配置，已改为Playwright request读取本地资源并从测试日志保存证据，重新测试构建通过；未添加无关依赖。

当前实现用临时JS数组组装后转typed arrays，未测峰值或宣称Worker/内存优化。下一步必须实现FillCutEdges/UV封口及ValidateOutput，组合原7平面连续裁切，再接碎片物理与真实场景。当前不会改变用户游戏画面，完整移植与微信/抖音真机验收仍未完成。


## 2026-09-09：FastHull有效性筛选

上轮surface split为 progress。本轮新增 runtime/fast-hull-validation.ts，迁移LengthAlongAxis、ValidateOutput、IsEmpty，提取ValidateOutput/LengthAlongAxis/FillCutEdges机器码与反汇编，140源文件SHA256验证通过。

FastHull静态构造从ELF0xcadb98读8字节：0ad7233ccdcc4c3d，smallestValidLength=0.009999999776482582、smallestValidRatio=0.05000000074505806（fast-hull-validation-constants.json含ELFSHA）。LengthAlongAxis遍历所有顶点，投影dot(axis,vertex)取max-min，空列表0；包含没有被indices引用的顶点，不归一化输入axis。代码保留Float32操作。

ValidateOutput先取A/B长度及和：和<length阈值，两侧isValid=false；否则若A占比<ratio，只标A无效；否则检查B占比<ratio标B无效。原代码按顺序分支，不主动设置true，不复活之前无效状态。IsEmpty=!isValid或verticesCount<3或indicesCount<3；并非只按三角形存在判断。

4项联合测试通过（349ms），包括双薄片、A/B薄片、0.01和5%边界、无效状态保持、非单位轴、未引用点、结构空条件及真实猪网格表面裁切。构建通过，日志fast-hull-validation-tests.log/build-fast-hull-validation.log。尚未在surface阶段提前调用验证：原版ValidateOutput发生在封口之后，未来完整Split应在该位置接入。

FillCutEdges已取得4456字节原生方法，直接可识别调用Triangulator构造0x20eb964；平面投影、边界环、索引映射、UV/颜色mapper与三角化接口仍需解析。没有自选fan/earcut替代原算法，也没有把开放表面送到物理。完整封口、七平面连续裁切、真实碎片/主场景及小游戏实测均未完成。


## 2026-09-09：Triangulator边界环与三维凹凸

上轮有效性筛选为 progress。本轮提取Triangulator构造、Fill、FindLoops、IsLinePairConcave与声明，149源文件SHA验证通过（shatter-boundary-source-verification.log）。修正本轮开头待核假设：不是已证明的二维投影管线；已解析凹凸方法直接在三维用planeNormal，不应先自创二维轮廓算法。

新增 runtime/shatter-boundary-loops.ts。FindLoops 0x20ec000按已排好序的(start,end)边对遍历，当前loop保存边数组偶数偏移0/2/4…，并非顶点编号。非首边若start!=前一end则LogError但继续；当当前end等于本环首边start时收环；开放末尾不收，奇数尾项按edgeCount/2忽略。函数用onDiscontinuity把源错误通知交给调用方，不自动修边或抛弃整轮。

IsLinePairConcave 0x20ed680等价dot(cross(line0,planeNormal),line1)>0，Float32逐操作、严格大于0；共线为false，法线反向翻转凹凸。不是dot(cross(line0,line1),normal)>0，符号不能弄反。测试含XY与YZ平面、法线反向、共线。

2项通过（283ms），覆盖多闭环、边偏移与顶点ID区别、开放尾部、不连续错误继续，以及三维符号；构建通过。日志shatter-boundary-loops-tests.log/build-shatter-boundary-loops.log。

FillCutEdges前处理可见最近距离搜索、边对重排及收环，但集合接口身份和完整重排/端点映射仍待严格迁移，不直接将未排序surface.edges喂给FindLoops。Triangulator.Fill调用顺序包含FindLoops→FindConcavities→PrepareDuplicateEdges→重叠判断/MergeLoops/FillTriangle→RemoveDuplicateEdges→SetOutput，具体填充与孔洞行为未完成。本轮仅环/凹凸基础，不宣称完整封口、碎片效果或main接入。


## 2026-09-09：真实切口边排序与闭环组合

上轮边界环/凹凸基础为 progress。本轮新增 runtime/shatter-boundary-order.ts，将FillCutEdges 0x20e183c..0x20e210c最近起点排序与输出点/边索引迁移，组合真实猪网格surface split→排序→FindLoops。

算法按源顺序：当前末点到当前环起点的距离作为初值，依次比较后续边起点，严格更近才替换（同距保留先遇到者）。当前边已超过环首且最近点为环首时收环；最后一条边若超过环首也收环；否则将最近候选边对交换到下一位置。收环时取每条边的起点写points，并生成连续索引与末尾回到起点。原流程不存在通用epsilon焊接、端点平均、搜索半径拒绝或自动翻转边。源修改临时边集合；实现复制后操作，避免更改surface输出。孤立末单边不成环。

4项联合测试通过（341ms），覆盖乱序正方形、分离双环、同距优先闭环、孤立边、不改输入，及真实猪mesh三轴切口。X20条边→1环20；Y42→1环42；Z53→3环8/40/5，所有输出索引连续、每个切口边被纳入。面积守恒与顶点/属性检查继续通过。结果piggy-surface-cuts.json已由本轮测试日志更新。构建通过，日志shatter-boundary-order-tests.log/build-shatter-boundary-order.log。

这是源算法的移植和本地组合结果，尚未与MuMu碎片几何直接比对。Z多环说明后续必须保持Triangulator的多环/凹凸/重叠处理；环是否为孔或外边界不能仅凭个数判定。尚未生成caps，接下来继续FindConcavities/FillTriangle/MergeLoops等源规则、UV/颜色封口与ValidateOutput接入，再进入物理/主场景和平台实测。


## 2026-09-09 跨关继续加载生命周期复核

上一目标轮仅答复位置现状，归类为 no progress；本轮追踪原版继续后的资源生命周期并归档新证据。StateGame.OnFinishContinue (0x227abc0) 依次恢复 timeScale=1、AdvanceCurrentLevel、清零实例 +0x28，再 TryShowPickGame；未进入选游戏分支时 ShowTransitionScreen 后 LoadLevels(callback)。FinishContinueLevelsLoaded (0x227ae80) 通过类型槽 0x4b7b748 调用 ChangeState，具体目标类型尚未闭合，不能猜为立即开始跑动。

AdvanceCurrentLevel (0x22cff40) 从 nextLevel 读取 +0x28 到管理器 currentLevelID(+0x38)，并增加 currentLevelIndex(+0x3c)。方法本身不销毁关卡，也不修改球或镜头位置。LoadLevels 协程 MoveNext (0x22d3c98) 先 PrepareCurrentLevels、UnloadInactiveLevels，再遍历 currentLevels：active(+0x20) 为真且 level(+0x28) 为 Unity null 的项才发起 LoadLevelAsync；每次发起后 yield null，再继续遍历。之后逐帧等待 IsAsyncLevelsLoadingCompleted，通过后 SetupLevelsAfterLoad，再 yield null 后退出。已存在有效 Level 的项不会走此处 LoadLevelAsync。

这证明当前 main.load 每次 dispose 当前/下一关并 assets.clear 的路径与源按条目复用不同。不能为了连续观感直接把整套预加载场景永久保留：PrepareCurrentLevels 的选择规则和 UnloadInactiveLevels 的释放规则仍需完整解析。SetupLevelsAfterLoad (0x22d104c，6180字节) 包含 CalculateLevelLocation、起止门定位、主题/传送门设置，已提取但尚未完成各分支及虚调用审计。因此此前“继续后必须保留原世界坐标、不允许重定位”的推断不成立；原版最终是否重定位还不能由这层协程判断。

证据：evidence/level-handoff-source/manifest.json 及逐文件 SHA256 已校验。本轮未改游戏运行代码，未用旧测试冒充新增验证。下一步先闭合 PrepareCurrentLevels、释放规则及 SetupLevelsAfterLoad 的初始化条件，再实现源关卡接管与坐标处理；保留 MuMu 同操作录像、完整局内机制与微信/抖音实机门禁。


## 2026-09-09 源关卡驻留规则与已初始化关卡定位门禁

上一目标轮为 progress（归档跨关加载证据）；本轮完成 PrepareCurrentLevels 0x22d097c 的主要列表规则，并新增 src/game/level-residency.ts。后置保留数 currentLevelID<=5 时为 7-currentLevelID，其他为1；后续预载数在关号<3时为3，其他默认2。源 UserPrefs 槽0x4b87008的整数若存在且在1..39，则后续数为1；key字符串尚未解析，模块显式接受可选值，不猜配置名也不映射为VIP。

空列表先创建当前，再逆向插入不低于1的前置关卡，最后追加后续关卡；非空列表仅把低于 current-behind 的条目标记inactive，并按当前索引补足后续数量，保留现有对象身份，不重新激活，也不因数量配置减小而截尾。actualLevelID由工厂负责调用既有映射，不能等同显示关号。UnloadInactiveLevels (0x22d05c0) 对所有 inactive 条目执行释放，之后仅删除连续inactive前缀并扣减currentIndex；末尾调用 UnloadUnusedAssets。原版释放包含声音事件解绑、Level虚调用、终点门/起点门池回收与传送门回收。模块释放回调尚未接到实际Scene/物理世界，不能把列表删除等同GPU资源回收。

新证据 SetInitialized (0x22d2ae8)明确写LoadedLevel+0x58=true；SetupLevelsAfterLoad的0x22d1278..127c读取此标记，跳过该条目的初始化段，包括CalculateLevelLocation。因此已初始化的预加载关卡不在该循环重复定位。+0x48是isCompositeLevel而非initialized，区分两者。仍需闭合球/镜头进入后续State时的位置处理，不能由此推导整个跨关镜头已对齐。

专项测试3项通过（610ms），覆盖初次第1/2/3/5/6关范围、配置边界、连续推进到763关的对象身份/有界数量/释放顺序，以及中间inactive条目不删除、配置缩小不截尾。首次测试的“总数<=5”假设失败；根据源规则第4关确实保留1..6共六关，修正断言并增加精确列表检查，未改代码来迁就错误上限。第6关起默认前一关+当前+后两关共四关。这里只测试763次逻辑推进，不代表763个实际场景机制验收。构建通过，日志 level-residency-tests.log / build-level-residency.log；21个原生证据文件SHA校验通过。

主程序仍只预加载下一关，并在继续时清空资源；新模块未接main。下一步实现同源条目对应LevelScene、门、传送门及物理所有权，处理共享纹理/几何缓存的引用释放，按初始化标记复用场景；追踪后续状态的球/镜头设置并与MuMu对比。局内全部机制、免广购买保护及微信/抖音实机性能门禁保持待办。


## 2026-09-09 后续多关预载接入主程序

上一目标轮为progress（源驻留规则实现/测试）。本轮审查Assets/LevelScene所有权：缓存几何/材质/纹理由Assets持有，LevelScene.retireInstances只释放自己生成的几何、材质和粒子。跨关保留场景时不能调用全局assets.clear；尚未实现逐资产引用计数。本轮发现setBall构造的三个球部件LevelScene未保留释放入口，新增playerScenes集合，在生命球视图释放之后销毁其场景，再清共享缓存。

main现调用levelResidencyLimits(n).ahead：第1/2关加载后三关，后续默认后两关；每个后续关卡使用上一关pack和累计placement计算，继续使用9单位pointStart衔接规则。futureLevels持有实际LevelScene和LifePickups，统一动画/预热/重载释放；nextLevel仍仅指立即下一关，制动支持碰撞仍只接该关。新增调试preloadedLevels展示实际生成的关号、出生点、终点与源渲染器数。调试单prefab路径不附加后续关卡。

测试multiple-preload.spec.ts实际加载1→5→1并核对[2,3,4]、[6,7]、[2,3,4]的非空场景/有限且不同的出生点/落点目标/无pageerror，列表不残留旧关。联合原有第1/5关main/worker抵达测试共5项通过（41.2秒），构建通过（3.49秒）。第5→6目标保持(26.999842,0,125.145767)，实际抵达约z125.135902。证据multiple-preload-tests.log、build-multiple-preload.log、multiple-preload-level1.png（已查看，道路/球/主页可见）。截图及日志指标紧接加载，包含加载耗时或前一关缓存样本，不能用其1FPS/54MiB作为稳态帧率/内存结论；本轮没有声称性能提升。

尚未完成：源前置关卡驻留、继续时直接接管已预载场景、资源引用释放、后续关卡动态物理生命周期、球/镜头后续状态与原版同步验证。当前继续仍全局重载，因此不标记跨关复用完成；多预载会增加资源常驻，需在完成源生命周期后实测drawcall/堆/GPU及加载尖峰。微信/抖音适配与实机门禁、所有局内机制目标保持不变。


## 2026-09-09 多关预载稳态采样与资源计数复核

上一轮为progress（main多关预载）。本轮修复性能面板跨加载窗口累计与旧关样本复用：开始/完成加载将sampleLevel/sampledAt标记无效，完成加载重置frameCount/metricTime；采样后暴露sampleLevel、sampledAt、sampleFrames。面板加载/等待时显示状态文字。sourceRenderers/staticBatches现包含所有已预载后续LevelScene，避免只报当前关源数。

新增tests/preload-performance.spec.ts，两种物理模式各加载1→5→1→5→1，每轮收集四个独立约500ms窗口，丢弃首窗口，核对样本关号/有效帧数与重复加载资源计数。首次主线程/Worker断言失败，未放宽数量阈值：debug.sampleRenderedResources以一次显式额外渲染记录实际Mesh绘制，并在finally恢复全部onBeforeRender回调。诊断定位多出的36顶点材质Pipe静态批，中心(-2.050125,-13.330084,229.989952)，在第2关远处。主页Camera time正弦摆动造成该物体进出视锥；第1关几何计数55→56→55并非本次证据中的持续累积。详细诊断保留preload-render-diagnostic-detail.log。

新增仅debug接口setCameraTime，测试固定camera时间相位0以控制视野；默认undefined继续使用原先时间，正常游戏行为不变。最终主线程/Worker两项通过；各自第1关62calls/55geometries/27textures，第5关87calls/61geometries/30textures，五次加载同关计数相等。采样平均帧时主线程第1关16.66..18.45ms，第5关16.66..17.81ms；Worker约16.66..18.45ms。仅411x731 headless Chromium主页、无输入、未强制GC；构建与采样部分时间重叠，不能据小幅帧耗时差异宣称Worker更快。JS heap常数51.02MiB缺少可信动态粒度，不作为内存无泄漏证据；几何/纹理数量仅证明这五次加载的渲染器计数未增长，不等于字节数或进程/GPU内存。

最终原始样本含逐Mesh清单保存preload-performance.json，日志preload-performance-tests.log，构建通过build-preload-performance.log。主场景仍全局重载、未接原版驻留复用；下一步完成跨关接管/引用释放，再补移动路线与机关负载、MuMu同操作输入、微信/抖音真机帧/内存/加载峰值验证。总目标未完成。


## 2026-09-09 继续后状态与球/镜头初始化源闭合

上一轮为progress（采样修复及实际重复加载证据）。本轮确认MuMu PID17413仍运行，在native-levels增加continue-state-type只读模式：从0x4b7b748类型句柄读取Il2CppType，检查类型CLASS(0x12)、元数据magic/version31、指针位于映射的global-metadata.dat类型表、88字节条目对齐和字符串索引范围，得到TypeDefinitionIndex1280=Gyro.StateMenu；运行字符串和本地metadata SHA/类型表再次交叉校验。证据native-continue-state-type.json。NDK编译/adb执行成功，仅推送读取器工具，不修改游戏代码、存档或购买。初次尝试su包装返回1，实际ADB shell已可直接读取；没有把失败输出当证据。

FinishContinueLevelsLoaded 0x227ae80传该类型给ChangeState，因此源继续完成后回到StateMenu。StateMenu.Enter 0x22be910的球初始化段依次PrepareForGame、SetVisualSphereGameController、Deactivate、SetInteractable(false)，从currentLevel的localPosition/localRotation和GetStartSpawnPoint(Space.Self)组成世界出生点，赋给Gameplay出生数据，StopAnimations，Respawn(5)，EnableCamera(true)、SetCameraMode(9)、ActivateCamera(true)，再ResetLevels(false)、StartLevels。GetStartSpawnPoint虚槽+0x2b8沿用先前CompositeLevel运行核验，非新猜方法。

Gameplay.Respawn 0x22fba88将出生数据传入物理接口，再CameraOperator.Reset(spawn,5)、VisualSphereGameController.Sync和可选respawn事件。该5是cameraStartDistanceOffset参数，不是5秒延迟；参数名由恢复签名且原生传递链确认。Respawn前有可选目标LookRotation分支，物理接口槽22/23及CameraOperator.Reset内部776字节尚未完全审计，不能据此写死球旋转或镜头初始距离。StateMenu中的ResetLevels/StartLevels已提取，各虚调用的机关重置语义仍需闭合。

结论修正：原版复用已初始化Level，但继续回主页仍显式重设球和镜头。不能把“接管场景”实现成完全不Respawn/不重置镜头；也不能把客户端当前整体load回原点当作正确的世界出生点保留。主程序未在本轮修改，未重跑无关Web测试。新增五方法十文件，level-handoff-source合计31文件SHA通过。下一步按此生命周期接管已预载LevelScene，保留原版世界出生点，再处理ResetLevels/StartLevels的实体及机关状态，完成实际跨关与MuMu同步验证；小游戏实机性能、全部局内机制和完整目标继续待办。


## 2026-09-09 预载场景跨关接管落地

上一轮为progress（MuMu类型句柄确认StateMenu）。本轮main为resident条目保留pack、累计placement、LevelScene、selection和结束门。仅正常完成后请求立即下一关时复用futureLevels[0]；调试跳关、重试仍执行完整加载。接管保留该场景对象与世界坐标，把原当前关移入pastLevels，按源behind范围销毁过旧条目，并按ahead范围补足后续关卡。已存在的后续场景不重复实例化；背景也在接管时复用。

新当前关补建关闭的起点门、复用其预载结束门、设置拾取闪光；球与生命球视图按既有流程重新准备，物理世界重新初始化为新当前关的世界坐标碰撞/机关规格，主页/制动时钟/输入状态重新初始化。未把物理世界复用、全部Level.Reset/Start语义或CameraOperator.Reset(5)的精确源行为冒充完成：当前仍用已有GameCamera.reset，源机关/球旋转/镜头细节待继续对照。初始化前明确释放被接管条目的旧LifePickups，避免重新构建后残留重复视图。

Assets.releaseUnused(scene)在加载和预热结束后清理未由驻留场景引用的缓存几何、材质和纹理，并释放不再使用的imageSources引用；包括隐藏Mesh、克隆材质的贴图、ShaderMaterial直接uniform纹理、Scene背景/environment。先拆除旧视图/物理拥有者，再释放；保留尚在场景中的共享资源。本实现不是通用异步引用计数：调用要求加载完成，非场景外部消费者须另行传递所有权；defs元数据未裁剪，静态合批后已不被Mesh引用的原始缓存几何可能在未来构建时重载，网络字节/CPU缓存仍需测量优化。

验证：finish-arrival第1/5关main/worker增加下一关sceneId与此前预载sceneId一致、前关保留、球位置与此前finishTarget距离<.025断言；scene-handoff覆盖隐藏共享资源保留/最后引用移除后释放，以及实际连续1→7关、每次世界出生点和场景身份、到第6/7关保留前置[5]/[6]。第7关世界出生点约(26.995669,-73.504272,931.123878)，不会回到原局部起点。另测1→5→1手动加载清理旧列表。最终7项通过（48.8秒）、构建通过，日志scene-handoff-final-tests.log/build-scene-handoff.log。首轮期间源代码热更新且Worker用例超时，该轮不作为最终通过证据；停止编辑后完整重跑通过。scene-handoff-level7.png已查看，球、道路、主页可见；scene-handoff-results.json记录连续结果。没有将这些调试门前放球测试称为整条赛道真实输入通关或原版视觉验收。

剩余：冷启动到高关仍没有源前置场景；跨关旧关仅视觉驻留，其动态物理/源ResetLevels所有分支未复刻；复杂关/传送门/主题变化生命周期待闭合。完成UI经济交易仍沿用既有不完整主流程。新增接管后的drawcall/堆/加载尖峰需重新测量，不能复用此前全量重载性能样本宣布提升。全部局内机制、MuMu同步操作、微信/抖音实机与完整目标继续active。


## 2026-09-09 CameraOperator.Reset门禁与返回主页分支

上一轮为progress（主场景接管）。本轮审计0x22fbcd8，发现前轮“调用Respawn因此重设镜头”的表述必须收窄为调用链：Reset先检查currentMode<=14且(1<<mode)&0x4201，只有game=0/menu=9/gate=14进入；gateFinish=15/gameFinish=18等直接return。进入后还需满足provider类型条件。源有效分支把distance设置为GameConfig.CAMERA_DISTANCE+cameraStartDistanceOffset，主线5+5=10，但不能不看模式就把客户端跨关距离改为10。pitch来自CAMERA_ANGLE_VERTICAL、verticalOffset来自静态字段，yaw由出生forward水平投影计算；不是当前GameCamera.reset固定12/20/5/0的无条件规则。

新增audit-camera-mode-transitions.py直接读取ELF指令0x22fbd58验证位掩码，并解码两级ushort跳表：新模式9在表0xcfb298落入0x22f85ec，旧模式表0xcfb2d2中15→0x22f88fc、18→0x22f8a38。15分支取menu provider +0x50，以旧gateFinish provider +0xb8为参数调用虚槽+0x198，再启用menu；18分支直接选择既有menu provider，没有在这条ChangeMode分支执行该同步调用。GameCameraPoseProvider.SyncWithGamePoseProvider (0x22fe914)复制current/destination/lerpFactors及两个airView标志。尚需把虚槽及每种provider override完整闭合，不能把“没有该同步调用”推广成其它位置从未改过menu状态。

证据camera-mode-transition-audit.json/.log；脚本所有地址/分支断言通过。新增3方法6文件，level-handoff-source合计37文件SHA通过。未改客户端镜头参数，也未重跑无关Web测试。下步须恢复显式mode与持久provider状态（包括结算mode18），按转换分支同步；仍需MuMu逐帧观察后才替换当前跨关cameraRig.reset。保留主程序接管已实现事实，但其镜头1:1未完成。全部局内机制、实际资源性能和小游戏实机门禁继续待办。


## 2026-09-09 当前15→9跨关镜头首帧继承

上一轮为progress（Reset位掩码/ChangeMode跳表）。当前main结束门后仍停留于既有gateFinish镜头，临时结算没有切到原版gameFinish=18；因此本轮仅按已审计15→9同步分支修复运行路径。GameCamera.returnToMenuFromGateFinish在确实有finishFocus时清除结束镜头模式，保留当前target、yaw/pitch/distance/verticalOffset，随后按现有menu更新目标。正常接管调用此入口；冷加载/普通重置不受影响，未无条件设置distance=10，也未把该分支套用到尚未实现的18。main输入yaw同步为继承镜头的yaw，不再置0。

测试新增：纯镜头在结束后切menu的dt=0帧保留position/quaternion/全部四参数，再向新的世界出生点过渡；实际main/worker到达临时结算后调用正常load(2)接管，比较返回前后首帧位置与四参数，完全一致，sceneId仍是预载对象。随后等待pitch<22，证明没有停留在结束镜头。实际观测main切换前后pitch29.573585、distance7.610978、position z139.263125保持一致；之后向下一关主页目标过渡。日志中settled仅表示达到测试pitch<22条件，非完全收敛或原版稳态。

联合结束镜头/资源释放/连续1→7关共6项通过（24.9秒），构建通过（3.92秒），证据handoff-camera-tests.log、handoff-camera-results.json、build-handoff-camera.log。此次测试显式固定debug时间相位以控制比较条件，不改变正常时间行为。未制作MuMu同步视频，不能称逐帧原版验收。

限制仍在：GameCamera仍是现有简化状态实现，未完整持有源current/destination/lerpFactors和airView全部字段；原版完整结算mode18及18→9持久menu状态待恢复，GyroTarget滤波/重置角度/球朝向仍待核查。跨关资源/物理接管已有进展，但冷加载前关、旧关碰撞和源ResetLevels全部机关语义、经济结算与小游戏实机门禁未完成。


## 2026-09-09 结算mode18触发假设审查

上一轮为progress（当前15→9运行衔接）。本轮追踪GameFinishCameraPoseProvider.CalculateDestinationAndLerpFactors (0x22ff76c)：先调用基础GameCamera计算，再用current.position覆盖destination.position、距离=CAMERA_DISTANCE*3、俯角=CAMERA_ANGLE_VERTICAL*1.5；当前主线常量对应15和39°。这只是provider算法存在，不等于普通关卡结算会启用该provider。其余插值系数计算已归档但未移植。

新增scripts/audit-camera-mode-callers.py，扫描ELF可执行PT_LOAD中直接B/BL到CameraOperator.ChangeMode(mode)0x22f81fc与Gameplay.SetCameraMode(mode)0x22f81e8，按最近恢复方法边界归属并记录调用前40字节反汇编。共93个候选，未见上下文中mov w1,#0x12；普通StateGame.FinishGate_OnGateEnter明确mov w1,#0xf。StateGamePortals/BonusPortal的终点用0x13(19)，Races用0x14(20)，需要各自机制路径，不能统一为18。此扫描不覆盖间接/反射/预先存入寄存器的模式值，不能证明18不可达；含最近方法边界归属也不作为运行覆盖率。证据camera-mode-callers.json/.log及可复跑脚本。

计划修正：此前多次写“普通完整结算仍需恢复mode18”证据不足，改为“mode18触发路径待证”，不为了补齐枚举而把它强行接入普通ScreenFinish。当前15→9规则有直接源分支支持，继续保留，仍需MuMu完整普通结算时序复核。原版所有已证实机制、结算UI/经济/跨关范围未缩减；仅删除无依据的必经顺序假设。

本轮没有修改游戏运行代码或重跑无关Web测试。扫描完成、93候选与无立即数18的检查通过；新增provider方法2文件，level-handoff-source共39文件SHA通过。后续优先补齐有证据的普通结算UI和源ResetLevels/StartLevels生命周期，同时保留特殊模式/传送门的镜头差异与小游戏实机门禁。


## 2026-09-09 Level生命周期虚槽与前关拾取物隐藏

上一轮为progress（镜头调用扫描修正计划）。MuMu PID17413已重新读取确认；native-levels新增level-lifecycle-slots，O_RDONLY检查CompositeLevel的已初始化虚表：+0x218→Level.SetActiveCollectables(0x231885c)，+0x228→CompositeLevel.ResetLevel(0x230c7b8)，+0x238→CompositeLevel.SetEnablePhysics(0x230c5dc)，+0x248→CompositeLevel.StartLevel(0x230c964)。返回地址逐一匹配method-map唯一方法，证据native-level-lifecycle-slots.json；未调用事件或修改存档/购买。

ResetLevels参数false时，各条目拾取物/钥匙active=(levelID>=currentLevelID)；参数true时全部false。每项先SetActiveCollectables，再SetActiveCollectableKeys。当前关调用SetEnablePhysics(true)后ResetLevel；其他关先ResetLevel再SetEnablePhysics(false)，顺序不同，不可粗略合并。StartLevels只调用currentIndex条目的StartLevel（错误索引走日志分支），不是启动所有驻留关。CompositeLevel转发到各子关，StartLevel随后发自身OnLevelStart；基础Level.StartLevel仅发事件。ResetLevel还更新源边界点并发OnLevelReset，不能以球reset替代各订阅机关reset。

运行修复：当当前关移入pastLevels时，LevelScene.disablePastCollectables关闭尚存金币对象、实例金币批以及CollectableKey节点；下一帧更新实例矩阵时仍保持batch不可见，不修改collected或发奖。只实现单向前置关生命周期，未增加未经验证的已拾取物恢复流程。此前旧关未拾取金币/钥匙仍会在回望道路显示，与源active=false不一致。调试pastLevels记录collectablesActive，连续跨关断言所有前关false。

专项包含隐藏共享资源保留、连续1→7世界坐标/身份/前关拾取物状态，以及实例金币下一帧不再显示/钥匙隐藏且未记为收集，共3项通过（15.1秒），构建通过（3.57秒）。证据past-collectables-tests.log/build-past-collectables.log；新增7方法14文件，源包53文件SHA通过。未重跑整套，未称为MuMu视觉验收或全部机关生命周期验收。

仍待：逐订阅对象恢复OnLevelReset/OnLevelStart与EnablePhysics/DisablePhysics（尤其预载动态机关），旧关生命球/特殊拾取物的完整可见性规则，以及冷启动前关、碰撞复用、结算UI经济和小游戏实机性能门禁。主物理仍按当前关重建，未宣称该步骤与全部源事件等价。


## 2026-09-09 驻留 MovingObject 初始姿态

上一轮仅回答落点状态，分类为no progress；本轮重新读取当前实现与原版机器码后完成修复。MovingObject.OnLevelReset(0x233280c)读取startT+0x40/startDirection+0x3c，清isActive+0x60，立即调用UpdateObject虚槽+0x218；OnLevelStart(0x2332920)设置isActive；FixedUpdate(0x23325b0)在isActive为false时跳过更新。不能让未来场景保持prefab默认姿态，或让前置场景停留在最后运动姿态。

LevelScene.resetMotionVisuals使用现有motionPose与源startT/startDirection，按bodyId将世界姿态转换为父节点局部姿态。main加载结束前对所有past/future驻留场景调用；当前关仍由Simulation.init初始化同一运动规格。不修改源MotionSpec、物理初始数据或非MotionSpec动态物体，也没有给未来关建立持续物理模拟。未来预载和旧关重置发生在加载阶段，不新增逐帧计算或drawcall。

验证：motion-reset-visuals测试覆盖跨关平移/旋转父节点、反向路径startT=.25、旋转机关、重复重置、源规格不变和无关物体不变；联合scene-handoff连续1→7关与拾取物/共享资源回归，共4项通过(15.5s)。npm run build通过。证据motion-reset-visuals-tests.log、build-motion-reset-visuals.log。原版四方法bin/capstone归档到level-handoff-source，manifest共61文件SHA全部通过。

限制：这不是全部Level.Reset/Start语义完成；非自动平衡板、可破坏物等动态实体和独立旋转组件仍需逐类恢复。测试未进行MuMu同步录像或小游戏真机验证；现有motionPose各类实现的完整原版轨迹仍保留验证事项。原版落点视觉/制动接触时序、全局内机制、驻留内存峰值及微信/抖音性能验收继续待办，完整目标保持active。


## 2026-09-09 连续接管性能实测（桌面，非平台验收）

上一轮为progress（驻留机关reset）。本轮新增handoff-performance.spec.ts，在411×731 headless Chromium分别运行main/worker，两种模式各两轮连续1→8关。固定菜单相位，关前调试放球触发实际终点，在结束UI出现时继续；每关取三个新500ms窗口、丢弃第一个，记录其余两个主页样本、结束制动样本、load耗时、场景身份、主isolate CDP堆和DOM计数。直接调用与按钮相同的load(next)并验证预载sceneId接管；不是完整赛道同输入通关，也没有与MuMu同步。

2项测试通过(1.9m)，构建通过(3.58s)。原始行、可复现汇总脚本及结果为tests/handoff-performance.spec.ts、scripts/summarize-handoff-performance.py、evidence/handoff-performance-tests.log、handoff-performance.json、handoff-performance-summary.log、build-handoff-performance.log。

两种模式、两轮的同关drawcall/geometry/texture计数一致，按1..8关分别为：62/55/27、126/101/29、103/150/33、90/213/34、95/172/35、77/97/33、79/94/33、116/105/39。第4关213几何对应六关驻留，第6关回到四关驻留后为97；没有本路线重复引入的计数累积证据，但不能扩展为全部资源无泄漏。测试强断言重复texture数相同，geometry和drawcall是实际观测结果；所有接管sceneId和6关起只保留前一关的断言通过。

main加载14次：中位86.25ms、最大115.9ms；worker中位122.5ms、最大168.1ms。主页帧间隔中位均16.668ms，最大约18.45ms。结束时稀疏物理样本main中位0.15ms、最大0.8ms，worker中位0.20ms、最大0.30ms；worker往返中位10.3ms、最大20.8ms。样本不足以比较持续复杂机关吞吐。当前Physics.init每次跨关创建Worker；其启动/传输可能贡献额外加载成本，但本轮没有分阶段计时，不能量化因果或宣称Worker必然更慢。

CDP主isolate used heap观测main25.77..51.40MiB、worker23.17..48.11MiB，无强制GC。第二轮部分关更高、部分更低；不能据此认定泄漏或worker节省总内存。Worker JS/WASM、GPU和进程总内存未计入。Assets.loadedBytes实际上是JSON字符数+网格字节的累计值，不含图片、不等于网络传输；保留原始值仅供排查，不能作为总资源量。longtask observer未记录加载重叠条目，但没有保存API支持标记，不将其解释为无阻塞或无加载尖峰。

下一步：保留main默认与worker可选；对代表性复杂关以同输入采集持续帧时间/物理步耗时和Worker整体内存，拆解加载阶段再决定是否复用Worker。第2关126calls值得进一步按实际绘制对象归因；优化须保留原版机关和驻留行为。MuMu逐帧轨迹、全部局内机制、微信/抖音真机与完整目标保持待办，不宣称1:1/平台性能验收。


## 2026-09-09 小木箱动态实例绘制

上一轮为progress（连续接管性能实测）。本轮先以handoff-draws.spec.ts复现1→2接管，sampleRenderedResources归因126次网格绘制，其中PushBoxSmall为60次；其他主要为Pipe16和道路各材质7..8次。采样时renderer总calls128含额外渲染开销，与上一轮更晚的稳态126不能直接混称同一测点。

新增runtime/rigid-mesh-batch.ts，LevelScene.add仅对bodyOwner带PushSmallBox、原始Mesh可见、相同geometry/material和阴影配置、单个不透明材质、正determinant的重复网格建立InstancedMesh。每个箱子的原对象、独立BodySpec/collider和物理更新保持原样，原网格只隐藏绘制。实例矩阵追踪各源世界变换并转为批父节点局部变换；祖先隐藏使用零缩放。矩阵变化才上传并更新包围球，未变化时保留缓存；每帧仍有矩阵检查成本，不声称CPU无开销。retireInstances按源instance释放批和实例GPU缓冲，不dispose共享geometry/material；resourceStats补充rigidBatches/rigidSlots。

同一诊断流程后PushBoxSmall降至2次，网格绘制126→68，renderer总calls128→70，几何101/纹理29不变；三角形39190→39334(+144，约0.37%)。实例批采用整体包围球，会包含部分单网格原本被剔除的三角形，这是减少drawcall的可见代价；未证明总帧时或移动端耗电改善。没有减少箱子数量或合并物理碰撞。

验证：真实第2关48个木箱、85个总物理body的独立测试，将实例绘制切回原网格作256×256近景像素对照，含单箱平移/旋转和隐藏。三帧像素RMS约0.001953（0..255颜色范围），非背景样本>16000，原近景24/24/23次绘制变为每帧1次。实例退场后批次数0，清缓存前共享geometry未释放。联合main/worker场景退场与连续1→7接管，共6项最终通过(26.2s)，构建通过。首轮2项旧退场测试失败，因为resourceStats增加的collectablesActive布尔值被旧every(n===0)断言当作资源数量；修正为对所有number计数断言零，仍覆盖全部资源数量和新增批/槽计数，不放宽共享资源误释放检查。

证据：handoff-draws.json、handoff-draws-batched.json及对应测试日志；rigid-mesh-batch.json、rigid-mesh-batch-final-tests.log、build-rigid-mesh-batch.log。未重新运行两轮长路线性能基准，不能将之前的堆/加载数字称为本优化后结果。下一步继续复杂关物理/同输入MuMu对照、完整机关生命周期，以及小游戏真机上矩阵更新CPU、实例包围球剔除和GPU收益验证。完整目标active。


## 2026-09-09 PushObject 驻留姿态重置

上一轮为progress（小木箱实例绘制）。本轮恢复源PushObject.OnLevelInit(0x233bd74)→Init(0x233b834)：设置阻尼，记录组件transform世界position/rotation，initialized=true。OnLevelReset(0x233be78)在initialized时调用ResetAll(0x233b910)。ResetAll恢复该世界位置/旋转，启用列表中的Renderer/Collider，刚体isKinematic=false、线/角速度归零、detectCollisions=true，dead=false。字段与调用均来自3.40 ARM64；PushBox/PushSmallBox/PushBall/CustomTrafficCone继承PushObject且恢复声明中无OnLevelReset/Init覆盖。不能按diffable里的32位字段offset读ARM64内存。

客户端LevelScene按这些组件的原对象保存初始世界姿态（不是假定theRigidbody必与组件同节点），retireInstances同步删除记录。resetPushVisuals将保存世界姿态转换为当前父节点局部姿态，恢复对象后立即同步RigidMeshBatch。main在加载完成前对past/future调用，再执行既有运动机关重置。当前关仍由新Simulation初始化身体与速度；没有创建旧关动态物理世界，也没有修改存档或购买。

真实第2关木箱测试先平移/旋转，再执行reset：世界位置误差0、旋转误差约2.98e-8rad、实例矩阵位置误差0。联合运动机关父变换、共享资源/拾取物、连续1→7接管共5项通过(17.4s)，构建通过。证据push-reset-tests.log、push-reset.json、build-push-reset.log。五个原方法bin/capstone归档后level-handoff-source共71文件SHA全部通过。

实现边界：本轮完成已推动对象的驻留姿态恢复；源死亡隐藏后的Renderer恢复、爆炸/掉落Die、Freeze/Unfreeze和全部EnablePhysics行为尚未完整移植，不能称为ResetAll全量完成。未重新进行MuMu同步或小游戏实机验证。完整局内机制、输入手感、跨关精确镜头/接触时序、加载和内存/Worker真机评估继续待办，目标active。


## 2026-09-09 PushObject 掉落死亡与恢复

上一轮为progress（驻留姿态重置）。源LateUpdate(0x233b2bc)先检查initialized/dead，再以float32的initialPosition.y-currentWorldY严格大于50调用Die(0x233b328)；恰好50不会死亡。Die设置dead，关闭renderers和colliders列表成员，刚体线/角速度归零并isKinematic=true。没有Destroy，也没有全局detectCollisions=false；不可把全部碰撞体或整个GameObject随意关闭。

LevelScene初始记录扩展为组件对应刚体ID、精确Collider组件ID、Renderer引用和dead。main在当前帧物理快照应用后调用fallenPushObjects（保持LateUpdate式逐帧检测），只对首次过阈值发送死亡命令。实例网格引入sourceRendererEnabled，保留原独立Renderer的启用语义，避免死亡后下一帧实例更新重新显示。resetPushVisuals恢复dead=false、列表渲染器启用及初始姿态，再同步实例矩阵；新关物理初始化继续恢复原碰撞配置。

Physics/Worker增加带generation的pushDeath命令，共用Simulation.killPushObject；按ShapeSpec.id映射精确关闭列表碰撞体，速度清零、转KinematicPositionBased并固定下一运动学位置/旋转。独立刚体与对象保留，旧关退场时释放；shape句柄索引随body退休和world销毁清理。没有以移除刚体冒充原版可重置状态。

验证：首轮6项包含死亡、真实材质实例对照及main/worker资源退场通过(19.5s)，构建通过(3.91s)。复核发现测试在Worker reset仍pending时尝试首个step，被既有背压机制拒绝，导致实际少跑一步；测试改为先等待reset完成，死亡专项3项重跑通过(8.0s)。同样10步下落+死亡后100步，main/worker冻结高度均-0.1408731043，关闭碰撞体上方球落至-8.4882936478，未列入关闭清单的碰撞体仍支撑球于0.8588207364。真实木箱50边界不触发、50.125触发一次，实例隐藏、reset恢复及再次死亡全部通过。

证据push-death-tests.log、push-death-final-tests.log、push-death.json、build-push-death.log；新增两方法bin/capstone后level-handoff-source共75文件SHA校验通过。边界：只恢复掉落死亡，爆炸触发/力/效果与Freeze/Unfreeze仍待移植；Worker命令排队与原版LateUpdate/PhysX之间的精确帧时仍需MuMu同步实测。当前主场景只检测当前关，前后驻留关不模拟动态掉落。没有宣称全部机关、1:1视觉或小游戏性能验收完成，完整目标active。


## 2026-09-09 爆炸路径资源审计与优先级纠正

上一轮为progress（PushObject掉落死亡）。本轮没有继续凭名称实现“爆炸箱”，而是扫描全部1304个唯一catalog资源包。16066个PushObject派生组件（PushSmallBox15009、PushBox679、PushBall374、CustomTrafficCone3、PushObject1）均有isExplosive字段且值为0；缺失字段数0。该结果只证明导出包序列化配置，不证明运行时绝不改写；PushObject爆炸分支保留为运行可达性待证，不删除目标范围。

PushObject.OnCollisionEnter(0x233b51c)确认initialized和isExplosive后比较碰撞对象layer与Layers.GyroSphere。MuMu PID17413重新pidof确认，既有只读mechanic-constants实测GyroSphere=11（Obstacle9、Ghost19），未改进程/存档。通过后先Die，再以当前位置和explosionRadius调用OverlapSphere；遍历attachedRigidbody并用已处理集合式列表避免重复施力，AddExplosionForce传power/position/radius/upwardsModifier和ForceMode值5。恢复的UnityEngine.ForceMode枚举5=Acceleration，禁止误实现成Impulse。末尾位置/半径事件的具体订阅链仍待恢复；不能把该分支混用到地雷。

真实本地机制：ExplosiveMine44个，位于11个包（10个关卡片段+Resources/prefabs/_level/explosivemine模板），44个在序列化父层级中均active，尺寸1.0有20、1.5有18、2.0有6。另有SpawnerExplosiveMine模板1个、ObjectSpawner85、ProjectileSpawner100。这里按唯一包中的节点计数，不是实际763关展开实例数或生成频率；完整映射/别名/包SHA/配置见explosive-spawner-inventory.json。

ExplosiveMine.OnTriggerEnter(0x231014c)只在GyroSphere层设置proximityTriggered=true，不是进入警戒范围立即爆炸。GetExplosionRadius(0x230ff50)=float32(size*10)。Explode(0x230fdf8)关闭container、置exploded，只有debug_ResetAfterExplode静态标记启用才调ResetMine(2)；该运行标记尚未读出，不能写死常规两秒复生。OnLevelInit(0x230fac4)为三个旋转分量生成随机符号/幅度，绑定explosiveTrigger.explosiveLevelPart=this，显示容器、UpdateSize并initialized。ExplosiveTrigger本身是字段容器；Gameplay.PhysicalSphere_OnExplosiveTriggerEnter是已定位但未展开的下一条调用入口。

后续实施顺序：先闭合Gameplay→IExplosiveLevelPart/PhysicalSphere受力与死亡、特效事件；再恢复地雷警戒旋转/抖动、触发尺寸及Reset/EnablePhysics；随后接主场景和Worker真实触发测试，并以含地雷的片段035_v01_End_0、050_v01_Mid_1、055_v01_Mid_0等作MuMu对照。SpawnerExplosiveMine复用关系和生成器周期单独恢复。不得用警戒传感器替代爆炸触发器或把PushObject的ForceMode猜作地雷受力模式。

证据：scripts/audit-push-explosives.py可重跑，push-explosive-inventory.json/.log、explosive-spawner-inventory.json、push-explosion-native-constants.json；5个原方法新增10文件，level-handoff-source共85文件SHA通过。本轮是资源/原版证据与设计计划的进展，无游戏运行代码修改，因此未重跑无关Web测试或构建。所有未完成局内机制、MuMu同步视觉/手感、小游戏真机性能与完整目标继续active。


## 2026-09-09 地雷主线爆炸调用链与UpdateSize

上一轮为progress（资源/爆炸路径审计）。本轮发现PhysicalSphere.HandleBombExplosion(0x235c5d0)只有ret，不能因方法名就在该入口实现弹飞或死亡。Gameplay.PhysicalSphere_OnExplosiveTriggerEnter(0x22fb744)取触发器组件，读其IExplosiveLevelPart并分发OnExplosiveTriggered；常规StateGame继承StateGameBase，处理方法为StateGameBase.Gameplay_OnExplosiveTriggered(0x228d1d0)。该方法通过接口先Explode，再振动、获取ParticleExplosion、设置爆炸位置和radius/5缩放并加入粒子集合，然后OverlapSphere(position,radius)，对唯一attachedRigidbody施加AddExplosionForce(800,position,radius,4,Acceleration=5)。800由指令立即数0x44480000按float解释确认。通知文本槽和虚方法仍需继续核验；没有在本轮猜测文案、额外生命扣除或擅加爆炸冲量。

源ExplosiveMine.UpdateSize(0x230fbcc)设置container.localScale=one*size、localPosition=forward*(float32(size*.5)+float32(.2))，proximityCollider.radius=size。偏移常量0xcf9adc从ELF PT_LOAD映射读取为0.20000000298023224；Vector3静态forward先前MuMu确认(0,0,1)。已接expandRuntime的深拷贝路径，先处理尺寸再计算世界变换及生成碰撞规格，避免未来size变更后视觉/警戒半径脱节。此步只适用于ExplosiveMine，不把SpawnerExplosiveMine当相同实现。

mine-sizing.spec.ts读取11个真实资源包，覆盖44个地雷、三个size取值、缩放/位置/SphereCollider半径与原包不变断言；1项通过(450ms)，构建通过。测试同时发现这44个源资源的保存尺寸已与UpdateSize一致，changed=0，因此本轮并未修复已知外观差异，不能把初始化支持称为警戒动画或完整爆炸落地。证据mine-sizing-tests.log、build-mine-sizing.log。新增5个方法10文件与常量JSON后level-handoff-source共96文件SHA校验通过。

后续必须恢复地雷警戒旋转/抖动及触发Collider尺寸/生命周期，接StateGameBase的粒子与受力流程；Rapier对AddExplosionForce的最近点、半径衰减、向上修正和单次Acceleration积分需按原版证据/PhysX语义核验，不能使用未经证明的中心点距离冲量替代。继而做真实地雷main/worker触发回归和MuMu同步测试。全关机制、小游戏真机性能和完整目标继续active。


## 2026-09-09 地雷警戒动画运行接入

上一轮为progress（地雷爆炸调用链及尺寸初始化）。本轮恢复ExplosiveMine.Update(0x230ff60)、OnTriggerExit(0x23101e4)、ResetMine无参(0x230fdac)/延时(0x230fe7c)、OnLevelReset(0x230fd90)。Update的0x2310004跳到ELF补丁区0x490eb70，补丁加载s11=常量0xcf9b18后返回0x2310008；该8字节及反汇编已归档，不能跳过分支而把随机范围当未知。常量上下界分别-0.05000000074505806和+0.05000000074505806。

MineAnimation保存初始化时一次采样的三轴整数角速度（每轴幅度Random.Range(10,60)、随机正负），使用局部Rotate的Euler增量。接近时rotateScale向5按clamp01(dt)插值，shakeScale向1按clamp01(dt*2)插值，模型局部位置为三轴随机[-.05,.05]*shakeScale并做坐标镜像。离开时shakeScale立即归0、模型局部位置归零，rotateScale向1按clamp01(dt*5)恢复。ResetMine清proximity/exploded并置rotateScale=1，不重置模型朝向；Update在exploded时停止。当前随机数使用JS生成器，并不匹配Unity随机序列，不能声称逐帧姿态相同。

LevelScene将ExplosiveMine从静态合批排除，保存模型/警戒tag与动画；源OnLevelEnablePhysics明确启用proximityCollider和explosiveTrigger.triggerCollider，故按组件引用恢复两者。已有Simulation只向球接触发出此类事件，applyPhysics据进入/离开更新警戒；每帧更新动画，退场清映射，加载当前及前后驻留关执行重置。未来关没有物理事件但保留空闲旋转，与源Update只检查initialized/exploded而不检查isActive的分支对应。dt=0保持插值/转角，但若proximity仍为true则仍采样抖动，遵循该方法语义；完整暂停状态是否关闭其对象仍需上层原版验证。

4项测试通过(5.0s)：警戒增速/离开归零/重置保留朝向/爆炸停止、真实模板传感器main和worker进入/退出（.1秒时scale均1.399999976），以及44个地雷尺寸。构建通过。证据mine-animation-tests.log、build-mine-animation.log。源证据manifest更新至108文件SHA全部通过。

本轮完成警戒动画和传感器运行接入，未把已启用的爆炸触发事件接成实际爆炸；爆炸受力、粒子、通知/振动、debug延迟复生和SpawnerExplosiveMine仍待完成。新增独立地雷绘制/动画有性能成本，未重测整场drawcall或小游戏真机。接续优先完成爆炸接入和真实片段MuMu对照，保持全部局内/平台目标active。


## 2026-09-09 Unity 引擎爆炸作用点与衰减

上一轮为progress（地雷警戒运行接入）。为避免把Acceleration简化成固定速度，核对Unity6官方API说明：[AddExplosionForce](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Rigidbody.AddExplosionForce.html)、[ForceMode.Acceleration](https://docs.unity3d.com/6000.0/Documentation/ScriptReference/ForceMode.Acceleration.html)。API说明涉及表面作用点、距离衰减和惯性张量，不能据此认为普通中心点冲量已等价；以下更具体结论来自本地引擎机器码。

IL2CPP AddExplosionForce_Injected(0x465cff4)读取icall缓存槽0x4ed61f0。native-levels新增explosion-icall只读模式；重新pidof确认MuMu PID17413，实测缓存resolved=false，未调用解析器或爆炸、未改存档。转而扫描本地libunity：字符串0xd87b7为UnityEngine.Rigidbody::AddExplosionForce_Injected，注册代码0x551e48以x0传字符串、x1=0x551130，stub跳0x790658。scripts/audit-unity-explosion.py断言该注册指令和分支，按PT_LOAD提取源码区；libunity SHA256 dfa1b4cc7758a4975e4849ea825a449700d113de041ae91848ac1d352b852492。

引擎0x790658首先以原爆心调用closest-point helper(0x7905b0)，保存平方距离；upwards非0时爆心Y减upwards，并再次调用同helper得到最终作用点。衰减仍用第一次距离：radius>float32(1e-6)时1-clamp01(sqrt(originalDistanceSquared)/radius)，否则1。方向则从下移后爆心指向重新查询的作用点，不是仅将原点方向加一个向上分量。后续有近零方向的COM/默认向上回退，再进入0x78accc的作用点施力及力矩分发。这些分发的物理后端、ForceMode和惯性细节尚未完全闭合，不能把有限距离核对推广为全部受力等价。

新增runtime/explosion-geometry.ts实现已核实的两次查询/独立衰减，查询回调由未来物理适配提供。先保存第一次distanceSquared，允许查询实现复用临时返回对象；保持float32半径、上下修正及关键运算。2测试通过(264ms)：曲面上向上修正需要改变作用点而衰减保持原距离、零修正仅一次查询、范围外零衰减、零半径全量。构建通过(3.71s)。该模块尚未接main/Simulation，地雷仍没有完整爆炸推力，不宣称本轮恢复实际弹飞。

证据native-explosion-icall.json、unity-explosion-audit.log、unity-explosion-source（5段10文件及独立manifest）、explosion-geometry-tests.log、build-explosion-geometry.log；IL2CPP证据扩展至110文件SHA通过。引擎静态注册已核实，运行icall未执行。下一步继续closest-point backend/ForceMode惯性映射与单物理步积分，然后接真实地雷main/worker、粒子和MuMu对照。完整局内机制、输入手感、小游戏真机性能与完整目标保持active。


## 2026-09-09 爆炸世界包围盒转换与后端分发证据

上一轮仅回答跨关落点核验状态，分类为no progress；本轮重新读取当前代码及原libunity机器码，继续爆炸物理链路，没有把状态说明当作实现进展。

补录此前已落盘的只读运行证据native-unity-physics-dispatch.json：PID17413捕获分发器0x8f2624及首32字节，操作16/17/40分别指向0x8f358c、0x8f35d0、0x8f3d94。本轮audit-unity-explosion.py重跑并核对该已存证据与本地ELF，不称为本轮重新运行MuMu。force/torque处理器将Unity模式5映射到后端3，分别调用actor虚槽0x178/0x180。最近点处理器合成actor/shape姿态并遍历shape，调用geometry bounds bridge，按世界轴对齐包围盒逐轴夹取查询点，严格更小距离才替换首选；内部点直接返回查询点，无shape才返回世界质心。此前通用曲面查询的测试只验证callback契约，不能作为此版本使用精确球面/网格最近点的证据。

本轮新增归档geometry-world-bounds 0x13e2b8c..0x13e35cc（含ret之后仍有分支抵达的尾块），并断言跳表0x25b6e8的9个目标。bridge传contactOffset=0、inflation=1。球分支0x13e2c04直接中心±半径；胶囊0x13e2d10按轴方向绝对值乘半线段长度再加半径；盒0x13e2e94用旋转矩阵各列绝对值加权半尺寸；网格普通路径读取烘焙几何局部中心/半尺寸，再做矩阵中心变换和绝对值半尺寸变换，不能用旋转后所有三角形的紧包围盒代替。网格烘焙数据的取得、缩放分支和Rapier convexHull结果差异尚未闭合。

新增runtime/explosion-world-bounds.ts，输入已缩放几何及已经合成的世界shape姿态，输出float32世界min/max；球、Y轴胶囊、盒和显式提供烘焙局部包围盒的网格四种规格。胶囊采用当前ShapeSpec/Rapier的Y轴约定，源PhysX为X轴，接入时不能重复轴变换。网格接口明确要求烘焙碰撞几何数据，不自动采用渲染网格边界。该模块与explosionBoundsQuery、explosionGeometry组合测试；未接入Simulation，未扫描逐帧顶点，暂无运行期成本/视觉变化可报告。

专项7项通过（359ms）：旋转细长盒外部但世界AABB内部的查询仍为零距离/全衰减系数，球姿态无关，胶囊转轴及退化球，偏心网格中心变换，复合shape最小距离/同距首选/无shape质心回退，以及向上修正保留原爆心衰减。npm run build通过（具体日志build-explosion-world-bounds.log），没有重跑无关全套。证据explosion-world-bounds-tests.log、unity-explosion-audit.log；引擎证据现22文件及manifest，脚本逐文件SHA校验通过，IL2CPP110文件未在本轮改动。

接续：取得真实body/shape世界姿态和烘焙mesh bounds，闭合近零作用方向/质心回退，然后按源OverlapSphere去重刚体、800/半径size*10/upwards4/Acceleration单物理步积分接入main和Worker，再恢复粒子、隐藏与重置生命周期。实际地雷爆炸仍未完成；跨关MuMu同操作轨迹、全部局内机制、完整UI/手感及微信/抖音实机性能仍待验证，完整目标active。


## 2026-09-09 爆炸近零方向与质心回退闭合

上一轮为progress（世界包围盒转换及7专项验证）。本轮重新读取AddExplosionForce与force-at-point原机器码，确认0x7907ac比较初始方向长度和float32(1e-6)，大于时归一化；否则调用0x78efdc取worldCenterOfMass，再减去向下修正后的爆心。0x790808只比较此回退向量长度与间接常量，0x79080c直接跳到共同缩放，不经过除法，因此此分支必须保留质心位移的长度。只有回退长度不大于阈值才采用(0,1,0)。共同缩放依次为float32(attenuation*power)再逐分量相乘；施力点仍为第二次包围盒查询结果，不随方向回退而替换成质心。

初次pidof误用com.pronetis.ironball无结果；随后只读ps确认实际包com.pronetis.ironball2、PID17413。新增native-levels explosion-epsilon只读模式，使用O_RDONLY读取libunity GOT槽0x1595a00；返回相对地址0x203900、bits0x3727c5ac、value9.9999997473787516e-06。NDK编译/推送读取器/执行成功，未调用Unity icall、未触发爆炸、未改存档或购买。audit-unity-explosion.py核对运行值与本地ELF的bit级一致，并将原worldCenterOfMass函数0x78efdc..0x78f150归档；该方法使用actor world pose和COM local pose转换，支持上述质心语义。引擎manifest现24文件SHA通过，证据native-explosion-epsilon.json及unity-explosion-audit.log。

新增runtime/explosion-force.ts，复用explosionGeometry并严格区分两个阈值，计算交给AddForceAtPosition的向量及原作用点。保持float32距离/归一化/缩放顺序，COM回退不归一化。模块尚未接Simulation，未声称已向刚体提交线性/角加速度。测试包括正常3-4-5方向、包围盒内部COM两单位产生1600向量、向上修正后COM位移、1e-6/1e-5精确阈值及刚超过阈值、范围外零力；联合此前包围盒/几何测试共11项通过（376ms），构建通过3.59s。首次有一处length表达式括号语法错误，修为分段计算后重新验证，保留初次日志，不以失败轮作为通过证据。最终日志explosion-force-final-tests.log、build-explosion-force-final.log。

接续按既定计划取得真实shape世界姿态、烘焙mesh bounds和OverlapSphere刚体去重，处理force/torque的单物理步提交与清理，再将地雷实际触发/隐藏/粒子/reset接入main和Worker并做MuMu同操作对照。当前修改仍是计算模块，不产生局内新增爆炸效果；完整剩余机关、跨关逐帧、UI/手感、资源加载/Worker成本及微信/抖音真机验收继续待办，完整目标active。


## 2026-09-09 Acceleration作用点主线程/Worker单步积分

上一轮为progress（方向回退常量及计算）。本轮重新核对Simulation固定步和原force-at-point机器码，并查询PhysX官方PxRigidBody接口文档。源后端将Unity模式5映射后端3，线性向量与(point-worldCOM)×vector分别送给force/torque；Acceleration直接修改线性/角加速度累积，不再次乘逆质量或逆惯量。接口依据：https://nvidia-omniverse.github.io/PhysX/physx/5.1.3/_build/physx/latest/class_px_rigid_body.html ，addForce/addTorque段。此文档解释接口模式，不据此宣称本地二进制就是PhysX5.1.3。

Simulation新增queueAccelerationAtPoint，按当前世界质心计算float32力臂叉积，按刚体累加线性/角加速度并唤醒。对缺失、非dynamic、disabled或零向量不提交；非有限参数报错。integrateAccelerations在实际world.step前给当前线速度/角速度增加a*dt，随后清空，避免Rapier持续addForce状态造成跨步重复。现有驱动/制动命令先完成，再提交累积；零步与menu不消耗，player reset清掉player累积而保留其他刚体累积，retire清目标、dispose清全部；提交时再检查刚体仍有效且dynamic/enabled。Physics及Worker增加generation保护的accelerationAtPoint命令，共用同一实现，没有逐帧增加广播或新增场景绘制。

新增真实Rapier测试，主线程/Worker均使用不同质量(1/10)及尺寸的两个偏移质心盒，同一物理步各提交两次30加速度，单步质心移动1/60、角速度对应1rad/s；姿态一致，后续步不重复加速。零步/menu保留等待，连续两步与一次batch2逐位一致；player reset取消未消费施力，retire不访问释放刚体。初次中心盒6项通过，扩展偏心盒时测试把body origin位移当成COM位移，2项失败；修正为用姿态转换局部COM再断言，未更改物理代码或放宽阈值。最终含方向计算和AutoBrake回归共9项通过（8.5s），构建通过3.66s，日志explosion-integration-verified-tests.log、build-explosion-integration-final.log；失败日志保留。

这是已接入真实模拟器和Worker的作用点Acceleration提交能力，尚未由地雷事件调用。当前验证是零重力/零阻尼隔离场景，不能证明PhysX/Rapier阻尼、碰撞、CCD、最大角速度与锁轴排序逐帧一致。后续需将源爆炸几何查询、真实shape姿态/烘焙mesh bounds、OverlapSphere去重和地雷触发串接，恢复隐藏/粒子/reset，并在MuMu含地雷关以同操作核验。原版粒子、全部其余机关、UI/手感/跨关和微信/抖音真机性能仍待验收，完整目标active。


## 2026-09-09 爆炸范围查询、几何与施力串接

上一轮为progress（Acceleration主线程/Worker固定步）。本轮在Simulation增加explode(position,radius,upwards,power,includeSensors)，通过实际world.intersectionsWithShape球查询收集dynamic且enabled的attached body，以handle去重。随后遍历每个目标当前enabled碰撞体，用实际世界位置/旋转构造AABB，调用既有explosionBoundsQuery→explosionForce→queueBodyAcceleration，下一物理步消费。源查询触发器策略作为显式参数传入，候选查询排除sensor不等于最近点阶段移除该刚体的所有sensor。public/assets/catalog.json实读PhysicsManager.m_QueriesHitTriggers=true，后续地雷接入应读取该值。主线程和Worker新增带generation的explosion命令；无新增逐帧通信。

球/盒/胶囊尺寸从实时collider读取，保留机关改变尺寸后的值；TriMesh/ConvexPolyhedron从Rapier实际烘焙后的collider.vertices读取局部min/max，缓存中心及半尺寸。首次对相应目标爆炸时才遍历顶点，后续只变换缓存；body retire删除对应handle缓存，dispose清全部。当前网格形状不在运行期改写；将来增加mesh顶点替换必须同步失效缓存。未支持的新形状明确报错，不静默套球/盒。烘焙数据来自实际碰撞几何，未使用渲染网格，但Rapier与源PhysX的烘焙边界仍需源数据核验，不能据此称二者完全相同。

真实main/worker分别测试单球shape、同刚体三个重叠球shape、纯sensor排除/包含、convex mesh、disabled collider。复合形状与单形状逐位相同，未多次施力；半径10/power60/目标中心x5/radius1下第一步x=5.0100002289、第二步x=5.0200004578。sensor开关和禁用符合断言，mesh产出有限位姿且向外移动，main cache从1随retire降0。六组的first/second全部位姿在主线程与Worker间逐项完全相等；这是这些隔离用例的证明，不推广到所有接触轨迹。联合上一轮积分专项共4项通过（9.0s），最终构建通过4.02s。证据explosion-query-tests.log、explosion-query-results.json、build-explosion-query-final.log；没有重跑无关全套。

本轮完成真实物理查询到既有施力队列的串接；尚未把ExplosiveMine触发器和隐藏/粒子/reset接进该接口。后续首先解析GetExplosionPosition具体源引用、触发后Collider启用状态及粒子资源，接真实地雷模板和关卡的main/worker回归，再与MuMu原版同操作比较；OverlapSphere接触边缘、cooking差异和固定步排序仍保留验收项。完整剩余机制、跨关/手感/UI、微信/抖音真机drawcall/内存/加载与Worker评估未完成，完整目标active。


## 2026-09-09 真实地雷触发、隐藏与爆炸施力接入

上一轮为progress（范围查询/去重串接）。本轮核对ExplosiveMine.GetExplosionPosition(0x230ff28)：读取+0x38 container，经GameObject transform取得世界position，与Explode读取同一container并SetActive(false)一致。GetExplosionPosition机器码/反汇编新增入level-handoff-source，112文件SHA校验通过。现有44地雷资源逐包SHA核对，triggerCollider均在container子层级，无Rigidbody/MovingPlatform/Hammer/Propeller/BalancePlatform/GameObjectRotator/ObjectSpawner/ProjectileSpawner/SpawnerExplosiveMine等已知运动祖先。复现脚本audit-mine-trigger.py，证据mine-trigger-inventory.json/.log。仅证明已查组件类型/序列化资源，未知脚本或动态生成路径仍需另验。

LevelScene解析container、explosiveTrigger.triggerCollider与所有container子层级碰撞ID，physicsScene输出MineSpec（世界container爆心、size*10、作用域triggerTag、子层级colliderIds）及源QueriesHitTriggers配置。Simulation在球进入正确trigger时单次标记exploded，关闭container范围内碰撞、保留根警戒区，调用源参数800/upwards4/Acceleration流程。施力累计在随后实际物理步消费；batch中同样逐步处理。PhysicsState新增持久explodedMines，LevelScene按该状态隐藏container并停止MineAnimation；不依赖易重复消费的一次性视觉事件。球reset保留地雷已炸状态，完整level初始化恢复；resetMineVisuals恢复可见/动画，retire清理对应地雷。未实现粒子、振动和通知标签。

真实模板main/worker进入container爆心均在触发步velocityY=0，下一步velocityY=13.2890377045（含现有球阻尼），模型隐藏、状态仅一个ID；退出/重入不再次受力，完整重新init后可再次触发且速度一致。警戒测试改为x偏移radius+.2，仅在警戒区内、爆炸区外，避免原测试直接传送爆心后仍期望警戒动画继续的错误。联合警戒/44尺寸共6项通过（8.8s），最终build通过3.60s。证据mine-trigger-tests.log、mine-trigger-results.json、build-mine-trigger-final.log。未用隔离场景结果代替原版物理/视觉验收，首帧/CCD/碰撞顺序仍需MuMu同操作验证。

额外只读重新pidof确认17413，尝试读取debug_ResetAfterExplode。该类型槽使用既有双间接klass工具时名称校验失败，改直读仍失败（exit83），未取得有效开关值；native-mine-debug.json明确resolved=false。没有调用类型初始化/Unity方法或修改存档。读取器新增mine-debug诊断并最终NDK编译通过，不能把未知开关记作false。当前没有自动2秒复生，源仅在debug开关为true时走该分支，仍需可用类型句柄/实际地雷场景核验。

后续优先恢复ResourceHandler.GetParticleExplosion和ParticleExplosion缩放/播放/回收，以及通知/振动和debug开关；在真实含地雷片段对比触发位置、粒子、后续受力与死亡/重开。SpawnerExplosiveMine未被本次地雷实现覆盖。全局内机制、UI/手感、跨关及微信/抖音真机drawcall/内存/加载与Worker成本仍未验收，完整目标active。


## 2026-09-09 原版爆炸粒子资源、缩放及销毁链路

上一轮为progress（地雷真实触发/施力）。本轮恢复ParticleExplosion.SetScale(0x2257980)、OnEnable(0x2257a7c)、CFX_AutoDestructShuriken.OnEnable(0x2256fd8)及CheckIfAlive.MoveNext(0x22570b8)，并归档既有ResourceHandler.GetParticleExplosion。原生清单新增10文件至122文件，全部SHA通过。ResourceHandler有资源加载/对象创建调用，其末尾泛型方法尚未逐一闭合，不据名称宣称使用对象池。

SetScale首次从particleSystems[0].main缓存startSizeMultiplier/startLifetimeMultiplier，然后对每个系统写相同的缓存值*value；没有写transform.scale或startSpeed。StateGameBase传radius/5，地雷size1/1.5/2对应参数2/3/4。OnEnable先遍历全部Stop/Clear，再遍历Play。原prefab首系统的序列化startSize为TwoConstants(.5,1)，startLifetime为TwoConstants(.2,.35)；getter/setter如何映射MinMaxCurve上下界、首轮OnEnable与SetScale的发射先后仍未核验，不能将所有系统原各自size/life直接乘scale冒充该共享基准行为。

销毁协程先等待WaitForSeconds(.5)，之后调用ParticleSystem.IsAlive(withChildren=true)；仍活继续每.5秒检查，结束根据OnlyDeactivate选择SetActive(false)或Destroy。当前root与White Lines均OnlyDeactivate=0，因此资源行为为销毁其GameObject，不能把“无粒子后立即每帧回池”当原版时序。WaitForSeconds受timeScale影响；精确调度与子对象先销毁/根结束链需接入后验证。

新增audit-explosion-particles.py逐引用核对完整4系统/3材质/3纹理，并对pack与实际纹理文件保存SHA。四系统为ParticleExplosionPrefab(50容量、stretched)、Smoke(100、billboard)、SmokeXZ(110、billboard)、White Lines(60、stretched)，作者容量总320，不等于实际同时粒子数；纹理文件合计3278bytes，不等于GPU内存。完整source module/renderer/config保存在explosion-particle-inventory.json，日志同名.log。主闪光与白线分别在.05秒burst40/50，烟雾为连续短时发射；源Four emitter并不自动等于当前实测4 drawcall。

对现有SourceParticles审查：纹理图集、球发射、旋转/尺寸/颜色与stretch已有部分实现；ForceModule未处理，sourceMode spawn分支未应用VelocityModule，SmokeXZ需要两者。ClampVelocityModule虽enabled，但dampen/drag为0、三轴limit500，仍应核对语义后再判是否可忽略；Unity RNG/每轴随机/透明混合仍有差异。下一步先核验MinMaxCurve multiplier setter，补烟雾受力/速度模块，再接持久地雷状态的一次性四系统播放、源半秒销毁时钟与资源回收；保持共享材质/贴图的所有权。

本轮完成原版代码与本地资源证据，没有修改游戏运行代码，未重复运行无关游戏测试或构建。当前局内依旧有地雷施力与隐藏，尚无新增爆炸粒子。通知/振动、debug复生读取、MuMu同操作粒子/物理对照、全部其余机关、跨关/UI/手感及微信/抖音实机drawcall/内存/加载与Worker评估仍未完成，完整目标active。


## 2026-09-09 爆炸烟雾Force/Velocity运行模块

上一轮为progress（粒子资源/源生命周期归档）。本轮重新读取SourceParticles和实际SmokeXZ配置，确认sourceMode未处理Force/Velocity。参照Unity6官方模块定义：Force随生命周期加速粒子，Space控制本地/世界方向，Randomize在Two Constants/Curves下逐帧重选；Velocity模块控制生命周期速度。来源：[Force module](https://docs.unity3d.com/6000.0/Documentation/Manual/PartSysForceOverLifeModule.html)、[Velocity module](https://docs.unity3d.com/6000.0/Documentation/Manual/PartSysVelOverLifeModule.html)。这些接口说明不证明本地Unity的具体随机发生器或积分浮点顺序。

SourceParticles的sourceMode粒子增加motion状态，仅启用Force/Velocity时分配每粒子各轴固定随机样本及复用effective Vector3。每次update以归一化年龄取Force.xyz，转换镜像X及本地/世界空间后按aliveDt积分到基础速度；randomizePerFrame仅aliveDt>0时刷新。Velocity.xyz作为当帧附加速度，与基础速度相加后应用speedModifier，用于位移及stretched粒子的方向buffer，不写回基础速度，避免每帧累积速度模块。重力仍在基础速度积分链。复用发射器moduleVector临时对象，未增加逐粒子每帧Vector3分配；新增随机数组/状态为出生时分配，尚未进行平台内存/CPU实测。无Force/Velocity的既有粒子不增加motion状态。

新增particle-motion测试用真实SmokeXZ材质/配置副本，将发射/寿命/重力及运动曲线设为可解析常数以隔离语义；不是未改配置的原版视觉验收。World ForceY=2、VelocityX=3时两帧.1秒基础Vy=.2/.4、最终x=-.6/y=.06，速度模块未重复累加；发射器Z转90度的local模式得到相应旋转轨迹。update0保持位置/速度/随机seed，effective速度写入拉伸方向。与既有宝箱爆发/粒子/实际GPU pivot及blend回归共4项通过（9.1s），构建通过3.66s。证据particle-motion-tests.log、particle-motion-results.json、build-particle-motion.log。资源审计脚本重跑，remaining更新为XYZ已实现但原版随机/积分尚未验收。

限制：这里只实现实际爆炸所需的线性XYZ速度/力，orbital/radial未实现；ClampVelocity仍待核对（当前SmokeXZ零dampen/drag），本地空间随发射器旋转的逐帧细节、各模块随机相关性、Unity积分与渲染差异需MuMu实测。尚未闭合MinMaxCurve multiplier setter与首轮发射顺序，四系统爆炸播放和源.5秒销毁尚未接入地雷；因此局内没有新增爆炸粒子。后续优先完成倍率/播放/回收接入及原版对照，所有局内机制、跨关/UI/手感和微信/抖音真机性能验收继续待办，完整目标active。


## 2026-09-09 爆炸粒子倍率setter原引擎闭合

上一轮为progress（Force/Velocity运行模块）。本轮扫描本地libunity实际icall字符串和ADRP/ADD注册，定位四个MainModule入口：get_startLifetimeMultiplier注册0x5719a8→0x56e994，set注册0x5719bc→0x56ea20；get_startSizeMultiplier注册0x5719f8→0x56ed14，set注册0x571a0c→0x56eda0。没有调用运行icall。audit-particle-multipliers.py按PT_LOAD读取并断言四组注册指令，保存4段注册/4个getter-setter/2个辅助函数，共20个bin及反汇编文件SHA，独立particle-multiplier-source manifest保存原libunity SHA。

getter读取main数据+0x1c(lifetime)/+0x9c(size)的scalar。setter只写入对应scalar，调用curve-cache 0xf1c134：Constant(0)/TwoConstants(3)直接返回，不缩放minScalar。size helper0x5729a0分别将scalar/minScalar夹在0..100000；lifetime setter分别将两者限制为不小于0.0001（原ro地址0x1a6448=9.9999997473787516e-05）。size上界ro0x1a63e8=100000。Curve/TwoCurves另有缓存行为，本轮实现不覆盖，不能将结论不加条件推广到全部MinMaxCurve模式。

新增game/explosion-particle-config.ts：深拷贝source prefab，按ParticleExplosion.particleSystems引用顺序取首系统scalar作为size/life共享基准，float32(radius/5)及float32乘积写入全部4系统；保留各自minScalar并执行原范围限制。没有改发射速度/数量、变换或资产缓存原件，重复准备从原件起算不会累乘；非有限/负半径及非Constant/TwoConstants曲线显式报错。当前真实资源仅使用0/3模式。

2项真实prefab专项通过（350ms），覆盖size1/1.5/2对应radius10/15/20、四系统共享scalar、自身minScalar、速度/发射/transform不变、原件不变、零半径/size上限/非法参数与曲线模式拒绝。构建通过3.64s。证据explosion-particle-config-tests.log、build-explosion-particle-config.log、particle-multiplier-audit.log及独立20文件清单；已有122 IL2CPP证据未修改。资源inventory重跑并更新setter已验证（限当前模式）的状态。

这是源倍率准备模块，尚未把四系统创建、OnEnable Stop/Clear/Play、源半秒IsAlive销毁接进地雷。原生OnEnable在SetScale前调用与首次实际发射的排序仍需核验；下一步按原配置准备效果实例并实测生命周期，再与MuMu录像比较外观/时序。通知/振动、debug复生、所有剩余局内机制、跨关/UI/手感与微信/抖音真机性能、资源加载/Worker成本仍未验收，完整目标active。


## 2026-09-09 地雷四系统播放、Alpha8 shader与回收

上一轮为progress（原倍率setter配置）。新增ExplosionParticles，使用源4节点层级、坐标/旋转及倍率配置创建SourceParticles；爆心覆盖prefab根节点预设位置（原root y=2不应叠加），不随被隐藏的地雷container消失。LevelScene依据持久explodedMines每地雷只创建一次，异步创建期间reset/retire设置cancelled，创建完成后销毁；失败记录warnings。已完成实例每帧更新，完成后释放引用，只保留轻量去重标记，reset/退场清标记。共享Assets纹理不由effect.dispose释放。

ExplosionParticles以缩放后的source lifetime/发射配置运行，每.5秒检查粒子、计划burst及未来rate发射是否结束，子White Lines先检查销毁，全部结束释放根及四系统自身geometry/material。SourceParticles增加simulateWhenCulled，仅爆炸启用；远处不绘制但继续年龄/发射/结束，避免旧clear重置sourceTime令rate发射系统永远活着。此生命周期实现的IsAlive定义/检查帧与Unity内部仍需实测：首轮Play在本实现已准备倍率后执行，原OnEnable先于SetScale，实际首发射时序不能宣称逐帧对齐。

初轮4 calls/粒子数量测试虽然通过，实际截图为空；补readPixels可见像素断言后失败，未把drawcall当成可见效果。诊断发现3张原贴图为Alpha8（RGB黑），材料shader为Cartoon FX/Particles Additive Alpha8。通过cocosgame既有export_shader_programs.py从3.40 data.unity3d导出2个GLES变体，原fragment仅取texture.a×vertex.a，RGB直接取vertex.rgb。解析pass状态确认RGB/alpha均SrcAlpha(5)/One(1)。SourceParticles增加专用shader模式3并按源输出/混合恢复，现有Mobile/Legacy测试保留。复现audit-explosion-shader.py核对导出SHA与原pass，证据explosion-shader-source及explosion-shader-audit.log；未使用AI生成贴图替换原资产。

最终播放/GPU/真实地雷main-worker及旧shader回归4项通过（9.3s），构建通过5.17s。实际地雷测试等待异步效果挂载，验证重复快照相同对象、reset后effect.disposed；单独播放验证4系统全部有粒子、4 drawcall、像素非纯背景、暂停保持年龄、远离camera继续结束、4次geometry释放且纹理释放0。截图explosion-playback.png已打开检查，闪光/烟雾可见；这是隔离相机下的浏览器证据，不是MuMu外观验收。日志explosion-playback-verified-tests.log、build-explosion-playback-complete.log及results.json。此前build因测试参数隐式any失败，补类型后构建通过；空图诊断和失败日志均保留。

剩余：与MuMu原版同操作核验爆炸尺寸/色彩/随机/时序、OnEnable/SetScale首发射顺序和IsAlive返回时机；异步首次资源加载延迟仍需测量及必要预热。通知/振动/debug复生未完成，SpawnerExplosiveMine及其它全部机制、UI/手感/跨关、微信/抖音真机drawcall/内存/加载与Worker评估仍待验收，完整目标active。


## 2026-09-09 重复爆炸资源计数、取消门禁与模板缓存

上一轮为progress（可见四系统播放/回收）。本轮检查异步创建过程：原先只在四系统全部建完后处理cancelled，切关/重置时仍会继续等待并创建剩余系统。ExplosionParticles.create现接受取消谓词，在开始、source加载完成、每系统创建前/后检查；取消后立即dispose已建实例并结束，不继续其余纹理/系统请求。LevelScene传入自身pending.cancelled；已发出的共享图片请求不强制中断，避免影响其它消费者。测试用可控首texture等待点验证取消后仅1次texture调用、返回disposed且root空。

新增explosion-resources.spec.ts，独立128x128 headless WebGL场景连续12次创建/播放/结束/销毁实际四系统，附带主线程/Worker真实地雷回归。每轮active为4 geometries、3 textures、4calls、1program；结束并render后为0 geometries、0calls、0program，3共享纹理继续缓存；assets.releaseUnused(emptyScene)后GPUtextures和textureCache都0。此证据是资源数量稳态，不是进程/JS堆/GPU字节无泄漏证明。第一次测试3项通过7.9s/build6.39s，原始12轮数据explosion-resources-results.json。

首轮计时暴露每次ExplosionParticles.create通过Assets.prefab重新fetch/parse同一JSON：首次29.3ms，后11次创建中位61.3ms、最大111.9ms。改为ExplosionParticles内部WeakMap按Assets实例和catalog对象缓存单份原prefab Promise；相同catalog复用，并发共享请求；catalog更换重新取源，失败清相应条目以便重试。每次爆炸依旧clone配置并创建独立geometry/material，结束仍释放。仅源JSON保留于Assets存活期间，不缓存全部关卡、不保留运行effect或GPU对象。Assets.clear后新实例重新add该源依赖；GPU纹理仍按现有生命周期重新获取。

缓存验证12轮bytesLoaded固定在首轮数值，证明不重复fetch/计入相同源JSON；全部资源/取消断言仍通过。本次首次11.7ms，暖创建中位0.7ms、最大1.5ms，模拟完整特效生命期间的update循环总耗时中位1.55ms（非每帧/非GPU时间）。前后测试是不同页面会话，环境/缓存/驱动可变，不以数字宣布跨设备固定倍数提速。最终3项通过7.5s，构建通过6.02s；证据explosion-resources-cached-tests.log、explosion-resources-cached-results.json、build-explosion-resources-cached.log。未重跑无关全套。

后续继续MuMu爆炸视觉/首次发射/IsAlive时序，以及其它全局内机制和通知/振动/debug复生；首次texture加载/GPU编译仍需实际赛道测量和必要预热。微信/抖音真机drawcall/内存/加载、Worker总成本、完整UI/手感/跨关均未验收，完整目标active。


## 2026-09-09 MuMu 采样时序修复与存档收尾

上一轮仅说明跨关落点验证状态，分类为no progress。本轮检查真实存档仍为62，拉取已有30.007644秒录像并抽帧，确认前约26秒仍在主页，未录到此前工具间隔里的完整操作；不将它当作地雷证据。先恢复73并核验，再以新备份跳62进行连续采样，最终再次恢复73；operation.json、截图及读回摘要均归档。两次恢复仅进度字段，购买/库存未由存档工具回写；最后lives=2、selectedSphere=29，画面LEVEL73/VIP/皇冠球已查看。

新增scripts/mumu-record-input.py，显式JSON计划→独立screenrecord PID→一秒预留→host monotonic连续输入→只停止本次录制→录像/截图/SHA/命令时间清单。实际62计划在0/2/4秒滑动、7秒暂停，最大开始迟延10.04ms，录制退出0、Python语法检查通过。0.5秒抽帧确认启动、弯道掉落、复活及暂停，没有观察地雷爆炸；这条路线不具备特效比较资格。下一步应基于弯道画面调整路线，先确认触发爆炸，再对照警戒、粒子、球运动和寿命；不能用继续跑独立浏览器测试替代源行为核验。

工具时钟只是主机命令边界，并非Android事件或视频帧时间；未完成浏览器同事件序列回放，未在录制负载下做性能结论。旧原视频移到cocosgame logs/v3.40/native-input-capture-20260909，新采样同处归档，客户端 evidence/mumu-mine-sampling-review.json指向来源。native-mine-debug-level62.json仍为class验证失败(exit83)，debug_ResetAfterExplode未知，不推断false。完整流程文档MUMU_INPUT_CAPTURE.md新增，进度/移植清单/局内计划/架构/物理记录已同步；跨关MuMu轨迹、全部局内机制和小游戏真机验收继续待办。


## 2026-09-09 第134关路线诊断与未解析元数据修正

上一轮为progress（连续采样工具、62录像和73恢复）。本轮检查44个地雷所在11个包，选134_v01_Start_0：地雷局部位置(-4.695691,0.5,63.657936)，位于箱堆前；MuMu主页LEVEL134与该布局交叉核对。首次从主页连续输入在弯道外侧掉落；第二次从复活后的暂停继续，起始状态/运动时序不同，预设转向更晚，仍未接触地雷，后续输入在再次复活后继续生效并出现NO BALLS。两次录像及0.5秒抽帧已查看，不能声称警戒/爆炸/粒子经过验证。后续应先控制起始状态并分段校准转向，再安排长序列；不要把主页和复活后的计划只平移时间视为等价。

采样结束按原备份20260909-065703-315314-jump-134恢复73，操作报告20260909-070041-276919-restore读回验证通过；inspect=73/lives2/sphere29，未改购买/库存。局内NO BALLS与存档lives2是两个观测，不推断生命没有消耗。视频/计划/时间戳/截图保留evidence/mumu-134-mine-route和route2，cocosgame logs/v3.40/native-input-capture-134-20260909镜像归档。

重新核对Explode原指令：slot0x4b838d0加载usage指针，随后[x20]才是已解析后的Il2CppClass，+0xb8是static_fields。旧读取器尝试直接/二次类名验证，却未区分未解析usage，产生笼统class validation failed。本轮按源两次读取，先检查编码低位，未解析时只报告原值与方法初始化标志，不解引用为类。NDK编译通过；恢复后的MuMu PID12896只读得到encodedUsage=0x2000a353、Explode初始化字节(0x4ec50e0)=0，exit83明确保持未解析，不是成功读取布尔值。

静态ELF的slot RELATIVE重定位目标0x4caa1b0，读取8字节同为0x2000a353；SHA d0f291dd012bce8083478296f19ed32c6bfe43ce446791f900a33ac869885147。证据native-mine-debug-usage.json、mine-metadata-usage-static.json；读不到静态字段不等于debug_ResetAfterExplode=false。本轮未向原版注入/调用爆炸、未修改内存；游戏代码未改，因此不重复构建浏览器或已有粒子专项。全部局内机制、原版爆炸与跨关轨迹和微信/抖音真机性能仍待验收。


## 2026-09-09 ObjectSpawner 固定步时序与资源清单

上一轮为progress（MuMu路线证据、未解析元数据诊断）。本轮回到尚未接入的生成器；src无ObjectSpawner/ProjectileSpawner运行实现。提取ObjectSpawner/SpawnerFallingObject/SpawnerExplosiveMine原生方法，68个bin/反汇编文件和SHA归档evidence/object-spawner-source，独立于既有跨关manifest。

ObjectSpawner.FixedUpdate(0x2334b08)仅active时执行。开始条件(time-startTime-delay)>=-fixedDeltaTime*0.5；首次激活lastIntervalTime=time-interval，nextDuration只取variation随机偏移。随后同一次FixedUpdate可Spawn；后续每次lastIntervalTime+=interval、nextDuration=interval+偏移。无while追赶，单步最多一次；variation<=0不调用Random.Range，正值Range(0,variation*2)-variation。OnLevelReset(0x23354cc)仅清active；OnLevelStart(0x23354d4)置active、清running并记录Time.time。

新增game/object-spawner-clock.ts，以源float32顺序计算，外部传入实际固定步时间和随机采样函数。2项专项覆盖半步等号、未开始/重置/再启动、时间跃迁不批量生成、首次与后续随机调用/间隔基准；300ms通过，npm run build通过。Unity随机序列、物体池、生成对象源生命周期与真实场景/Worker接入未完成，不能把单元测试当成原版行为或小游戏验收。

85个ObjectSpawner源包SHA重新核对，objectType=0共75、1共9、2共1。唯一地雷生成器在130_v01_Mid_1，delay0/interval4，详见object-spawner-schedule-inventory.json。SpawnerExplosiveMine.UpdateSize是根localScale=size*Vector3.one并设置proximityCollider.radius=size，和静态ExplosiveMine不能直接混用；Spawn先调用FallingObject.Spawn，再清exploded/proximity、更新尺寸并缓存scale。下一步沿SpawnerPool.GetObject、FallingObject.Spawn/裁剪面/物理激活和归还链路完成实际对象，不先给场景加无物理的定时视觉替代品。MuMu地雷/跨关轨迹与所有小游戏门禁继续待办。


## 2026-09-09 生成物出口运动与掉落边界

上一轮为progress（ObjectSpawner固定步时序）。本轮核对SpawnerFallingObject.Spawn(0x234642c)：调用基类Spawn，SetClipActive(true)，刚体kinematic=true，DOTween.To(0,1,spawnDuration).SetEase(2/InSine)，回调SetTransitionValue与OnSpawnFinish；缓存initialScale。SetTransitionValue(0x23477cc)对传入的已缓动值clamp01，再对世界spawnPosition/finalPosition做float32向量插值，并写刚体Transform.position。

OnSpawnFinish(0x2347848)先kinematic=false，调用Rigidbody.AddForce((final-start)/spawnDuration,2)，最后SetClipActive(false)；源ForceMode枚举2=VelocityChange，不能误作Force或直接替换已有速度。新增spawner-falling-motion.ts的插值/释放增量函数，输出对象由调用者复用，无每次向量分配。缓动调度、Transform与刚体同步时序、DOTween暂停/生命周期仍需接入和验证。

基类SpawnerObject.LateUpdate(0x2347500)在spawnY-currentY>fallDistance时Die，Die清alive、GameObject.SetActive(false)、SpawnerPool.ReleaseObject。子类LateUpdate先调用基类，仅仍alive时按距离>fallDistance*.666开始缩放，比例=(fallDistance-distance)/(fallDistance*.333)。ELF常量0xcf9c90=0.6660000085830688、0xcf9bf4=0.3330000042915344，已保存原4字节与ELF SHA，不改成2/3或1/3。恰好fallDistance时缩放0但尚不归还，超过才归还；开始收缩处可能略大于1，不额外clamp。

新模块只计算边界和比例，避免先归还后继续修改对象；未代替实际SpawnerPool或生命周期执行。四项含时序回归及世界插值/释放增量/边界测试313ms通过，npm run build通过。object-spawner-source增补SpawnerObject原生证据与fall-constants.json、重建SHA清单。下一步闭合CreateSpawningObject配置和池Get/Release，接实际场景与共用物理命令，再做MuMu/小游戏验证；当前不能声称生成物已在关卡中出现或全部机制完成。


## 2026-09-09 生成物池的分配与归还规则

上一轮为progress（出口运动和掉落边界）。本轮提取Gyro.SpawnerPool<T>构造、GetObject、ReleaseObject。泛型共享代码的method-map“下一个已知方法”边界会包含后续无名实例化代码；证据已按实际范围裁剪：构造0x2caf358..0x2caf418，GetObject0x2caf418..0x2caf5ec，ReleaseObject0x2caf5ec..0x2caf748，末尾为LogWarning尾调用。原完整提取文件仍在cocosgame sourceConfigs，局部证据新增pool-ranges.json和6个代码文件。

构造创建对象列表、占用布尔列表、保存工厂；Get从index0扫描首个false，标记true返回原对象，全部占用才调用工厂并追加true。Release遍历所有对象的Equals，匹配清false、不提前break；找不到时warning，重复释放已空闲项无额外错误。池不做Spawn/激活/清速度/重置姿态/销毁。新增game/spawner-pool.ts保持此顺序；Equals作为适配参数，默认JS对象身份，Unity已销毁对象的Equals语义未映射，实际接入需维持存活句柄约束。

测试覆盖逆序归还仍按创建顺序复用、10000轮3对象复用只调用factory3次、状态未由池重置、多个Equals匹配、重复释放、缺失对象和factory抛错不追加。联合时序/运动共6专项324ms通过，npm run build通过。这只证明纯模块的工厂调用与占用规则，不证明真实Three.js/Rapier资源或平台内存稳定；池按源无任意容量上限，完整退场需要场景所有者释放持有资源，不能把清标志当成GPU/刚体释放。

object-spawner-source清单98文件SHA归档，日志spawner-pool-tests.log/build-spawner-pool.log。模块尚未接入ObjectSpawner.CreateSpawningObject和真实场景，下一步先恢复初始化的起终点/时长/裁剪面/质量及模板引用，再把工厂、Spawn/Die、物理代际和旧关退场串接；保留MuMu同操作和小游戏性能验证。


## 2026-09-09 生成器模板与世界初始化数据

上一轮为progress（池分配与复用）。本轮读取ObjectSpawner.Init/SetSpawningObject/CreateSpawningObject/GetClipPlane的完整原指令。Init为每个生成器新建池；球/地雷分别LoadSpawnerBall/LoadSpawnerExplosiveMine并SetSpawningObject，尺寸取objectSize.z；箱使用已有spawningObject转SpawnerBox，写完整objectSize。并非三种都加载通用模板。

公共配置spawnDuration=(objectOffset+objectOffset)/spawningSpeed、fallDistance直接复制、spawnRotation复制objectRotation。spawnPosition=TransformPoint(Vector3.back*objectOffset)，finalPosition=TransformPoint(Vector3.forward*objectOffset)；Vector3静态字段+0x54/back、+0x48/forward由恢复类型字段核对。TransformPoint包含世界缩放，而duration不按缩放补偿；非均匀缩放下实际出口速度可能不同于spawningSpeed。GetClipPlane=(transform.forward,-dot(forward,worldPosition))，forward来自旋转，不应直接用含缩放矩阵列作法线。

新增object-spawner-setup.ts接受已转换客户端坐标的matrixWorld与旋转方向，返回世界点/时长/尺寸/裁剪面；尚未施加spawnRotation，它仍由后续模板/实例适配层负责。Three.js矩阵乘法采用JS双精度后收敛f32，与Unity逐指令TransformPoint没有位级验证，不能宣称精确数值一致。8联合专项（含池/运动/时序回归）通过，npm run build通过；新增非均匀缩放释放速度与旋转裁剪面断言，防止把局部时长错误改成世界距离/速度。

85个ObjectSpawner源SHA复核，所有spawningSpeed/objectOffset正值；9个box类型的spawningObject均解析为同包内SpawnerBox组件，其引用和数据保存spawner-template-references.json。Init先禁用模板并放到spawnPosition；CreateSpawningObject克隆模板、激活、命名、父级设生成器、SetLevel、虚Init(pool)、SetClipPlane。后续必须保留内嵌箱体依赖与每个生成器池所有权，不直接复用通用PushBox视觉或全局物理实例。

本轮计算模块未接LevelScene/Simulation，原生Init虚槽、各类质量/碰撞与裁剪shader、异步加载取消和跨关退场仍需完成；资源清单/架构/计划已同步，原版录像与小游戏真机验收保持待办。


## 2026-09-09 生成物世界裁剪与独立材质

上一轮为progress（初始化计算与模板引用核对）。本轮从原data.unity3d导出Legacy Shaders/Reflective/Diffuse_clip的30个GLES程序。程序12片元计算dot(_ClipPlane.xyz,worldPosition)+_ClipPlane.w*_Clip，严格<0时discard；_Clip并不乘整个平面表达式。SpawnerBall.SetClipActive(0x23465e4)把clipActive写入对象，shadowCastingMode=!state，启用写真实plane，关闭写零向量，同时Material.SetInt(_Clip,state)。仅关闭_Clip且保留xyz会留下错误裁剪。

新增runtime/spawner-clip.ts，为单Mesh克隆独立Phong材质并链式保留原onBeforeCompile（包括反射tint），固定program cache key后缀；uniform持有独立plane/clip。顶点从transformed经instanceMatrix/modelMatrix得到世界点，片元按源条件discard。setActive关闭清零并恢复castShadow，dispose恢复原材质/原投影标志并只释放自己的材质，不释放共享纹理。尚未支持批处理不同实例逐个平面；此适配是独立生成物材质，不应直接套到整批实例上。

实际WebGL像素专项用两个共享原材质、位于不同世界位置的面，设置相反独立裁剪面，验证四采样点显隐；关闭左侧后只有左侧恢复、右侧仍裁剪，投影标志true/false，释放恢复共享材质。1专项985ms通过，构建通过。该测试未模拟投影贴图视觉，只检验投影开关；也未证明原反射/光照全貌、骨骼或批处理路径完整对齐。

evidence/spawner-clip-source含30程序、原programs.json和Ball/Box/Mine的SetClipActive bin/反汇编，共37文件SHA校验。日志spawner-clip-tests.log/build-spawner-clip.log/spawner-clip-export.log。尚未从LevelScene的生成物工厂调用适配，实际生成/物理/生命周期与MuMu对照继续待办；不把GPU局部证明提升为机关或小游戏验收。


## 2026-09-09 生成物刚体初始化接入预编译

上一轮为progress（原shader裁剪适配）。本轮核对SpawnerObject.Init(0x234755c)：读取同节点Renderer/Rigidbody、保存池，linearDamping与angularDamping均.25，isKinematic=true。SpawnerBall.Init/SpawnerExplosiveMine.Init按size设置根scale，质量=Pow(size*.5,3)*(float)4/3*(float)PI*8，maxAngularVelocity20；SpawnerBox.Init根scale=one、质量=size.y*size.x*size.z*3、角速度上限20。原常量0xcf9a68=1.3333333730697632、0xcf9c5c=3.1415927410125732，原字节和ELF SHA写mass-constants.json。JS幂运算后f32不保证与平台powf所有输入位级相同，保留精确比较待办。

expandRuntime现在克隆节点后为三类生成物写入源Init状态，再交由现有LevelScene编译变换/碰撞/BodySpec；不改写原JSON，不把父级世界缩放乘入源质量。缺失同节点Rigidbody明确报错，不偷偷补默认刚体。仍只接Init，SpawnerExplosiveMine.UpdateSize在Spawn时的近距半径写入、完整Spawn/Die和生成器工厂尚未调用。

原Spawn链另外确认：基类复用时root scale=one，root与Rigidbody Transform位置为spawnPosition，localRotation=spawnRotation；仅当原刚体不是kinematic时清线/角速度，然后SetActive(true)。FallingObject随后设kinematic并启用裁剪，具体球/地雷再恢复尺寸并缓存initialScale。因此不能把复用一律清速度等同源规则，后续需结合Freeze/Unfreeze与Rapier模式切换处理。

测试实际球/地雷模板size2→root scale2、球体质量约33.5103、两阻尼.25、kinematic与角速度20；9个内嵌箱体模板均通过体积质量和unit scale核对。真实LevelScene加载SpawnerBall后，PhysicsScene得到上述参数及碰撞半径1，证明该部分已在预编译链路执行。联合44静态地雷回归共4项1.1秒通过，npm run build通过。没有声称物体已定时生成或MuMu/小游戏行为验收。

object-spawner-source补Ball/Box方法和质量常量，121文件SHA归档，日志spawner-body-init-tests.log/build-spawner-body-init.log。下一步生成器模板准备、源Spawn状态切换、共用物理动态对象注册/归还与场景裁剪串接；完整目标保持active。


## 2026-09-09 用户优先级：主界面/通关UI接入

已将HomeUI原图页签与源比例、FinishUI真实字体/图片/布局渲染接入main，替换字符图标和通用结算弹窗。普通关运行覆盖titleY=-420、rewardY=580已按MuMu录像与ARM64修正；修复drawcall只统计最后一次UI render的问题。主线程/Worker 1→2和5→6跨关及UI组合5项通过，resize与真实结束门UI另有专项，构建通过。

下一步优先执行 /Users/jiaojian/Documents/goingball/clientThreeJS/docs/MAIN_FINISH_UI.md：金币飞入与经济时机、普通自动结算→Pachinko衔接、三钥匙分支、VIP/主菜单细节、特殊关变体。当前CONTINUE为临时可用入口，DOM主菜单仍有子界面占位，不能称1:1完成。MuMu进度已恢复73，VIP/皇冠29保持；取样中正常消费3钥匙/取得比赛票及关内奖励，库存不是未变。目标仍active；生成器/破碎既有待办保留，勿覆盖用户UI优先级。


## 2026-09-09 运动学释放质量修复收尾

Simulation.addBody为dynamic与kinematic都初始化源质量；sensor显式质量0，避免警戒范围贡献重量。真实Rapier复现：size2生成球应33.5103，修复前释放为默认密度4.18879；只修非sensor时带radius2警戒sensor会变67.0206，最终一起修正。生成体初始化、带/不带sensor释放与冲量、地雷main/worker联合7项通过（5.7s），spawner-mass-verified-tests.log及build-spawner-mass-final.log构建通过。

另确认SpawnerFallingObject.Freeze(0x23478c4)/Unfreeze(0x23478c8)均ret，具体类型暂停不可臆造为基类缓存速度。OnLevelReset存活则Die。此修复没有完成生成器主程序工厂装配或MuMu生成物碰撞验收。当前用户优先级已转主界面/通关UI，完整生成器生命周期待办保留。


## 2026-09-09 结算缩放稳定性与飞币取证

上一轮实际主界面/通关窗口接入属于progress。本轮读取当前FinishUI后修复实际窗口持续resize追加字号的问题：每次重建准备独立1024×1024 R8字形页，UIWindowLayer成功替换旧网格后才交换并释放旧页；失败/过期请求释放候选页，保留旧窗口。不能先dispose旧atlas再异步等纹理，否则会破坏仍在显示的窗口。

连续20种高度450…659后回到初始视口：前后17glyph、1MiB CPU/纹理页、6个图片纹理/6引用、21图形→18提交、FreeType1face/allocated53488bytes/heap4MiB完全一致。证据finish-ui-resize-final-tests.log。这仅证明此窗口的字体页/引用有界，不是完整进程或小游戏显存实测。

首轮压力测试还复现“此文字需要换行或垂直截断”：ContentSizeFitter的advance/scale乘回scale存在double舍入误差。uiTextLine宽度比较加入2个相对double epsilon，仅吸收浮点计算误差，不放宽实际像素或取消换行检查。4项联合测试通过（16.2s）：真实主程序resize、结束门通关/继续、41条原版缓存544顶点逐项一致、未支持样式拒绝。

飞币已归档Gyro.CoinParticles全方法与两个协程，coin-particles-source/manifest.json含SHA。AffectParticle 0x23873c4：remainingLifetime < startLifetime*affectLifetime时开始吸附，首次保存位置与remaining，随后t=(savedRemaining-currentRemaining)/savedRemaining；t>=float(.95)直接1，再Clamp01线性插值到每次更新的target，velocity清零。前半程清空保存值。不是整段Bezier，也不是出生就向钱包匀速移动。GetWorldPos为Rect中心TransformPoint。addMoreParticles每帧最多Emit(1)，delay严格>.02且left>0时发射/清零，再累加unscaledDeltaTime。常量及ELFSHA已归档。

当前金币飞行尚未接入main：源粒子尺寸/速度为世界单位，Big为Shape17、Small为Shape4，需继续UI相机投影、发射重载与曲线时序后接真实单批粒子。未添加自选像素散射替代源行为。普通自动结算/钱包时机/Pachinko及主界面VIP动态仍是下一优先事项；完整目标active。


## 2026-09-09 通关飞币实际接入

前轮缩放/文字误判修复为progress。本轮FinishCoins接入FinishUI.update/render/hide：实际拾币后过结束门，普通结算出现时按当前0.2s触发发射，金币粒子与结算共用游戏WebGLRenderer，切关取消未完成请求并清空实例计数。200容量预分配，实际Big burst80+显式Emit1=81个，最高1个InstancedMesh提交；生命周期结束停止提交，纹理/缓冲按单一应用实例保留以复用。不会为每枚金币创建Mesh或DOM。

已用源CoinParticles.Show(float duration=1,affectLifetime=.5)、Big ParticleSystem、Particle Coin材质/texture1646：life随机1…2、size.04、speed.07、torus radius/donutRadius .01、radiusThickness .01、screen maxParticleSize .06。AffectParticle后半寿命首次保存位置/剩余寿命，t到.95跳1，线性飞向每帧更新的钱包中心并清velocity。UIMainCamera源数据FOV10，两份相机16271/16285同值，CanvasScreens planeDistance1；全Camera提取在coin-particles-source/cameras.json。

边界须保留：目前世界到屏幕使用上述FOV/plane映射，maxSize采用短边归一化；运行Canvas相机绑定/投影、UnityDonut的精确概率分布/发射顺序、Unity随机序列和材质混合数值仍需原版粒子缓存/同帧对照。当前torus采样是待校准实现，不能称1:1或源码逐粒子精确。普通结算时间线仍保留手动CONTINUE，触发点还未组合完整Mediator的附加interval和Pachinko，因此金币飞币已可见不等于自动结算/经济时机已完成；余额仍旧的终点提前入账。

首轮真实结束门逻辑测试通过但截图显示粒子被剔除，证明仅alive/提交计数不能证明视觉。原因是Y向下的正交屏幕投影和FrontSide；改为DoubleSide后看到了粒子。新增GPU readPixels检测实际非透明金币像素，再检测生命周期末尾画布无像素。该测试又发现透明DoubleSide默认2次提交，最终设置平面粒子forceSinglePass=true；不可拿stats声明的1替代真实renderer.info计数。失败日志finish-coins-tests/visible/final保留，最终以finish-coins-final-verified-tests.log为准。实际画面finish-coins-active.png，构建build-finish-coins-verified.log。没有根据测试中的瞬时FPS宣称性能达标。

下一步保持UI优先：校准飞币发射/投影/时间线与钱包动画，接普通自动结算→Pachinko完整交互及奖励事务，再补VIP/特殊关。其他机关、全关验证及微信抖音真机门禁均保留，目标active。


## 2026-09-09 通关钱包数字动画接入

WalletDisplay 已接入 main 与 FinishUI 飞币启动回调：显示值不再在结束门触发时直接跳到库存余额；飞币启动后经过3个更新帧、1秒延迟，再最多8步显示，每步间隔float32(.1)。源 CoinsDisplay.StartSetValueAnimated / MoveNext / callback 的 float32 运算和 ties-to-even 取整已对应实现。替换动画从当前显示值开始；切关 set 取消旧动画。源方法及 SHA 归档 evidence/wallet-display-source。

验证：wallet-display-tests.log 3项通过（7.3s），包括真实拾币过终点时飞币已出现但余额显示仍保持初值、动画后等于实际库存、跨关清理，以及取整/替换/取消；GPU readPixels 21608 个金币像素、实际1次提交、寿命结束无残留。

边界：仅修正显示动画，库存仍在结束门提前入账，完整经济事务和普通自动结算→Pachinko 尚未接通。协程与 DOTween 的同帧执行顺序、后台暂停、首次异步纹理加载相位、钱包 pulse/UI事件仍待原版对齐。不能把此改动称为完整通关还原。下一步继续普通结算流程、VIP动态和特殊关；其他局内机制与小游戏真机验证仍在清单，完整目标未完成。


## 2026-09-09 普通通关飞币延迟与基础金币入账

上一轮钱包显示接入为 progress。本轮继续实际 main 集成：结束门不再调用 inventory.addCoins；飞币启动时只把 inventory.coins + runCoins 作为钱包显示目标；临时 CONTINUE 到达 continueFinish 后才入账并切关。continueFinish 使用 loading/finishScreenShown 防止同一次结算重复领取，资源失败的继续按钮也走同一入口。直接调试跳关不会隐式领取未结算收益。

源证据：ShowFinishScreen 0x22183e8 的 ELF 0xcf9adc 为 float32(.2)；ScreenFinish_Continue 0x2219364 的0xcf9c28为float32(.3)，后续自动分支等待0xcf9a04为float32(1.2)。Continue 0x2217890 检查advanceOnFinish，默认false时0x22178b0才AddCoins(run reward)。方法/字节/常量/ELF SHA见 evidence/finish-credit-source/manifest.json。FinishUI 飞币触发由错误的单独.2秒改为.2+.3秒；目前合并为同一UI elapsed，尚未逐帧校准 DOVirtual 独立时钟与 DOTween sequence 时钟/调度相位。

真实主程序3项测试通过（14.9s，finish-credit-tests.log）：拾币后过终点，钱包动画已显示奖励但 inventory 尚未加币，继续后下一关 inventory 才等于预览目标；主界面与通关点击/缩放仍通过；飞币实际GPU单提交且寿命结束无残留。

必须保留的差异：原版普通通关隐藏按钮并自动进入 ScreenFinishOver/Pachinko，当前仍由临时 CONTINUE 触发，因此仅入账阶段归属被纠正，不能宣称整段入账墙钟时间或结算流程一致。advanceOnFinish=true、额外奖励、票券、小游戏收益/持久化、特殊关未接通。下一步接源自动时间线和Pachinko真实场景，随后移除临时按钮；不要用直接自动跳下一关冒充源Pachinko流程。完整目标保持active。


## 2026-09-09 Pachinko 实际入口与相机布局核验

上一轮基础金币入账修正为 progress。本轮为装配通关自动流程提取 MediatorPachinko.Init、UIPachinko.SetDetails/SetPachinkoTransition 全部ARM64方法，归档 evidence/pachinko-entry-source。新增可重跑 scripts/extract-pachinko-entry.py，运行通过，结果 evidence/pachinko-entry-layout.json。

关键发现：普通通关 Create(null machine) 创建 Resources/prefabs/_level/pachinkomachine（3049），不是直接使用8547裸板。UI来自 Resources/prefabs/ui（3068）的 UIPachinko 47478，215节点；独立UIPachinkoPiggy来自3820。Init先ResetSlotsLocation、把机器放到UI相机TransformPoint(forward*10)，并把机器localScale设零。SetDetails把PachinkoBehaviour重新挂到theCamera、保持world变换后记录起始局部TRS，再通过过渡恢复。因此不能简单保留零scale，也不能直接将全部机器放进当前游戏相机前。

独立Camera16289序列化FOV62、near .01、far30、depth3、cullingMask25174016，无RT、HDR/MSAA关闭。SetDetails目标局部位置(0,-2.9000000953674316,14)，常量ELF0xcadef0；目标旋转identity、scale1。SetPachinkoTransition位置/缩放为Clamp01线性插值，旋转先EasedValue枚举3再Quaternion.Lerp；同时改变piggy与shadow。不能拿普通飞币FOV10替代它。运行态copyCamera和动画时长/投影仍待验证，不以序列化相机参数声称最终像素一致。

脚本核对UIPachinko直接引用全部可解析，记录相机父链、资源文件大小与SHA。三个完整pack的网格/纹理/pack共115个去重文件、5995574字节（磁盘文件统计，不是UI子树最小依赖集，也不是解码内存或GPU占用；sprite/fonts尚未列入该统计）。这次没有改运行画面，没有进行无关构建。下一步按此入口准备UI子树/相机及机器的统一生命周期，然后接投球和自动结算；原版同帧验证、Pachinko完整交互和平台真机验收未完成，目标保持active。


## 2026-09-09 Pachinko UI资源包与世界空间Canvas缺口

上一轮入口取证为 progress。本轮扩展 extract-finish-sprites.py 的显式 --pachinko 分支（默认finish选择保持），新增 package-pachinko-ui.py，生成 public/assets/pachinko-ui-layout.json：215个源节点、10个Sprite、6纹理（文件2499615bytes）、2字体，验证字体/纹理SHA、图片引用和父链。字体来源包括2474与Unity默认Arial10102，不能假定仅一套字体。包不执行源示例奖励状态。

实际浏览器装配测试失败并保留 pachinko-ui-package-tests.log：UI根/Camera等为普通Transform，uiHierarchy先访问不存在的rect。进一步核对发现唯一Canvas14102挂在Camera6826下，m_RenderMode=2（world space），CanvasScaler固定像素模式0、dynamicPixelsPerUnit2。当前uiLayout只支持屏幕CanvasScaler模式1，而UILayer使用屏幕正交相机，不能将此包直接送入FinishUI路径，更不能改源Canvas模式/删除相机来让测试通过。

已将真实渲染测试显式标记fixme，待世界空间布局/投影实现后恢复；没有声称其通过。独立资源验证1通过、渲染1跳过，日志pachinko-ui-package-resource-tests.log。验证仅覆盖世界Canvas和相机父关系、资源可访问，未证明渲染效果或像素一致。包明确renderMode=world-space、screenRendererCompatible=false、runtimeStateApplied=false。

下一步优先实现世界空间RectTransform及保留z的网格/相机渲染路径，使用源Canvas尺寸和父TRS；随后恢复本次渲染测试并接Pachinko机器、投球与原版结算时间线。本轮未改变主程序画面，完整目标active，不能称自动结算或Pachinko可玩已完成。


## 2026-09-09 世界空间Canvas布局/透视渲染路径

上一轮世界Canvas缺口取证为 progress。本轮实际修改 uiLayout/uiAutoLayout/UILayer/UIWindowLayer：增加显式 world(parentMatrix,camera) 参数，世界Canvas保留源根SizeDelta/LocalTRS，子节点沿源锚点/局部z组合完整矩阵，字体密度采用m_DynamicPixelsPerUnit；UILayer使用提供的透视相机、世界UI启用深度测试，保留已有批处理/纹理lease所有权。默认屏幕路径保持原行为。矩阵中的z保留用于渲染；UIRect.corners仍是XY诊断值，世界空间点击投影/事件尚未接入。

UIPachinko.LateUpdate ARM64新提取表明copyCamera有效时只复制position/rotation，不在该方法改FOV。源Canvas缩放(.01,.01,1)，宽高1170×2532；Background局部z15，其他控件不同z，故不能把所有控件压成同一个屏幕平面。

首次整页绘制已越过此前缺RectTransform/世界Canvas问题，继续失败于原有文字样式限制（world-ui-tests.log）。源Arial Bold和Fredoka左中对齐未支持，不能取消校验或改成其他字体冒充还原。整页测试明确fixme；世界路径另有数值与GPU投影测试，未以其替代整页验收。

world-ui-verified-tests.log：11通过、1跳过（3.6s）。验证源非均匀缩放/父级90度旋转/局部深度，视口改变不改源世界尺寸；真实WebGL像素，深度4为7396像素、深度8为1936像素，约1/4面积，释放后drawCount0。既有屏幕布局/遮罩/批处理/失败重建测试通过。这不是原版像素对齐或小游戏性能验收。

下一步：实现并验证缺失文字样式，恢复Pachinko整页绘制，然后把世界UI与机器、物理球、奖励事务和自动结算生命周期接到主程序。完整目标仍active。


## 2026-09-09 Pachinko文字支持与完整序列化绘制

前一轮响应用户启动Web请求，已确认5173返回HTTP200并请求应用打开level5；本轮恢复UI工作。FreeType C ABI增加gb_glyph_style，style1在加载轮廓后调用FT_GlyphSlot_Embolden再灰度渲染，advance取最近整数像素。普通gb_glyph兼容保留。TS度量/光栅/字形图集以style参与缓存key，uiTextLine及preferred传递style，补左中对齐anchor3。WASM已按固定FreeType2.13.3重新构建，许可证和构建SHA在ui-freetype-build.json。合成粗体是待原版校准实现，不能把普通字体回归通过扩大为粗体逐位一致。

整页继续遇到源径向Image方法4、fillAmount1；只增加填充恰好1时完整矩形路径，其他径向比例仍显式拒绝，未强制修改源比例。完整0…1径向裁切还需实现，Pachinko运行progress不能据此称已完成。

本轮恢复此前fixme整页绘制测试并通过。pachinko-font-final-tests.log共11通过（2.7s），包括2套字体整页渲染、普通/粗体交替光栅不污染缓存、独立UV条目、原2,287字体度量/70位图/544原版缓存顶点均一致、图片回归。整页125graphics→74实际提交、6纹理引用，销毁后draw/submissions/entries/references全0，GPU非黑像素119539。截图pachinko-ui-serialized.png已人工查看，显示源YOU WIN示例窗口及叠放的按钮；这证明资源可绘制，不是原版正常投球状态或UI验收图，不能放进主程序作为已还原结算。

下一步优先应用源ShowBreakPiggy/ShowButtons/ShowPrizes/SetDetails运行状态，接机器、球和奖励状态；完成径向进度裁切及粗体原版缓存验证。world路径仍未接main，Pachinko可玩/自动结算/全关和小游戏真机验收均未完成。目标active。


## 2026-09-09 Pachinko普通投球界面状态

上一轮字体与整页资源绘制为 progress。本轮提取 UIPachinko.ShowBreakPiggy/ShowButtons/ShowPrizes/OnShowAniFinished 原生方法，并实现 runtime/pachinko-view.ts 的确定状态快照。SetDetails入场按钮全隐藏，OnShowAniFinished调用ShowButtons(true,false)；Drop后全隐藏，claim时Claim和Exit同状态。破碎三个按钮/背景/奖励窗口保持关闭，奖品仅在非入场且调用方prizesAlive为真时显示，piggyCoins入场隐藏完成后显示。它仅处理已结束的显示状态，不冒充动画、粒子清理、物理准备或奖励事务。

真实渲染测试同时保留 serialized（覆盖全部样式）与 ready（明确测试prizesAlive=[false,false]）两种画面，不以隐藏复杂分支替代全部资源绘制验证。pachinko-ready-view-final-tests.log 4通过（2.0s）；ready由125图形/74提交/6纹理降为26图形/23实际提交/3纹理，关闭引用与提交归零。差异来自显示状态，不是小游戏性能验收。pachinko-ui-ready-visibility.png已查看：仅DROP、钱包、目标金额和进度，叠放的YOU WIN/LOSE PIGGY等已消失。

截图中的10000、+2000、22%仍为序列化样例，不是实际玩家经济；没有机器与球，不能当作可玩或完整复刻。主程序尚未使用此控制器。下一步使用真实PachinkoUserData/奖品值驱动文字与径向进度，接机器和物理球，再接普通自动结算，继续保留平台与全关验收未完成。


## 2026-09-09 Pachinko机器与UI同相机装配

上一轮普通界面开关为 progress。本轮新增 game/pachinko-machine-view.ts，复用Assets/LevelScene加载完整3049机器，沿PachinkoMachine.pachinko/ballPrefab引用得到板和球模板；把板重新挂到自己的渲染根，使用源SetDetails最终位置(0,-2.9,14)、unit scale，结合LevelScene反射X与Three相机-Z做Y轴pi旋转/负z转换。模板隐藏，尚未创建可投球；类目前renderOnly，不生成可运行的Pachinko物理。关闭拆除独立板并dispose LevelScene，纹理/基础网格仍由传入Assets负责释放。

实际加载首次失败：3049 BlobShadow材质14的_CameraFadeParams.g为Infinity，Python导出允许但JSON.parse拒绝。新增parseSourceJSON用于Assets.json：仅在字符串之外将±Infinity数值token转换为±1e999，标准JSON.parse保持相同非有限数值；不eval、不修改原资源、不随意写零，NaN/错误语法仍拒绝。测试覆盖引号/转义字符串、正负Infinity和非法代码输入。原pack SHA保持。

模型与ready UI共用单一相机/WebGLRenderer绘制，截图pachinko-ui-ready-machine.png已查看。这里灯光为测试环境Ambient .7/Directional1，并非源相机灯光已校准；金额/进度仍为样例、无存钱罐/球/真实奖品状态，不能当作主流程或1:1验收。原test只读最后一次render的UI calls23，现关闭autoReset并在整帧前reset，机器+UI真实46次提交（UI23）。不要把UI提交数当全帧性能。

pachinko-machine-final-tests.log 4通过（2.3s），可见像素104109；机器/资源/UI清理后renderer.info.memory.geometries和textures均0。该计数只验证本测试释放，不代表进程内存或小游戏真机显存。首轮构建TS发现组件data可能undefined，已添加缺组件显式错误，重新构建。主程序尚未接入这一场景；下一步投球刚体/目标碰撞/源灯光及真实经济状态，然后接自动结算生命周期。完整目标active。


## 2026-09-09 Pachinko板内物理与目标触发

上一轮机器渲染装配为 progress。本轮PachinkoMachineView从完整机器选取PachinkoBehaviour子树，按SetDetails最终unit scale前的板局部坐标生成渲染与碰撞，不再把机器原始.1835968缩放带入球半径/物理。外侧机器入口Trigger不属于板内，因此板内23碰撞体（旧完整机器24）；首次测试误把24当板数量，按引用范围纠正为23，保留失败日志。暴露physicsScene/ballBodyId/targets和球模板clone，为后续控制器装配服务。

新增game/pachinko-physics.ts，独立板局部Rapier World，复用源BodySpec/ShapeSpec形状、位置、旋转、摩擦/弹性combine。模板球运动学准备，Drop切动态；半径.30000001192、质量1、restitution1、源阻尼，固定步1/60。源PachinkoBall.FixedUpdate为mode5加速度(0,-20,0)，另加全局重力-9.81000042，首步vy=-.496833384。所有板内目标从PachinkoElementTarget.index映射，球进入对应触发器后停用。该阶段单球，不是完整球池/多球投放实现。

真实资源浏览器测试pachinko-physics-verified-tests.log通过（523ms）：准备球保持(0,7.03000021,0)，投球383step后碰撞进入index1目标，物理球disabled。目标槽结果为当前Rapier确定性测试结果，不是原版相同操作轨迹结论。机器/世界UI回归pachinko-physics-assembly-tests.log通过；构建build-pachinko-physics.log通过。

待办明确：OnCollisionEnter重复碰撞衰减/脱困加速度尚未接入，物理奖品生死与回调、声音/粒子、多球、源球销毁而非仅停用、输入与渲染逐帧绑定、main自动结算和真实PachinkoUserData奖励尚未完成。此模块未运行主关卡球的移动辅助，也未声称Rapier与Unity PhysX轨迹一致。完整目标active。


## 2026-09-09 Pachinko重复碰撞修正接入

上一轮独立单球物理为 progress。本轮PachinkoContacts接入PachinkoPhysics碰撞事件，读取源OnCollisionEnter：碰撞对象等于倒数第二个时，非kinematic速度按float32(.666)缩放并增加计数；否则等于最近对象仅计数；新对象清零。计数>=11时AddForce(Vector3.right*100,ForceMode.Acceleration)，再清零。随后previous=last,last=current，次序不可调换。Vector3静态字段0x3c为rightVector，不是up/down。板物理使用反射X坐标，因此Unity右向加速度在下一步转换为本地-X。传感器不进入实体碰撞衰减，目标触发独立处理。

2项测试通过（675ms，pachinko-contact-tests.log）：覆盖A→B→A与连续A不同分支、kinematic计数不衰减、11次阈值和新对象重置；真实23碰撞体落球仍成功目标触发。接入后测试从旧383步/index1变为376步/index0，证明规则会影响后续轨迹；不能据此断言新轨迹就是Unity原版。基础半径/质量/重力首步仍通过。

原生方法及Vector3字段声明归档pachinko-contacts-20260909（SHA manifest）。主流程、可视球逐帧同步、多球/奖品、完整原版同操作比对仍待完成。Rapier事件排序、求解器与Unity PhysX差异未验收，完整目标active。


## 2026-09-09 可视弹珠生命周期

上一轮重复碰撞修正为 progress。本轮新增game/pachinko-run.ts，把PachinkoMachineView和PachinkoPhysics装配为单球运行实例：create载入/准备，drop仅ready可调用，fixedUpdate同步位置与旋转，目标触发先回调再移除可见球，设置target状态防重复结算；即使回调抛错也finally移除可见球。dispose幂等关闭物理和视图，Assets仍由宿主拥有。源物理球目前停用后等待world销毁，尚未逐球removeRigidBody，不冒充完整多球生命周期。

真实浏览器验证pachinko-run-verified-tests.log通过（1.1s），准备10步不移动，投球模型更新，376步到目标0、回调时模型尚attached、随后detached，额外fixedUpdate不重复回调；关闭两次且Assets清空后renderer.info.memory几何/纹理均0。截图pachinko-visible-ball.png已查看，球在板上真实可见。测试首轮只因-0与0深比较失败，改为坐标数值比较，未改物理轨迹。构建build-pachinko-run.log通过。

当前截图使用球模板与测试灯光，无真实玩家球皮肤和源光照校准；不含UI按钮输入与奖励事务。该运行实例仍未接main，下一步接输入/多球与实际PachinkoUserData，再把源普通通关生命周期连接起来。全关与小游戏平台验收未完成，完整目标active。


## 2026-09-09 自动横向摆动与投球时机

上一轮可视落球为 progress。本轮核实源PachinkoBehaviour准备球是自动横移，不是拖拽决定落点：OnEnable调用StartMoveAni；序列先设置horizontalMoveValue=-1，再-1→1一秒和1→-1一秒，两段Ease4(InOutSine)，SetLoops(-1)。SetHorizontalMoveValue仅写值，Update调用UpdateReadyToDropPositions。构造器ARM64 0x2337bd0/7bd8给xLimit=2.5。

新增pachinkoHorizontalValue及PachinkoRun.update(dt)：独立接收scaled表现/tween时间，复用已核验pachinkoReadyLayout(1,diameter,2.5,…)；球模板y/z不变、坐标反射X后同时写模型和准备刚体。物理fixedUpdate仍由宿主独立推进，Drop后横移时钟继续但不再移动已落球。没有添加拖动操作或人为发射横向速度。

真实运行测试pachinko-horizontal-verified-tests.log 2通过（1.1s）：源半径.3单球边界±2.18499994，.5秒中点0、1秒另一端；Drop后update(.5)位置保持，再固定步自然落球149步进入目标2、回调一次、关闭资源计数0。另验证两秒周期/非线性四分之一时刻与非法时间。build-pachinko-horizontal.log通过。此结果是Rapier测试，不是MuMu同操作轨迹；Math.cos与DOTween中间float32取整/真实OnEnable到UI按钮出现的时钟相位仍需同帧校准。

主流程输入入口、多球和真实奖品/奖励数据仍待接入。下一步以点击投球时机为操作接口，而不是继续错误地设计横向拖拽。全关与平台门禁未完成，目标active。


## 2026-09-09：第 5 关双箱初始失稳修复

用户反馈截图中的两块为 005_v01 的 Push Box (-31244)/(-31232)，源节点 637162199451465040 / 910700960644101456，并非铰链。位置 x≈±0.5、y≈0.5、z=39.5，质量1.5；各自由窄 Pipe 支撑。复现：无球接触推进600固定步，左箱自行倾倒并落到 y≈-149。源 Gyro.PushObject.Init/OnLevelEnablePhysics/Unfreeze 表明箱子可动态推动，不能永久固定。单纯 sleep 及网格顶点合并实验未解决，未保留这些实验修改。

Rapier 适配：只给源 PushBox 标记 restUntilContact。初始化对单盒、竖直、dynamic 的候选向下做固定实体碰撞检测，底面±0.01内有支撑时暂用运动学保持源姿态。真实动态实体碰撞或外力使其永久转为动态；无支撑箱子正常自由落体。退休/死亡/销毁清理记录，爆炸查询包含等待唤醒的箱子。此为防初始数值失稳的适配，并非已证明 Unity 使用同样算法；首次接触转换发生在该物理步事件处理阶段，碰撞轨迹仍需MuMu同操作校准。只在初始化查询支撑，不增加逐帧射线、渲染或drawcall。

验证：push-box-rest-tests.log 5项通过，包含主线程/Worker静置10秒位置偏差<0.001、球撞后位移>0.1、悬空箱下落、外力唤醒，以及既有铰链受力不脱离回归。build-push-box-rest.log构建通过。本轮未修改MuMu存档。

仍待办：第5关钥匙拾取反馈、截图上方机关动画，及所有关卡机制逐关验收；不能宣称全关显示正常或1:1完成。Pachinko独立交互预览文件已编写并构建过，但浏览器验收和主流程接入仍未完成，暂让位于局内问题。


## 2026-09-09：钥匙反馈接入；按用户反馈撤销箱子预固定

用户明确优先首次碰撞立即受力，宁可保留掉落问题。已完整撤销 restUntilContact、支撑射线和事件后切动态适配；PushBox 从创建起即动态，爆炸/外力沿原始路径处理。上一节“双箱初始失稳修复”的实现已失效，相关历史测试不能证明当前箱子稳定。失稳仍为未解决项，后续只能在不牺牲首次碰撞反应的前提下对齐接触求解。

钥匙无反馈根因：场景加载了触发体却未处理拾取事件。现按源 CollectableKey 注册 key/triggerCollider 引用，接入主线程与 Worker 的实体碰撞事件，立刻标记 collected 并关闭触发体。KeyCollectAnimation 按 ARM64 DoAnimation 0x23079e8，在世界 +Y 移动10，时长float32(.2)，Ease=2/InSine；完成lambda仅ret，因此不凭空增加隐藏/缩放/飞HUD动画。父节点旋转/缩放下仍按世界方向移动。退休时清理引用，不创建额外纹理或几何。

证据 key-pickup-source.json 含源ELF/方法SHA与duration映射地址0xcf9adc；归档 logs/v3.40/key-pickup-20260909。UserInventory.AddKeys为正整数累加；客户端暂接会话内uniqueID去重计数和现有HUD通知。完整钥匙栏源UI、Economy上限/消费/跨启动持久化与MuMu同操作画面尚未校准，不宣称经济系统或视觉1:1完成。

key-pickup-tests.log：主线程/Worker真实碰撞、10单位世界升起、重复碰撞不重复计数，以及变换父节点下InSine中点，共3通过。最终key-and-dynamic-box-tests.log另包含有支撑/无支撑箱子从开始为动态及外力/自由落体回归；构建见build-key-and-dynamic-box.log。上方机关动画、全关机制审查、平台真机门禁继续待办，目标保持active。本轮未操作MuMu存档。


## 2026-09-09：箭头坡道 UV 动画

当前005_v01无ObjectSpawner/Animator，含1个Spawnpoint和6个RampTerrain。用户截图上方疑似存档点，尚无同位置MuMu画面证明，不把坡道修复当作截图机关已验收。

已核验并接入另一个实际缺口：Gyro.RampTerrain.Start启动Animation协程；<Animation>d__7.MoveNext首次yield，随后PrepareMaterials、offset.y -= speed*Time.deltaTime，负数只加1一次（不是通用取模），float32运算。PrepareMaterials只克隆槽2、保留源初始UV偏移。现RampMaterial通过UV矩阵uniform更新顶部材质，不改共享Texture；同一加载实例中相同源材质/速度共用变体并保持空间合批。静态合批键纳入实际材质UUID，避免动画顶部与未动画表面混用。退出实例清理变体引用及已登记材质，不新增纹理/几何。

验证见ramp-animation-tests.log（源时序/负V/环绕、共享纹理不变、第5关LevelScene更新与退休）和build-ramp-animation.log。源方法与SHA归档logs/v3.40/ramp-animation-20260909。协程起始帧和MuMu画面滚动相位仍需同步实测；截图存档点的动画待继续核验。保留用户优先首次撞击受力的要求，箱子没有重新固定。全目标仍active。


## 2026-09-09：第5关原版静置录像与判断纠正

本轮是证据进展，未修改运行代码。MuMu起初stopped，CLI启动设备0并连接16384；inspect确认原进度73、lives4/capacity5、selectedSphere29。通过mumu-save.py备份跳5，home截图实际显示LEVEL5，随后录制5秒无输入静置视频。证据：checkpoint-native-home5.png、checkpoint-native-idle5/recording.mp4、manifest.json（completed=true、recorderExit=0）、checkpoint-native-idle-frame.png。

重要纠正：之前猜测RayOn与Ray On名称不一致，但当前scene.ts实际已匹配RayOn，该猜测被当前代码否定，没有做名称修补。当前005_v01仅1个Spawnpoint，无ObjectSpawner/Animator，截图绿色标识的实际驱动尚不能确定；不要将其他坡道动画修复当作该标识已恢复。后续应对绿色标识做画面定位并追踪运行时生成来源，而不是依靠小截图外观猜测。

使用20260909-122053-952919-jump-5/playerprefs.xml恢复原进度；checkpoint-native-after.json显示73，checkpoint-native-restore-audit.json比较完整UserInventory（除modified）changedInventoryFields=[]。购买、皮肤和库存均保留。本轮没有局内移动或消费输入。全关机制、原版画面与小游戏真机门禁仍未完成，目标active。


## 2026-09-09：绿色标识箭头缺失已定位为叠加材质；纠正滚动属性

客户端靠近z50截图checkpoint-client-close5.png显示绿色标识为空底；接入叠加shader后的overlay-client-close5.png可见白色箭头。实际缺口是Assets.material此前忽略Custom/DiffuseColoredOverlay的_OverlayTex，不能继续归因于存档点或漏RayOn粒子。

源Custom_DiffuseColoredOverlay_program_13.glsl 126–137明确main.rgb*(1-overlay.a)+overlay.rgb*overlay.a，随后_Color调色并叠加与DiffuseColored一致的无光照项，输出alpha1；独立_MainTex_ST与_OverlayTex_ST。现overlay-material.ts恢复对应双纹理UV采样、alpha混合和自发光项，使用单pass和共享纹理；Assets资源扫描通过overlayMap成员保留其所有权，RampMaterial克隆显式继承引用。

关键逆向纠正：extract-ramp-property.py解析ELF RELATIVE relocation和metadata-v31，0x4b89b98→0x4d13678→literal17480，字符串为_OverlayTex。上一轮RampMaterial滚动底图的实现因此被替换：现在只更新sourceOverlayST uniform，保持底图UV不动；保留原协程首帧yield、float32减速率及负数加1一次。没有修改球体、箱子物理，也没有增加运动学固定。

证据：ramp-property-static.json含ELF/metadata SHA、地址和字符串；源shader与SHA归档logs/v3.40/overlay-material-20260909；overlay-material-tests.log包含真实GPU像素alpha混合、叠加UV移动像素改变、level5真实shader编译、关卡动画与退休回归；build-overlay-material.log构建。原版逐帧滚动相位/光照仍未同步校准，不宣称1:1。此前关于“截图标识就是存档点”的猜测不作为结论。MuMu保持已恢复73，本轮无存档写入。全目标active。


## 2026-09-09：叠加材质驻留与切关资源审计

本轮为验证进展。新增inventory-overlay-materials.py扫描全部本地theme/prefab JSON：26个Custom/DiffuseColoredOverlay材质、39个唯一纹理文件，编码文件合计6,400,566字节，引用缺失0、同ID定义冲突0。此为全包依赖清单，不等于同时驻留内存或全关视觉验收；详见overlay-resource-inventory.json。

新增overlay-residency.spec.ts真实WebGL生命周期测试：源TopArrowsGreen材质克隆为RampMaterial后，隐藏但仍驻留的mesh必须保留overlay纹理；退掉最后场景拥有者再releaseUnused，只释放一次。3轮render/隐藏/恢复/退场后GPU geometry/texture均归零，live计数一致，单面quad1draw；overlay-residency-tests.log 1通过。构建build-overlay-residency.log通过。

实际客户端debug load 5→6→5→6→5记录overlay-level-cycle.json：每次第5关61几何/31纹理/76drawCalls，第6关57几何/28纹理/65drawCalls，无pageerror，未来关分别6/7与7/8，重复回来资源计数一致。只等加载完成后两帧，用于驻留计数检查：其fps/frameMs包含加载阶段，不可当稳定运行性能；JS heap数值粗粒度且不含GPU/进程，loadedBytes为累计JSON计数，不可当驻留内存或网络字节。不是原版自然通关，也不是微信/抖音真机验收。后续仍需真实运行采样、内存上限、分包及逐关机制/画面对齐。


## 2026-09-09：生成物主线程/Worker物理接口

此前ObjectSpawnerClock/SpawnerPool/setup/clip/运动公式仅独立模块，Physics公共接口无法在关卡运行中添加生成物。现新增addSpawnerBody/placeSpawnerBody/releaseSpawnerBody，并打通Worker同generation消息分发。添加要求唯一刚体和碰撞ID、kinematic初始状态；生成阶段按源SetTransitionValue的Transform.set_position直接设置位置并同步运动学目标，不人为从位移推导发射速度。释放要求仍为kinematic及正duration，转dynamic后按现存速度加(end-start)/duration（源VelocityChange）；源shape质量保留。

spawner-runtime-bridge-tests.log 4通过：主线程/Worker用真实SpawnerBall经LevelScene编译的BodySpec动态加入空世界，生成阶段位置保持、释放首步2/60位移、外力后3/60位移、真实固定墙挡住、退休移除；既有有/无sensor质量回归均通过。测试为隔离速度验证把重力和linearDamping设0，不能据此宣称原版掉落轨迹一致。build-spawner-runtime-bridge.log构建通过。

尚未完成：85处关卡生成器的clock→模板/池→渲染clip→新物理接口接线、生成物缩小回收及mine爆炸整合。下一步必须接实际关卡流程，不能把本轮公共接口视为生成器完整验收。用户要求普通PushBox首次撞击立即受力仍保留，本轮kinematic接口仅供源生成阶段使用，没有恢复碰撞前固定箱子。MuMu无操作，目标active。


## 2026-09-09：真实SpawnerBall单次生成生命周期

新增SpawnedBall：从源spawnerball prefab复制节点配置size，复用Assets几何/纹理并由LevelScene编译源刚体；每个生成物使用独立UUID碰撞ID。以SpawnerClip控制生成裁剪面，InSine时间值经既有float32插值同步渲染位置和Physics；完成后关闭clip、释放为动态，依据PhysicsState回写位置/旋转。落差超过源fallDistance时移除物理/模型并销毁实例材质，dispose幂等；进入末段则使用既有source fall-state计算视觉缩小。

spawned-ball-tests.log：main/worker两项真实源模型WebGL测试通过，验证半程InSine位置、emerging→falling→dead、无shader/pageerror、实际draw、死亡后物理IDs只剩player且场景根已移除。build-spawned-ball.log通过。此测试使用独立物理场景，不是用户当前主关卡已经周期出球。

明确剩余：ObjectSpawnerClock按关卡起始时间驱动、源旋转/portal配置传入、同步预热模板与对象池、实际主关卡接线；生成物缩小阶段目前仅视觉，球碰撞半径随缩小同步及source质量变化策略还需核对，不能宣称全部生命周期已1:1。Box/Mine尚未接入该owner。后续以真实关卡85个生成器总清单为范围，不以单球演示作为完成条件。普通PushBox保持动态初次受力。目标active，MuMu未操作。


## 2026-09-09：生成球缩小阶段同步真实碰撞

源SpawnerFallingObject.LateUpdate尾部只设置Transform.localScale（0x23474e0），SpawnerBall.Init设置初始质量，缩小过程不重新赋值质量。现Simulation在addSpawnerBody时记录单球实体形状的原始半径/中心/质量，scaleSpawnerBall按绝对比例更新SphereCollider尺寸与局部中心并保持初始质量、重新计算惯性；每帧不以当前半径再次相乘，避免累计缩小误差。比例0时暂禁用碰撞而保留动态下落刚体，避免Rapier退化球质量属性；这是引擎边界适配，不是原版代码使用同一禁用操作。退休/销毁清理规格记录。

公共Physics/Worker增加同generation缩放消息，SpawnedBall.sync在源末段缩放时同时修改视觉和碰撞，消除“模型小了碰撞还大”的缺口。spawner-scale-tests.log 3项通过：原始半径1→.5→.25→0→1，射线从命中变为不命中、质量始终8，零尺寸仍dynamic、复用恢复、无效参数/退休拒绝；真实源模型的主线程/Worker生成和退场两项回归通过。build-spawner-scale.log通过。源方法SHA归档logs/v3.40/spawner-scale-20260909。

剩余重点未变：关卡时钟/模板预热/对象池与主流程接线，Box/Mine完整生成碰撞及爆炸，MuMu同输入比对和小游戏平台实测。当前新生命周期模块尚非全关生成器已启用；目标active，普通PushBox仍立即动态受力，MuMu本轮未操作。


## 2026-09-09：生成操作进入批量固定步

主循环一次最多补4个固定步；若宿主把生成/移动/释放都先发送再step(4)，生成物会错误地提前参与整批物理，无法保持源FixedUpdate语义。本轮新增SpawnerStepAction（add/place/release/scale/retire及零基step），Physics.step和Worker透传到Simulation，在批量for循环对应步开始时按序执行；空操作数组保留原路径、输入分摊与原碰撞事件聚合。预检步号整数、排序、范围后再执行，避免无效步序部分推进。

spawner-step-actions-tests.log 4项通过：main/worker分别比较4步一批与4次单步，step0加入、step1放置、step2释放、step3缩放，生成球姿态数组完全相同且只经历2步动态运动；另验证同批退休后再次使用同ID只存在1个实例；已有真实源球生成/退场main+worker回归通过。build-spawner-step-actions.log通过。

此为周期生成接线所需时序能力，主关卡仍未调用该调度；没有把接口通过当成实际关卡已运行。接下来必须预热可同步分配的源模型/对象池并由ObjectSpawnerClock生成操作清单，维护主线程与Worker一致输入。源Tween的Update/FixedUpdate相位、随机数、85处机关完整行为和平台性能仍待验收。目标active，普通PushBox动态行为未改变。


## 2026-09-09：球体模板预热与同步模型池

新增SpawnerBallPool：加载阶段读取/克隆源spawnerball配置size并经LevelScene编译模型和碰撞规格；预创建并归还首个含裁剪材质的槽。getObject/releaseObject沿既有源SpawnerPool的创建顺序、优先首个空闲槽语义同步执行，不fetch、不await；每次取出恢复源位置/旋转/scale。每槽独立物理/碰撞UUID与SpawnerClip材质，但共享源几何/纹理。池根包含隐藏模板与空闲槽，供Assets.releaseUnused识别仍被持有的资源；dispose清理全部槽材质、节点和底层pool引用，拒绝销毁后取出。

spawner-ball-pool-tests.log 3项通过：真实模型两槽中释放首槽后100轮复用同一对象、分配数始终2，assets.bytesLoaded无增加，scale从.01恢复1.5，几何/纹理共享但材质独立；渲染后隐藏空闲槽不会提前释放GPU资源，最终dispose+releaseUnused后geometry/texture为0；源pool顺序与异常工厂回归通过。build-spawner-ball-pool.log通过。

注意预热目前完成CPU模板与首槽材质建立；GPU编译仍需宿主挂载pool.root后统一renderer.compileAsync，不能宣称GPU首次使用无卡顿。此前SpawnedBall独立验证入口仍用其原异步构造，本轮准备的新同步池需要在ObjectSpawnerClock/固定步actions主关卡控制器中使用并统一生命周期，尚未把真实关卡周期出球打开。Box/Mine、原版时序/随机数、平台真机性能依旧待验收。目标active。


## 2026-09-09：周期球体生成器接入实际关卡

上一轮首次碰撞回归为有效进展（新增真实球接触首步证据）。本轮ObjectSpawners终于将既有clock/setup/同步模型池/clip/固定步actions接入main加载与animate：仅扫描当前关卡有效ObjectSpawner objectType=0，加载时准备各源生成器模型池并挂入scene；开始playing后启动源delay/interval/variation时钟，每个物理步依次add/place/release，后续物理状态回写渲染、按fallDistance缩小与排队退休，释放槽后可同批复用ID。暂停不调用plan；切关在physics.dispose之前清理owner。debug state.spawners记录生成器数、累计生成数、活跃/分配槽与姿态。

源旋转证据：ObjectSpawner.Init 0x2334efc复制objectRotation到SpawnerObject+0x3c；SpawnerObject.Spawn 0x234769c/0x2347704明确set_localRotation。因此世界旋转使用生成器worldQuaternion乘镜像后的objectRotation，而非直接把局部值当世界值。普通PushBox始终动态逻辑未改变。

验证：object-spawners-main-tests.log 4通过，包括实际133_v01_End_0 prefab主线程/Worker从主页0球→周期至少2球→动态释放→暂停时钟不变→load5清空，以及既有批量/逐步物理时序一致回归。build-object-spawners.log构建通过。object-spawners-client.json/png为实际主入口debug指定prefab并将玩家置于(0,.5,62)观察：2.1秒累计2球，一球落在横轨y约.8，另一球仍生成中；截图可见紫黄源球材质。无pageerror。该位置为调试放置，不是原版同输入通关，截图FPS亦不作为稳态/平台性能结论。

限制与下一步：通用扫描已接球体类型，但未逐一验收75处球生成器；9箱/1地雷生成器尚未接入。源Tween在Unity Update执行，当前按固定步采样InSine；随机数使用Math.random注入，不保证Unity序列。缩小/死亡从最近完成物理批次状态采样，Worker最多一批延迟，尚未逐帧对照。预加载未来关卡/复活的源生成器生命周期、父级缩放、clip与portal原版视觉、池增长上限/小游戏性能均需后续核对。MuMu本轮未操作，目标保持active，不宣称1:1或平台验收完成。


## 2026-09-09：9处箱体生成器接入与主题字段纠正

上一轮真实球生成器接线属于有效进展。本轮按spawner-template-references清单，确认箱体9处来自3个关卡包，均使用嵌入、初始inactive的单节点SpawnerBox模板，size均(1,1,1)。ObjectSpawners按同一LevelScene实例范围解析spawningObject组件引用，将模板复制为独立局部根并激活，不把编辑器模板原始位置当作生成点。SpawnerModelPool复用球池实现，保留旧SpawnerBallPool导出兼容测试；箱体采用源网格/BoxCollider，源Init单位root scale、volume*3质量，出场完成即dynamic。多材质mesh逐槽独立SpawnerClip，拷贝材质数组避免污染其它槽；geometry/texture共享。

源Init/OnLevelThemeChanged/SetClipActive等ARM64已提取并归档logs/v3.40/spawner-box-20260909。OnLevelThemeChanged创建两个槽，对应MaterialsObjectSpawnerBox.margin/center。修正scene主题映射：SpawnerBall/Box/ExplosiveMine应读取objectSpawnerBall/Box/ExplosiveMine。此前直接小写SpawnerBall会跳过主题覆盖，本轮纠正。另修正调度config.variation为实际intervalVariation；清单85处当前该字段全部0，因此此前未观察到抖动差异不证明字段正确。

缩小复用现有scale action/Worker路径，单box记录原始size和center，按绝对比例setHalfExtents与局部偏移，保留源初始质量、重算惯性；零比例禁碰撞但继续动态下落。scaleSpawnerBall名称为兼容旧调用保留，目前支持单sphere或box。主关卡普通PushBox首次受力逻辑未改。

证据：spawner-box-tests.log首轮6通过1失败，失败仅测试立即读取尚未传播的collider世界坐标；改为检查translationWrtParent并推进一个物理步再查world后，spawner-box-scale-tests.log两项通过，未改实现来迁就测试。真实球/箱prefab主入口main/worker启动周期生成、释放、暂停、切关4项及模型池复用1项此前已通过。spawner-box-inventory-tests.log覆盖全部3包9生成器，推进180步，均生成动态cuboid，模型具有两材质槽。build-spawner-box.log完整构建通过。

限制：3秒测试证明引用与运行接线，不代表9处原版同输入轨迹或视觉全部对齐；未覆盖长时回收/生成箱碰撞音效、Unity Tween相位/批次延迟、未来关驻留/复活生命周期。75球仍待逐处实测，1地雷生成器仍未接入；MuMu本轮未操作。小游戏drawcall/内存、源shader最终像素对照仍待实测，不宣称1:1或平台验收。目标保持active。


## 2026-09-09：生成地雷进入真实关卡与爆炸流程

上一轮9处箱体生成器接线为有效进展。本轮接入清单唯一type2生成器（130_v01_Mid_1 prefab），使用Resources/prefabs/_level/spawnerexplosivemine源模型。模型池记录实体球、外层proximity与内层ExplosiveTrigger的独立槽/标签、mine视觉节点，每次复用恢复视觉偏移；add action携带MineSpec并与刚体同一步注册到main/worker。源UpdateSize不仅root scale=size，还将proximityCollider.local radius=size，所以继承世界缩放后的外层半径为size²，不能“修正”为size。

源依据：SpawnerExplosiveMine.Spawn重置exploded/proximityTriggered；Explode设置标志后直接SpawnerObject.Die；GetExplosionPosition调用当前Transform.position，GetExplosionRadius=size*10。Update只做接近抖动，不复用静态MineAnimation的自旋；shakeScale向1以dt*2插值，三轴Random.Range常数从ELF 0xcf9bdc/0xcf9b18读出-.05/+.05（float32）。客户端按X镜像位移，外层事件控制接近，退出归零。源代码/二进制归档logs/v3.40/spawner-mine-20260909。

Simulation接触内层触发时，用生成刚体当时位置计算既有爆炸力，禁用生成物与其碰撞，并通过explodedMines反馈owner；render sync隐藏模型、创建源ExplosionParticles，下次接受物理批次retire并归还池。移除清理旧MineSpec，同ID复用重新注册exploded=false。缩小规格记录扩展为整组sphere/box colliders，按同一绝对比例缩放实体和sensor，sensor质量0，实体保持源质量。普通PushBox首次碰撞规则保持不变。

验证：spawner-mine-tests.log初跑9通过1超时，唯一失败是4秒源间隔在5秒墙钟poll窗口未等到第二次生成；未改游戏间隔，将测试窗口放宽15秒，spawner-mine-main-recheck.log真实源关卡main/worker周期生成/暂停/切关两项通过。spawner-mine-explosion-tests.log四项通过：真实模板外层接近不爆、内层接触爆、故意把初始爆点放100单位外仍按移动后的中心施力、退休复用不残留爆炸标志；实际主入口调试放球接触，两个模式均模型退场并创建源爆炸粒子，无pageerror/consoleerror。spawner-mine-explosion-main/worker.png保存实际截图；图中亮闪证明效果在渲染，不证明与原版亮度/大小/时间完全一致。build-spawner-mine.log构建通过。

当前85处ObjectSpawner三种类型均有通用运行接线，但仍不能称全关机制复刻完成。剩余重点：MuMu同输入验证生成/接近/爆炸/回收、75球逐处覆盖、原版Tween与批次时序、未来关与复活生命周期、生成物/爆炸声音、完整机关清单及GUI。爆炸粒子仍首次异步创建，截图瞬时17FPS不是稳定性能结论，需预热与主线程/Worker性能实测；微信/抖音真机未验收。MuMu本轮无操作，目标active。


## 2026-09-09：85处生成器全包运行与资源审计

上一轮生成地雷运行/引爆验证为有效进展。本轮新增spawner-full-audit.spec.ts，对source参考清单28个prefab逐包加载、预热模型池、推进源delay+两周期+生成完成时长，并逐生成器source ID/type匹配（75球/9箱/1雷）。ObjectSpawners.stats.sources新增各源实例累计生成数与池槽计数，用于节点级覆盖，避免某生成器多出球掩盖另一处缺失。所有85处均至少生成2次，共303生成、10退休，无非有限物理姿态；全部包shader编译/渲染无pageerror/consoleerror，dispose+releaseUnused后测试renderer geometry/texture计数归零。

证据：spawner-full-audit.json记录每包source IDs、运行时长/耗时、池分配、退休/峰值刚体数、单视角drawcall/三角形/GPU计数；spawner-full-audit-tests.log最终通过（10.9秒）；SPAWNER_RUNTIME_AUDIT.md为资源表和验证边界。build-spawner-full-audit.log最终构建通过。首次构建遇到测试静态node:fs/promises导入缺少Node类型声明；仅改Node测试runner为动态模块导入，未向浏览器tsconfig添加Node全局，重跑完整审计通过。

性能线索：自定义256像素相机下最大138drawcall（hardlevel_007_v01）、最大67192三角形；该关13处HingePlatform、28处Trampoline仅是排查线索，尚未归因。这里没有主游戏UI/玩家操作/阴影，渲染器逐包新建，时间数值不是稳态FPS/平台实测；零计数也不等于进程/GPU字节为零或长期共享缓存稳定。仍需绘制调用归因、长期常驻/爆炸预热以及小游戏真机。

范围纠正：75球从“尚无逐处运行覆盖”推进到“全部源节点加载与周期物理运行覆盖”；并非75处已与MuMu逐帧对齐。所有关卡完整机制、碰撞手感、相位/音效、UI及平台验收仍未完成，目标active。普通PushBox稳定性/首次碰撞优先规则没有变化；MuMu本轮无操作。


## 2026-09-09：铰链主题修复与实例绘制优化

上一轮全85生成器审计为有效进展。本轮profile-hardlevel-draws.mjs用onBeforeRender逐实际material group归因：无生成球初始视角136次中，铰链66、弹跳板44、其余26。发现两者仍使用_blank，根因通用主题覆盖只识别theRenderer/renderer/renderers，遗漏HingePlatform的rendererPlatform/Mount/Nut1/Nut2与Trampoline.renderer1/2。源OnLevelThemeChanged明确：平台[top,side]，支架[nut]，两个螺帽[mount,nut]；支架使用nut并非笔误，ARM64配置+0x30与renderer+0xb0指令可查。弹跳板两个renderer均main。现按明确引用覆盖，缺失抛出可诊断错误。源方法、数据类/slot字段证据归档logs/v3.40/hinge-render-20260909。

共享资源铰链RuntimeHinge刚体内网格复用RigidMeshBatch，允许完整多材质数组，仅不透明、正行列式且geometry/全部材质/shadow相同者合并，附加48单位空间格以限制整组裁剪范围。仍保留每个源父节点的独立刚体/碰撞/矩阵；只隐藏原renderer并更新instanceMatrix，退休释放实例缓冲，保留共享几何材质所有权。普通PushBox首次动态受力未变化。

证据：hardlevel-draw-profile.json旧_blank初始136次；hardlevel-themed-draw-profile.json修正主题后137次；hardlevel-instanced-draw-profile.json同主题实例后95次，三角形均16972。有效性能比较是137→95（减少42，约30.7%），不能把材质修复前或包含生成物的138直接当相同比较基线。hinge-render-batch-tests.log铰链与既有小箱2项通过；补强可见刚体施力后hinge-render-motion-tests.log通过，三帧RMS0，帧间像素改变626/522字节，10批33部件，刚体14/碰撞123前后不变。build-hinge-render-batch.log构建通过。

因主题与批处理影响全部关卡，重跑28包85生成器，spawner-full-audit-after-hinge-tests.log通过；新版spawner-full-audit.json中hardlevel_007为97次（含生成物），旧数据另存before-hinge-batch.json，SPAWNER_RUNTIME_AUDIT.md表已更新。全部退出geometry/texture0，无shader/pageerror。仅隔离测试，无原版/真机FPS证明。

剩余：弹跳板44次绘制仍需分析其动画适用性，首用爆炸卡顿、长期驻留、WeChat/Douyin性能；材质映射恢复并不代表最终shader/光照像素与MuMu已1:1。所有机制/声音/UI、同输入轨迹等总目标未完成。MuMu本轮无操作，目标active。


## 2026-09-09：弹跳板连续触发修正与绘制合批

上一轮铰链主题/实例优化为有效进展。源Trampoline.DoAnimation 0x234bba4明确：首次捕获局部Y；已有sequence Kill(false)；Append两个DOLocalMoveY绝对Linear tween，先initialY+.4再initialY，各.08秒。ELF 0xcf9cf0=.40000000596、0xcf9ba4=.07999999821；StopAnimation只Kill(false)，不强行恢复坐标。此前elapsed=0固定三角波会在再次触发后跳回底部，现TrampolineAnimation记录当前起始Y并从当前位置重启，终点仍是首次initialY+.4，返回首次initialY。原触发速度/层过滤物理保持。

Trampoline子节点共享不透明网格加入既有RigidMeshBatch，按完整材质/geometry/shadow与48单位空间格匹配；没有把动画冻结或改成静态合并。updateAnimations先更新源visual localY，再回写instanceMatrix。困难关固定视角hardlevel-trampoline-instanced-profile.json为59调用、17332三角形，对比上轮同口径95/16972减少36次调用（37.9%），增加360三角形（2.1%）为整组frustum culling代价，需在平台GPU时间中验证净收益。

证据：trampoline-batch-tests.log四项通过（铰链/组合实例像素、动画单元、main/worker原弹板触发方向速度与层过滤）；trampoline-animation-render-tests.log两项通过，真实源关卡通过physics effects入口连续触发，局部抬升依次.2/.3/.4/0，四帧对照原renderer与实例renderer的像素RMS均约.102/255，画面改变6105/6069/4800字节，排除静止画面误验收。Stop不完成动画的测试通过。build-trampoline-batch.log构建通过。

重跑28包85生成器，spawner-full-audit-after-trampoline-tests.log通过，退出资源归零；新版审计hardlevel_007为61调用（含生成物），旧97次数据另存before-trampoline-batch.json，资源表已更新。动画/主题native归档logs/v3.40/trampoline-render-20260909。

限制：仍是客户端源码/像素回归，不证明与MuMu原版动画帧相位或声音一致；约.102像素RMS不是精确0，未宣称逐像素1:1。整组裁剪的额外三角形、CPU矩阵上传/遍历、首次爆炸卡顿及微信/抖音真机尚需实测。全目标active，普通PushBox首次受力规则不变，MuMu本轮无操作。


## 2026-09-09：开始点击无推力，首个拖动直接生效

用户原版实测纠正：点击开始不会自动获得速度，需要拖动。删除 main 的 launchPending、DriveInput.launch 和 Simulation 的开始时 400 加速度调用；仅知道 Gameplay.PushSphereForward 方法存在不足以证明它应在此时调用。Input.pointerdown 只进入游玩状态，位移按既有输入公式处理；删除吞掉整个首拖手势的 starting 分支。pointerup 不额外施力，保留最后未消费位移；取消/复活清空输入。没有通过锁定刚体或逐帧归零速度实现静止，重力、惯性和碰撞仍然生效。

验证：tests/start-input.spec.ts 覆盖真实第 5 关 main/worker 的 PLAY 点击、画布单击、首页首拖、复活后 30 物理步无水平推力，以及末次位移仅消费一次和取消输入。证据 start-input-tests.log、build-start-input.log。此前 Worker 测试首次失败是 reset 后 state 暂时为空，取 undefined tick 导致等待永不成立；现先等待有限 tick 后取样，不更改生产 Worker 逻辑。原版完整输入增益/采样相位、切关运动衔接仍需分别对照，不能由本次回归宣称全部 1:1。


## 2026-09-09：暂停输入残留修复

上一轮点击启动修复为有效进展。本轮真实第5关复现：PLAY→暂停→按住ArrowUp→点继续，没有新的方向按下事件，30物理步后 main/worker 水平速度均约4.38378。原因是showModal仅在打开时清空输入，暂停期间的window.keydown仍能填入Input.keys。修复前两项失败记录：docs/evidence/input-pause-before.log。

Input新增canAccept回调，由主流程提供!loading&&!paused&&!won&&!finishing&&!document.hidden。pointerdown、pointermove、keydown和sample在禁用期拒绝并清空输入；恢复后没有对应已接纳keydown的repeat事件也拒绝，避免暂停期间按下的键通过自动重复重新驱动。普通PLAY和画布点击仍只切换游玩状态，首拖仍直接有效；不冻结球或障碍物，不改物理增益。

修复后input-pause-after.log 9项通过：真实main/worker暂停恢复、恢复后新方向键有效、禁用手势及重复键过滤、先前启动/首拖/复活/末帧输入回归和自动制动。build-input-pause.log构建通过。触摸门禁的独立测试为合成PointerEvent，未宣称微信/抖音真机已验收。低帧率采样相位和原版同起点拖动轨迹仍待验证；MuMu本轮未操作，保持上一轮暂停现场。完整移植目标继续进行。


## 2026-09-09：补帧输入节奏量化与源码核对

上一轮暂停残留修复为有效进展。本轮新增INPUT_CADENCE_AUDIT.md、tests/input-cadence.spec.ts与input-cadence.json原始轨迹。真实第5关、24次12px拖动、120固定步、1/2/4步输入归组：峰值12.10549/11.64530/9.19911，累计标准化位移均1370.002736。main/worker同组轨迹完全相同，批量与首步消费后零输入的逐步控制一致。测试通过，typecheck通过；这是模拟消费节奏，不是实测60/30/15FPS。

ARM64重新提取Process、AppendInput、ConsumeGyroInput、PhysicalSphere.FixedUpdate/HandleInput和NormalActuator.HandleInput，字节与哈希归档input-cadence-source。原版在FixedUpdate调用actuator消费并清空累计输入；保持当前一次消费语义，本轮未改生产公式。相同位移在不同消费节奏下的差异已量化，但限幅/摩擦/时间因素未分离，原版实测相位仍缺失。不要用旧swipe-comparison启动假设报告宣称当前原版对齐。下一步需原版精确起点/镜头/消费时序后同条件回放及平台实测。MuMu未操作，目标active。


## 2026-09-09：机关复活生命周期核查

新增MECHANISM_RESPAWN_AUDIT.md按机制区分玩家复活与整关重载。源TemporaryTerrain复活回调直接恢复Collider/Renderer并ResetFade；ObjectSpawner关卡Reset/Start字段已提取，但Gameplay.Respawn接口及委托分派未全部确认，不能宣称原版复活节奏已对齐。原生字节与SHA归档mechanism-respawn-source。

扩展真实main生成器测试：球/箱/地雷×main/worker从UI检查点重试后，时间与累计生成不回退、源ID保留、继续生成、live ID唯一、位置有限；随后整关加载清理。与既有58关消失地板接触/坠落/恢复测试共9项通过（58.9s，mechanism-respawn-tests.log），typecheck通过。本轮生产代码及资源未变、MuMu未操作；不是所有85生成器逐处复活验证。第5关两箱稳定性、其他机关复活规则、原版同条件与小游戏真机仍待完成。目标继续active。


## 2026-09-09：箱子 autosleep 假设实测

用户建议启用autosleep。检查当前Rapier 0.20运行时RigidBodyDesc.dynamic().canSleep=true；普通箱子没有setCanSleep(false)，只有玩家球禁用休眠。真实第5关两箱600步对照写入evidence/push-box-sleep.json：默认休眠开启时，一箱倾倒坠落，另一箱倾倒后在低位休眠；初始化后主动body.sleep()同样在第1物理步被唤醒并随后倾倒。因此单独开启自动休眠或初始化sleep不能修复当前窄支撑接触问题。未修改生产刚体类型、休眠设置或支撑形状，保留首次接触即时动态响应。

push-box-sleep.spec.ts为本问题诊断实验，断言用于复现当前失败假设，不是原版期望状态；将来修复接触后应更新该诊断，不应为了维持该测试而保留坠落。与push-box-rest.spec.ts验证日志见push-box-sleep-tests.log。仍需核对原版碰撞形状/接触偏移/质心与支撑，不能直接强制每帧sleep掩盖不稳定。目标继续active。


## 2026-09-09：第5关箱子支撑隔离实验

上一轮autosleep排除实验为有效进展。新增BOX_SUPPORT_AUDIT.md及probe-box-support.mjs：真实场景7变体×600步，baseline/20次solver/两档skin/移除邻箱/归整箱子浮点误差均倾倒；仅把两支撑改为convexHull的隔离副本稳定在Y约.4999并正常休眠。原始支撑顶点、索引、碰撞姿态/接触在box-support-shapes.json和box-support-probe.json。

收敛到支撑碰撞表示差异，尚未证明源网格与凸包等价，故未改生产几何或刚体设置。下一步核对源拓扑/凸标志及表面体积等价性，再做实际球碰撞/Worker回归，避免填平凹处。MuMu本轮未操作，资源未变；两箱问题仍开放，目标active。


## 2026-09-09：支撑拓扑核查，排除直接凸包替换

上一轮7变体实验为有效进展。本轮audit-box-support-topology.py确认两处源支撑各18顶点（16唯一）、18三角形（2零面积）、16边界边，两端开放的八边形管壁，源convex=false；结果box-support-topology.json。凸包会封端，因此不能把上轮稳定结果当成源形状等价证明，也未应用到客户端。

probe-box-support.mjs新增cleanDegenerates和supportNoEdgeFix两对照：只删除零面积面，或只取消支撑FIX_INTERNAL_EDGES，均未稳定两箱。600步最终Y前者约-149.254/.26214，后者-149.615/.25994。原始形状、接触和姿态在既有box-support-shapes/probe JSON，最新9变体摘要box-support-probe-summary.json。两脚本正常退出，生产代码、资源和MuMu未改动。

结论：未发现可以直接采用的几何等价修复；稳定凸包方案附带端面碰撞变化，清理退化面/关闭内边修正无效。下一步需核对源运行时是否调整支撑Collider及PhysX箱体接触生成差异，必要时研究保持开放端面的接触适配，而不是每帧强制箱子休眠。两箱问题仍开放，全部机制及平台验证目标active。


## 2026-09-09：保持开放表面的直管接触修复已接入

上轮拓扑排查为有效进展。源Pipe初始化/重置路径检查没有发现凸包转换；PushObject.Init使用drag/angularDrag，隐式质心和惯量仍来自collider。源PushBox静摩擦.4、动摩擦.25，Pipe两者.6；实验仅改摩擦为.4或关闭双方反弹仍倾倒，不以这两项解释稳定问题。源字节/SHA归档pipe-runtime-source。

新增separateTriangles对照保持原16个有效侧面，仅改变窄相位接触表示：600步两箱Y=.499897左右、自动休眠。已生产接入pipe-contacts.ts：仅对Pipe组件、静态刚体、源网格30f347a7_7703131806334922322拆成16个triangleSurface ShapeSpec；每面保留原顶点、旋转、位置、材料、layer/tag，丢弃2个零面积面，不封端、不扩大接触外皮。Simulation用ColliderDesc.triangle创建面。原始几何索引仍保留便于现有mesh查询/边界逻辑使用；每面独立ID保证清理映射，源tag保持一致。

完整资源扫描显示该网格分布7个pack共14处（pipe-contact-inventory.json），每处碰撞shape由1→16；第5关两根支撑增加30个静态collider，渲染geometry/material没有改变，不增加drawcall。这是物理开销换稳定性，尚未实测小游戏CPU/内存净影响，不推广到所有曲管和其他网格。源资源包字节未变。

验证：pipe-contact-tests.log 6项通过（原面逐顶点/材质保留、main/worker两箱600步静置后第一接触移动、无支撑坠落、外力和原第一接触回归、默认自动休眠）；pipe-contact-final-tests.log 7项通过，增加真实物理轴向射线穿过两个开放端部、向下射线命中顶部，以及此前点击无推力/首拖/复活输入回归。build-pipe-contacts.log构建通过，pipe-contact-typecheck.log最终类型检查通过。

初始化主动body.sleep()在新表示下仍可能倾倒；仅诊断行保留，不用于生产。默认自然休眠两箱稳定；测试已更新为该预期，不再要求保留旧坠落缺陷。最早sleep失败及中间构建类型错误已纠正并完成最终检查。

限制：完成的是第5关稳定性客户端修复，不证明所有接触轨迹与原版PhysX一致。7包14处其他使用位置尚未逐一MuMu验收，双面Triangle对内部穿入等边界也需对照；无新增封端，开放射线检查已通过。原始诊断baseline单独保存before-triangle-fix，probe脚本改从旧原始shape fixture重建以免将修复后数据误当baseline；主客户端文件保持新表示。MuMu本轮未操作，完整移植目标active。


## 2026-09-09：直管修复7包14处运行审计

上一轮稳定性修复为有效进展。本轮pipe-inventory.spec.ts按源ID覆盖全部7包14处，每包main/worker×组合trimesh基线/独立三角面，共28组×600步均有限坐标，collider数量每包+30，验证与类型检查通过。资源位置及成本表见PIPE_CONTACT_COST.md、pipe-inventory-runtime.json与对应测试日志。

典型第5关独立pack碰撞总数87→117（含球）；其他包57→87等。桌面内部step中位数约.005–.030ms，固定顺序单次采样受JIT/计时分辨率/休眠状态影响，不能称性能改善；Worker宿主wall时间包含轮询等待。未测内存字节或小游戏真机。不改变生产代码/资源，新增范围与成本证据；全部机制和平台目标仍未完成，MuMu未操作。


## 2026-09-09：按需预热首次爆炸资源

上一轮直管范围/成本审计为有效进展。本轮新增ExplosionWarmup：在独立场景创建源ExplosionParticles，通过renderer.initTexture上传其3张贴图、compileAsync编译shader，再隐藏root并挂到主scene作为资源owner。预热阶段不渲染、不推进粒子；隐藏root保留资源引用，使Assets.releaseUnused不会提前回收纹理/program。卸载当前关卡时先dispose，移除owner并释放其材质/几何。

main仅在当前physicsScene有mine、ObjectSpawner类型2、或源组件isExplosive时预热；普通第5关不额外加载该owner。生成器尚未启动时预热已经完成；切回普通关清理。debug状态explosionPrepared用于检查，不进入产品UI。预加载将3贴图及1个shader程序常驻到该关卸载，保留4个粒子系统的CPU配置/缓冲引用，不是免费优化。

证据：explosion-warmup-tests.log 5项通过（独立资源预热/释放，生成地雷位置/物理与实际main/worker触发粒子）；explosion-warmup-owner-tests.log 2项通过（首次可见效果及main普通→地雷→普通关owner）；build-explosion-warmup.log构建通过，最终explosion-warmup-typecheck.log通过。最新explosion-warmup.json：预热22.1ms，第一次创建+update+render约4.2ms；这是单次桌面诊断，不是原版或小游戏帧时间。首次前后贴图3、程序1不增长；预热显示调用0，真实效果4调用；关闭两owner并releaseUnused后geometry/texture/program均0。

首次效果前强制后续assets.json请求抛错仍能创建，bytesLoaded未增加；该计数包含此前catalog/源JSON并非图片总字节。实际爆炸仍会创建SourceParticles数组/几何缓冲并首次上传顶点，本轮没有实现粒子对象池或保证零卡顿。生成地雷主线程/Worker轨迹依旧通过。原资源包不变，新增当前关卡的按需驻留策略；微信/抖音真机/内存字节与原版对照仍待完成，MuMu未操作，目标active。


## 2026-09-09：补齐Conveyor物理输送（表现层待续）

上一轮爆炸预热为有效进展。本轮从全关组件清单发现Conveyor在13包29处仍无运行处理，源三collider保存为disabled，现按OnLevelEnablePhysics将引用加入运行碰撞启用集合。LevelScene编译ConveyorSpec（源刚体ID、锚点、世界forward、speed）进入PhysicsScene；Simulation创建运动学对象，在每个非菜单固定步先setTranslation(anchor-forward*speed*dt)，再setNextKinematicTranslation(anchor)。未用直接给球速度或重力方向替代源接触输送。retireBodies同步删除控制项，dispose清理列表，主线程/Worker共用实现。

源ARM64 FixedUpdate 0x230da98：dt<.001早退（ELF0xcf9d40 float32 .0010000000475）；启用时计算speed*dt，Rigidbody.position退后并MovePosition回OnLevelStart所存锚点，随后纹理offset.y-=.25*speed*dt。Init克隆材质；OnLevelStart记录刚体位置。完整8方法字节/哈希在conveyor-native。本轮只接物理及碰撞，纹理滚动、主题renderer引用仍待补，Conveyor不标完整。

验证：conveyor-tests.log 3项通过（真实85关代表配置，main/worker分别正向/反向/0速度，菜单静止、60步后保持锚点、退场删除后继续step；全部13包29实例引用、刚体、碰撞及120步有限状态）。代表球正/反位移约+1.7482/-1.7488，沿带速度±2.09038，主线程/Worker一致；这些是Rapier客户端数值，未与MuMu PhysX匹配。build-conveyor.log构建与conveyor-typecheck.log类型检查通过。独立构建前测试的菜单坐标严格相等因float32表示差异首次失败，已改数值容差验证，生产逻辑未为测试放宽。

docs/mechanics-status.json更新Conveyor状态后重新生成全关机制索引，避免只有进度日志更新而清单仍称待分析。物理配置增加原本缺失的接触，不修改原资源文件。下一步Conveyor主题材质/滚动表现、球以外可推物验证和MuMu原版对照，然后ProjectileSpawner等未接机关。MuMu本轮未操作，全局目标active。


## 2026-09-09：Conveyor主题与固定步纹理滚动

上一轮Conveyor物理为有效进展。本轮按ARM64 OnLevelThemeChanged明确引用映射：rendererBelt→belt，两个step→step，四个lid→lid。此前通用主题逻辑没有处理这7个renderer引用；现逐项校验缺失并覆盖，源theme00分别169/171/170材质。

ConveyorMaterial克隆带面材质、保留共享贴图，以独立mat3 uniform同时更新map和emissiveMap UV，避免Custom/DiffuseColored的发光采样静止。纹理offset本身不改，不为每个传送带复制图片/GPU纹理。材质归属加入LevelScene实例，退场/销毁一起释放；静态合批仍可使用动态uniform，每条独立材质保持不同速度能力。

Simulation每个实际运行固定步按float32累计offsetY += -.25*(speed*dt)，进入PhysicsState.conveyors，由LevelScene.applyPhysics应用。菜单/暂停无额外渲染时钟推进，Worker回包保持同一物理/视觉状态；dt<源.001阈值不推进。完整关卡重建为0偏移，单纯玩家respawn不重置输送时钟。未实现运行中theme事件重选，不能因此宣称源全部生命周期完成。

验证：conveyor-render-tests.log4项通过（材质/像素/主线程WorkerUV及此前正反输送、13包29处）；conveyor-render-final-tests.log强化代表3条传送带共21renderer实际材质引用核对通过。12固定步speed6得到offset约-.30000004，main/worker完全一致；共享texture.offset保持0，前后35809字节像素变化，隔离256px相机23calls，截图conveyor-beforePNG/afterPNG.png已查看。测试场景为黑底俯视，不是原版机位或完整游戏首屏，不称逐像素原版一致。dispose及releaseUnused后geometry/texture计数0。

build-conveyor-render.log构建通过，最终conveyor-render-typecheck.log通过。状态写入mechanics-status.json并重建清单。源资源不变，新增按引用主题和独立UVuniform；仍需MuMu原版同机位/同速度、其他接触物与全29处视觉、小游戏性能。MuMu本轮未操作，完整目标active。


## 2026-09-09：抛射物审计

上一轮箱子答复仅核对既有状态，归类no progress；本轮完成源抛射物分析、全量引用审计及碰撞修复。audit-projectile-source.py确认19包100处、1模板、0缺失引用，200个默认disabled碰撞引用均需源OnLevelEnablePhysics恢复。LevelScene已补齐这一类型；逐包main/worker各120步有限值与200引用覆盖回归通过。源脚本/刚体/renderer在同一根节点，确认发射位置为门户局部back*.5、质量100、无重力、持续速度、局部轴.01纠偏及严格距离裁切/回收条件。原ELF、方法和常量SHA证据已归档。详见PROJECTILE_SPAWNER_AUDIT.md。未接入抛射物生成与运动，不宣称机关完成；下一步按文档实现固定步控制器与独立裁切池。MuMu本轮未操作，完整目标保持active。


## 2026-09-09：抛射物公共物理驱动

新增ProjectileDriveSpec与projectileShot固定步动作，沿用Physics.step的主线程/Worker有序动作通道。shootProjectile接收源动态、无重力刚体及角速度；每实际非菜单固定步恢复direction*speed，生成器局部X/Y严格超过float32(.01)时保留localZ纠偏。parentWorld及inverse由调用方提供，支持旋转和非均匀缩放；retireBodies与dispose清理驱动归属，允许退场后同ID重新发射。未给自由落球路径添加这个规则。

Rapier没有动态MovePosition接口，当前在求解接触前setTranslation到源目标；这是明确的引擎适配，PhysX的接触/插值是否相同未验证。矩阵运算最后float32归整，并非逐ARM64浮点指令模拟。随机角速度由调用者提供，主游戏RNG及Shot姿态还待生成控制器接入。

tests/projectile-drive.spec.ts使用本地源运行时模板（质量100、无重力）测试size1/.8 × main/worker：旋转90度、父缩放2/1/3，菜单不移动，60步前进12单位，横向外力后恢复轴线，.01严格边界，退场后重用ID，以及实际撞动玩家球。projectile-drive-runtime.json记录结果；projectile-drive-final-tests.log5项通过，含19包200门户引用与Conveyor既有回归。初次测试类型推断unknown报错已显式修正；build-projectile-drive.log构建通过。

本轮为物理运行通道接入，不是游戏机关完成：主游戏尚未发送projectileShot，未显示新抛射物。下一步接入当前关生成时钟、源双材质裁切/可复用视觉实例、距离回收及主题；再做100处运行与MuMu对照、小游戏性能。不以隔离测试替代原版/平台验收，MuMu未操作，完整目标active。


## 2026-09-09：抛射物裁切回收

上一轮公共物理驱动为有效进展。本轮新增src/game/projectile-flight.ts，落实3.40 SpawnerProjectile.Init/Update的方向、float32距离阈值与有状态裁切/回收：阈值相等不切换、单帧跳过中间区不补造切换、允许回退到入口、径向距离超终点只报告一次Die。shot恢复入口裁切，reset关闭active。主游戏还未实例化此类，不宣称视觉已经上线。

projectile-flight.spec.ts覆盖入口/出口等值边界、反向移动、跳帧、径向偏离、零长度路线、重复Update只回收一次、reset和重新发射；同时将状态应用到两个SpawnerClip材质，检查平面一致、裁切时不投影、退出裁切恢复投影以及dispose恢复原材质。projectile-flight-tests.log通过，详细结果projectile-flight-runtime.json。没有GPU像素或MuMu对照，不能据此证明原shader视觉一致。构建见build-projectile-flight.log。

下一步准备源双材质和视觉池，并将生成控制器接入main；以PhysicsState位姿每渲染快照采样此状态，将Die排为下一可接受物理批次的retire，避免同一Worker回包重复释放。不得用按时间寿命替代距离回收。完整目标active，MuMu本轮未操作。


## 2026-09-09：抛射物视觉池

上一轮裁切回收模块为有效进展。本轮SpawnerModelPool.createProjectile准备源Resources/prefabs/_level/spawnerprojectile：Init以size覆盖原.8缩放，重设局部旋转与位置，保持源质量100/无重力，不套用SpawnerBall的质量/阻尼/运动规则。LevelScene按projectileSpawnerProjectile配置明确映射renderer双槽main/led，避免通用类型名找不到主题配置。

复用现有视觉池：预备一个槽，克隆实例共享geometry和贴图、每槽保留独立SpawnerClip双材质；get重置姿态与裁切，release隐藏，dispose释放全部克隆材质与模板归属。预备模型不代表GPU shader已预热，尚需游戏接入后的首次出现和峰值内存实测。

projectile-pool.spec.ts覆盖size1/.8、真实源主题main/led引用、两实例共享geometry/贴图且裁切独立、释放再取同槽、两槽只分配2个、dispose四个材质事件及节点脱离。projectile-pool-runtime.json记录结果，projectile-pool-tests.log三项通过（含此前物理/裁切状态）。build-projectile-pool.log构建通过。此轮未做GPU像素、其他主题全覆盖或MuMu对照。

主游戏尚未创建ProjectileSpawners控制器；下一步连接源门户变换、时钟、视觉池、projectileShot与距离回收。只有这些连到实际关卡后才能测试完整发射循环。MuMu未操作，完整目标active。


## 2026-09-09：主游戏抛射物与全量阻塞

上一轮视觉池为有效进展。本轮新增ProjectileSpawners并接入main当前关生命周期：加载准备池，开始后以ObjectSpawnerClock逐固定步发射，和ObjectSpawner动作稳定按step排序；世界端点取两门户TransformPoint(back*.5)，旋转继承生成器，半径/视觉考虑父缩放，初始角速度按坐标反射的轴向量变换。PhysicsState驱动位姿和ProjectileFlight裁切，Die隐藏并排队retire后释放槽，换关dispose。预加载关段不建立发射循环。debug state.projectiles暴露发射/回收/池计数。

重新逐分支核对ProjectileSpawner.FixedUpdate 0x2338bc8，与ObjectSpawnerClock的active/running、半步容差、delay、interval累加和variation规则吻合；本地100处variation均0。源Unity随机序列、渲染帧时序及respawn调用链尚未完成原版验证。

全量实际物理测试首次发现全部生成物卡在入口，不能依赖代表游戏约20秒才出现的回收通过。原因是源PhysicsManager碰撞矩阵9↔18均false，而此前没有对抛射物过滤门户。PhysicsScene现在传源32层矩阵，Simulation只给抛射物Collider启用contact/intersection hooks，按双方矩阵过滤；其他普通碰撞体之间尚未全面接入源矩阵。该作用域是当前抛射物接入范围，不宣称整个物理层完成。回调CPU开销与小游戏真机待测。

修复后projectile-game-final-tests.log5项通过，包括真实main入口049 Mid 0在main/worker下菜单不发射、开始后多次发射/回收、加载第5关清理，以及既有物理/裁切/池回归。build-projectile-game.log构建通过。

projectile-inventory-runtime.json记录19包100处各900步（15秒）：全部至少发射2次且姿态有限，18包发生回收；055_v01_Start_0仍15发0回收，最早球约移动4.45单位后停留，原定终点距离17。接触涉及层8的Pipe (-128008)、Pipe (-128076)、Pipe (-128652)、S1 | Pipe (-228008)以及层9抛射物；源矩阵允许9↔8与9↔9，不能通过关闭这些碰撞掩盖问题。projectile-inventory-tests.log按每包有回收的测试要求仍失败。这个要求是排查标准，不是已经确认的原版行为；需MuMu此处实际发射对照，区分原版设计停留与Rapier管道接触差异。未强制超时回收、未加数量上限隐藏证据。持续运行可能积累对象，尚不满足性能验收。

下一步优先定位055 Start 0的Pipe接触并对照MuMu，再验证门户材质/角速度/像素及全100处Worker、跨关内存和小游戏。代表入口通过不能替代全量验收。MuMu本轮未操作，完整目标active。


## 2026-09-09：055管道停留诊断

上一轮主游戏接入与全量发现属于有效进展。本轮新增tests/projectile-pipe-probe.spec.ts，在真实055_v01_Start_0物理场景副本做6组900步对照。每组重置同一LCG种子12345控制发射角速度（仅测试覆盖Math.random，finally恢复），不声称Unity随机序列相同。生产代码与资源未改。

结果（每组15次发射）：baseline回收0；去除13个Pipe形状回收14；将管道mesh逐面triangle表示回收0；管道friction=0回收0；关闭局部轴纠偏回收14；关闭层9自碰撞回收0。所有姿态有限。关闭纠偏会允许球离开发射轴并下落，其回收不证明正确复刻。去除管道也改变玩家/机关碰撞，不能采用；拆三角面与去摩擦均无效，不推广此前第5关薄管接触修复。

证据projectile-pipe-probe.json包含逐组受影响碰撞ID/面数及每秒计数/位姿；firstPose字段跟踪首次分配的槽ID，槽复用后代表该槽的新发射，不能解释为同一发射物的完整轨迹。projectile-pipe-probe-tests.log通过只说明诊断运行有限且输出完整，不表示055问题解决。类型检查通过。

下一步仍需MuMu对应关发射路径与原版动态Rigidbody.MovePosition/碰撞响应对照，重点是Pipe接触与.01轴纠偏组合。当前证据不能判定是源设计停留还是Rapier适配差异，不移除源纠偏、不设超时回收、不屏蔽允许的Pipe碰撞。全量projectile-inventory测试仍失败且对象积累风险保留，目标active。MuMu本轮未操作。


## 2026-09-09：MuMu 55静止基线

上一轮六组诊断为有效进展。本轮按MUMU_SAVE_WORKFLOW使用进度专用工具从持久化关73跳到55，工具备份当前购买后存档，非进度字段相等校验及读回验证通过。备份路径见evidence/mumu-projectile55-manifest.json，未恢复旧库存、金币、皮肤或购买。原版首页截图明确Hard Level 55、皇冠皮肤；1440x2560。

首次tap(720,2470)后仍在首页：mumu-projectile55-native.mp4和文件名running.png实际是首页证据，不能当作运行采样。随后tap(720,1800)进入局内HUD，未拖动；录制mumu-projectile55-running.mp4共12秒，同时只读proc-mem采集711条玩家physics，max speed=0.000813338、allGrounded=True。这支持玩家基本静止，不能推出完全零速度或抛射物状态。该读取器未采样抛射物实例/位置/池计数。

查看录制第10秒frame10截图，目标区域过远且部分不在清晰可辨范围，无法判定055抛射物是否被管道阻挡。保留客户端全量失败，不能因原版截图未看到堆积就宣布差异修复。下一步从第55关起点靠近目标，或扩展只读抛射物采样；必须先确认具体原版实例与客户端Start0对应。

采样后tap(125,140)，截图mumu-projectile55-paused.png已实际查看并确认CONTINUE暂停遮罩。当前MuMu停在第55关暂停状态；未回到原第73关。录像/读取进程均已正常结束；本轮客户端生产代码未改，完整目标active。


## 2026-09-09：055互斥布局更正

上一轮原版55基线为有效进展。本轮新增scripts/native-projectiles.c：O_RDONLY读取目标进程，精确校验Gyro.SpawnerProjectile类名/命名空间，按已逆向字段扫描并记录active、clipping、size、distance²、limit²、start/end。不注入、不调用Unity、不写游戏内存。固定元数据槽扫描未找到类并正确退出5；补充元数据类名地址→托管类结构定位后，在暂停的原版55找到22个候选对象，1秒采样正常退出。记录mumu-projectile55-paused-scan.jsonl，代码/二进制SHA见reader-manifest。单次初始扫描可能含inactive或遗留对象，不是完整GC存活枚举，不能以没找到对象证明从未生成。

关键更正：055_v01_Start_0的S2 | Projectile Spawner (-137788)在Level.setup2；阻挡的S1 | Pipe (-228008)在Level.setup1，同时还有两个S1 PushBox。之前raw prefab审计同时打开互斥布局，因此“055源合法关卡会卡住”未成立。主游戏defineLevel.setupVisibility此前已经正确排除未选布局，生产无需禁用Pipe或取消纠偏。原版55只读记录的limit²为5012/6528等，无289的短路程候选，与Setup1选择一致，但直接决定性证据是源setup引用及客户端合法布局对照。

tests/projectile-inventory.spec.ts改为分别应用Setup1和2的源引用，明确禁用其他setup分支。覆盖19包×2布局，每布局900步；以path+scoped nodeID精确核对原始100处清单，不靠总数凑齐。所有合法有生成器布局均多次发射并回收、姿态有限，projectile-inventory-tests.log通过。旧冲突场景结果另存projectile-inventory-raw-conflict.json，保留历史诊断；不能把raw冲突消失称为生产物理修复。

按现有源进度映射，209对应authored55 Setup2；下一步MuMu应跳209核对这个短路线，而不是继续在首轮55寻找它。当前MuMu仍为55暂停，本轮未点击/跳关/改存档。其他全100处Worker、源材质/旋转/声音、运行内存和小游戏验收仍未完成。完整目标active。


## 2026-09-09：209首页抛射物证据

上一轮合法Setup测试更正为有效进展。本轮再次进度专用备份，从55跳209，启动前后截图均明确Hard Level209/首页PLAY，皇冠皮肤与190金币等当前库存保持，未执行开始或拖动输入。当前MuMu停在209主界面（不是55暂停）。备份路径见mumu-projectile209-home-summary.json。

只读native-projectiles扫描62个候选，8秒采样。按limitSquared约289筛选出两个短路线槽（13、25），start约[-.74985,.50003,279.13763]、end约[7.75011,.50003,264.41516]；距离平方从.04000到289.031，各有4次active→inactive，发生回收/重用，支持合法Setup2短路线不存在此前混载的持续卡住。样本为单次扫描候选，不证明原版池总大小或所有对象完整覆盖。

更重要的新差异：以上运动与回收发生在首页、尚未开始游戏；前后首页截图以及8秒home.mp4留证。当前客户端ProjectileSpawners.plan受playing门控，Simulation.menu直接跳过world.step，故“开始前不发射”的代表测试是错误预期。需根据新原版证据修正生命周期：区分已加载关卡机关物理与玩家操控/暂停，不能简单给玩家施加启动速度，也不能只在渲染层假移动而漏掉碰撞。该修复本轮尚未实施，不把现有通过测试当作原版一致。

summary记录径向差分速度估计，50ms轮询不是逐固定步速度，不能直接作为1:1速度验收。下一步修复主页机关运行，并复测玩家静止、点击无推力、暂停/恢复及main/worker；同时确认其他生成器和Conveyor是否同生命周期。读取与录像进程已结束，客户端代码未改，完整目标active。


## 2026-09-09：首页物理运行修复

上一轮原版209首页采样为有效进展。本轮依据该证据修正客户端：main首页传menu+homeWorld，ProjectileSpawners在当前关加载后的实际物理批次即可plan，不再等待playing。暂停/文档隐藏/加载/结算的既有外层运行门仍生效，未来关不创建发射控制器。

Simulation新增homeWorld显式区分首页世界运行与旧menu冻结调用。homeWorld模式执行真实world.step及抛射物碰撞/回收；玩家改为保持当前位置的kinematic，进入操控恢复dynamic并清零线/角速度，不加启动冲量。阻止homeWorld时即便误传active/输入仍给玩家施力；暂停由host不提交step实现。首页其他已存在刚体也参与求解，Conveyor等现有物理控制随世界推进；ObjectSpawners自身发射仍保留playing门控，是否同样需提前启动待独立原版证据。不能宣称所有机关生命周期已对齐。

玩家kinematic待机是客户端实现选择，原版此阶段实际bodyType尚未采样确认；原版玩家在首页受到外部机关碰撞的反馈仍待比较。该选择确保当前已验证的玩家静止和点击无推力，不用渲染假移动代替抛射物碰撞。

home-world.spec.ts以无地面场景验证main/worker：首页60步玩家精确保持(0,10,0)/零速度、抛射物前进12单位；开始首步无水平推力，首拖有效。projectile-game.spec.ts更正旧“开始前不发射”的错误预期，代表实际入口首页即可多次生成/回收、换关清理；补充首页设置暂停后计数和时钟完全不变、恢复继续。home-world-tests.log9项通过（含点击/首拖/复活、暂停输入回归）；home-world-pause-tests.log两模式增强暂停检查通过；build-home-world.log构建通过。

进度与设计已更新。后续需全100处Worker、原版菜单/游戏切换时钟、其他生成器生命周期、GPU首次出现/首页CPU内存、小游戏真机。MuMu本轮未操作，仍209首页，完整目标active。


## 2026-09-09：抛射物全量Worker与draw call

上一轮首页门控修复为有效进展。本轮新增projectile-worker-inventory.spec.ts，19包×Setup1/2共38布局，分别main与Worker执行900固定步，每批4步，相同LCG种子2468控制发射角速度。逐秒比较完整stats、活跃实例源ID/位置/裁切、玩家位置，两模式精确一致；以path+源节点ID核对全部100处。所有有生成器的合法布局均多次发射、发生回收且姿态有限。测试46.7秒通过，原始数据projectile-worker-inventory.json、摘要projectile-worker-summary.json。

单批4步计时包含Simulation.step内部处理；各布局median main 0–.20ms、worker 0–.40ms，最大布局p95 main .80ms、worker1.20ms。0是时钟分辨率下的量化结果，不是零成本。wallMs含消息/轮询等待，不能当作物理耗时；顺序测试与JIT/线程调度均有影响，不能宣称Worker更快或真机60FPS。测试为隔离无GPU场景，15秒逻辑时间不能证明无限期池稳定。

新增projectile-render-cost.spec.ts对138_v01_Mid_0 Setup1运行15秒后隔离渲染：20发射器共300发、220回收、80活动，每发射器5槽（总100槽）。所有活动模型纳入256px正交相机、无阴影，仅抛射物即160 draw calls、143360 triangles。GPU计数1 geometry、2 textures、4 programs；dispose/releaseUnused后geometry与texture均0。该检查只证明这一场景资源释放及渲染提交，没包含关卡/UI/环境，更不是原版机位或小游戏帧率。

这提供下一步优先级：源模型/贴图共享不足以控制draw call，需对抛射物建立保持独立位置、双材质、裁切平面/投影状态的实例化批次；不能删球、减发射频率或改轨迹来通过性能指标。先做像素与裁切/投影一致性测试，再接入main。测试日志projectile-render-cost-tests.log通过；类型检查projectile-cost-typecheck.log通过。本轮生产代码未改，MuMu未操作仍209首页，完整目标active。


## 2026-09-09：实例化抛射物

上一轮全量Worker与160calls基线为有效进展。本轮新增runtime/ProjectileBatch和game/ProjectileBatches并接入ProjectileSpawners.plan/sync：按源geometry、main/led双材质及castShadow分组，实例属性传世界裁切平面，instanceMatrix传世界姿态。保持源反光shader前置hook，裁切时分到不投影组；完整球进入投影组。池原对象仍供独立物理/裁切状态与坐标，隐藏其原Mesh，只批量提交渲染。每组容量按2次幂增长，空组count=0隐藏，换关释放batch geometry/material/instance buffers。

ProjectileBatch克隆每组geometry以拥有独立实例平面属性，共享源贴图。新建或扩容可能产生CPU/GPU分配，尚未做首页首次shader预热。分组覆盖当前关相同模型，不按空间分区，可能减少逐对象视锥裁剪收益；真实机位GPU三角形/耗时仍须验证，不能只以draw call少宣称真机更快。

projectile-batch.spec.ts用12个真实源模型，包含非均匀缩放、不同旋转、入口/出口裁切、反光和方向光阴影/接收地面，512px前后对照：33→7calls，像素RMSE .007873（0–255尺度）、20通道有差异、最大4。before/after PNG已实际查看，形态和阴影一致。初次TypeScript slots隐式any报错已显式修正。该对照验证优化前后客户端一致，不是APK shader逐像素一致。

接入后138_v01_Mid_0 Setup1在15秒同一采样点仍300发、220回收、80活动、143360triangles，隔离draw calls从160降到2（当前采样所有可见实例同投影组；两投影状态并存时会增加组数，阴影pass另计）。旧基线存projectile-render-cost-before-batching.json，新结果projectile-render-cost.json；GPU已上传geometry1/texture2，销毁并releaseUnused后均0。没有删球、降低频率或改运动路径。

projectile-batching-integrated-tests.log4项通过：优化前后像素、main/worker实际首页发射/暂停/恢复/换关、密集渲染与释放。build-projectile-batching-integrated.log通过。全量38布局Worker正在复核，完成结果另记。下一步实际机位视锥/峰值三角形、首页扩容首帧与长时内存、原版外观和小游戏GPU实测。MuMu未操作仍209首页，完整目标active。

## 连续切关门体重复
旧终点门与新起点门只错开0.5单位，导致道路/护栏叠面。旧Physics dispose后按SceneInstance退场旧终点门（包含合批网格和碰撞条目），再创建新起点门；保留旧道路及新关场景身份。
- 门体重叠最终验证：5项通过（20.3秒），含连续1→7关场景身份/落点/驻留/旧门退场及main/worker结束门事件；构建通过。已查看evidence/gate-overlap-level6.png，修复后截图护栏不再有重复立柱/交错面（机位与用户截图不同，未作为原版像素对齐证据）。

- 2026-09-09 内存诊断：旧内置标签约1.6GB，刷新不恢复；同浏览器新标签同第6关45.8MiB，关闭旧标签后46.5MiB。已替换旧标签缓解，根因保留链未定位。两遍1→8分别无强制GC/强制GC诊断2项通过；补used/allocated/limit测量口径，构建通过。详见MEMORY_RETENTION_AUDIT.md，长期/小游戏验收未完成。

- 2026-09-09 内存生命周期：main/worker各16轮真实坠落、结算、6→7接管及重载6，全程无强制GC；2项通过（3.3分钟）。主isolate堆分别28.34–49.90/24.64–51.99MiB，纹理28/几何57稳定，Worker模式始终1个。未复现旧标签1.6GB，保留链仍待定位；约100秒/模式不等于长期或小游戏验收。证据与范围见MEMORY_RETENTION_AUDIT.md。

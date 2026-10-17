> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-07-tamaweb-native-ts-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Tamaweb 本地化与原生 TypeScript 移植阶段复盘

此文记录进行中的工程，不代表完整一比一移植通过验收。

## 输入与交付口径

来源为 AutoSam/Tamaweb 1.14.5.1，自定义 JavaScript、DOM 与 Canvas 引擎。原始快照、commit、归档与逐文件哈希保存在 `myprojects/tamaweb/input` 和 `sourceConfigs/workflow/source.lock.json`。图片、音频、原始许可证均保留，静态资源门禁为 847 个运行时引用无缺失。

本地化对照位于 `webprojects`，最终 Cocos Creator 3.8.8 工程位于 `/Users/jiaojian/Documents/tamagotchi/client/tamagotchi`。通过 MCP 创建场景和绑定脚本，禁止直接写 scene、prefab、anim、meta。

WebView 对照不能充当原生完成证明。最终逻辑须按模块重构为严格 TypeScript；已验证单元只能声明其实际测试范围。

## 已验证进展

- 原版离线副本的建档和自动孵化。
- Cocos 原生中文建档、孵化及建档状态刷新恢复；中英切换。
- 方舟像素字库固定版本，TTF 原生导入；实际使用字符无缺字。
- 随机数、孵化状态边界、时钟和 i18n 基础行为对照测试。
- 宠物数值系统已拆为严格 TypeScript，1080 组场景 × 8 次调用与原版对照通过；完整控制器及离线时序尚未集成。
- 固定 seed/时间的校准场景经 MCP 创建；裂蛋画面已在指定地址验证，正式场景已恢复普通存档模式。
- 原生竖屏 Web Mobile 构建成功，初始场景为 TamawebNative；构建运行时补充截图已归档。
- 候选差异工具检测文件与 JavaScript 符号变化，输出模块清单和单元过期清单；空变更与单规则变更用例已运行。

## 本轮故障与可复用处理

1. 大 JSON 文件复制未完成时可能被资源监听器提前导入。MCP 导入返回后检查 importer 状态，必要时 reimport；不能把返回成功等同于运行时可加载。
2. Cocos Label 默认 Overflow.NONE 会在修改字符串和字体时改变尺寸。先设置排版策略，再设置字体与字符串，最后确定内容尺寸。
3. EditBox 的 TEXT_LABEL、PLACEHOLDER_LABEL 必须预先制作并在 Prefab 绑定，避免依赖运行时自动生成标签。绑定像素字体，按输入框布局设置左上锚点；Creator 3.8.8 的 backgroundImage 是 SpriteFrame。
4. SpriteFrame 切片必须同时设置 rect、originalSize、offset。幼体帧为 16 像素，不能统一使用成年角色 32 像素规格。
5. 原版 CSS 在透明蛋壳纹理下面有不透明奶油色底层。原生只放 PNG 会产生缺口，必须复现底色和蒙版。
6. Native 预览更新需要确认新脚本已经导入；遇到旧画面经 MCP reimport 后刷新，不能仅凭源码已保存就认定修复生效。
7. 本机效果验收入口固定为 `http://localhost:7456/`。记录实际场景、视口、语言、输入步骤与随机/时间条件。

## 更新流程

用户新增要求已落实到工作区 AGENTS.md、PROJECT_CONSTRAINTS.md、CURRENT_STATUS.md：禁止运行时生成界面，按职责使用原生组件。首段已改为四个可编辑 Prefab；主界面、起名、等待提示、点击特效可分别维护。ScrollView、ProgressBar、流式 Layout 仍随尚未移植的页面待办，不放空控件假充完成。

Prefab 制作中发现 MCP builder 的自定义类名与部分属性序列化不正确，导致重复脚本、空字体、默认按钮缩放。修复方式为 Prefab 编辑模式下 mount_script，使用实际返回的类型绑定，再通过 component.set_property 落实属性、保存并重开。不要直接修补序列化 JSON。父 Prefab 的制作还必须检查嵌套关联，不能把展开副本误当关联实例。

新增 verify_prefabs.mjs，并纳入 verify_native.mjs。除了静态结构，已在指定预览验证中英文输入、提交、语言切换、等待弹窗与点击特效；最新记录为 logs/calibration/prefab-validation.json。构建切换场景还发现子节点先销毁的问题，事件移除与自有精灵帧释放增加有效性检查后重新构建通过。保留两场景且新构建排除了已删除的 WebView 场景。

独立候选快照 → 逐文件哈希与符号差异 → 受影响模块/单元清单 → 候选文本提取 → 原生模块改造 → 严格类型、行为、资源、字体、存档及 UI 校准 → 归档证据 → 接收基线。候选对比不会自动提升版本；已有审阅目录不得覆盖。

工程内权威流程为 `myprojects/tamaweb/sourceConfigs/workflow/更新与重新移植流程.md`，机器清单为 migration.json，可读清单由脚本生成。源锁、字体锁、布局参数和验证地址独立维护。

## 仍需完成

完整宠物状态与成长、喂食清洁睡眠、活动小游戏、世界、菜单、音频、旧存档兼容和全量中文翻译均尚待移植。当前只有首批 30 个原生文本键完成中英配置；首轮完整候选 857 条待处理。不得将首屏或基础单元通过标记为整个游戏一比一完成。

## 新增阶段：先按 URL 还原 UI 和数据

用户新增 C13：用 URL 切不同界面，先还原各页 UI 和数据，复杂逻辑以后逐步做。已沉淀进工程 AGENTS.md、PROJECT_CONSTRAINTS.md 和 CURRENT_STATUS.md。页面目录独立维护 UI、数据、玩法和视觉状态；不能把固定样例数据显示当成完整业务接入。

新增 MainMenu、InformationMenu、StatsPanel 三个关联 Prefab，共七个。原生 ScrollView/ScrollBar 管理滚动，ProgressBar 接七项数值，Layout 管理网格、列表和技能说明；字体图标保留原版 Font Awesome。首批八个 URL 支持中英文和四组固定样例，不读写玩家存档，刷新恢复同一状态。

本轮遇到两项真实组件问题：Label 设置字体/字号/overflow 后覆盖了设计宽度，导致标题、金币断行；应最后设置 UITransform 尺寸。Layout.type 设置会将 resizeMode 重置为 NONE，MCP 批量属性的设置顺序因此导致长内容无法滚到底；应先设置 type，再单独设 CONTAINER，并检查序列化真实值与运行滚动范围。技能长文案采用 Label RESIZE_HEIGHT + Layout，不固定一块高度适配所有语言。

CSS repeating-linear-gradient 的周期是首尾色标之差。原版进度条首个色标 5px、末尾 10px，周期为 5px，不能误作从 0 开始的 10px；已修正生成纹理并保留源图哈希。图标黑色描边、未达到的灰星和三项技能照料评级提示已制作；活动星色相、阴影、词间距、菜单动画等仍待严格校准。

更新检查新增 page-worklist.json，按来源文件保守关联受影响页面，再看符号差异；输出中英四组样例的重新校准 URL。合成 App.js 变更验证返回 21 页面、64 URL，未变输入返回零页面，原版基线哈希保持不变。严格 TS、64 组路由数据测试和原生组件门禁通过，并在 localhost:7456 实际检查菜单、数值、滚动和实体按钮返回链路；本阶段尚无全页像素差异通过结论。

## 档案页阶段：Prefab、数据与确定性说明 URL

新增 ProfilePanel、TraitIcon、InfoPopup 三个关联 Prefab，共十个。档案有固定样例与 48 个说明状态；9 个页面入口支持 72 组中英文数据。源定义经 AST 提取，保留 28 个性格与 99 个食物条目，重复精灵编号按原版第一次匹配。出生时间是展示快照；玩法状态与实时出生计时仍未接入。

原版档案星座以出生日期的日数循环选择，不是真实星座日期区间；源版本的行为应保留并注明。未知性格和空偏好先明确为展示空态，不能推断为玩法完成。正常模式当前档案也使用展示样例。

实际排版发现 Cocos TTF RESIZE_HEIGHT 包含 0.26 行基线留白，直接用于 CSS 卡片高度会逐行累计空白。保留原生 Label 测量后确定 CSS 行盒高度，再由 Layout 排版，英文四卡片高度接近原版 DOM 实测；没有据此宣称严格像素验收。姓名/性别与天使图标行使用水平 Layout，消除重叠。九宫切片边距由编辑器中的 PixelSprite 属性保存，运行时仅产生自有 SpriteFrame，不创建节点或组件。

MCP move 的 siblingIndex 在本机未生效，reorder 曾把节点移到 Prefab 场景根；应检查真实父级与顺序，必要时用已验证的 move 顺序重排，保存后只读检查。重挂载还应归零旧纵坐标。新增门禁防止字段顺序和旧坐标回归。Grid 精确宽度在浮点比较时可能让最后一个图标换行，校准时预留极小余量并核对实际行数。

字体门禁发现 即/奖/悠/热 四字缺失，本阶段换用含义相同且字库覆盖的译法；不要静默依赖系统回退。28 项性格说明均进入配置，非样例食物名称暂回退原版英文。

更新工具读取 page-catalog 的 detailRoutes。verify_page_update.mjs 在独立候选快照验证：上游 App.js 改动产生 21 页及 120 个重校准 URL；不改基线、锁或验收状态。本阶段原生类型、数据、字体与组件门禁通过，并在 localhost:7456 真实验证；详见 logs/calibration/profile-validation.json。仍需同状态原版 URL 适配、成对截图、裁剪/焦点/阴影细节和后续页面，不能把样例档案当作完整游戏。

## 原版同参数对照阶段

已建立 calibration.html + ReferenceBridge.ts，复用原生纯 TS 解析器、随机源、展示字段及同一份配置。它只用于已锁定原版的 DOM/Canvas 对照，Cocos 仍使用关联 Prefab。固定视口默认 720×1280；原生实际验证始终使用 localhost:7456。

首次对照发现，冻结 App.onFrameUpdate 不足以固定状态：Drawer.draw 还会调用 Pet.onLateDraw → think → statsManager，满值被扣为 99.9855，空值还会锁住菜单。必须冻结绘制后的业务回调并检查实际绑定数值，等待原版加载层、字体和图片结束后才发出 Ready。

浏览器窗口尺寸与游戏内部视口、设备像素比不是同一个量。不同缩放的整窗截图不能直接相减；窄屏桌面可能有系统滚动条，而移动浏览器可能覆盖显示。保留原版 CSS，列为明确差异，不能隐藏滚动条或清除 word-spacing 来凑相似画面。

Cocos 在预览尺寸切换时应同步更新已有组件：先 Canvas Widget.updateAlignment，再用公开的 alignCanvasWithScreen 重新对齐相机，随后重排 TamaView、ScrollView 与卡片 Layout。否则相机早于 Widget 居中，会出现底部留白。该修正已通过 720×1280 / 393×852 往返切换验证。

新增 verify_reference.mjs、reference_build.json、原版与原生逐页校准.md；启动注入门禁覆盖 120 组参数和 958 个锁定文件，浏览器结果独立记录。更新工作清单增加 120 对原生与原版参考 URL，参考仍指向已接收基线；候选必须独立准备，不自动推进锁或验收状态。

本轮修正起名标题的英文冒号及中文档案中拉丁姓名的大写规则；背景星光、系统滚动条、词间距、奖励徽标、性别设置对应标题及图标裁剪等仍未严格验收。资料与说明数据显示并不等于完整玩法接入。

## C14：编辑器里的 Prefab 也必须无重叠

用户截图暴露了真实缺陷：ProfilePanel 的 Traits 外框高 200，内部 Body 已约 472；标题又在分组边界之外绝对定位。此前只检查运行态补算后的排版，遗漏了编辑器中可见的重叠。C14 已沉淀为“不重叠、不贴太近”，且优先于原版中拥挤的排法。

通过 MCP 将四张档案卡与说明弹窗改为同节点九宫格 Sprite + Layout(CONTAINER)，Body 作为唯一排版子节点；删除旧背景子节点，避免背景被 Layout 计入内容。四个特征分组使用垂直 Layout，标题占真实高度。标题/内容、分组、卡片间距分别为 8.1/16.2/20.25 设计单位。容器变高后由 ScrollView 滚动，不缩小字号。

MCP 新增 Sprite/Layout 可能重置 UITransform 的宽度（本轮曾变成 40），所以最终尺寸必须最后绑定并读取保存资产核对。编辑器 Label 自动高度与运行态 CSS 行盒测量不同，两边都要做边界检查，不能只看类型检查成功。新增 verify_profile_layout.mjs 检查卡片宽度、内容包含与最小间距，并以原错误尺寸和零间距做反例。

实际 localhost:7456 验证中英 8 组样例、每组 13 个 Layout 均无记录的包含/间距问题；检查长姓名、滚动、多图标换行和说明弹窗。分辨率下拉框虽选 720×1280，宿主限制下实际 frame 为 720×1088，证据必须记录实际值。见 profile-spacing-validation.json。场景/Prefab 均经 MCP，仍只保留原有两个场景和十个 Prefab。家族树数据/参考分支与蓝图仅为待制作内容，原生 URL 尚未开放。

## 2026-09-07 追加：数值行与原生组件边界

用户再次指出数值页排版拥挤，原因是行高仅为进度条的40.5，标题悬在行外。通过MCP将八个金币/状态/技能行改为垂直Layout(CONTAINER)，标题/值间距12.15、行间24.3、图标/内容列间距16.2；金币标题/金额左边缘一致。照料星星及技能图例也采用Layout，Tabs的背景改为同节点九宫格Sprite，Content随当前页签增高。

图标应由Widget对齐整行中心，但不能作为Meter的孩子：Meter的Mask会把列外图标裁掉。最终图标放在没有Mask的Title下，Widget.target指向所属行。MCP移动节点或设置局部坐标可能反写Widget间距，必须最后设置verticalCenter=0，并检查保存后的真实坐标。隐藏页签需在编辑器激活一次完成布局再保存回默认页。

独立StatsPanel根节点原为DEFAULT层，造成Prefab编辑界面空白，而嵌入正式Canvas时仍可渲染。改为UI_2D后重新进入Prefab即可显示；反复调整编辑器相机不能解决层级类型错误。添加Sprite会把UITransform宽度改为40，仍需最后恢复卡片宽度并运行资产门禁。

verify_stats_layout.mjs检查14个保存后Layout、8个图标列、标题栏焦点/箭头/标题间距，旧40.5高行作为反例被拒绝。实际localhost:7456完成中英×四数据×两页16组（720×1088）、一次393×852及四组393×850满值，滚动底部、手机语言切换和设备键焦点均检查。证据在stats-spacing-validation.json，编辑器真实截图stats-editor-spacing.png / stats-editor-skills-spacing.png。一次内置浏览器标签崩溃后，验证函数还持有旧Tab对象；新检查函数显式传入新Tab后恢复。崩溃原因尚未诊断。

家族树在此阶段前已用MCP建立三个关联Prefab并接入family-tree路由、FamilyData/FamilyPanel及ghost Effect；此前“未制作”的记录已过期。源handler/数据门禁和128对更新URL通过，家族树最新全套浏览器校准仍待收尾。全游严格1:1尚未通过。


## 2026-09-07 追加：关联成员容器与证据有效期

家族成员节点宽72.9而姓名宽137.7，原生 Layout 排列的是窄容器，文字会伸入同伴区域。通过 MCP 将成员列扩为137.7、双列网格宽291.65、列间16.2，并同步祖先行与当前成员的外层容器。装饰连接线不作为 Grid 的额外成员；光环和阴影计入头像占位，同伴共用头像和姓名高度，避免一侧有幽灵装饰时姓名起点不同。独立 Prefab 根节点使用 UI_2D，保证编辑器可见。

关联 Prefab 在序列化文件里只有引用与覆盖项，不能把普通 JSON 遍历缺失的孩子误当成没有内容。新增 verify_family_layout.mjs 同时检查基底尺寸和 MCP 展开的保存快照，以三个资产 SHA256 约束证据有效期。MCP 快照整数尺寸仅用1.1单位的组合舍入容差；运行态仍须检查实际浮点边界。16个展开布局、5个成员区域和2对同伴通过，旧容器尺寸的反例被拒绝。

中文四组浏览器检查之后又修改成对姓名对齐，因此旧通过记录不能代表最终代码。随后 Mac 锁屏，CUA 无法继续；把该限制写入 family-validation.json 和交接文档，清单保持 implemented/pending。历史编辑器 PNG 也早于第二代编号修正，明确标为旧图。需要人工解锁后复核，不绕过锁屏，也不把静态门禁当成视觉验收。严格 TS/原生门禁及128对更新 URL 检查通过，上游基线保持不变。


## 收藏数据：打开页面本身会改变显示集合

原版收藏不是简单读取历史列表：open_character_collection 先把当前角色写入 ch_unl 事件，再遍历384个ALL_PLAYABLE_CHARACTERS。因此空历史打开后是1/384。CollectionData用不变显示集合模拟该结果，URL样例不写真实历史；AST提取保留原始顺序及16/24/32首帧尺寸。五组原版handler对照覆盖1920个格子，原生配置镜像一致；这只验证模型，Prefab、URL与锁定滤镜还未接入。

更新依赖不能只写App.js。角色定义表变更即使没有修改handler也会改变计数和排列。inspect_update新增可声明的unit.dependencies与逐项sourceChanges；模拟只改CharacterDefinitions后，collection-display-model变为stale，主App.js前后哈希仍相同。尚未开放的收藏页不生成URL。继续保持源锁、数据镜像、页面状态和模型验收范围分开记录。

本回合Mac仍锁屏，CUA无法补家族预览；完成了独立数据工作，未绕过锁屏，也未把数据对照结果冒充视觉验收。


## 2026-09-07 解锁后复核与收藏 Prefab

解锁后，家族树最后的共同头像/姓名占位已完成 8 中英手机样例 + 3 重复/大画布复核，补齐冻结/定时空提示、长家谱滚动和设备返回，清除旧锁屏阻塞；接入收藏后又做中文 mixed 回归。仍仅接受 C14，严格像素与真实家谱持久化未完成。

收藏页新增 Item/Row/Panel 三个 MCP 关联 Prefab，严格 TS 绑定 384 角色，保存四行，首次打开通过 instantiate 既有 Row 增加到 96 行。角色按源表顺序，stage 的首格为16/24/32，锁定为 grayscale(1) contrast(.01)，保留 alpha。普通格子不是按钮。原版右下角浮动提示在手机覆盖第四列头像，按用户 C14 改用独立 14.175 ScrollBar 区域，行间10.125/列间16.875，明确记录适配差异。

初次 prefab.create 虽成功却丢失自定义 CID、资产和字体绑定。稳定做法是 native-only 骨架首次创建后，进入 Prefab 编辑模式挂载脚本、绑定字体/素材/引用、保存退出，再重开；不可直接写序列化文件。设置 Layout.type 后另设 resizeMode，最后修正 UITransform，根和孩子明确 UI_2D。删除临时制作节点后还要保存正式场景，否则内存已删除而磁盘仍残留坏引用。新类型静态门禁发现这些问题，比仅检查 MCP 成功可靠。

TypeScript reimport 有一次未让预览使用最新模块；MCP asset.refresh 后编译更新，必须通过真实 UI layout 新字段确认，不能把新时间戳误当作新代码。中文源参考按钮固定 Pixel 覆盖了 html 字体，桥接增加 button 字体覆盖后 computed font 为 ReferenceArk。源基线不变；旧中文按钮截图不能充当当前字体像素证据。

最终收藏8组393×852 +1组720×1088，在本机浏览器比较3456个格子的顺序/源帧/首格/锁定/计数；5个保存后布局16格静态边界通过。滚动末尾、返回、重进、语言切换和设备键检查均有范围记录。136对更新URL、角色表依赖变更使模型stale的门禁通过。当前16 Prefab、41 CSS纹理，继续成就等UI/数据；像素、性能、持久化与完整玩法仍未完成。


## 2026-09-07 成就 UI、奖励快照与更新依赖

新增3个关联Prefab和严格TS控制器；24项成就、4样例、74项成就/奖励文案。源模型对照1992项列表、72门槛、24奖励、16种子食品选择；三技能记忆保留。奖励shuffle对99食品每项消耗随机数，取首个cookableOnly，19种均补中英。田园实际10/提示5是源差异，不能擅改。源参考使用独立奖励随机流，避免启动随机调用影响配对。

8组手机列表比较192实际DOM记录，设备逐一打开48个中英说明；说明Card与两个纵向按钮共享滚动。保存资产18组Layout/39子项和5资产指纹通过。实际领取发现食品键未翻译、图标顺序错误，修正后再次对照中英提示。信息页新增徽标使原来固定行高滚动公式失效，改用真实行底并留8.1；焦点与标题对齐。滚动动画中即时日志并非最终位置，稍后无动作轻点取稳定日志核对。

MCP move.siblingIndex返回成功却未改变同父顺序；必须保存退出重开读实际树。将需要位于末尾的节点移出再移回可得到明确顺序。嵌套Prefab另会保留Layout生成的位置覆盖，造成Close横偏114.4125；用MCP revert清除实例覆盖后正常。静态门禁应包含最终实例父级资产哈希，不能只验独立子Prefab。

角色286误删、287/290误覆盖曾阻碍预览，用户确认是误操作并授权还原；全部通过MCP从锁定源恢复。资源完整性新增只读PNG哈希/meta存在检查，共393图、384收藏引用。工具超时仍可能完成导入，先查实际状态再重试。

当前19Prefab、43CSS图、12页194对更新URL；Definitions-only与Utils-only均使成就模型stale并输出58对成就URL。UI/data先完成、逻辑deferred、visual pending保持分开；仍有字体/阴影/星标/数量字号差异及大画布/性能未验收。预览仍预载所有角色，部分冷启动30–55秒，后续按页优化。


## 昵称页与角色恢复（2026-09-07）

用户确认图片误删并授权恢复：通过MCP还原，393原图哈希/384收藏引用通过。昵称页新增RenamePanel、RenameData/Panel TS、8对URL；总20Prefab、45CSS图、13入口202对更新URL。目标仍进行中。

源displayPrompt用回调的falsy结果关闭窗口，所以昵称空输入会关闭，不能只看handler返回false推断保留。源没有Back按钮，设备右键不会关闭。UTF-16 slice32、五态性别即时变化、空格合法与源实际模型对照40/36/8检查通过。

Cocos原生EditBox会自动重排子Label的2单位边距，采用外层九宫格Surface、内层实际EditBox留白。内层Sprite alpha=0会连带隐藏失焦文字，应保持255并禁用背景渲染；此错误由编辑器截图发现，修正后编辑器与本机失焦文字可见。Gender按钮从源绝对定位改为有12.15间距的横排，保留设备索引顺序。所有节点通过MCP制作。

实际中英四样例共8组，44组布局包含/间距检查通过；前4组在背景渲染修正前且几何不变，后4组及混合聚焦/失焦、首尾空格改名、五态图标、语言保留草稿、2秒返回和改后档案在最终版本验证。默认保存5布局/8子项，独立和关联MCP50节点。严格像素、家族改后成员、宽屏与IME仍待补，不把有限通过描述成1:1。

资源路径 fonts/FASolid 不存在导致启动失败，改为实际 fonts/FontAwesomeSolid，经MCP reimport后reload取得新Ready；静态门禁现检查loadFont/loadJson字面路径。PNG库升级仅改变压缩流时，先比IHDR和解压扫描行，相同光栅保留现有字节，避免45已校准纹理产生无意义哈希变化。资产哈希与像素哈希职责分开。

证据和规格：rename_gate.json、rename_layout_gate.json、calibration/rename-validation.json、rename-editor-current.png、sourceConfigs/ui/昵称页移植规格.md；CURRENT_STATUS.md为最新交接入口。


## 2026-09-08 照料卡片、历史列表收尾与喂食草稿

截图差异先修原有Prefab：Care横排、源310度星色、说明卡/图标/分隔线、8个Label源文字阴影。中英实际预览与滚动末尾有证据；中文normal行盒与Cocos显式lineHeight仍待严格校准，不能把模型/布局通过写成1:1。历史最终8列表补齐80流/32行；独立编辑器必须先双击根聚焦，空截图不算证据。

喂食仅完成99条静态定义、76组/667行真实源函数对照及24节点独立Prefab，未接URL。默认baby禁用cook；源码cook内只有camera/harvests，不能根据语义臆造recipes入口。三种特殊payload登记原文/哈希且deferred。显示模型、UI状态与行为状态分开维护。

MCP导出后再次丢失Label字体/颜色与ScrollBar.handle。Prefab重新打开后逐一核对；handle采用component类型加节点路径绑定，UUID对象在本次未绑定成功。删除节点在引擎帧尾生效，立即create可能带入旧节点，须下一次查询确认再保存。MCP import overwrite本机仍弹覆盖窗口，超时先看真实编辑器提示；已复制普通TTF后取消旧导入并reimport，绝不直接写meta。

Ark锁定版缺药，系统回退使编辑器看似正常，实际字体门禁才揭示缺字。只从同作者Fusion Pixel同版本12px加入U+836F，所有24471原映射/24174原轮廓及字宽/行高逐项相等；派生OFL字体保留原输入、构建脚本、补字白名单和全部许可证。不得把此证明写成光栅或行盒一致。详见项目sourceConfigs/workflow/像素字体补字与更新.md。门禁23项与参考242路由通过，完整游戏仍进行中。


## 2026-09-08 字体解码与原生词间距修正

此前补字虽保留cmap/轮廓/水平度量，却漏了新增字的vmtx，浏览器整份拒绝并回退；这是此前字体已生效表述的修正。实际OTS定位最后竖排边距缺失，补齐vmtx并核对vhea，增加真实破坏表负例和浏览器FontFace就绪检查。Cocos3.8.8字体加载器失败可回调成功，nativeAsset还可能返回null，需按公开nativeUrl确定实际字体族。旧回退字体截图不作Ark排版证据。

原版英文说明5行、原生6行的差异来自CSS负词间距。保存原生RichText子类，只改变空格占位与首行图标留位，不替换英文字形、不塞固定换行。使用真实引擎方法与锁定字体字宽验证，保留渲染器替身范围。MCP/Inspector设置子类字段不会自动触发内置文本setter，增加属性变化刷新后，真实编辑器组件读数也由6行变为5行；恢复中文默认保存并退出。

25项工程门禁、242参考路由通过；但本机再次锁屏，新RichText的编辑器/7456画面仍待解锁验收。stats-css-rich-text-editor-final.json只证明实际组件尺寸与结构，不是截图。工作文档、migration和page-catalog保持视觉pending，避免把旧Label截图混入新版本通过记录。


## 2026-09-08 FoodSlider 默认草稿与脚本序列化

锁屏期间只完成独立FoodSlider默认牛奶样例：21节点、5 Button、9 Label、2 Layout，未接控制器/URL。原版slider表示翻页选物而非数值范围，不能机械对应Cocos Slider。实际源图集为24px/33列，一基编号1036；默认唯一免费牛奶禁用两箭头。默认静态间距通过不能推断长名/新标记/英文也通过。

builder初次输出默认层1073741824，必须明确所有21节点UI_2D；字体、Layout.resizeMode和按钮禁用态也要在保存后复核。更隐蔽的问题是mount_and_bind挂载的PixelSprite看似可设置属性，序列化却是类名，重开后成为MissingScript。通过node.remove_script移除实际MissingScript，node.mount_script按TS路径挂载，再用返回CID和明确spriteFrame类型绑定资源；重开后核验实际组件与保存CID。只查sourceFrame字段会漏掉该错误，通用Prefab门禁首次阻止了错误版本。

保存Prefab会自动保存来源场景，临时制作实例须通过MCP删除并再次保存场景；只看当前树没有节点不够，还要检查保存结果。最终快照重新采集后绑定11个资源指纹，不能仅更新旧快照哈希。26项工程门禁通过；24Prefab、50CSS纹理、494已翻译字符，仍只有14页面/242对可生成URL。Mac未解锁，没有新截图。后续先补照料新RichText真实视觉，再继续FoodSlider和其余喂食分支。


## 2026-09-08 解锁后的宽度回归

新RichText需真实预览才能发现剩余问题：原版当前手机滚动条没有扣除内容宽，固定14CSS像素gutter使原生正文窄了28.35设计单位。改为将3CSS像素原生ScrollBar放到4CSS像素外侧padding内，保留1CSS像素间隙并从标题下方开始，避免内容重叠；桌面保持7CSS像素独立条。8个中英样例逐行匹配、照料星数正确，连同宽屏/基础页共79流通过。独立Prefab上下部截图已取得，旧空截图替换成有效图。

预设尺寸、真实Canvas尺寸和DPR必须分别记录。本轮手机393×813、宽屏720×814，原生/参考日志DPR1.6/0.8，不能称逐像素通过。工具Console累积历史FontReady记录，取当前启动每个资产最后记录，而不是断言总数恰好3。浏览器宿主变化使原来正确的滚动条假设失效，因此更新流程要比较原版实际盒模型。C14保留的图例留白与引擎RichText尾部行盒是不同原因，后续分别校准。


## 2026-09-08：说明段落的额外尾部行高

原生RichText总高是(lineCount+0.26)×lineHeight；这段额外高度使分隔线偏下。CssRichText增加仅供纯文本段使用的useCssLineBox，并通过MCP保存于StatsPanel说明段。向父Layout提供lineCount×lineHeight，内部保留引擎高度，以锚点补偿保持字形相对顶边位置。没有改字号、字体、换行配置或C14的16.2图例间距。

当前7456中英default实测393×813，说明高129.6/189.84375，卡片高366.525/426.76875；14流通过，上部和滚动底部均实际查看。引擎回归8项包含三种锚点、开关恢复和重复刷新；保存布局及完整26工程检查通过。新MCP独立/关联快照107节点、7指纹，见stats-css-linebox-editor-layout.json及stats-css-linebox-validation.json。

当前版本的编辑器画面仍待复核：浏览器检查后Mac再次锁屏，未取得新截图。旧stats-rich-current的8样例/79流及截图属于去尾前版本，禁止替换其指纹。DPR/光栅及剩余像素差异未验收，页面visual保持pending。

## 滚动提示与宽度校准（2026-09-08）

修复范围为 StatsPanel。原先65px圆图以32px九宫格压入6.075宽，导致端部被拉成长针；手机还误留常驻白色轨道，首次进入未显示原版双下箭头。现由MCP保存独立MobileBar（6×6胶囊、边3）、桌面Bar（仅右圆角、左边0/其他14），保留原生ScrollView/ScrollBar管理长度、位置与淡出。手机轨道不渲染，滑动显示、停止后自动隐藏；首次向下滚动移除双箭头，回顶不重现，重新开页才恢复。桌面轨道改为原版半透明白底与半透明橙色左边线，避免纯白竖条。

用户随后指出页面宽度变化。对锁定原版作了真实DOM测量：720×1280宽屏，外屏192 CSS像素，内容/标题185、卡片177，固定占7像素；393×852手机为192/192/184，原版覆盖式滑块不占内容宽。换算388.8设计单位后，原生标题/卡片分别374.625/358.425和388.8/372.6，与原版一致。中英两个样例各记录ready/scrolling/settled，五项宽度及四项横坐标完全不变；手机滑块alpha为0→255→0。不能根据“CSS写7px”就推断所有平台都需要占位，也不能为消除正确的宽屏占位而偏离原版。

上轮校准曾把预览切到720宽并停留；本轮已恢复Apple iPhone 14 Pro、真实393×852、中文full顶部。今后验证结束恢复原预览预设，记录实际frame，避免把测试尺寸变化当成滑块引起的页面变化。

代码仍只更新已有原生组件，未运行时创建UI。PixelSprite新增默认-1的左切片覆盖值，仅桌面滑块设0；URL模式增加只读滚动测量日志，正常玩家模式不启用。StatsPanel保存/重开独立与关联均108节点，临时Content y620/810取图后恢复194.4；编辑器已退出回TamawebNative。CUA查看了居中的完整Prefab；MCP窗口PNG包含面板并裁掉部分左边，仅证明所见滚动条、说明与图例局部，不冒称完整页面截图。

当前26工程检查通过，后续临时偏移恢复后Stats门禁再次通过；9项当前资产指纹匹配，53张CSS派生纹理与原生镜像一致。24Prefab、14路由、242对可生成URL不变。证据为logs/calibration/stats-scroll-width-validation.json、stats-scroll-editor-layout.json及stats_layout_gate.json。旧行盒证据保留原哈希/范围，不改成当前证据。

严格像素仍pending：双箭头的CSS脉动和多偏移阴影、DPR/字体光栅、卡片阴影尚未全验；本轮不代表其他页面的滚动条都已校准，也不代表整游完成。C14留白不撤销，FoodSlider仍未接URL。


## 2026-09-08：双箭头确定相位与宽度回归

原版双箭头使用FontAwesome f103、11 CSS字号、右10/下4、八个±1/±2像素阴影，0.55秒alternate-reverse ease-in-out。参考桥原先只禁止普通元素动画，::after仍在动；现两端URL提供hintMs=0..1100（默认0），live检查实时动画。真实源采样0/137.5/275/550/825/1100；原生0/137.5/550参数一致，实际组件测试覆盖周期、冻结、重新启用和编辑器姿态。

StatsPanel通过MCP保存Scroll/Viewport/ScrollHint，Widget以Viewport为父级；Visual包含Face和8个原生Label阴影，TS只更新已有节点。独立与关联118节点，完整编辑器截图stats-hint-editor.png已查看，Content194.4且已退出正式场景。注意Widget不能可靠指向兄弟节点；组件引用应按工具的节点路径解析，不能传组件UUID假定成功。批量复制和重新排序均需检查实际树及组件，不以工具成功消息替代结构核对。

当前英文empty手机393×852和宽屏实际720×983，各ready/scrolling/settled的panel/header/viewport/content/tabs宽度及横坐标不变，手机滑块alpha0/255/0、桌面255；首次滚动后双箭头消失。结束恢复手机en/empty顶部。27工程检查、242对参考/更新检查通过，958锁定源文件未变。新证据stats-hint-phase-validation.json、stats-hint-editor-layout.json及scroll_hint_gate.json，旧证据保留旧指纹。

没有将本轮标为严格1:1：DPR1.5源正常行盒10.6667而原生名义11，桌面hint left有0.333CSS子像素差异；CSS先合成整组后乘透明度与Cocos按子节点乘透明度也须像素比较。保留C14留白，其他页面与完整玩法仍未验收。目标active，当前无锁屏阻碍。


## 2026-09-08：原生Label内合成多重阴影

8个独立Label各自乘透明度会在重叠处累积，不能代替CSS先合成后整体opacity。现CssShadowLabel继承原生Label，只在本组件的assembler更新期间临时包装其已有Canvas的fillText，依CSS逆序绘制8层阴影再绘制Face，随后一次上传。finally恢复接口，原生Label继续管理字体、材质、缓存和释放；没有新建UI/Canvas/Texture，也没有改引擎。原生UIOpacity仅应用一次。此专用组件当前限Stats双箭头的完整TTF纹理、无原生outline/shadow；不可未经校准改成CHAR缓存或泛用于多行文本。

升级Creator必须运行verify_css_shadow_label.mjs（读取当前3.8.8 Label._flushAssembler/updateRenderData和TextProcessing纹理绘制方法），检查原生flush不会因包装对象不同而反复销毁数据，接口在异常后恢复，普通Label不受影响，缩放后阴影偏移正确。单元测试检查一次上传包含8阴影+字形；浏览器rendered日志确认9次绘制和24×30纹理。MCP删除旧8个阴影节点、替换Face为原生Label子类，110节点独立/关联保存并查看完整编辑器图。

ready日志早于字体绘制，不能证明纹理已生成。新增rendered观测还发现原生ScrollView初次布局短暂闪出手机滑块。已有MobileBar现等首次SCROLLING才激活，原生ScrollBar继续掌管长度/位置/淡出。当前中文full四阶段ready/rendered/scrolling/settled的visibleAlpha0/0/255/0、宽度/x不变；英文empty初始同样隐藏。inactive节点内部alpha不等于可见透明度。

28项工程检查通过。证据stats-shadow-composite-validation.json、stats-shadow-composite-editor-layout.json、stats-shadow-composite-editor.png、css_shadow_label_gate.json。旧118节点/旧哈希仅历史。DPR行盒、桌面子像素取整及光栅像素仍pending；不直接用DPR猜浏览器CSS缩放取整公式。来源/参考桥未修改。全游目标active，FoodSlider未接URL及其他页面仍需推进。

## 2026-09-08：喂食分支UI接入阶段

目标是将99条源显示定义接入真实原生Prefab、固定URL与原版桥，同时保留游戏逻辑后续做的顺序。当前28Prefab/15路由/494对URL，喂食252对可生成组合；代表性手机画面已对照，全部严格像素尚未通过。

实际发现：将Grid改成Horizontal Layout并不会清掉子节点原有y偏移，导致图标/文字贴顶；应检查保存和实际预览中的包含关系并归零横排中心。原版absolute心形不能误改为流式行，否则卡片高度改变；应读取源CSS再安排Prefab子节点。复制的空弹窗可能保留inactive，运行截图正确仍不能证明独立编辑器可看。

动作全部通过MCP保存序列化资产，Controller只更新已有组件并实例化行Prefab。源参数/样例共享解析，食品名/类别/索引详情一并进入更新工作单；生成器改为由目录计算数量，避免旧242文案滞留。父Prefab新增关联后，旧截图不换新哈希冒充证据；重新取得关联MCP快照，同时保留未改独立页面的历史范围。

最终28项native检查、494参考注入及494更新URL通过；596译文字形/OTS通过，新字白名单药旋蘑酱餐保留原度量。视觉记录feeding-ui-validation.json与feeding-final-editor-layout.json明确分阶段。剩余英文断词/星标光栅/牛奶细边/阴影/滚动动画/桌面尺寸及吃食烹饪逻辑，均未标verified。

## 2026-09-08 食品文字与采样校准补充

紧密sprite sheet即使POINT采样、PNG未变，边缘仍可能显示邻格细线。先确认实际rect、texture、atlas及原PNG边列，再用可选材质限定当前格像素中心；不可裁小图块或偷偷修PNG掩盖。此例仅FoodSlider/FoodIndexRow绑定，其他用途保持原样。

RichText移植CSS词间距须同时验证行尾空格的居中权重、长词换行与字体回退；只比行数会漏掉横向偏移。索引外高应拆开内容、padding和不等宽上下border，此例42→38CSS且不缩小文字。用实际Cocos引擎方法+锁定字宽测试，并复查共享Stats页面和Prefab编辑器。证据见tamaweb/logs/calibration/feeding-text-validation.json；全页面像素仍未完成，切勿从代表性样例扩展验收范围。

## 2026-09-08 可复用滚动提示与滑块绑定

新增MCP制作的ScrollHint.prefab（3节点），喂食菜单/索引/烹饪菜单在Scroll/Viewport下保留嵌套关联。FeedingMenu27、FoodIndex21、CookingMenu21、FoodIndexRow6、正式TamaView展开688节点；工程29Prefab。提示使用Widget定位、原生Label子类绘制8阴影、UIOpacity整体透明度及源0.55秒往返动画。hintMs=0/550真实对照；首次向下滚动后隐藏，重新打开重置，短列表不显示。

发现三个列表ScrollView.verticalScrollBar和ScrollBar.scrollView均为空，手工显隐虽然能出现滑块，但长度一直170、位置不变。已通过MCP显式双向绑定，保存并重开确认；门禁拒绝空绑定。手机药品索引滑块高106.8866、滚动后y55.1134→34；停止后淡出，正文388.8不变。桌面实际720×922（不是预设720×1280），固定7CSS槽、正文374.625，滑块高128.2639、y66.1361→40.8，停止后保持显示。原版该尺寸clientWidth185/offsetWidth192，内容高582CSS。

为遵循C14，索引右padding44.55，Body宽287.55/x=-2.025，按保存的Layout参数计算运行宽度；含文字和箭头阴影仍留9.61875间距。页面/视口宽度不随提示改变，但部分省略号比原版提前，此为明确适配差异。门禁同时检查保存的Body位置和宽度，防止只改padding留下旧坐标。

短牛奶索引与两行烹饪菜单在393×852均不显示提示/滑块。回到用户stats-skills/en/empty再检查ready/rendered/scrolling/settled，正文388.8、Tabs372.6均不变，滑块可见alpha0/0/255/0。该项为增量复核，不将先前Stats证据或全252路由都说成新验收。

新证据feeding-scroll-hint-validation.json、feeding-scroll-hint-editor-layout.json；实际查看scroll-hint-prefab-editor.png与feeding-menu-scroll-hint-editor.png。独立及关联Prefab均经MCP重开快照，指纹为本轮版本，旧证据不换哈希。当前28项native检查及追加绑定/留白断言通过。严格视觉、其余状态、长卡滚动、心形角标、卡片阴影及吃食/相机/收获/存档仍待后续。

## 2026-09-08 当前用户页宽度复核与在途交接

用户原标签19已可用，直接在同393×852/en/empty技能页比较显隐，四阶段正文388.8、卡片372.6、横坐标均不变；原版list192不变。证据myprojects/tamaweb/logs/calibration/stats-scroll-current-tab-verification.json。不要只比较不同设备预设的截图，也不要用滑块内部alpha代替activeInHierarchy后的实际可见alpha。此次未再次修改Stats实现。

中断的喂食角标/三键/提示碰撞代码与MCP资产保留，并单独写入待验收记录：FoodIndexRow7节点、FoodSlider28节点；29项native通过，但真实三键序列和最后碰撞适配尚未验收。移植清单新增in_progress项，不把纯函数通过标成完整UI通过。

## 2026-09-08 喂食角标、三键与滑动内容

FoodIndexRow7节点角标已在英文full和中文full查看；第四行偏好与提示不再重叠，root提示Y=-114.4125，正文388.8不变。源自身存在该重叠，按C14上移60.75；角标文本含阴影间距8.1。原版与原生三键实际检查了父菜单焦点保留、索引Header首项、禁用按钮和四项循环；动画接入后再检查延迟换项及右键返回。

FoodSlider现30节点，新增Card/Clip/Item及原生Mask/Layout。只移动内部内容，外框原位；原版100ms滑出、150ms换项、100ms滑入，左右±200CSS（405设计单位），保留连续点击的排队和索引直接选项语义。37步测试执行锁定displaySlider原函数和CSS关键帧；实际7456两方向中间帧裁剪及最终归零已查看。原版校准器的通用冻结此前连交互滑动也禁用，现仅排除.slider-item，初始固定URL仍无翻页动画。

食品配置从强制换行改为自然空格；英文汤由4行还原3行，SOUP与(X3)同排。Caption保存keepWordGroups=true，中文数量括号整组换行，牛奶保持两行，避免右括号独占一行。11个原生RichText引擎案例通过，Ark有限数量用真实度量，∞为浏览器回退字形且已在原版和7456实际查看，不冒称Ark内置字形。

当前30项native、494原版注入/958文件锁/零存档访问通过。MCP保存并重开FoodSlider30、FoodIndexRow7、正式TamaView695节点；新编辑器图food-slider-word-groups-editor.png有效，前一张food-slider-motion-final-editor.png含已修复的孤立括号，属于失败过程证据。最新证据feeding-badge-focus-validation.json和feeding-badge-focus-editor-layout.json分别限定各版本测试范围，旧图不换哈希。

喂食页面仍in_progress/visual pending：全252状态、桌面交互动画、焦点/爱心脉动、卡片阴影、字体光栅及玩法/音效/存档未完成。代表UI与操作已可继续迭代；下一步进入page-catalog仍pending的bath/care等菜单UI和固定数据，保留本页差异清单，不反复重做Stats宽度测试。



2026-09-08 喂食更新门禁收尾：新增独立HTML变更用例发现“单元已stale，但页面未生成复校准URL”。根因是page-catalog缺少index.html来源依赖；补齐后494对全目录URL与252对喂食URL检查通过。CSS、PixelColeco和FontAwesome各自变更也验证新单元失效。后续更新验证应同时检查单元状态与可执行页面清单，不能只检查其中一层。证据：logs/page_update_gate.json。


## 2026-09-08 线上发布身份与可读源码同步

用户要求更新线上原版。本地main提交未变，但线上19文件字节不同；进一步验证gh-pages为同一源提交的自动压缩子提交。958非隐藏源Git blob与本地字节一致，43线上文本文件与发布树一致，30离线JS保留已审计补丁且匹配。没有新的游戏源码变化。新增check_online_update、online-source/online-release锁、migration.upstreamSync及give_food_once独立pending项，避免压缩差异产生伪移植任务。后续候选必须取线上部署的源父提交，不能默认main即线上版本；GitHub树截断、CDN不一致或离线额外差异均明确失败，不覆盖源锁。

同轮清洁菜单BathMenu的MCP复制暴露字体、滚动组件引用和自定义脚本CID丢失；必须重新挂载正确CID、绑定资源，并用独立/关联快照及7456实际Ready证明恢复，不能只看节点数量。Bath27/TamaView722，31项native通过；中文初始UI已看，原版对照/设备三键/其他语言与材质仍待继续，整游未完成。

## 2026-09-08：线上核对状态与头部默认缩放

线上文件逐字节检查仍为1.14.5.1，本地30个原版脚本已同步；没有真实源码更新。检查器补足线上实读版本号和local-script-review-required，五个HTTP重放回归覆盖本地差异、源码更新、CDN混版和main领先发布。可读移植清单由upstreamSync生成同步状态，证据不能只藏在JSON中。

用户指出FEEDING头部缩放；根因是三个原生返回头部沿用Button默认SCALE/1.2，而原版头部不含stylized。MCP改为NONE/1，保存重开及关联实例核对；7456真实检查三条返回路径，组件门禁通过。创建原生Button后必须根据源选择过渡，不能把引擎默认效果当作原版交互。完整像素和按住连续帧仍独立验收。详见项目feeding-header-validation和online_update_gate。

## 2026-09-08：源按压颜色、Prefab图层与滑块重算

头部去除默认缩放后还需核对themes.css：原版primary solid按下背景混黑至75%，当前四个返回头部用原生Button COLOR/duration0/zoomScale1补齐；不是只设NONE即等同原版。最终7456三个返回路径实际查看，按住连续帧仍单列pending。

Bath独立编辑器空白但节点齐全，聚焦相机和只改根图层无效；24个自有节点全部MCP改为UI_2D后可见。有效图cleaning-material-editor-all-ui.png与此前失败图分开记录。CSS内阴影应从padding edge计算，并按负spread调整圆角；共享menu-row只改1/53张，保留UUID和其他哈希，不能批量刷新历史验收基线。

手机/桌面切换时先换handle再改轨道，会留下旧长度直到第一次滚动。最终布局后调用公开ScrollBar.onScroll，让引擎计算长度位置；实际切换的首个shell日志必须在scrolling之前已正确。保存TS但未刷新资产会继续运行旧编译代码，因此须确认MCP刷新及编译产物，再采集最终证据。

31项native与502对更新入口通过；themes.css单独变化现在同时使头部/材质/Bath单元stale并生成252喂食和8清洁入口。证据见cleaning-material-validation.json及page_update_gate.json；整游、全状态视觉和活动玩法仍未完成。

## 2026-09-08：照料条件与 Prefab 复校准

目标是先还原care菜单UI及数据，再接活动。新增CareMenu54节点、双按钮/七项/角标、严格TS条件及8对中英样例；正式TamaView776节点。源isSleepHour默认读取真实Date，校准桥必须显式冻结函数小时参数；仅设置App.hour会让夜间角标漂移。1176睡眠组合和128源菜单条件已对照。

MCP复制留旧Y，横向Layout不会修正；reorder/move成功不保证树顺序。Widget会在尺寸/位置修改时重算边距，最后按真实参考恢复并检查top/right。独立Prefab和正式关联、UI_2D与字体/脚本CID/双向ScrollBar引用均须检查。焦点/表情及月亮/文本保留8.1，明确记为C14适配。

新父级链接使既有4份整资产指纹失效，初次native失败并非可忽略。重新MCP捕获独立和正式父级，仅字节未变的叶子沿用旧独立快照，旧JSON不改哈希；新*-care-link-layout用于当前门禁。最终32native通过，510对更新URL和零存档访问通过。Missions.js与管教图片独立变更会产生8对Care复校准URL，themes.css也触发材质单元失效。

中文empty、英文default/full手机首轮及源中英代表样例已查看，完整矩阵、桌面、训斥attention/摇动、指针动画、按压填色、角标形状和字体光栅尚未完成。现有菜单点击只记录动作，不能称活动/任务/睡眠/托管玩法已移植。工作证据care-ui-validation、care-editor-layout、care-material-validation分别限定范围；纹理锁只有49项，不能把55张目录文件数量写成55项锁全部通过。

FEEDING头部COLOR/1保持不缩放，7456再次返回验证通过，仍未采集按住连续帧。Bath中文源手机/宽屏对照补入独立观察记录。整游目标继续，无外部阻碍。

## 2026-09-08：CSS运动分层与同一入口快照

训斥按钮的attention使用transform缩放，按压使用独立scale，拇指有自己的rotate/translate。不能用一个节点同时承载三者；MCP保存scold/Visual及图标层，原生Button继续处理输入。CSS rotate后translate需要按旋转矩阵换算位移，Cocos的Y和旋转方向相反。3个真实源DOM矩阵验证了60/125/250ms的插值。

Widget与动画层缩放冲突，初始误把高度压至56.475并上移10.2375。移除Visual上的Widget后，保存固定占位与零位置，外层Layout管理布局，TS只调整已有节点。careMs固定/实时参数以及原版负delay/暂停应同时更新；只放开具体训斥节点，避免顺带改变其他页面冻结状态。减少运动按原CSS只停fa-shake，并清理动态偏好监听。

URL直达通过不等于菜单进入的数据一致。参考桥曾仅在初始care页注入任务/捣乱/父母条件，导致Main进入可能使用其他状态。改为在原open_care_menu入口设置同一固定样例，再执行真实源handler；原生和原版Main→Care都已看见正确full角标及0相位。输入方式不同的焦点不拿来作配对结论。

CareMenu55/TamaView777，33native及522对更新URL通过。Font Awesome CSS需纳入依赖，不能只锁woff图标文件；其关键帧变化会使动画及Prefab单元stale并生成care20对URL。源3矩阵、1501手机边界样例、手机/桌面代表帧和实时/静止状态证明已声明范围；按住全帧、全状态像素、初始焦点及活动仍待完成。


## 2026-09-08 外出旅行增量

目标：接通原版外出展示运动，保留Prefab与严格TS边界。发现源在绘制后更新宠物、最后更新相机；逐段节点分组还会破坏跨段树/地面的全局层序。另发现MCP创建临时Prefab把脚本CID写成类名，实例产生MissingScript，同父级move的siblingIndex未生效。

通过MCP改为ActivityPanel56节点、33个全局排序舞台直接子节点、两段宠物Sprite，删除未接入ActivityPlace。挂载使用脚本路径，临时父节点移出/移回后核对并保存。独立/关联TamaView均913节点，资源引用门禁通过。ActivityTravel保留可见帧与下一状态，支持反向、循环、索引选择和最新三段场景；真实源函数26序列7540帧及实际原生12阶段坐标通过。

URL新增travel/travelMs，更新脚本现生成1986对全局入口；10个外出依赖单独改动触发四单元stale和1464对页面校准。原版桥只重放显示函数，think/粒子/音效保持冻结，目的地玩法未冒充实现。保存MCP及运行阶段证据，旧快照保留原指纹。CSS x-small必须测量实际行盒：本机12px、辅助Chromium10px，Canvas.font解析值还可能不同。可见界面仍用原生Label，字体测量临时元素同步移除。整游1:1及全量页面像素仍未完成。

## 2026-09-08 物品菜单条件模型

继续全游移植，先执行原版顶部菜单handler，而非依据默认截图只制作四行。源显示逻辑发现：卸载模组后保留spriteSkin仍要显示角色入口；家具确认的Yes与异步布置回调有独立先后。严格TS模型和76状态源对照覆盖显示、路由返回值、确认Yes/No、路径转换和恢复角色可用性；原生36项门禁通过。Prefab、子页和运行绑定仍待制作，清单因此保留零URL和UI pending，不用纯模型通过掩盖页面缺失。后续继续MCP与实际7456校准。

## 2026-09-08 物品独立Prefab阶段

MCP复制既有原生菜单/确认结构，保存StuffMenu32节点、FurnitureConfirm17节点；37项门禁通过，默认源角标红色修正后专门重验。组件引用、默认隐藏项、实际段落高度与列表间距检查通过，但尚未关联正式场景及7456，清单不提升为可用。MCP摘要size整数化不能用于8.1单位的精确断言；使用保存尺寸与明确坐标舍入精度。新UI节点层也需核对，不能假设prefab编辑上下文自动使用正确层。


## 2026-09-08 Stuff接入与确认正文

源确认正文具有word-spacing:-3px；相同字号、相同宽度的普通Label仍会错误换行。复用编辑器保存的CssRichText，并单独校准normal行盒和容器padding+margin；不要通过加宽卡片掩盖字体规则。条件Modded角标在源会遮挡英文，按用户C14保留独立宽度与8.1间距并允许增高，适配差异要明记。

MCP自定义组件用node.mount_script真实路径挂载；component.add压缩CID可能被误认为类名而失败。node_snapshot只输出部分组件详情，查询具体Body应使用component.info。场景查询返回全路径，解析时可用UUID避开场景名前缀差异。

当前新增12对Stuff URL纳入更新门禁，模型和Prefab单元均随App变化失效。最终证据为tamaweb/logs/calibration/stuff-ui-validation.json；全游仍未完成，不把子页点击记录当子页实现。


## 2026-09-08 道具显示模型边界

不要把年龄限制提前变成列表禁用态：源open_item_list在点击Use时检查，customPayload比年龄分支更早。购买请求金额也不等于最终扣款，源pay先足额校验，再做性格收益/随机折扣。隔离测试可执行无性格pay验证基础条件，但不能声称性格支付或真实库存已移植。

16道具定义只导出显示字段，完整动作函数仍保留源锁待TS重构；未经UI集成不增加伪URL。三个源依赖独立变化均使item-list-display-model失效；常规门禁不自动重导出配置。证据见item_list_gate.json、calibration/item-model-validation.json。


## 2026-09-08 道具Prefab复制排障

复制同类滑动UI时除了sourceFrame/cellNumber，还要检查cropWidth/Height等显式裁剪，它们优先于cell路径；复制食品索引导致道具透明即此原因。道具源图块22×22、10列，不能凭常见像素尺寸猜。

中文两字按钮必须重新检查保存态宽度。Focus可能与Text同级，也可能挂在Name下，先读真实父节点再计算间距。Layout isAlign=false时改变padding不会自动把Body的旧x改正，需保存明确位置并重开。批量修改返回顶层success仍可能包含failed，必须逐项读结果。最终三Prefab通过39项门禁，尚未关联运行UI。


### 2026-09-08 商城三级页面正式接入

目标：使用现有MCP制作的MallMenu与严格TS数据，接主/装修/客厅及道具购买往返。正式TamaView关联后1099节点，20可用页/2376对。实际7456检查中英与英文说明滚到底，发现并修正子菜单头部错误地沿用BACK；源应显示入口名称。进入购买隐藏商城根，返回恢复同一实例，保留原生控件和已有Prefab。

阻塞与根因：浏览器短时沿用旧脚本，出现Unknown UI page；重导入相关TS并刷新解决。关联TamaView触发旧指纹门禁，属证据失效而非可忽略报错；重新采集独立/正式MCP快照以及关联面板，另写mall-relinked证据，保留旧指纹。英文返回首次被热刷新干扰不计通过，加载稳定后实际重做路径。

验证：最终44native、2376对原版桥（零玩家存档）和更新门禁通过；校准记录myprojects/tamaweb/logs/calibration/mall-route-validation.json。未完成：票券pulse/全部NEW/宽屏与精确图标字号，商城入场/收货动画和共享购物会话、其他商品页与持久化。UI局部可操作不能代替全游1:1。

### 2026-09-08 刮奖Prefab草稿

通过MCP恢复未保存编辑并保存11节点，原生TILED涂层需同时锁定NEAREST；仅设Sprite.TILED仍继承线性采样导致模糊。PixelSprite增加默认关闭的tiled开关并由Prefab启用。原生48检查通过，票面外轮廓及7456接入未验收，独立Prefab不可计入可用页。

### 2026-09-08 票面裁切与冻结参考桥

浏览器computed style证明背景100% auto、mask auto右中，不能用整图同尺寸缩放代替。头像inline行框也影响scale4位置，父行框与图像边界须分别测量。仅冻结onFrameUpdate会让真实setScene不重绘，参考桥改为原setScene后解码等待加一次RAF绘制，保持存档隔离与时间冻结。MCP reorder异常移动到场景根时必须find后恢复并保存重开核实，不能只信错误前的计划。

### 2026-09-08 刮奖宠物绑定

Pet百分比y先减半格，additionalY包含阶段offset，阴影另有ceil(cell/2.1)和距离缩放。按源回调对照三个角色格与八奖项，避免只校准baby样例。Prefab保存15节点，TS绑定独立验证通过，仍等待7456集成与视觉验收。

### 2026-09-08 刮奖URL实际接入

通过校准入口加载已保存Prefab并instantiate；原生透明背景必须补完整Sky层，否则露出旧home。原版setScene内部applySky读取现实时间，固定参考桥需恢复fixture天空再单次重绘。7456与原版两状态已看，50门禁通过；128新增链接是可生成覆盖范围，不等于逐一视觉验收。

### 2026-09-08 幸运券介绍转换

配置JSON写入后仍需MCP重导入，否则浏览器可能显示键名；动态RichText未激活时自然宽度不可靠，字体就绪后再测量。通过真实商城按钮验证介绍→约3秒→刮奖，并用独立timer门禁检查取消/一次回调。非校准完整玩法未接，不能把校准点击转换当作存档玩法完成。

> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-15-pool-资源恢复与Cocos基线-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# pool：资源恢复与 Cocos 基线

## 目标与范围

将 Ultrapool 0.15.7 Android 包归档到六大目录，恢复资源/配置/脚本，建立 Cocos 原生 Prefab 移植工作流与竖屏预览基线。整游移植未完成。

## 来源与动作

- 项目：`myprojects/pool`；当前 Cocos 工程 `/Users/jiaojian/Documents/poolbattle/ultrapool`，项目内通过 `webprojects/ultrapool` 符号链接引用。
- 原引擎为 Godot 4.6，XAPK 的 assetPackInstallTime 中有文本场景/配置及编译脚本。
- 使用 GDRE 2.6.4 与 2.7.0-beta.2，保留两个恢复快照，以 beta 输出处理目录。
- 导出 1052 媒体、597 资源、41 Shader、220 场景、436 脚本（257 游戏/179 插件），识别 226 球资源。
- MuMu 启动同版应用，保存菜单与套组选择截图，不清除原存档。
- MCP 制作 9 节点 AssetReview Prefab，通过序列化 JsonAsset/Label、Button 事件读取并翻页；不运行时创建节点。
- 移植原 GlobalPhysics 中 3 个预测数学函数，6 组守恒/边界测试通过。

## 阻塞与根因

- GDRE 能导出脚本但仍报告 bytecode revision 识别警告；不可视为语义已验证。
- GDRE 报 816 有损转换、ASTC 警告与 1 个 GodotSteam 扩展失败。beta 翻译仍缺 9/866 键，语言列不同步。
- MCP 初次创建 Prefab 将自定义脚本写为类名，编辑器出现 MissingScript，Web 报 null.__prefab；静态 validate 未发现。进入 Prefab 编辑模式、移除 MissingScript、按查询到的 CID 重挂脚本并保存后解决。
- 嵌套 resources 目录未作为 Cocos resources bundle 加载；改为 Prefab 序列化 JsonAsset 引用。
- Label 默认自动尺寸覆盖手设尺寸；先设 overflow 再设 UITransform 尺寸。
- 预览虽然选择 720×1280，但浏览器可见高度不足时，真实 canvas 被压为 720×687。调整浏览器内容区至 820×1350 后实测 canvas 为 720×1280，和 MuMu 1440×2560 同为 9:16。

## 验证证据

- `myprojects/pool/logs/source-processing-result.json`
- `myprojects/pool/logs/cocos-validation.json`：9 节点、0 MissingScript、JsonAsset 已绑定、无运行时建节点代码。
- `myprojects/pool/logs/prediction-tests.txt`：6 组测试通过，不能替代原版运动轨迹验证。
- Cocos Web 地址 `http://192.168.110.141:7456`，实测配置从 1-BALL 切换至 2-BALL。
- 原版截图 `logs/mumu-launch.png` / `logs/mumu-start.png`。核验界面不作为原版 UI 还原证据。

## 下一步与遗留风险

依照项目工作流首要原则：Prefab 优先制作、避免运行时产生节点、尽量利用 Cocos 组件。下一步制作原版 MainMenu/RunSetup/Table/Ball Prefab，逐模块绑定 TS，并在同画幅、同状态下做独立原版对照。翻译缺键、ASTC 图像、脚本版本警告、球面材质、碰撞/事件顺序及完整玩法均待验收。

## 主菜单增量

制作 MainMenu 46 节点原生 Prefab、6 个 Button 和多层面板；源默认调色板与 CRT 乘法材质已移植，按压脚本挂接完成。发现 create_prefab 丢 customMaterial、create_image 的 color 快捷值未生效、透明裁切改变部件尺寸，已在 Prefab 编辑模式显式回写。预览只走 Codex 右侧面板并后台验证。菜单滚动球、功能跳转、字体、CRT 最新改动、逐像素及完整玩法仍待验收。

> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-04-17-oldproject-u3d-web本地化-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-04-17 oldproject U3D Web 本地化阶段复盘

## 目标
- 为 `https://dobestapp.oss-cn-hangzhou.aliyuncs.com/app-3/Release/ljzs_lt/DRGM/1.01/index.html` 创建项目工作区。
- 完成 Unity WebGL 本地镜像，并尽量消除运行时外部资源依赖。

## 动作
- 创建 `myprojects/oldproject/` 六大目录。
- 下载 WebGL 主体：`index.html`、`Build/WebGL_0415_1525.*`、`TemplateData/*`。
- 解析 Addressables `catalog.bin`，下载 11 个 `StreamingAssets/aa/WebGL/*.bundle`。
- 下载运行时 CDN `ABFiles.txt` 及清单内 20 个 `*.unity3d`/配置资源。
- 在 `index.html` 增加本地化补丁：
  - CDN 运行时资源重写到本地 `StreamingAssets/WebGL/ljzs_lt/`。
  - Unity Analytics 请求返回本地空配置。
  - 移除移动端默认 WebGL warning。
- 按 `drgm_ljpx2_lt` 的代码补丁经验处理运行时覆盖问题：
  - 入口层将 DebugSystem/Feishu/DRGM 鉴权请求返回成功。
  - `/mini-data/sys/nowTime` 返回本地时间，避免访问内网 IP。
  - 解包 `Build/WebGL_0415_1525.data`，移除 `DebugSystemStaticStart` 初始化，并从 `ScriptingAssemblies.json` 删除 `DebugSystem.dll`。
  - 在 `.data` 内置 `data.unity3d` 和 `StreamingAssets/WebGL/ljzs_lt/scene/minegamemain.unity.unity3d` 中禁用 `Debug/DebuggerSystemUGUI/DRGMUI/userInputKey` 等对象。

## 阻塞与根因
- 第一轮冒烟没有抓到请求，是因为 CDP 连接到了 Chrome 扩展 background page；修正为选择 `type=page` 目标。
- Addressables 静态资源并不覆盖全部运行时资源；游戏启动后仍会读取单独的 `ABFiles.txt` 资源体系。
- Unity Analytics 配置请求最初没有被拦截，是因为传给 `fetch` 的对象不是标准 `Request` 实例，且 URL 可能没有尾部 `/`。
- “请输入密钥”不是 DOM/prompt，而是 Unity 场景里的 `DRGMUI/userInputKey`；只 hook `window.prompt` 或网络请求不会让画布 UI 消失。
- DebugSystem 有两条来源：运行时初始化和场景内对象。只删 `RuntimeInitializeOnLoads` 不够，还要禁用 `.data` 初始场景和运行时场景里的 Debug 根对象。

## 验证证据
- 最终冒烟日志：`myprojects/oldproject/logs/external_probe_final.log`
- Debug/密钥补丁后最终冒烟：`myprojects/oldproject/logs/final_debug_smoke.log`
- Debug/密钥补丁截图：`myprojects/oldproject/logs/final_debug_smoke.png`
- 关键结果：
  - `REQUEST_COUNT 14`
  - `EXTERNAL_COUNT 0`
  - `HTTP_ERROR_COUNT 0`
  - `FAILURE_COUNT 0`
  - `GAME_TAG_COUNT 84`
- 补丁后已进入战斗引导画面；截图中无 Debug 面板、无“请输入密钥/Enter text”等待层。补丁后网络外链为 0，剩余 `ProductConfigs.db/xml` 404 为可选内购配置探测，不阻断启动。

## 可复用经验
- Unity WebGL Addressables 项目要同时看 `StreamingAssets/aa/catalog.bin` 和运行时业务自己的资源清单。
- CDP 自动化冒烟要排除扩展 background page，否则 Network 统计会误判。
- 入口级本地化补丁要同时兼容 string、URL-like object、非标准 Request-like object。
- Unity 画布内等待层要用 UnityPy 定位真实 `GameObject`；同名对象可能同时存在于 `.data` 初始场景与后续 `StreamingAssets` 场景包中，二者都要处理。

## 遗留风险
- 尚未做 TT/抖音包转换。
- 尚未导出 `sourceImages/`，如需美术替换再进入资源导出/回写流程。
- Headless Chrome 中的 WebGL shader warning 属运行环境噪声，后续真机/桌面浏览器仍需人工看一次画面。

# Unity WebGL (U3D) 本地化与 TT 适配流程

## 使用说明（示例与通用边界）
- 文中路径、文件模式、日志关键字为常见示例（如 `StreamingAssets/...`、`*.unity3d`、`TT_STAGE`）。
- 实际项目可用等价路径/字段替换。
- 重点在定位顺序、回写策略和门禁判据，不在某个项目的固定命名。

## 适用范围
- 将 Unity WebGL 游戏镜像到本地并可运行。
- 修复缺失资源、修改 UI/文本。
- 转换为 TT 包并联调远程资源链路。

## 输入
- 远程入口 URL
- 本地项目目录
- 本地测试运行地址（origin）

## 一、Web 本地化基础流程

### 1) 镜像壳文件
- 下载：`index.html`、`Build/*.loader.js`、`Build/*.framework.js`、`Build/*.wasm`、`Build/*.data`
- 下载 `TemplateData/*`
- 核对远端响应头与本地文件大小（重点：`.data`、`.wasm`）

### 2) 处理 StreamingAssets 清单
- 拉取 `StreamingAssets/.../PackageManifest_*.version`
- 解析版本号下载：
  - `PackageManifest_*_<code>.bytes`
  - `PackageManifest_*_<code>.hash`
- 从 manifest 哈希批量下载 bundle：
  - `<hash>.unity3d`（或 `.unity3dc/.bundle`）

### 3) 404 修复循环
- 启动本地静态服务并运行游戏
- 在 Network 中观察缺失 `StreamingAssets/*.unity3d`
- 从远端补齐后重试，直到首轮场景可进入

## 二、内容修改流程

### A) 运行时请求补丁（可选）
- 在 `Build/*.loader.js` hook `fetch` / `XMLHttpRequest.open`
- 重写 API 路径或资源域名
- 对 `StreamingAssets/*.unity3d` 增加 cache-busting 参数

### B) bundle 内文本/节点修改
- 使用 UnityPy 打开 `.unity3d`
- 定位 `GameObject` / `MonoBehaviour.m_Text`
- 修改 `m_Text`、`m_IsActive`，或禁用 `Canvas`

### C) `WebGL_*.data` 级修改
- `.data` 是 UnityWebData 容器，常见条目：
  - `data.unity3d`
  - `resources.resource`
  - `Il2CppData/Metadata/global-metadata.dat`
- 如需改内容，解包后修改再回包

## 三、`.data` 重打包
- 解包：`unity_webdata_extract.py <data> <out_dir>`
- 修改解包目录
- 回包：`unity_webdata_pack.py <out_dir> <data>`

## 四、TT 适配流程（U3D）

### 1) 先保证启动，再做包体优化
- 第一阶段目标：TT 真机可启动。
- 第二阶段目标：再做主包/分包/CDN 收敛。

### 2) 数据加载关键点
- UnityPlugin 的 data 常规路径：`tt.loadSubpackage(data-package)` -> `readFile(.data/.br)` -> 解压 -> `onDataReady`
- 若本地 `readFile` 大文件报 OOM（如 `read may cause OOM`），可改为远程 `tt.request(arraybuffer)` 回传同一二进制。

### 3) 回调契约必须保持
- FS 拦截后回调建议保持：
  - `success({ data, errMsg: 'readFile:ok' })`
  - `complete(...)`
- 否则可能出现“下载成功但流程不前进”。

### 4) 阶段日志判读
- `TT_STAGE` 顺序不保证严格递增（Data/WASM 并行），`0 -> 3 -> 1` 可接受。
- 真正异常判据：
  - 已出现 data handoff，但长期没有 `readAssets(5)` / `prepareGame(6)`。

### 5) CDN 联调注意
- 局域网 HTTP 可做开发联调，不适合作为最终链路。
- VPN/代理会影响请求超时与连通性，需用服务端日志确认请求是否真正到达。
- 提测前切公网 HTTPS CDN，并完成域名白名单配置。

## 五、验证与输出

### 验证
- 清理缓存（站点数据 / IndexedDB `UnityCache` / TT 本地缓存）
- 强制刷新或重启小游戏
- 对照日志确认资源到达与阶段推进

### 输出
- 本地项目路径
- 已修改 bundle / data 列表
- TT 侧改动点（`game.js` / 配置项）
- 剩余风险与下一步建议


## 2026-10-09 通用补充：嵌入式 Demo 的本地化

- 从 iframe 或站点页面定位真实构建入口；原始下载壳与本地运行壳分开保存。
- CSS 引用、核心 loader/framework/wasm/data 请求分别核实；装饰图片 404 不应误判为游戏核心资源缺失。
- 保存核心输入文件 SHA-256；解析数据包头部时按魔数字节长度计算，逐项检查偏移、长度和边界。
- 将初始化成功、资源请求成功、视觉和交互通过分别记录。加载日志或截图单独都不能证明端到端验收。

> 归档来源：`cocosgame2/experience/01-流程标准/Cocos-Web本地化标准流程.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Cocos Web 游戏本地化流程

## 使用说明（示例与通用边界）
- 文中出现的路径与目录（如 `webprojects/<project_name>`、`logs/<project_name>`）是示例模板。
- 执行时可替换为你的实际项目路径。
- 重点在流程顺序、验收门禁和排障思路，不在固定目录命名。

## 适用范围
- 目标：将远程 Cocos Web 游戏 URL 转为本地可运行工程，并可进一步转换为 TT 小游戏包。
- 适用：Cocos Creator 2.x/3.x Web 包（以 2.4.x 为主）。

## 工具调用原则
- 流程文档不再内嵌 Python 代码。
- 仅记录 `tools/` 下工具名、参数和调用方式。
- 工具说明统一维护在 [tools/工具目录.md](../../../../tools/工具目录.md)。

## 核心工具
- `tools/cocos_prefetch_assets.py`
  - 按 `assets/*/config.*.json` 扫描/预抓资源。
- `tools/cocos_export_source_images.py`
  - 导出可编辑贴图和 `manifest.json`。
- `tools/cocos_import_source_images.py`
  - 按 `manifest.json` 增量回写贴图。
- `tools/convert_cc24_web_to_tt.py`
  - Cocos 2.4 Web -> TT 包骨架转换。
- `tools/wxapkg_batch_unpack.js`
  - 微信小游戏包离线解密+解包（支持一个目录内多个 `.wxapkg`）。

## 一、Web 本地化标准流程

### 1) 镜像壳文件
- 同步 `index.html`、顶层 `*.js/*.css`、`assets/*/config.*.json`。
- 保持原始目录结构与哈希文件名。

### 2) 预扫描（不下载）
```bash
python3 tools/cocos_prefetch_assets.py \
  --project webprojects/<project_name> \
  --scan-only \
  --report logs/<project_name>/preflight_report.json
```
- 关注报告字段：`missing_local`、`missing_local_entries`。

### 3) 全量预抓
```bash
python3 tools/cocos_prefetch_assets.py \
  --project webprojects/<project_name> \
  --base-url "<remote_base_url>" \
  --workers 32 \
  --report logs/<project_name>/prefetch_report.json
```
- 关注：`downloaded`、`remote_missing`、`errors`。

### 4) 定向补抓（单 bundle）
```bash
python3 tools/cocos_prefetch_assets.py \
  --project webprojects/<project_name> \
  --base-url "<remote_base_url>" \
  cfg_NewStage \
  --workers 16 \
  --report logs/<project_name>/prefetch_cfg_NewStage_report.json
```
- 场景：某个卡点 bundle 独立缺失时。

### 5) 启动前门禁
```bash
python3 tools/cocos_prefetch_assets.py \
  --project webprojects/<project_name> \
  --scan-only \
  --report logs/<project_name>/post_prefetch_scan_report.json
```
- 门禁标准：`missing_local == 0`。

### 6) 运行时补抓
- 运行本地服务并打开页面。
- 从 console/network 失败请求提取 `assets/...` 路径补抓。
- 直到关键场景无新增 404。

### 7) 错误分诊
- `404`：优先判定为真实资源缺失。
- `ERR_CONNECTION_REFUSED` / `status=0`：先修本地服务问题。
- 启动链路阻断优先级高于非阻断告警。

## 一-B、微信小游戏包还原为 Web（Cocos 2.4.x）

### 1) 适用场景
- 输入是 `input/<wxid>/`（目录内有多个 `.wxapkg`）。
- 目标是恢复为可在浏览器运行的 `webprojects/<project_name>/`。

### 2) 还原步骤
1. 先批量解包成文件夹
- macOS/Linux：
```bash
node tools/wxapkg_batch_unpack.js \
  --input input/<wxid> \
  --clean \
  --report logs/<project_name>/unpack_report.json
```
- Windows PowerShell：
```powershell
node .\tools\wxapkg_batch_unpack.js `
  --input .\input\<wxid> `
  --clean `
  --report .\logs\<project_name>\unpack_report.json
```
- Windows CMD：
```bat
tools\wxapkg_batch_unpack.cmd --input input\<wxid> --clean --report logs\<project_name>\unpack_report.json
```

2. 判型与版本
- 先确认 Cocos 版本（例如 `2.4.15`），再选择对应 web 壳模板（如 `templates/web-mobile-2.4.15`）。

3. 抽取主包/子包模块
- 从主 `game.js` 提取并恢复：
  - `main.*.js`
  - `src/settings.*.js`
  - `assets/*/index.js`
- 子包映射到 web bundle 目录：
  - `subpackages/loading/game.js -> assets/loading/index.js`
  - `subpackages/scripts/game.js -> assets/scripts/index.js`

4. 补齐版本化入口
- 按 `settings.bundleVers` 校验每个 bundle 的 `index.<ver>.js` 是否存在。
- 若仅有 `index.js`，需补齐 `index.<ver>.js`（可拷贝同内容）。

5. 补齐远程资源
- 先抓 `assets/<bundle>/config.<ver>.json`，再按 config 补抓 `import/native`。
- 启动前门禁：`missing_local == 0`。

6. 本地化运行模式
- 将 `settings` 调整为本地加载：
  - `remoteBundles=[]`
  - `subpackages=[]`
  - `server=''`

7. 浏览器兼容修复
- 若 bundle 顶层出现 `require("@babel/runtime/...")` 且浏览器报 `require is not defined`：
  - 处理为内联 helper 或替换为浏览器可用实现。

8. 启动链路对齐
- 对齐 web 模板的 splash 逻辑：首场景启动后隐藏 `#splash`，恢复 canvas 可见。
- 建议监听：`cc.director.once(cc.Director.EVENT_AFTER_SCENE_LAUNCH, ...)`。

### 3) 验收标准
- 无阻断错误（尤其 `ERROR 4928`、`require is not defined`）。
- 可进入目标首场景（不仅是 Cocos loading 进度条）。
- Playwright 校验通过（场景名到达 + 无 page error/console error）。
- 本地服务建议使用：
  - `http-server . -p 8080 -a 127.0.0.1 -c-1`（禁缓存）。

## 二、反调试与混淆处理

### 1) 定位原则
- 只处理会阻断运行的反调试段。
- 保持启动链路语义不变，不做无必要反混淆。

### 2) 安全补丁
- 先备份，再最小范围修改。
- 常见策略：将反调试 IIFE 置空或短路，不动业务主链。

### 3) 回归检查
- 启动链路可达。
- 无新增 JS 语法错误。
- 资源请求路径未被破坏。

## 三、资源解密、集中导出与回写（贴图）

### 1) 全量导出
```bash
python3 tools/cocos_export_source_images.py \
  --project webprojects/<project_name> \
  --out sourceImages/<project_name> \
  --clean
```
- 输出：
  - `sourceImages/<project_name>/textures/**`
  - `sourceImages/<project_name>/manifest.json`

### 2) 本地修改
- 只改 `sourceImages/<project_name>/textures/**`。
- 尺寸必须与 `manifest.json` 记录一致。

### 3) 干跑验收
```bash
python3 tools/cocos_import_source_images.py \
  --project webprojects/<project_name> \
  --source sourceImages/<project_name> \
  --dry-run
```

### 4) 增量回写（回血）
```bash
python3 tools/cocos_import_source_images.py \
  --project webprojects/<project_name> \
  --source sourceImages/<project_name> \
  --backup-dir logs/<project_name>/backup_before_import
```
- 默认仅覆盖变更文件。
- 保持原始加密/明文格式。

### 5) 全量强制回写（必要时）
```bash
python3 tools/cocos_import_source_images.py \
  --project webprojects/<project_name> \
  --source sourceImages/<project_name> \
  --all \
  --backup-dir logs/<project_name>/backup_before_import_all
```

## 四、非贴图资源经验（音频/字体/Spine/二进制）
- 低风险：`.mp3/.ogg/.wav/.json/.txt/.ttf`。
- 中风险：`Spine(.skel/.json + .atlas + 纹理)` 需成组替换。
- 高风险：`.bin/.cconb` 谨慎替换，通常与序列化格式强绑定。
- 通用原则：路径不变、资源组完整、先备份后覆盖。

## 五、Web -> TT 的主要转换方法

### 1) 判型与模板选择
- Cocos 2.4：`templates/bytedance-mini-game-cc2.4`
- Cocos 3.x：`templates/bytedance-mini-game-3.8`

### 2) 产出 TT 包
```bash
python3 tools/convert_cc24_web_to_tt.py \
  --source webprojects/<project_name> \
  --template templates/bytedance-mini-game-cc2.4 \
  --dest output/<project_name>/tt
```

### 3) 运行时桥接
- 对接平台能力时区分 runtime（web/tt）。
- 避免把 TT 接口路径误注入 web runtime。
- 场景切换链路以“回调到达 + 节点存在”双重验证。

### 4) TT 场景卡住排查优先级
1. 资源完整性（`missing_local`、`remote_missing`）
2. 切场景主链路（`runScene/loadScene/onLaunched`）
3. UI 节点实例化链路（如 `GameUI` 是否实际入树）
4. 平台接口噪声（如 `showShareMenu disabled`）是否阻断主链

## 六、验收口径（最小可交付）
- 能稳定进入目标场景（例如 `game`）。
- 关键 UI 节点存在且可交互。
- 无新增阻断错误（允许非阻断平台告警）。
- 产物、日志、复盘分别落位：
  - `output/<project>/<platform>/`
  - `logs/<project>/`
  - `experience/<date>-<project>-<platform>-复盘.md`

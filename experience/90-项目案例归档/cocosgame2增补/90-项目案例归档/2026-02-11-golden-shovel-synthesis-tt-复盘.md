> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-02-11-golden-shovel-synthesis-tt-复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 抖音(TT)小游戏打包复盘文档

> **项目名称：** 金铲子合成 (Golden Shovel Synthesis)
> **Cocos Creator 版本：** 3.6.2
> **目标平台：** bytedance-mini-game (抖音/TikTok小游戏)
> **AppID：** mgox8hu23gbtdkt4
> **复盘日期：** 2026-02-11

---

# 第一部分：转换原理与文件分析

---

## 一、项目目录结构

```
cz/
├── base/                          # Cocos Creator 原始构建输出 (Web平台)
│   ├── application.js             # 应用入口
│   ├── assets/                    # 资源包 (internal, main, MoreGames, res_remote1, resources, scripts)
│   ├── cocos-js/                  # Cocos 引擎文件 (cc.js ~1.8MB)
│   ├── config.json                # 游戏配置数据表 (~160KB)
│   ├── cz配置文件/                # 13个JSON数据表
│   ├── src/                       # 脚本源码、settings、import-map
│   ├── index.html                 # Web入口页面
│   └── index.js                   # Web启动脚本
│
├── bytedance-mini-game/           # 最终打包版本 (修改后)
│   ├── game.js                    # 小游戏入口（核心修改文件）
│   ├── game.json                  # 小游戏配置（分包声明）
│   ├── project.config.json        # 项目配置
│   ├── engine-adapter.js          # 引擎适配器
│   ├── web-adapter.js             # Web适配器
│   ├── application.js             # 应用模块
│   ├── cocos-js/                  # 引擎文件 (cc.js ~1.7MB)
│   ├── src/                       # 脚本、设置
│   ├── assets/                    # 资源文件
│   └── subpackages/               # 分包目录
│       ├── ammo/                  # 物理引擎分包 (1.5MB) ← 新增
│       ├── scripts/               # 脚本分包 (~540KB)
│       ├── res_remote1/           # 远程资源分包
│       └── MoreGames/             # 交叉推广分包 (~7KB)
│
└── bytedance-mini-game_backup/    # 修改前的备份版本
```

---

## 二、Web 构建 → TT 小游戏完整转换指南（逐文件分析）

> 以下基于 `base/`（Cocos Creator Web-Mobile 构建产物）与 `bytedance-mini-game/`（最终抖音小游戏包）的逐文件对比整理。

### 2.1 整体架构变化

```
Web 构建 (base/, ~42MB)                    TT 小游戏 (bytedance-mini-game/, ~5MB)
┌──────────────────────┐                   ┌──────────────────────────────┐
│ index.html (入口)     │    ──删除──→      │ game.js (新入口)              │
│ index.js             │                   │ game.json (分包声明)          │
│ style.css            │                   │ project.config.json (AppID)  │
│                      │                   │ engine-adapter.js (新增适配)   │
│                      │                   │ web-adapter.js (新增适配)      │
├──────────────────────┤                   ├──────────────────────────────┤
│ cocos-js/cc.js 1.8M  │    ──裁剪──→      │ cocos-js/cc.js 1.7M          │
│                      │                   │ cocos-js/instantiated-*.js   │
│                      │                   │ cocos-js/wait-for-ammo-*.js  │
├──────────────────────┤                   ├──────────────────────────────┤
│ assets/internal/     │    ──保留──→      │ assets/internal/  (不变)      │
│ assets/main/         │    ──修改──→      │ assets/main/  (瘦身)          │
│ assets/scripts/      │    ──移入分包──→   │ subpackages/scripts/         │
│ assets/MoreGames/    │    ──移入分包──→   │ subpackages/MoreGames/       │
│ assets/res_remote1/  │    ──移入分包──→   │ subpackages/res_remote1/     │
│ assets/resources/ 37M│    ──移到CDN──→   │ (远程加载, 不在包内)           │
│                      │                   │ subpackages/ammo/ (新增)      │
├──────────────────────┤                   ├──────────────────────────────┤
│ src/settings.json    │    ──修改──→      │ src/settings.json             │
│ src/import-map.json  │    ──转换──→      │ src/import-map.js             │
│ src/loadConfig.js    │    ──修改──→      │ src/loadConfig.js             │
│ src/chunks/bundle.js │    ──修改──→      │ src/chunks/bundle.js          │
│ src/system.bundle.js │    ──裁剪──→      │ src/system.bundle.js          │
│ src/polyfills.*.js   │    ──修改──→      │ src/polyfills.bundle.js       │
└──────────────────────┘                   └──────────────────────────────┘
```

### 2.2 逐文件转换清单

#### 第一类：直接删除（Web 专属文件）

| 文件 | 说明 |
|------|------|
| `index.html` | Web 页面入口，小游戏不需要 |
| `index.js` | Web 启动脚本，被 game.js 替代 |
| `style.css` | Web 样式，小游戏无 CSS |
| `config.json` (160KB) | 构建配置，运行时不需要 |
| `.vscode/` | 开发工具配置 |

#### 第二类：新建文件（TT 平台专属）

| 文件 | 大小 | 用途 |
|------|------|------|
| `game.js` | 3.6KB | **小游戏入口**：TextDecoder polyfill、适配器加载、画布设置、ammo 分包加载、引擎初始化 |
| `game.json` | 628B | **分包声明**：deviceOrientation、subpackages 列表 |
| `project.config.json` | 158B | **项目配置**：appid、projectname |
| `engine-adapter.js` | 17KB | **引擎适配器**：TT 平台 API 适配 |
| `web-adapter.js` | 65KB | **Web API 适配**：FileSystem、XMLHttpRequest 等 polyfill |
| `cocos-js/instantiated-64c3001d.js` | 57B | Ammo 加载器存根 |
| `cocos-js/wait-for-ammo-instantiation.js` | 147B | Ammo 异步等待模块 |
| `src/import-map.js` | 293B | 从 .json 转换为 .js 模块（含 ammo 引用） |
| `src/project` | 45B | 占位文件 |
| `src/bundle-scripts/` | — | 各 bundle 入口副本目录 |
| `subpackages/ammo/game.js` | 25B | ammo 分包入口 |
| `subpackages/ammo/instantiated-64c3001d.js` | 1.5MB | Ammo 物理引擎（从 cc.js 中抽离） |

#### 第三类：原样复制（无修改）

| Base 路径 | ByteDance 路径 | 校验 |
|-----------|---------------|------|
| `application.js` | `application.js` | MD5 一致 |
| `assets/internal/` | `assets/internal/` | 内容一致 |
| `src/assets/scripts/libs/k-cocos.js` | `src/assets/scripts/libs/k-cocos.js` | MD5 一致 |

#### 第四类：移动到分包（路径变化，index.js 改名 game.js）

| Base 路径 | ByteDance 路径 | 备注 |
|-----------|---------------|------|
| `assets/scripts/config.json` | `subpackages/scripts/config.json` | 一致 |
| `assets/scripts/index.js` (1.1MB) | `subpackages/scripts/game.js` (540KB) | 重新压缩，体积减半 |
| `assets/MoreGames/index.js` | `subpackages/MoreGames/game.js` | 一致（仅改名） |
| `assets/MoreGames/config.json` | `subpackages/MoreGames/config.json` | 一致 |
| `assets/MoreGames/import/**` | `subpackages/MoreGames/import/**` | 一致 |
| `assets/MoreGames/native/**` | `subpackages/MoreGames/native/**` | 一致 |
| `assets/res_remote1/index.js` | `subpackages/res_remote1/game.js` | 一致（仅改名） |
| `assets/res_remote1/config.json` | `subpackages/res_remote1/config.json` | 一致 |
| `assets/res_remote1/import/**` | `subpackages/res_remote1/import/**` | 一致 |
| `assets/res_remote1/native/**` | `subpackages/res_remote1/native/**` | 一致 |

> **重要规则：** 分包中的 bundle 入口文件必须命名为 `game.js`（TT 平台要求），而 base 中是 `index.js`。

#### 第五类：需要修改的文件

| 文件 | 变化 | 关键修改点 |
|------|------|-----------|
| `cocos-js/cc.js` | 1.8M → 1.7M | 抽离 ammo 物理引擎代码 |
| `assets/main/index.js` | 38KB → 21KB | 代码优化/移除未使用模块 |
| `src/settings.json` | 大幅修改 | 见 2.3 详细对比 |
| `src/loadConfig.js` | 82KB → 76KB | 配置瘦身 |
| `src/system.bundle.js` | 12KB → 6.3KB | 裁剪平台无关代码 |
| `src/chunks/bundle.js` | 修改 | 平台适配调整 |
| `src/polyfills.bundle.js` | 修改 | 平台适配调整 |

#### 第六类：移到 CDN 远程加载

| Base 路径 | CDN 路径 | 大小 |
|-----------|---------|------|
| `assets/resources/**` (全部) | `https://cdn-corp.leyouxi.xyz/.../v1.1/resources/` | ~37MB |

> 这是最大的优化点：37MB 的 resources 资源包不打入小游戏包，改为运行时从 CDN 远程加载。

### 2.3 settings.json 完整对比

| 配置项 | Base (Web) | ByteDance (小游戏) |
|--------|------------|-------------------|
| `platform` | `"web-mobile"` | `"bytedance-mini-game"` |
| `customLayers` | 17 个自定义层 | `[]` 清空 |
| `subpackages` | `[]` | `["scripts", "res_remote1", "MoreGames"]` |
| `remoteBundles` | `[]` | `["resources"]` |
| `server` | `""` | `"https://cdn-corp.leyouxi.xyz/.../v1.1/"` |
| `physicsEngine` | `"physics-ammo"` | `"physics-builtin"` |
| `gravity.y` | `-300` | `-10` |
| `collisionGroups` | 完整碰撞矩阵 | 无 |
| `plugins.jsList` | `["assets/scripts/libs/k-cocos.js"]` | `[]` (改为 game.js 中 require) |
| `orientation` | `"portrait"` | 无 (在 game.json 中配置) |

### 2.4 包体积对比

| 类别 | Base (Web) | ByteDance (小游戏) | 说明 |
|------|-----------|-------------------|------|
| 引擎 cc.js | 1.8MB | 1.7MB | 抽离 ammo |
| 适配器 | 0 | 82KB | engine-adapter + web-adapter |
| internal 资源 | ~200KB | ~200KB | 不变 |
| main 资源 | ~60KB | ~40KB | 优化 |
| scripts 分包 | 1.1MB | 540KB | 压缩 50% |
| MoreGames 分包 | ~300KB | ~300KB | 不变 |
| res_remote1 分包 | ~2MB | ~2MB | 不变 |
| ammo 分包 | (含在 cc.js) | 1.5MB | 独立分包 |
| resources | 37MB | 0 (CDN) | **最大优化点** |
| **总计** | **~42MB** | **~5MB + 37MB CDN** | 主包减少 88% |

---

## 三、Bundle 资源来源判定与切换指南

### 3.1 资源来源判定规则

每个 bundle 的加载来源由 `src/settings.json` 中 `assets` 段的三个配置项共同决定：

```json
// bytedance-mini-game/src/settings.json
"assets": {
    "server": "https://cdn-corp.leyouxi.xyz/.../v1.1/",   // CDN 根地址
    "remoteBundles": ["resources"],                         // 走 CDN 的 bundle
    "subpackages": ["scripts", "res_remote1", "MoreGames"] // 本地分包的 bundle
}
```

**判定逻辑如下：**

```
                    ┌─ 在 remoteBundles 中？─── 是 ──→ 【CDN 远程加载】
                    │                                    路径: {server}/{bundleName}/
一个 bundle ────────┤
                    │                    ┌─ 是 ──→ 【本地分包】
                    └─ 否 ──→ 在 subpackages 中？        路径: subpackages/{bundleName}/
                                         │
                                         └─ 否 ──→ 【主包内置】
                                                     路径: assets/{bundleName}/
```

**本项目各 bundle 来源：**

| Bundle 名称 | `remoteBundles`? | `subpackages`? | 来源 | 实际路径 |
|-------------|:---:|:---:|------|---------|
| `resources` | **是** | 否 | CDN 远程 | `https://cdn-corp.leyouxi.xyz/.../resources/` |
| `scripts` | 否 | **是** | 本地分包 | `subpackages/scripts/` |
| `res_remote1` | 否 | **是** | 本地分包 | `subpackages/res_remote1/` |
| `MoreGames` | 否 | **是** | 本地分包 | `subpackages/MoreGames/` |
| `internal` | 否 | 否 | 主包内置 | `assets/internal/` |
| `main` | 否 | 否 | 主包内置 | `assets/main/` |

> **注意：** `ammo` 分包比较特殊，它不是 Cocos bundle，而是 TT 平台原生分包，只在 `game.json` 中声明，由 `game.js` 中 `tt.loadSubpackage()` 手动加载。

### 3.2 三种来源的区别

| 对比项 | 主包内置 | 本地分包 | CDN 远程 |
|--------|---------|---------|---------|
| 文件位置 | `assets/{name}/` | `subpackages/{name}/` | CDN 服务器 |
| 入口文件名 | `index.js` | `game.js` | `index.js` |
| 占用主包大小 | **是** | 否 | 否 |
| 占用分包大小 | — | **是** | 否 |
| 需要网络 | 否 | 否 | **是** |
| 加载速度 | 最快 | 快 | 取决于网速 |
| 需要 game.json 声明 | 否 | **是** | 否 |
| 需要 CDN 部署 | 否 | 否 | **是** |

### 3.3 切换操作指南

#### 场景一：本地分包 → CDN 远程

> 例：把 `res_remote1` 从本地分包改到 CDN 加载

**需要修改的地方：**

| # | 文件 | 操作 |
|---|------|------|
| 1 | `src/settings.json` | `remoteBundles` 加入 `"res_remote1"` |
| 2 | `src/settings.json` | `subpackages` 移除 `"res_remote1"` |
| 3 | `game.json` | `subpackages` 移除 res_remote1 的声明 |
| 4 | CDN 服务器 | 上传 `subpackages/res_remote1/` 整个目录到 `{server}/res_remote1/` |
| 5 | 本地 | 删除 `subpackages/res_remote1/` 目录 |

```json
// settings.json 修改前
"remoteBundles": ["resources"],
"subpackages": ["scripts", "res_remote1", "MoreGames"],

// settings.json 修改后
"remoteBundles": ["resources", "res_remote1"],
"subpackages": ["scripts", "MoreGames"],
```

```json
// game.json 修改前
"subpackages": [
    { "name": "scripts",    "root": "subpackages/scripts/" },
    { "name": "res_remote1", "root": "subpackages/res_remote1/" },
    { "name": "MoreGames",  "root": "subpackages/MoreGames/" },
    { "name": "ammo",       "root": "subpackages/ammo/" }
]

// game.json 修改后
"subpackages": [
    { "name": "scripts",    "root": "subpackages/scripts/" },
    { "name": "MoreGames",  "root": "subpackages/MoreGames/" },
    { "name": "ammo",       "root": "subpackages/ammo/" }
]
```

---

#### 场景二：CDN 远程 → 本地分包

> 例：把 `resources` 从 CDN 拉回本地分包

**需要修改的地方：**

| # | 文件 | 操作 |
|---|------|------|
| 1 | `src/settings.json` | `remoteBundles` 移除 `"resources"` |
| 2 | `src/settings.json` | `subpackages` 加入 `"resources"` |
| 3 | `game.json` | `subpackages` 加入 resources 声明 |
| 4 | 本地 | 将 CDN 上的 resources 目录放入 `subpackages/resources/` |
| 5 | 本地 | 入口文件 `index.js` **改名为** `game.js` |

```json
// settings.json 修改后
"remoteBundles": [],
"subpackages": ["scripts", "res_remote1", "MoreGames", "resources"],
```

```json
// game.json 加入
{ "name": "resources", "root": "subpackages/resources/" }
```

> **警告：** resources 有 37MB，放入本地会严重超出 TT 分包大小限制，一般不建议。

---

#### 场景三：主包内置 → 本地分包

> 例：把 `main` 从主包移到分包（减小主包体积）

**需要修改的地方：**

| # | 文件 | 操作 |
|---|------|------|
| 1 | `src/settings.json` | `subpackages` 加入 `"main"` |
| 2 | `game.json` | `subpackages` 加入 main 声明 |
| 3 | 本地 | `assets/main/` 整个移到 `subpackages/main/` |
| 4 | 本地 | `subpackages/main/index.js` **改名为** `game.js` |

---

#### 场景四：主包内置 → CDN 远程

> 例：把 `main` 放到 CDN 上

**需要修改的地方：**

| # | 文件 | 操作 |
|---|------|------|
| 1 | `src/settings.json` | `remoteBundles` 加入 `"main"` |
| 2 | CDN 服务器 | 上传 `assets/main/` 到 `{server}/main/` |
| 3 | 本地 | 删除 `assets/main/` 目录 |

---

#### 场景五：本地分包 → 主包内置

> 例：把 `MoreGames` 从分包移回主包

**需要修改的地方：**

| # | 文件 | 操作 |
|---|------|------|
| 1 | `src/settings.json` | `subpackages` 移除 `"MoreGames"` |
| 2 | `game.json` | `subpackages` 移除 MoreGames 声明 |
| 3 | 本地 | `subpackages/MoreGames/` 移到 `assets/MoreGames/` |
| 4 | 本地 | `assets/MoreGames/game.js` **改名为** `index.js` |

### 3.4 操作速查表

| 操作方向 | `settings.json` remoteBundles | `settings.json` subpackages | `game.json` subpackages | 入口文件名 | 文件放哪 |
|---------|:---:|:---:|:---:|:---:|------|
| **→ CDN 远程** | **加入** | 移除 | 移除 | `index.js` | 上传到 `{server}/{name}/` |
| **→ 本地分包** | 移除 | **加入** | **加入** | `game.js` | `subpackages/{name}/` |
| **→ 主包内置** | 移除 | 移除 | 移除 | `index.js` | `assets/{name}/` |

> **核心要点：**
> 1. `settings.json` 控制 Cocos 引擎的加载行为
> 2. `game.json` 控制 TT 平台的分包识别，两处必须同步
> 3. 分包中入口必须叫 `game.js`，主包/CDN 中叫 `index.js`
> 4. CDN 模式需要确保 `server` 字段配置了正确的根地址
> 5. 同一个 bundle 不能同时出现在 `remoteBundles` 和 `subpackages` 中

---

## 四、本项目加载时序图

```
game.js 执行
    │
    ├─ 1. TextDecoder polyfill
    ├─ 2. require('web-adapter.js')
    ├─ 3. require('loadConfig.js')
    ├─ 4. require('polyfills.bundle.js')
    ├─ 5. require('system.bundle.js')
    ├─ 6. Canvas 尺寸设置
    │
    ├─ 7. tt.loadSubpackage('ammo')
    │      │
    │      ├─ success ──→ initEngine()
    │      │                  │
    │      │                  ├─ System.import('import-map.json')
    │      │                  ├─ System.import('cc')        ← 引擎加载
    │      │                  ├─ System.import('application.js')
    │      │                  ├─ module.default({ canvas })  ← 应用初始化
    │      │                  ├─ require('engine-adapter.js')
    │      │                  ├─ require('k-cocos.js')       ← 扩展库
    │      │                  └─ Game Started!
    │      │
    │      └─ fail ──→ console.error(...)
    │
    └─ (同时) 引擎内部自动加载各分包资源
           ├─ scripts 分包
           ├─ res_remote1 分包
           ├─ MoreGames 分包
           └─ resources (远程CDN)
```

---

# 第二部分：转换操作步骤

---

## 五、从 Web 构建到 TT 小游戏的完整流程

### 第1步：Cocos Creator 构建 Web 版本

使用 Cocos Creator 3.6.2 构建 Web 平台版本，输出到 `base/` 目录。这是所有后续操作的基础。

**关键产出：**
- `cc.js` — Cocos 引擎核心
- `assets/` — 所有资源包
- `src/` — 编译后的脚本和配置
- `config.json` — 游戏数据配置

### 第2步：创建 TT 小游戏项目结构

**需要创建/迁移的文件清单：**

| 文件 | 来源 | 说明 |
|------|------|------|
| `game.js` | 手动编写 | 小游戏启动入口，替代 index.html |
| `game.json` | 手动编写 | 声明分包结构、设备方向等 |
| `project.config.json` | 手动编写 | 项目AppID等基础信息 |
| `engine-adapter.js` | Cocos 生成/修改 | TT平台引擎适配 |
| `web-adapter.js` | Cocos 生成/修改 | Web API 适配层 |
| `application.js` | 从 base 复制 | 应用入口模块 |
| `cocos-js/cc.js` | 从 base 复制/裁剪 | 引擎核心 |
| `src/` | 从 base 复制/修改 | 脚本和设置 |
| `assets/` | 从 base 复制 | 资源文件 |

### 第3步：分包规划

抖音小游戏对主包大小有限制（通常 4MB），因此必须合理分包。

**分包策略：**

```
主包 (~4MB):
  ├── cc.js (1.7MB)          # Cocos 引擎核心
  ├── engine-adapter.js       # 引擎适配
  ├── web-adapter.js          # Web适配
  ├── game.js                 # 启动入口
  ├── application.js          # 应用模块
  ├── src/settings.json       # 配置
  ├── src/import-map.json     # 模块映射
  └── assets/internal/        # 内部资源

分包:
  ├── ammo (1.5MB)            # 物理引擎 (按需加载)
  ├── scripts (~540KB)        # 游戏逻辑脚本
  ├── res_remote1             # 额外资源
  └── MoreGames (~7KB)        # 交叉推广
```

### 第4步：配置文件编写

#### 4.1 project.config.json

```json
{
  "setting": {
    "urlCheck": false
  },
  "appid": "mgox8hu23gbtdkt4",
  "projectname": "Golden_Shovel_Synthesis"
}
```

#### 4.2 game.json — 分包声明

```json
{
  "deviceOrientation": "portrait",
  "openDataContext": "",
  "subpackages": [
    { "name": "scripts",    "root": "subpackages/scripts/" },
    { "name": "res_remote1", "root": "subpackages/res_remote1/" },
    { "name": "MoreGames",  "root": "subpackages/MoreGames/" },
    { "name": "ammo",       "root": "subpackages/ammo/" }
  ]
}
```

> **要点：** 每个分包都需要在 game.json 中显式声明，否则 TT 开发者工具无法识别。

#### 4.3 game.js — 启动入口（最核心文件）

```javascript
// ========== game.js 核心结构 ==========

// 1. TextDecoder 兼容性处理（TT平台部分设备缺失）
if (typeof TextDecoder === 'undefined') {
    TextDecoder = function () { /* polyfill */ };
    TextDecoder.prototype.decode = function (input) { /* ... */ };
}

// 2. 加载适配器
require('./web-adapter.js');

// 3. 加载配置
require('./src/loadConfig.js');

// 4. 加载 polyfill 和 SystemJS
require('./src/polyfills.bundle.js');
require('./src/system.bundle.js');

// 5. 画布设置（适配设备像素比）
const canvas = window.__canvas;
const systemInfo = tt.getSystemInfoSync();
const dpr = systemInfo.pixelRatio;
canvas.width = systemInfo.screenWidth * dpr;
canvas.height = systemInfo.screenHeight * dpr;

// 6. 定义引擎初始化函数
function initEngine() {
    System.import('./src/import-map.json')
        .then(function (data) {
            System.addImportMap(data);
            System.warmup();
            return System.import('cc');
        })
        .then(function () {
            return System.import('./application.js');
        })
        .then(function (module) {
            return module.default({
                findCanvas: function() { return canvas; }
            });
        })
        .then(function () {
            require('./engine-adapter.js');
            require('src/assets/scripts/libs/k-cocos.js');
            console.log('Game Started');
        });
}

// 7. 先加载 ammo 分包，再初始化引擎
tt.loadSubpackage({
    name: 'ammo',
    success: function () {
        initEngine();
    },
    fail: function (res) {
        console.error('Failed to load ammo subpackage', res);
    }
});
```

### 第5步：转换操作步骤（可复用）

以下是将任意 Cocos Creator Web 构建转换为 TT 小游戏的标准步骤：

```
Step 1: 创建目标目录
    mkdir bytedance-mini-game

Step 2: 新建平台文件
    ├── 编写 game.js         (入口，含 polyfill + 分包加载 + 引擎初始化)
    ├── 编写 game.json       (分包声明)
    ├── 编写 project.config.json (AppID)
    ├── 获取 engine-adapter.js   (从 Cocos 或自行编写)
    └── 获取 web-adapter.js      (从 Cocos 或自行编写)

Step 3: 复制不变文件
    cp base/application.js → bytedance-mini-game/
    cp base/assets/internal/ → bytedance-mini-game/assets/internal/
    cp base/src/assets/scripts/libs/ → bytedance-mini-game/src/assets/scripts/libs/

Step 4: 复制并修改引擎
    cp base/cocos-js/cc.js → bytedance-mini-game/cocos-js/cc.js
    (如需分离 ammo：裁剪 cc.js 并创建 ammo 分包)

Step 5: 资源包 → 分包 (index.js 改名 game.js)
    mv base/assets/scripts/   → subpackages/scripts/   (index.js → game.js)
    mv base/assets/MoreGames/ → subpackages/MoreGames/ (index.js → game.js)
    mv base/assets/res_remote1/ → subpackages/res_remote1/ (index.js → game.js)

Step 6: 大资源包 → CDN
    上传 base/assets/resources/ → CDN 服务器
    (不放入小游戏包)

Step 7: 修改配置
    修改 src/settings.json:
      - platform → "bytedance-mini-game"
      - subpackages → 声明分包名
      - remoteBundles → ["resources"]
      - server → CDN 地址
      - physicsEngine → 按需调整
      - plugins.jsList → 清空 (改到 game.js require)

Step 8: 转换 import-map
    src/import-map.json → src/import-map.js (转为 JS 模块)

Step 9: 复制并适配 src/ 下的运行时文件
    loadConfig.js, polyfills.bundle.js, system.bundle.js, chunks/bundle.js
    (可能需要针对小游戏平台重新构建)

Step 10: 创建 bundle-scripts 目录
    cp assets/internal/index.js → src/bundle-scripts/internal/index.js
    修改后的 main/index.js → src/bundle-scripts/main/index.js
    创建 resources/index.js 占位

Step 11: 在 TT 开发者工具中测试验证
```

---

# 第三部分：本项目修改记录

---

## 六、关键修改点复盘（Backup → Final 的差异）

### 修改1：Ammo 物理引擎分包化

**问题：** 物理引擎 (ammo.js, ~1.5MB) 嵌入主包会导致超出包大小限制。

**解决方案：**
1. 将 `instantiated-64c3001d.js` (1.5MB) 移入 `subpackages/ammo/` 目录
2. 在 `subpackages/ammo/` 下创建一个 `game.js` 作为分包入口
3. 在 `cocos-js/` 下添加 `wait-for-ammo-instantiation.js` 用于等待加载
4. 在 `cocos-js/` 下添加 `instantiated-64c3001d.js` (57 bytes) 引用文件
5. 在 `game.json` 中声明 ammo 分包

**文件变化：**
```
新增:
  subpackages/ammo/game.js                   (25 bytes, 分包入口)
  subpackages/ammo/instantiated-64c3001d.js  (1.5MB, 物理引擎)
  cocos-js/wait-for-ammo-instantiation.js    (147 bytes)
  cocos-js/instantiated-64c3001d.js          (57 bytes, 引用)
```

### 修改2：game.js 引擎初始化流程重构

**修改前（Backup）：**
```javascript
// 直接在 loadCC() 中初始化引擎
function loadCC() {
    System.import(...)
        .then(...)  // 直接初始化，不等待 ammo
}
loadCC();
```

**修改后（Final）：**
```javascript
// 1. 将引擎初始化封装为 initEngine() 函数
function initEngine() {
    System.import(...)
        .then(...)
}

// 2. 先加载 ammo 分包，成功后再初始化引擎
tt.loadSubpackage({
    name: 'ammo',
    success: function () {
        initEngine();
    },
    fail: function (res) {
        console.error('Failed to load ammo subpackage', res);
    }
});
```

> **关键点：** 必须确保 ammo 分包加载完成后再初始化引擎，否则物理系统初始化会失败。

### 修改3：settings.json 物理引擎配置

**修改前：**
```json
"physicsEngine": "physics-ammo"
```

**修改后：**
```json
"physicsEngine": "physics-builtin"
```

> **说明：** 将物理引擎从 ammo（完整 Bullet 物理）切换到 builtin（轻量内置物理）。ammo 仍作为分包加载，可能用于特定场景。

### 修改4：k-cocos.js 加载方式变更

**修改前（Backup）：** 在 settings.json 的 plugins 中声明
```json
"plugins": {
    "jsList": ["assets/scripts/libs/k-cocos.js"]
}
```

**修改后（Final）：** 在 game.js 中直接 require
```javascript
require('src/assets/scripts/libs/k-cocos.js');
```

> **原因：** 通过 game.js 直接 require 可以精确控制加载时机，确保在引擎初始化完成后再加载。

### 修改5：引擎文件瘦身

| 文件 | Backup | Final | 变化 |
|------|--------|-------|------|
| cc.js | 1.8MB | 1.7MB | -100KB (ammo 代码抽离) |
| main/index.js | 38KB | 21KB | -17KB (-45%) |
| loadConfig.js | 84KB | 77KB | -7KB |

---

## 七、关键文件修改对照表

| 文件 | 修改内容 | 原因 |
|------|----------|------|
| `game.js` | 新增 ammo 分包加载 + initEngine() 封装 | 确保物理引擎先于引擎初始化加载 |
| `game.js` | 新增 `require('k-cocos.js')` | 从 plugins 迁移到手动加载，控制时机 |
| `game.json` | 新增 ammo 分包声明 | 平台需要声明才能识别分包 |
| `settings.json` | `physicsEngine`: ammo → builtin | 切换默认物理引擎 |
| `settings.json` | `plugins.jsList`: 清空 | k-cocos 改由 game.js require |
| `cc.js` | 体积减小 ~100KB | 物理引擎代码抽离到分包 |
| `main/index.js` | 体积减小 45% | 代码优化/未使用模块移除 |

---

# 第四部分：问题排查与日常维护

---

## 八、常见问题与排查清单

### 问题1：主包超过大小限制

**症状：** TT 开发者工具提示主包超过 4MB
**排查：**
- [ ] 检查 cc.js 大小，是否已提取 ammo 物理引擎
- [ ] 检查是否有大资源文件未放入分包
- [ ] 使用 `du -sh` 统计各目录大小
- [ ] 确认分包在 game.json 中正确声明

### 问题2：分包加载失败

**症状：** 控制台报错 "Failed to load subpackage"
**排查：**
- [ ] game.json 中分包路径是否正确 (`"root": "subpackages/xxx/"`)
- [ ] 分包目录是否存在且包含 game.js 入口文件
- [ ] 分包名称是否与 `tt.loadSubpackage({ name: "xxx" })` 一致
- [ ] 检查文件路径大小写是否匹配

### 问题3：物理引擎加载异常

**症状：** 游戏中物理效果不正常或报 "ammo not found" 类错误
**排查：**
- [ ] ammo 分包是否在引擎初始化之前加载完成
- [ ] `cocos-js/wait-for-ammo-instantiation.js` 是否存在
- [ ] `cocos-js/instantiated-64c3001d.js` 引用是否正确
- [ ] settings.json 中 `physicsEngine` 配置是否匹配
- [ ] game.js 中的加载顺序：ammo 分包 → initEngine()

### 问题4：TextDecoder 兼容性问题

**症状：** 部分设备上报 "TextDecoder is not defined"
**解决：** 在 game.js 最顶部添加 polyfill：
```javascript
if (typeof TextDecoder === 'undefined') {
    TextDecoder = function () {};
    TextDecoder.prototype.decode = function (input) {
        var s = '';
        for (var i = 0; i < input.length; i++) {
            s += String.fromCharCode(input[i]);
        }
        return s;
    };
}
```

### 问题5：画布尺寸不正确

**症状：** 游戏画面模糊或不居中
**解决：** 在 game.js 中正确设置画布尺寸：
```javascript
const canvas = window.__canvas;
const systemInfo = tt.getSystemInfoSync();
const dpr = systemInfo.pixelRatio;
canvas.width = systemInfo.screenWidth * dpr;
canvas.height = systemInfo.screenHeight * dpr;
```

### 问题6：第三方库加载时机问题

**症状：** 自定义库（如 k-cocos.js）未生效
**排查：**
- [ ] 如果库依赖 `cc` 命名空间，必须在引擎初始化后加载
- [ ] 使用 game.js 中 `require()` 代替 settings.json 的 plugins.jsList
- [ ] 确保 require 路径正确

### 问题7：远程资源 CDN 加载失败

**症状：** 资源加载超时或 404
**排查：**
- [ ] CDN 地址是否正确（本项目：`https://cdn-corp.leyouxi.xyz/tiktok/remote/...`）
- [ ] CDN 是否支持 HTTPS
- [ ] settings.json 中 `server` 字段是否配置正确
- [ ] 抖音开发者后台是否配置了合法域名

---

## 九、马甲包替换指南

> 基于已打好的抖音包，快速出一个马甲包需要替换以下内容。

### 9.1 替换 AppID

| 项目 | 内容 |
|------|------|
| **当前值** | `mgox8hu23gbtdkt4` |
| **文件位置** | `bytedance-mini-game/project.config.json` |

**操作：**
```json
// project.config.json
{
  "appid": "mgox8hu23gbtdkt4",        // ← 改成新的 AppID
  "projectname": "Golden Shovel Synthesis"  // ← 同步改名
}
```

---

### 9.2 替换广告 ID

| 项目 | 内容 |
|------|------|
| **当前值** | `ad7586890685237200952`（激励视频广告） |
| **文件位置** | `bytedance-mini-game/subpackages/scripts/game.js` |
| **代码位置** | `PlatformDefault` 类的 `rewardVideo` 方法中 |

**操作：** 在 `subpackages/scripts/game.js` 中搜索替换：
```
ad7586890685237200952  →  你的新广告ID
```

> **说明：** 这是目前唯一的 TT 格式广告 ID（`ad` + 数字）。文件是压缩的单行 JS，直接全文搜索替换即可。

---

### 9.3 替换 Splash 启动封面图

| 项目 | 内容 |
|------|------|
| **文件名** | `2f7e6b24-af98-4749-9ef2-23564a7c0345.jpg` |
| **所属资源包** | `resources`（CDN 远程，不在本地包内） |
| **CDN 完整路径** | `https://cdn-corp.leyouxi.xyz/tiktok/remote/Golden_Shovel_Synthesis/v1.1/resources/native/2f/2f7e6b24-af98-4749-9ef2-23564a7c0345.jpg` |
| **引用位置** | `startLoadingScene` 场景中的 `jbg`（加载背景）节点 |

**操作：**

1. 复制整个 CDN `resources/` 目录到新路径
2. 在新目录中替换 `resources/native/2f/2f7e6b24-af98-4749-9ef2-23564a7c0345.jpg` 为新封面图（**必须同名**）
3. 修改 `src/settings.json` 的 `server` 字段指向新 CDN 地址（见 9.6）

> **说明：** CDN 不支持原地覆盖，必须复制到新目录生成新地址。因为 `server` 字段是所有远程资源的根路径，需要把整个 `resources/` 目录都复制过去，仅替换其中的封面图文件。

---

### 9.4 替换 Sidebar Icon（侧边栏 Logo）

| 项目 | 内容 |
|------|------|
| **文件名** | `73d1e4a8-af44-418b-a0fc-d060dab2a0d6.png` |
| **所属资源包** | `MoreGames` 分包（本地包内） |
| **抖音包内路径** | `bytedance-mini-game/subpackages/MoreGames/native/73/73d1e4a8-af44-418b-a0fc-d060dab2a0d6.png` |

**操作：** 直接用新图片覆盖（保持同名），建议 128×128 PNG。

---

### 9.5 替换 Sidebar 游戏名

| 项目 | 内容 |
|------|------|
| **当前文本** | `Golden Shovel Synthesis` |
| **文件位置** | `bytedance-mini-game/subpackages/MoreGames/import/01/014aad7f2.json` |

**操作：** 在 `014aad7f2.json` 中搜索 `"Golden Shovel Synthesis"` 替换为新名字。

---

### 9.6 马甲包替换速查表

| # | 替换内容 | 文件 | 位置 | 操作 |
|---|----------|------|------|------|
| 1 | **AppID** | `project.config.json` | `"appid"` 字段 | 改为新 AppID |
| 2 | **项目名** | `project.config.json` | `"projectname"` 字段 | 改为新名字 |
| 3 | **广告 ID** | `subpackages/scripts/game.js` | 搜索 `ad7586890685237200952` | 替换为新广告 ID |
| 4 | **Splash 封面** | CDN: `resources/native/2f/2f7e6b24-...jpg` | CDN 远程 | 新目录中同名替换 |
| 5 | **Sidebar Icon** | `subpackages/MoreGames/native/73/73d1e4a8-...png` | 本地包内 | 同名覆盖 |
| 6 | **Sidebar 名字** | `subpackages/MoreGames/import/01/014aad7f2.json` | 搜索文本 | 字符串替换 |
| 7 | **CDN 地址** | `src/settings.json` | `"server"` 字段 (第48行) | 改为新 CDN URL |

> **出包流程：** 复制整个 `bytedance-mini-game/` → 按上表 7 步替换 → TT 开发者工具验证 → 上传发布

---

## 十、后续打包其他TT小游戏时的注意事项

1. **先确认包大小限制** — 抖音小游戏主包限制可能会随政策更新，打包前先查看最新文档
2. **优先考虑分包** — 物理引擎、大型资源、非首屏功能模块都应该放入分包
3. **备份原始构建** — 每次修改前先备份 (`_backup`)，方便对比排查问题
4. **game.js 是核心** — 所有加载顺序、兼容性处理、平台适配都在这里控制
5. **远程资源用 CDN** — 大资源文件走 CDN 加载，减轻包体积压力
6. **TT开发者工具实测** — 每次修改后都在开发者工具中验证，不要等到最后再测
7. **关注 settings.json** — 物理引擎、插件列表、服务器地址等关键配置都在这里
8. **TextDecoder 兼容** — TT 平台低版本设备可能缺失，务必添加 polyfill

---

*本文档基于 2026-02-11 的项目状态整理，供后续 TT 小游戏打包参考。*

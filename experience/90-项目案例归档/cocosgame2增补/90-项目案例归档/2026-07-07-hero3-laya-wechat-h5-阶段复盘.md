> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-07-07-hero3-laya-wechat-h5-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# hero3 Laya 微信小游戏转 H5 阶段复盘

日期：2026-07-07  
项目：`myprojects/hero3`  
阶段：微信小游戏包还原为本地 H5，可本地服务启动并进入主页

## 产物

- H5 工程：`myprojects/hero3/webprojects/h5`
- 构建脚本：`myprojects/hero3/logs/scripts/build_h5.js`
- 构建报告：`myprojects/hero3/logs/h5_build_report.json`
- 验证报告：`myprojects/hero3/logs/h5_verify_report.json`
- 验证截图：`myprojects/hero3/logs/h5_verify_mobile.png`
- DragonBones 导出脚本：`myprojects/hero3/logs/scripts/export_laya_sk_to_dragonbones.js`
- DragonBones 示例产物：`myprojects/hero3/output/dragonbones/hero_1`
- DragonBones 批量产物：`myprojects/hero3/output/dragonbones/all_spine`

## 关键结论

- hero3 不是 Cocos 包，而是 Laya 小游戏包：主包 `game.js` 里包含 AMD 风格 `define(...)` 模块和 Laya 引擎模块。
- H5 不能提前暴露全局 `wx`。`ggLibs/index.js` 会通过 `typeof wx` 选择微信适配器；H5 应让它走内置 `gg.webAdapter.js`。
- `index.js` 首屏先调用 `wx.loadSubpackage({ name: "page" })`，所以 H5 适配层必须把这一步改成真实加载 `page/game.js`，后续 `firstLoad()` 里的分包也要通过 `gg.webAdapter.loadSubPack` 真实加载。
- 远程表格接口 `https://www.greatgood666.com/gameTable/getGameTable` 必须下载为本地 JSON，并在 XHR shim 里转向本地文件。
- CDN 资源需要从代码、场景 JSON 和表格配置三路收集；本次构建下载 342 个远程文件，失败 0 个，并为角色 Spine 生成 210 个本地 fallback。
- `hero_1.sk` 是 Laya `LAYAANIMATION:1.7.0` 二进制骨骼资源，文件内标记为 `DragonBone`。无需从零反解二进制，可以启动本地 H5，借 `Laya.Templet.parseData(null, arrayBuffer)` 完成反序列化，再把运行时对象映射为 DragonBones 播放用 `ske.json/tex.json`。

## 踩坑

- `game.js` 里有多个 `wx.loadSubpackage`，不能做“第一个匹配替换”；入口替换要定位到 `index.js` 模块里的 `name: 'page'`。
- `customEnv:{wx:wx}` 出现不止一次；只替换第一处仍会触发 `ReferenceError: wx is not defined`，要全量替换为 `window.wx || {}`。
- 自定义 XHR shim 转发真实 XHR 时，`responseType="arraybuffer"` 不能读取 `responseText`，否则会触发 `InvalidStateError`。
- Headless Chromium 会拦截音频自动播放，表现为 `Bgm_Main.mp3 net::ERR_ABORTED` 和 autoplay warning；这不是资源缺失。
- 角色表里 `resPath` 的基础名如 `Mod_Human_001.sk` 远端不存在，实际常用资源是 `a/b` 变体；H5 构建中需要用 `a` 版补基础名 fallback，用 `a/b` 补缺失皮肤 fallback。
- DragonBones 反导时要注意 mesh：Laya 的 `bones` 是每个顶点的骨骼索引串，`weights` 是 `x/y/weight` 三元组；导出 DragonBones 5.x JSON 时要转成 `vertices/weights/bonePose/slotPose`，否则只会得到图片槽位，蒙皮播放会丢。
- Laya texture UV 反算 atlas 坐标时会有浮点尾差，写 `tex.json` 前应取整；旋转切片要根据 display UV 判断并写入 `rotated: true`。

## 验收

- 本地服务：`http://127.0.0.1:8088/`
- Playwright 手机竖屏验证结果：
  - `hasLaya: true`
  - `hasGG: true`
  - 画面进入主页，可见“第1章 火苗窜动”和“开始游戏”按钮
  - 无脚本异常、无资源 404
  - 仅剩浏览器音频自动播放 warning
- DragonBones 导出验证：
  - 输入：`webprojects/h5/remote/cdn.greatgood666.com/YingXiongWuDi_2d/2dSpine_1210/hero_1.sk`
  - 输出：`hero_1_ske.json`、`hero_1_tex.json`、`hero_1.png`
  - 解析计数：72 bones、33 slots、1 skin、33 subtextures、5 animations
  - 已保留 image/mesh display、slot 显隐/透明度帧、骨骼位移/旋转/缩放帧；本样例无 FFD、drawOrder、event 帧
- DragonBones 批量导出验证：
  - 命令：`export_laya_sk_to_dragonbones.js --all --out myprojects/hero3/output/dragonbones/all_spine --no-dump`
  - 结果：207 个 `.sk` 全部导出成功，失败 0
  - 产物：207 个子文件夹，829 个文件，总大小约 144M
  - 汇总计数：8395 bones、4915 slots、207 skins、6077 subtextures、1233 animations
  - 11 个资源包含 transform/path constraints 尚未映射到 DragonBones JSON，已在 `batch_export_report.json` 的 `skipped` 字段中标出

## 后续建议

- 若要覆盖战斗流程，需要继续点击“开始游戏”后按需补抓 3D 战斗特效、章节地图和战斗音效。
- 当前 H5 适配优先保证启动与主页，本地后端接口为 mock；涉及排行榜、房间、PVP 上传等线上功能应继续按路径补接口行为。
- 若要批量反导更多 `.sk`，直接复用 `export_laya_sk_to_dragonbones.js --all --out <dir> --no-dump`；单个资源用 `--sk <relative sk path> --name <name>`。如遇 transform/path constraints 或 FFD，需要针对具体资源再做一次播放器回归。

> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-package-font-and-remote-split-stage-review.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 包体、字体图集与远程 Bundle 阶段复盘

## 目标

在不改变作者资源和 Cocos UUID 的前提下，降低抖音小游戏上传包体；普通 PNG 接受 70–90 质量，字体图集必须保持 1:1 像素；准备正式 CDN 分包但不在本阶段部署。

## 根因

此前构建后 PNG 处理把 `input-fonts` 字体图集也交给了有损量化，包体约 187MB，但会把字形覆盖数据纳入有损路径。远程验证构建又没有复用相同后处理，因此与正式包 PNG 哈希不一致。

## 动作

- `tools/build/compress_png_output.py` 仅在生成目录工作，不改 `assets` 源文件。
- 普通美术 PNG 使用 `pngquant --quality=70-90`；`input-fonts` 图集改用逐像素一致的无损 PNG 重编码，透明度变化自动回退。
- `build_remote_validation.py` 在远程资源哈希验证前复用同一后处理，避免候选包与正式包不一致。
- Cocos CLI 构建仍由 `tools/build/build_douyin.py` 完成，不启动编辑器运行预览。

## 验证证据

- 正式 CLI：`temp/douyin-cli/20260928-155431-cli.log`，成功，产物 236,375,722 字节，脚本错误0。
- PNG：742张解码通过；68张字体图集与未压缩 CLI 原图逐像素一致，节省约51.44MB；普通 PNG 与字体图集合计节省55.13MB。
- 远程候选：`temp/douyin-cli/20260928-155519-remote-cli.log`，本地上传估算12,154,844字节；PNG/WAV/TTF/BIN与正式基线哈希完全一致；远程无可执行文件。
- staging：`temp/remote-stage-20260928-1556`，1668个文件，manifest与verification已生成。
- 业务回归：存档桥接、任务事件/事务/UI、字体 Bundle 19+44项、TypeScript均通过。

## 遗留风险

正式 CDN 地址、上传权限和真机冷启动尚未配置，不能把本地远程验证当成发布完成；236MB的本地调试包仍不是最终 CDN 上传包体。排行榜和输入文字当前继续使用已验证的系统字/无损字体策略。

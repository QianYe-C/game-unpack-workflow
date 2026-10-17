> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-remote-bundle-current-rebuild-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 当前源远程分包候选重建

## 目标

让远程分包候选与最近的 Cocos 场景修复保持同一源快照，并重新确认抖音主包上传估算、资源字节一致性和远程目录安全边界。

## 动作

运行 `python3 tools/build/build_remote_validation.py --server http://127.0.0.1:8797/ --local-validation`，再用 `stage_remote_distribution.py` 生成独立 staging。没有部署 CDN、没有改正式平台配置，也没有启动编辑器预览。

## 验证证据

- CLI：`/Users/jiaojian/Documents/idlecat/idlecat/temp/douyin-cli/20260928-175409-remote-cli.log`
- 产物：`/Users/jiaojian/Documents/idlecat/idlecat/build/remote-validation`
- staging：`/Users/jiaojian/Documents/idlecat/idlecat/temp/remote-stage-20260928-1755`
- 本地上传估算：12,156,777 字节；远程资源：218,652,612 字节；主包预算通过。
- 742 PNG、16 WAV、2 TTF、44 BIN 与正式基线字节多重集一致；远程目录没有 JS/WASM/MJS 可执行文件；脚本错误为空。

## 遗留风险

这是本地候选验证。正式 CDN 上传、HTTPS 地址、抖音模拟器冷启动、断网/缓存恢复和真机验证仍按用户要求延后，不能把候选结果当成正式发布完成。

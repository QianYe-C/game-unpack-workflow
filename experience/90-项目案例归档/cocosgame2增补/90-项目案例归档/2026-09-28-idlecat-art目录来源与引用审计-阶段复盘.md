> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-art目录来源与引用审计-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# idlecat `assets/art` 目录来源与引用审计

2026-09-28。

## 结论

`assets/art` 是早期从 Unity 包/Frida 内存导出流程留下的旧 ID 命名素材目录；当前规范目录是 `assets/native-art`。它不是可以直接删掉的临时缓存，因为 Cocos 序列化文件仍可能按旧 UUID 持有引用。

本轮对 `assets/art/*.meta` 的 670 个 UUID 扫描全部工程序列化与脚本文件：只有 1 个旧 UUID 在目录外仍被使用：`assets/gun-module/Gun_UI__SafeArea.prefab` 的钻石图标 `sharedassets0.assets__904__currency_dia_1.png`。其余 669 张图片没有运行时序列化 UUID 引用。源数据里出现的 `art` 字段是原版导出记录，不能当作 Cocos 资源引用。

## 处理边界

本轮没有删除或文本替换 `.prefab/.meta`。下一步要用 Cocos MCP 将 Gun prefab 的 1 个 SpriteFrame 重绑到 `assets/native-art/sprites/_UI/currency_dia_1__sharedassets0.assets_904.png`，保存后做场景断链和完整 CLI 构建；确认包体和运行画面都不变后，才能分批移除旧目录。证据：`idlecat/docs/evidence/art-usage-audit-20260928.json`。

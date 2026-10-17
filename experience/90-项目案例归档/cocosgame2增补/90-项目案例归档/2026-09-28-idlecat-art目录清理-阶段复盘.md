> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-28-idlecat-art目录清理-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat `assets/art` 旧素材目录清理（2026-09-28）

## 结论

`assets/art` 是早期 Unity/Frida 内存导出留下的旧素材目录。引用审计确认 670 张 PNG 中只有 `sharedassets0.assets__904__currency_dia_1.png` 的旧 UUID 仍被 `assets/gun-module/Gun_UI__SafeArea.prefab` 使用，其余 669 张没有目录外 Cocos UUID 引用。

本轮通过 Cocos MCP 的 `cocos_asset.delete` 删除了 668 张 PNG 及对应 `.meta`，没有直接修改任何 `.scene/.prefab/.anim/.meta` 序列化内容。剩余钻石图和 `assets/native-art/sprites/_UI/currency_dia_1__sharedassets0.assets_904.png` 尺寸与 SHA-256 相同。

## 验证

- `cocos_scene.validate_scene`：`brokenCount=0`。
- `python3 tools/build/build_douyin.py`：成功，产物 236,382,580 bytes，脚本错误 0。
- 构建后 PNG 质量保持 70–90，242 张参与压缩、68 张字体图集保护。
- 构建产物不再出现 `assets/art` 路径。

## 遗留

Cocos 编辑器对 `Gun_UI__SafeArea.prefab` 进入 prefab 编辑时抛出 `PrefabSceneProxy ... null.instance`，因此没有用文本替换强行重绑最后一个旧 UUID；该图先保留，避免破坏枪械面板。后续若 Cocos MCP 能正常加载该 prefab，再将引用换到 `assets/native-art` 后删除最后一张。

证据：`idlecat/docs/evidence/art-cleanup-20260928.json`。

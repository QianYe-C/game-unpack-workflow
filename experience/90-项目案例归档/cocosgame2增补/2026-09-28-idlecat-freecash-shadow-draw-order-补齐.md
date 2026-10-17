> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-freecash-shadow-draw-order-补齐.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat ADS Free 阴影绘制顺序补齐

## 现象

首页 ADS Free 图标周围出现黑色覆盖，图标或 `Free` 文字被半透明阴影压住。点击区扩大后，根节点的 Circle 阴影已经拆到 `ShadowVisual`，但该节点排在按钮内容末尾，仍会覆盖前面的内容。

## 处理

通过 Cocos MCP 在 `loading.scene`、`Main_UI.prefab`、`MainHUD.prefab` 的 `FreeCash_Btn__u736` 下把 `ShadowVisual` 调到子节点索引 0。根 `cc.Sprite` 继续关闭，独立阴影保留原 Circle、SIMPLE、88.96×41、`FreeCashAlpha68627.mtl` 和 175/255 透明度；160×160 只用于命中区。

## 验证

- `node tools/migration/verify_home_hit_areas.mjs`：通过，阴影为首子节点，视觉资源与点击区分离。
- `node tools/migration/verify_presentation_rules.mjs`：通过。
- `python3 tools/migration/verify_freecash_prefabs.py`：通过。
- `python3 tools/build/build_douyin.py`：通过，`temp/douyin-cli/20260928-175029-cli.log`，脚本错误 0。
- 证据：`/Users/jiaojian/Documents/idlecat/idlecat/docs/evidence/home-freecash-shadow-20260928.json`。

未启动 Cocos 编辑器预览，避免卡死；正式浏览器/真机像素验收仍需用户刷新后检查 ADS Free 图标。

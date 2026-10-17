# 远程 Bundle 上线发布模板

## 使用说明（示例与通用边界）
- 文中 Bundle 名（如 `res_ZombiesDieFirst`、`cfg_Train`）和发布记录为示例。
- 实际发布请替换为真实包名、环境与时间。
- 重点是灰度节奏、回滚路径和发布门禁，不是某一组固定包名。

## 1. 发布信息

- 发布日期：`YYYY-MM-DD`
- 发布人：`@owner`
- 环境：`test / staging / prod`
- 版本号：`vX.Y.Z`
- 影响 Bundle：`res_ZombiesDieFirst, cfg_Train, ...`

## 2. CDN 目录规范

远程目录统一使用 `retorm/`。

```text
https://cdn.example.com/retorm/
  game/
    config.21759.json
    import/
    native/
    index.21759.js
  res_ZombiesDieFirst/
    config.6d748.json
    import/
    native/
    index.6d748.js
  cfg_Train/
    config.d6e97.json
    import/
    native/
    index.d6e97.js
```

要求：
- 保持构建产物原始目录结构，不扁平化。
- 同步上传同一 Bundle 的 `config.*.json + import + native (+ index.*.js)`。
- 开启 CDN 缓存时，确保新版本文件可立即命中（新哈希文件天然可并存）。

## 3. 发布前检查清单

- [ ] `retorm/` 下目标 Bundle 文件齐全。
- [ ] `config.*.json` 中依赖 Bundle 已可访问。
- [ ] `game.js` 远程目录后缀为 `retorm/`。
- [ ] 可用参数验证：`remoteServer`、`remoteBundles`。
- [ ] 测试环境冷启动通过。

## 4. 灰度发布步骤

1. 仅灰度 1 个玩法 Bundle（示例：`res_ZombiesDieFirst`）。
2. 启动参数示例：

```text
?remoteServer=https://cdn.example.com/&remoteBundles=res_ZombiesDieFirst
```

3. 观察 10~30 分钟：
   - 资源加载成功率
   - 首次进入耗时
   - 404 / 下载失败 / JSON 解析错误
4. 无异常后放量到完整远程列表。

## 5. 全量发布参数示例

```text
?remoteServer=https://cdn.example.com/&remoteBundles=game,home,res,res_ZombiesDieFirst,res_ZCrossFire,res_RussianBlock,cfg_Train,cfg_Level1
```

> 未传 `remoteBundles` 时，将使用代码内默认远程 Bundle 列表。

## 6. 回滚方案

### 方案 A（最快）

- 清空远程配置，让客户端回落本地：
  - 不传 `remoteServer`
  - 或删除存储键 `remoteServer/remoteBundles`

### 方案 B（定向）

- 保留 `remoteServer`，仅下掉异常 Bundle：
  - 从 `remoteBundles` 中移除故障包

### 方案 C（CDN 回滚）

- 将故障 Bundle 目录恢复为上一稳定版本（整包回滚，不要只替换单文件）。

## 7. 常见问题排查

### Q1: `config.xxx.json` 404

- 检查 `remoteServer` 是否最终指向 `.../retorm/`。
- 检查 Bundle 名是否和目录名完全一致（区分大小写）。

### Q2: `native/*` 或 `import/*` 404

- 说明只传了 `config` 或文件不完整，需补齐整个 Bundle 目录。

### Q3: 能启动但进玩法失败

- 检查玩法依赖包是否同时可访问（`deps`）。

### Q4: 更新后仍加载旧资源

- 清平台缓存（抖音开发者工具/真机缓存）。
- 确认引用的是新 `config.*.json` 与新哈希文件。

## 8. 发布记录（示例）

```text
2026-03-05 14:00  test  灰度 res_ZombiesDieFirst  成功
2026-03-05 16:00  test  扩展到 res_ZCrossFire     成功
2026-03-05 18:00  prod  全量发布                    成功
```

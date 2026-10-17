> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-07-21-vitasort-android-il2cpp-关卡随机还原-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# vitasort Android IL2CPP 关卡随机还原阶段复盘

## 目标

同时使用静态和动态方法恢复 Vita Sort 1.1.1 的关卡初始化与随机逻辑，输出分析文档、可控 seed 探针和可运行 H5。

## 阻塞

- IL2CPP 恢复 DLL 的方法体大多不可直接反编译，需要回到 ARM64/ISIL。
- App 带 Pairip 安装来源检查，错误安装来源的冷启动会打开 Google Play。
- 业务结果不仅由随机数决定，还受 win-rate tier、AB 表和持久化 child pointer 影响。

## 根因

- 关卡随机由多个无参 `System.Random` 组成；每个实例的 seed 来自线程随机流，线程流最初由系统加密随机数初始化。
- 题库和配置数组顺序参与随机索引，不能只复刻公式而忽略资源原序。
- 卡面 child 分配实际是持久化循环指针，不是 RNG。
- Google Play 跳转由 App 的 Pairip `LicenseActivity` 触发，不是自动化误点。

## 动作

1. 使用 Il2CppDumper + Cpp2IL ISIL 恢复关键调用顺序与数据结构。
2. 从 AssetBundle 导出两套 13 个题库池，从 Luban 二进制解出 Level/Card/Conflict 表。
3. 用 Frida 历史日志核对无参 Random 的内部带 seed 构造与 Fill 输出。
4. 将动态方式改成 attach-only，不再 spawn 或自动点击。
5. 在关卡入口建立主种子到 sub-seed 的明确注入契约。
6. 用 TypeScript 实现 System.Random、题面 parser、选题、类型补充、child pointer 与 Fill。
7. 构建 Seed Lab H5，提供分层棋盘、随机时间线、assignment 与 JSON 导出。

## 验证证据

- System.Random 与 .NET 的 0/1/1337/int 边界测试向量一致。
- `npm run lint` 与 `npm run build` 通过。
- seed 1337 指纹 `vs11-9d678419`，1338 为 `vs11-e63ea4fe`，回到 1337 后指纹恢复。
- 顺序玩法生成 15 张从 `-100` 开始的 order-pile 分类牌，模式切换无错误。
- 浏览器无 error/warn；375px 视口无页面级横向溢出。
- 历史动态 Fill 显示 type `10000202` 的 child 1/2/3 与静态队列行为一致。
- 新安装可 attach；错误 installer 导致的 Google Play 跳转根因已确认。

## 遗留风险

- 新安装后尚需用户手动进入关卡，再做一次同 master seed 的 App/H5 全量 Cell diff。
- win-rate tier 和 child pointer 必须作为输入状态记录，不能把“相同 seed”误写成“忽略所有其他状态也相同”。
- 本结论绑定 App 1.1.1；升级后二进制、表或题库数组变化都需重新校验。

## 可复用方法

- IL2CPP 方法体不可读时，metadata 用于定类型/字段，ISIL 用于恢复控制流，动态 hook 用于确认实际调用次序。
- 遇到多个无参 Random，应控制 `GenerateSeed` 或同等级的 seed 分发点，而不是只替换全局初始 seed。
- 对“确定性复刻”要显式列出所有非 RNG 状态，尤其是 AB 配置与 PlayerPrefs 指针。
- 授权/安装来源检查与业务动态分析应分离；采用 attach-only 可避免把启动门禁误判为脚本行为。

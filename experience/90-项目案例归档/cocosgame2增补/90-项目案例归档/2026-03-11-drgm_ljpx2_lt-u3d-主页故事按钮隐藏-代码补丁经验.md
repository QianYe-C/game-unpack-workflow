> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-03-11-drgm_ljpx2_lt-u3d-主页故事按钮隐藏-代码补丁经验.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-03-11 DRGM（ljpx2_lt）U3D 主页故事按钮隐藏代码补丁经验

## 问题背景
- 目标：隐藏主界面右侧“故事模式”按钮。
- 现象：仅修改资源内 `StoryButton.m_IsActive=false` 后，运行时按钮仍会出现（或出现不稳定）。

## 根因结论
- 资源层隐藏不是最终态，主页初始化脚本会在运行时重新设置按钮显示状态。
- 关键链路：
  - `HomePanel` 初始化流程会触发 `HomeCommon.UpdateVisual`。
  - `HomeCommon.UpdateVisual` 内部存在多次 `GameObject.SetActive(bool)` 调用。
- 结论：如果只改 prefab/asset 的初始 active，容易被运行时代码覆盖。

## 定位方法（可复用）
1. 用 UnityPy 确认目标节点与层级路径：
   - `HomePanel > HomeCommon > Buttons > StoryButton`
   - `HomeWindow > HomeCommon > Buttons > StoryButton`
2. 用 `WebGL_0309_1459.symbols.json` 建立函数名与 wasm 函数号映射，重点关注：
   - `HomeCommon_UpdateVisual`
   - `HomeCommon_Awake`
   - `GameObject_SetActive`
3. 用 `wasm2wat --generate-names` 反汇编，定位 `SetActive` 调用点与入参来源，确认存在运行时覆盖逻辑。

## 本次采用方案（代码层）
- 放弃“资源强制隐藏”，回滚 `.data` 到正常版本。
- 改为在 wasm 运行时逻辑里强制 `storyButton` 的 `SetActive(false)`：
  - 在 `HomeCommon_Awake` 对应函数段中，`call $f549`（`GameObject_SetActive`）前，将布尔入参强制为 `0`。
  - 实际做法：在该调用前插入 `i32.const 0` + `i32.and`，把原值归零。

## 关键经验
- 同一 UI 在多个容器中可能各有一份（`HomePanel` 与 `HomeWindow`），只改一处会漏。
- “看起来能关掉”不代表最终有效，必须区分“资源初值”与“运行时重设”。
- wasm 补丁前必须先做双备份（`.data` 与 `.wasm`），并准备可回滚路径。
- 反汇编后尽量做“最小改动补丁”（只改目标调用入参），降低联动风险。

## 验证门禁
- 静态验证：
  - `wasm-validate` 必须通过。
  - 反汇编复查补丁指令确实存在于目标函数上下文。
- 运行验证：
  - 强刷缓存后进入主界面确认“故事模式”按钮隐藏。
  - 同时检查“第X关”按钮、Logo、其他按钮无异常。

## 回滚策略
- 若补丁异常，先恢复 `WebGL_0309_1459.wasm` 备份，再回归验证。
- 不建议使用破坏性命令，统一通过“备份文件覆盖恢复”。

## 适用边界
- 适用于 IL2CPP WebGL 且可获取 `symbols.json` 的项目。
- 若无符号映射，定位成本会显著上升，建议优先改 C# 源码重新出包。

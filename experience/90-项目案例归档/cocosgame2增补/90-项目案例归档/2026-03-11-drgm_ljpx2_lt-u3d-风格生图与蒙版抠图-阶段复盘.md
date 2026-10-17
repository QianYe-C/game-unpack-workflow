> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-03-11-drgm_ljpx2_lt-u3d-风格生图与蒙版抠图-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-03-11 DRGM（ljpx2_lt）U3D 风格生图与蒙版抠图阶段复盘

## 目标
- 在不覆盖原图的前提下，为第1关分类图批量生成风格图（sidecar）。
- 回写阶段优先使用风格图，不存在风格图时自动回退原图。
- 探索“生图白底 + 蒙版扣除”得到可用透明贴图流程。

## 阻塞与现象
- 直接复用原图 alpha 会产生“假透明”，不符合需求。
- 边缘扩散抠图会误伤黑色描边，主体边缘被吃掉。
- 生图若输入原图，会明显继承原图形状，不符合“只用文字要素”的要求。
- 蒙版黑白语义不稳定，存在把主体当背景扣除的风险。
- 风格参考图较大时触发 `HTTP 413`（输入 token 超限）。

## 根因
- 蒙版提示词对“黑/白语义”约束不够，模型输出方向易反。
- 缺少“只允许扣白底”的后处理门禁，导致描边被误扣。
- 风格参考图未做预缩放，输入体积不可控。
- 生成链路阶段较多，若没有三图对照（原始图/蒙版图/结果图）很难快速定位问题。

## 动作
- 保留原图，输出统一 sidecar 后缀（`_restyle`），回写优先风格图并自动回退原图。
- 生图链路调整为：
  - 原图仅用于“要素文字提取”；
  - 生图仅输入风格参考图（`style-ref-only`）。
- 新增三图落盘能力：
  - 原始彩图：`*_rawcolor.png`
  - 蒙版图：`*_alphamask.png`
  - 结果图：`*_restyle*.png`
- 蒙版生成改为“原始彩图 + 蒙版提示词”单独生成，再对彩图执行扣除。
- 增加扣图门禁：
  - 自动选择蒙版极性（黑扣或白扣）；
  - 只允许在“原始彩图近白背景区域”扣除，禁止扣非白主体像素。
- 增加风格图预缩放（`--style-ref-max-side`，默认 768）规避 413。

## 验证证据
- 单图三联输出（fix2）：
  - `myprojects/drgm_ljpx2_lt/sourceImages/images/Main_Level_1/ct198_蓝发/*_restyle_textonly_fix2_rawcolor.png`
  - `myprojects/drgm_ljpx2_lt/sourceImages/images/Main_Level_1/ct198_蓝发/*_restyle_textonly_fix2_alphamask.png`
  - `myprojects/drgm_ljpx2_lt/sourceImages/images/Main_Level_1/ct198_蓝发/*_restyle_textonly_fix2.png`
- 报告：
  - `myprojects/drgm_ljpx2_lt/logs/nanobanana_edit_Main_Level_1_20260311_170553.json`
  - `sourceImageSentToModel=false`（生图未输入 source image）
  - `styleRefInfo.resized=true`（风格图已缩放）
- 像素校验：
  - `cut_nonwhite=0`（扣除区域无非白像素）。

## 结论与决策
- 当前方向“技术可跑通”，但实际美术效果仍不理想，已按需求暂停继续研究。
- 可复用成果保留在脚本参数与回写链路，不影响现有原图流程。

## 遗留风险
- 蒙版质量仍受模型稳定性影响，风格变化大时仍可能需要人工抽检。
- 仅靠白底扣图对复杂背景容错有限，若后续恢复该方向需先设定质量门禁样本集。

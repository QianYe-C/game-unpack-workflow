> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-08-11-light_up_sort-ios-unity-资源提取-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-08-11 Light Up Sort iOS Unity 资源提取阶段复盘

## 阶段结论

- 已从 `LightUpSort.app` 的 `Data/data.unity3d` 完成关卡与视觉资源提取。
- 共提取 68 份可读关卡 JSON，其中 `LevelListData` 明确引用 35 份主关卡。
- 共导出 331 个 Sprite、60 张独立纹理、95 个 OBJ、30 个 TTF、154 份材质 JSON 和 83 份 Shader 文本。
- 已为 68 个关卡生成俯视预览和总览图，全部通过文件完整性校验。

## 目标

- 在不改动原始 iOS App 的前提下，将关卡数据与可复用美术资源整理到规范项目目录。
- 恢复主关卡顺序，避免按 TextAsset 的物理顺序或文件名猜测。
- 对 Sprite 分图与底层合图进行分层管理，为后续编辑或重建保留稳定映射。

## 阻塞与根因

### 1. 原目录名包含空格，不符合项目命名规范

- 原输入目录为 `myprojects/light up sort/`。
- 新建规范目录 `myprojects/light_up_sort/`，在 `input/` 中用来源链接保留原包位置；没有移动或复制原始 App。

### 2. IL2CPP 包缺少业务 MonoBehaviour TypeTree

- `MonoBehaviour.read()` 无法直接展开 `LevelListData` 的业务字段。
- 根因是 iOS IL2CPP 构建对业务类型信息进行了裁剪。
- `LevelListData` 仍保留 Unity 通用 MonoBehaviour 头和序列化 PPtr 数组，因此可从原始字节恢复关卡引用链。

### 3. PathID 不是全包唯一键

- `data.unity3d` 内包含多个 SerializedFile，相同 PathID 会在不同文件中重复。
- 所有清单统一使用 `(assetsFile, pathId)` 作为对象主键，禁止只按 PathID 关联。

### 4. Texture2D 同时包含独立纹理、Sprite 底图和空字体占位

- 直接全量导出会把合图混入可编辑美术目录，并产生 36 个 `0 × 0` 字体占位报错。
- 通过 `Sprite.m_RD.texture` 建立底图引用：已裁切 Sprite 输出到 `sourceImages`，168 张底图只保留在日志中间层；60 张无 Sprite 引用的独立纹理正常输出。

## 动作

1. 读取工作流并建立 `myprojects/light_up_sort/` 六大目录。
2. 对 `data.unity3d` 建立对象类型与 SerializedFile 索引。
3. 直接导出 68 份关卡 TextAsset JSON。
4. 手工解析 `LevelListData` 的 PPtr 数组，恢复 35 个主关卡顺序。
5. 导出 Sprite、独立纹理、Mesh、Font、Material、Shader 和 App 外壳图片。
6. 生成关卡预览、资源拼图、对象清单和 SHA-256 摘要。

## 验证证据

- 关卡 JSON：68/68 可解析。
- 主关卡引用：35 个已解析，0 缺失，0 重复。
- 关卡预览：68/68 可打开。
- Sprite：331/331 可打开。
- 独立纹理：60/60 可打开。
- Sprite 底图中间件：168/168 可打开。
- Mesh：95/95 OBJ 非空且具有有效网格组。
- Font：30/30 具有有效字体文件头。
- 完整摘要：`myprojects/light_up_sort/sourceConfigs/extraction_summary.json`。

## 可复用经验

- Unity iOS 单包应优先检查 `App/Data/data.unity3d`，不要默认套用 Android Addressables 或 WebGL PackageManifest 链路。
- IL2CPP TypeTree 缺失不等于引用链丢失；业务对象若只含标准 PPtr 列表，可基于通用 MonoBehaviour 头恢复。
- 多 SerializedFile 环境必须使用 `(assetsFile, pathId)` 作为稳定对象标识。
- 可编辑美术目录只保留 Sprite 分图与独立纹理，底层合图作为可追溯中间件单独保存。

## 遗留风险

- 33 份非主关卡的具体运行时用途尚未动态验证，当前仅按编号和是否被主列表引用进行客观分类。
- 当前 Mesh 为裸 OBJ，材质映射独立保存；如需整套关卡 GLB，还需依据场景 Transform、MeshRenderer 和 Material 引用继续重建实例层级。
- 1 个 Shader 编译数据对象无法由当前 UnityPy 版本完整展开，不影响关卡 JSON、图片、模型或材质清单。

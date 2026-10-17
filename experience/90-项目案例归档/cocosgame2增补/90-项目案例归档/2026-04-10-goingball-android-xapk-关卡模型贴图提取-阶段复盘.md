> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-04-10-goingball-android-xapk-关卡模型贴图提取-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# 2026-04-10 Going Balls Android XAPK 关卡模型贴图提取阶段复盘

## 阶段结论
- 已完成 `Going Balls_3.24_APKPure.xapk` 解包。
- 已完成关卡 prefab 的 `obj + mtl + png` 提取，共导出：
  - `obj`：`732`
  - `mtl`：`732`
  - `png`：`435`
- 已完成关卡 prefab 的 `glb` 批量转换，共导出：
  - `glb`：`732`
  - 转换失败：`0`

## 项目目录
- 项目目录：`myprojects/goingball`
- 原始包：`myprojects/goingball/input/Going Balls_3.24_APKPure.xapk`
- 输入中间层：`myprojects/goingball/input`
- OBJ 工作区：`myprojects/goingball/sourceImages/level_prefabs_obj`
- GLB 输出：`myprojects/goingball/sourceImages/level_prefabs_glb`
- 报告目录：`myprojects/goingball/sourceConfigs/reports`

## 包体结构结论
- 这是标准 Android `XAPK + split APK` 结构：
  - `com.pronetis.ironball2.apk`
  - `config.arm64_v8a.apk`
- 关键 Unity 资源位于 `base.apk`：
  - `assets/aa/Android/levels_assets_all_*.bundle`
  - `assets/aa/Android/*unitybuiltinassets*.bundle`
  - `assets/bin/Data/data.unity3d`
- 关卡主体是 `Assets/Resources_moved/LevelPrefabs/**/*.prefab`，其中：
  - `000_NormalTiled` 共 `500` 个
  - 其余是 `bonus / dif / races / sbl` 等专题关卡 prefab

## 关键经验

### 1. 不能只加载 `levels` bundle，本地导出时要把 builtin 和 data 一起挂上
- 只读 `levels_assets_all_*.bundle` 时，部分材质贴图会解析失败。
- 把下面三份资源一起交给 `UnityPy.load(...)` 后，贴图链路才完整：
  - `levels_assets_all_*.bundle`
  - `*unitybuiltinassets*.bundle`
  - `data.unity3d`

### 2. 关卡 prefab 要按“层级实例”导，而不是按裸 Mesh 导
- 用户需要的是关卡段模型，不是散的基础网格。
- 这次稳定做法是：
  1. 读取 prefab 根节点
  2. 递归遍历子节点 `Transform`
  3. 找到 `MeshRenderer / SkinnedMeshRenderer`
  4. 把每个实例的位移、旋转、缩放烘进导出结果
- 这样导出的 `glb` 是完整关卡段，直接可看。

### 3. 合并 OBJ 时，`v / vt / vn` 必须分别维护偏移量
- 一开始把顶点、UV、法线共用同一套偏移量，导致：
  - `obj2gltf` 报 `UV index ... is out of bounds`
- 根因是不同 mesh 有的没有 UV 或法线，不能假设三套索引长度始终一致。
- 修复后按三套独立 offset 写 face，`732` 份 `glb` 全部转换成功。

### 4. Unity 法线数据不能假设固定是 3 维
- 部分 mesh 的法线数据会带到 4 维。
- 导出前要裁成前 3 维，否则矩阵乘法会报维度不匹配。

## 当前产物
- OBJ 导出脚本：
  - `myprojects/goingball/sourceConfigs/export_level_prefabs_obj.py`
- GLB 转换脚本：
  - `myprojects/goingball/sourceConfigs/convert_level_prefabs_glb.py`
- OBJ 导出报告：
  - `myprojects/goingball/sourceConfigs/reports/level_prefab_obj_export_report.json`
- OBJ 路径清单：
  - `myprojects/goingball/sourceConfigs/reports/level_prefab_obj_paths.txt`
- GLB 转换报告：
  - `myprojects/goingball/sourceConfigs/reports/level_prefab_glb_convert_report.json`
- GLB 路径清单：
  - `myprojects/goingball/sourceConfigs/reports/level_prefab_glb_paths.txt`

## 可复用命令
```bash
python3 myprojects/goingball/sourceConfigs/export_level_prefabs_obj.py --clean
python3 myprojects/goingball/sourceConfigs/convert_level_prefabs_glb.py --clean --jobs 4
```

## 风险与遗留
- 当前输出以“关卡 prefab 段”为粒度，不是整张大地图拼装场景。
- `glb` 已内嵌材质贴图；如果后续需要单独整理一份“平铺贴图库”，还可以基于 `level_prefabs_obj/**/*.png` 二次汇总。
- 当前未额外生成 `fbx`；如后续确实只接受 `fbx`，建议再走一轮 Blender/Assimp 批转。

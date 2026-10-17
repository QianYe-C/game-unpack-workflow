> 归档来源：`cocosgame2/experience/2026-09-28-idlecat-tmp-glyph-cache-边界保护.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat TMP fallback glyph cache 边界保护

## 现象
平台字体回调在异常或刷新窗口返回不完整记录时，`NativeTmpGlyphCache.key` 会直接读取 `selected.key`/`selected.glyph`，导致 `Cannot read properties of undefined` 并中断文字渲染。

## 处理
在 `NativeTmpGlyphCache` 中对 key/glyph 做完整性检查：无效记录不进入 selected map，`get` 返回明确的有限错误；`NativeTmpFallbackGeometry` 对缺失缓存项跳过当前字形，避免整帧崩溃。正常字体资源与布局算法不变。

## 验证
TypeScript、TMP fallback/paragraph/geometry/settings 几何回归和 CLI 构建均通过。未启动编辑器预览；真实平台字体 provider 的异常回调仍需真机验证。

> 归档来源：`cocosgame2/experience/90-项目案例归档/2026-09-27-idlecat-备用字体显示与GPU缓存-阶段复盘.md`。历史项目记录；具体实现、参数与成功范围须重新核验。

# Idlecat 备用字体显示与 GPU 缓存阶段复盘

2026-09-27。目标仍为全模块原版1:1移植，本次仅完成普通输入的混合字体显示阶段。

## 目标与实现

复用原 Meetme/JP/Liberation/Emoji 图集和已采集 TMP 几何，昵称与兑换码既有 Label 接入多材质渲染。不创建运行时 UI 节点；Setting/Rank_manager prefab 与 loading.scene 经 MCP/EditorExtends 序列化。68 PNG 和 JSON 经 MCP 导入，PNG 与原导出字节一致。打开输入面板预热元数据，实际图集按文字逐页加载；小块字形共享纹理，最后用户关闭20秒后回收。4页后优先回收无引用页，但活跃文字多时允许更多页。

## 根因与验证

原 Creator WebGL1 blit manager 的 pipeline blend state 为 null，继承前一 UI 绘制的混合状态。原先少数字形测试通过，但混入 Liberation 后发现 alpha 值10复制后为0。改用 WebGL copyTexSubImage2D，并在 finally 中恢复纹理和读写 framebuffer；其他后端保持gfx路径，尚待平台验证。

GM fontqa=1会将源GPU纹理与缓存GPU纹理逐字节比较；正式路径没有读回。混合样本 Cat猫咪😀☹☺𠮷 和缺字U+0378共10字形368780字节一致；重开累计12字形475036字节一致。首次关闭后GPU缓存0页0字形0用户0字节；重开可重建。68组原生排版1456坐标回归通过，最大误差0.0000812；类型检查通过。

CLI20260927-191320 success=true、sourceUnchanged=true、22.91秒，源SHA256 63cf1c5c967f2b2a1cef67e0c2bcba9e7d6f7aadbef8e37331fe54d4c8f646b4。未启动编辑器预览；临时安装脚本和组件已清理。证据在主工程 docs/evidence/redeem-20260927，归档在源项目logs/input-fallback-render-20260927-191320。

## 遗留与下一步

排行榜31行动态名字尚未接入，原17组长名字/换行/富文本采样已恢复原文本。需实现原自动缩字、换行、富文本，不能直接用固定字号替换。输入富文本/视窗裁切、编辑中DOM字体一致性、抖音真机/SDK和全部模块最终视觉仍待完成。完整字体使本地测试包约295MB，需处理发布资源分包/远端策略和真机性能，不能把CLI构建成功当作发布达标。

## 可复用门禁

GPU纹理复制必须验证透明度与RGBA原值，至少覆盖前一次draw采用不同混合方式的情况。少数ASCII字形通过不代表跨字体复制正确；copy/blit都要验证状态恢复与资源释放。

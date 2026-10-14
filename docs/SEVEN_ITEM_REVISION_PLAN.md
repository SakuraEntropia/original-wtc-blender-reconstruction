# 七项纠错实施记录

2026-10-14；承接用户已授权的修正，沿用现有项目与原始资料约束。

架构：四个独立、幂等的 Blender Python 修正模块，分别管理立面、大堂、WTC7屋顶、铺装。`build.py` 与 `revise.py` 调用同一入口。资料尺寸与照片推定尺寸分别标注；照片不进入公开仓库。

追加原图节点模块`original_junction_revision.py`及独立实际几何验收`verify_original_junction.py`，纠正斜接、双折边和不等分角板。原通用U框和同宽八角帽檐撤换；见`ORIGINAL_JUNCTION_IMPLEMENTATION.md`。

- [x] `facade_revision.py`：查普通幕墙边框、转角三分板、塔冠曲线收合、换乘层结构；只替换对应构件，保留独立钢柱。
- [x] `lobby_revision.py`：核大堂照片，增加模块顶棚、灯具、核心外饰；查询Sphere资产及再分发许可。
- [x] `wtc7_roof_revision.py`：按NIST两机房、五冷却塔组织屋顶模块，记录未注尺寸。
- [x] `paving_revision.py` / `planar.py`：方砖沿喷泉与24个圆花盆轮廓裁切，统一铺装标高，保留每砖独立mesh。纯几何面积守恒与网格闭合验收。
- [x] 集成：近景镜头覆盖七项；实际运行Blender、检查渲染、重开文件检查几何和资产依赖。
- [x] 更新交付清单、生产缺口、版权记录；压缩包重打包并推送现有public仓库。

验收命令：Blender后台打开`wtc_detailed_cg.blend`执行`revise.py`；再打开执行`verify.py`；空场景执行`verify_assets.py`；最后Python运行`package.py`。技术通过不代表未取得原图的细节达到历史测绘精度。

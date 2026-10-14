# 原图节点执行记录

2026-10-14第二次纠正。原160mm/65mm通用U框、等分角板和上下相同截角的帽檐已撤换。此前检查只能证明构件存在，不能证明节点符合原建筑；本轮另加实际顶点/截面的检查。本文件取代上一版`CROWN_JUNCTION_EVIDENCE.md`的节点参数。

## 原图及证据层级

[A·AB·321：角部立面及平面，7-31-67](https://www0.ae911truth.org/images/articles/ElectricalDrawings/134_0.png)；[A·AB·323：冠部角节点，7-31-67](https://www0.ae911truth.org/images/articles/ElectricalDrawings/135_0.png)。镜像的其他文字未作为几何依据。完整核读见`CROWN_ORIGINAL_DRAWINGS_RESEARCH.md`和`EDGE_FRAME_RESEARCH.md`。

| 构件 | 采用尺寸/形态 | 证据及不确定度 |
|---|---|---|
| 成对AL returns、PSS前表面 | 总宽5in=0.127m；突出7in=0.1778m；中心分开 | 323A明标。铝3mm、不锈钢1.5mm厚为CG参数，原制造公差未知 |
| 垂直角板三块 | 1ft11⅛in / 3ft4in / 1ft11⅛in；总7ft2¼in=2.19075m | 321E/F明标；6mm缝、3mm厚为CG参数；角板从柱罩面退入 |
| 顶部标高 | FIN110→parapet6ft；再升9ft到roof panel top | 321/323H明标；总塔高锚映射到panel top仍为假设 |
| 顶部角板 | 三块三角板下缘截角、上端收尖；两侧屋面共享端点斜接 | 321E/F、角立面的几何推断；内交汇线同时属于支承框，缺竣工变更核对 |
| 水平内退 | 2.19075/√2=1.549095m，约5ft1in | 平面腿长有标注；作为外皮全高run属节点对应推断，未独立核实 |
| fascia顶回折 | 3½in=0.0889m，独立件 | 323E明标；实际sheet gauge未知 |
| 上部曲线收口 | FIN110+4ft2in映射；保留NIST曲线高度 | 323J/H与321节点对应推断，没有独立fascia底标高。曲率与7in视觉宽为拟合；原75mm独立曲线改为25mm扁平连通网格，见FLAT_CROWN_CORRECTION |
| 局部钢支承 | ¼in折弯板；其余I形支架、purlin、girt独立件 | 323D明标板厚；截面/细部TYPE，非竣工钢构清单 |
| parapet | 6in混凝土；11⅝in±压顶范围 | 323D明标；绝对位置及混凝土底部映射估计 |

## 实际模块

`original_junction_revision.py`在保存场景迁移和clean build中共同调用。两塔对应资产集合：`*_FACADE_corner_transition_frames`、`*_corner_three_panels`、`*_CROWN_CAP_mitered_panels`、`*_CROWN_CAP_steel_support_TYPE`。金属框分段、分材料；中轴洗窗轨道留缝；终端柱罩有朝内退角板的斜折回边。角部三角板、屋面板、斜接盖条、fascia和翻边分别可选。

主屋面及维修构件映射到FIN110；旧高位完整平板不再填平整个斜冠。南塔公众观景平台仍是单独高位研究层，尺寸/高度缺公开施工核定。核心柱及帽桁架保留此前结构研究标高；冠顶绝对映射不能视为核心施工数据。

`crown_miter`、`edge_profile`、`edge_top`近景检查收尖、两侧斜接及独立框件。`verify_original_junction.py`核实际世界坐标，验证框截面/轴位、角板不等分、屋面共点和斜接路径。技术验收不证明未核事项。

新几何全部自行编码生成。源扫描图/照片仅在临时缓存查看，未复制进交付或仓库；未核尺寸的数值不确定度保持未知。

渲染诊断：保持几何不变的无阴影图仍出现斜接条纹；把近景正交相机远裁剪从10000m缩至100m，条纹消失。近景采用紧裁剪以保留毫米薄板的深度精度；帽檐双折边仍按两侧真实斜面制作。诊断临时图未打包。

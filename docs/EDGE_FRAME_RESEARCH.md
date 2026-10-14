# 角板交界框核读，2026-10-14

## 原图给出的构造

- [A-AB-321：典型层及塔冠角立面／平面，1967-07-31](https://www0.ae911truth.org/images/articles/ElectricalDrawings/134_0.png)，G／E／F：角板与端柱罩分面；罩面前的投影、洗窗轨及回折有独立线条。
- [A-AB-323：塔冠角细部，1967-07-31](https://www0.ae911truth.org/images/articles/ElectricalDrawings/135_0.png)，A：明确标注 `AL. RETURNS`、`POL. STAINLESS STL. FACE OF PROJECTION`，两条铝回折夹洗窗轨，前端各有抛光不锈钢面。不是一整块平口U罩。
- [NIST NCSTAR 1-5A v1](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-5av1.pdf)，印刷p33／36–38：普通玻璃退罩面11½in；窗框1in；角板每层3段；Fig4-8可核塔冠末端。1in是窗框读数，不能用于角部投影。
- [Brian Rose／Edward Fausty 1981原照](https://www.brianrose.com/blog/2015/10/new-yorkthe-walk/)：塔冠开口区末端有细亮边及深度阴影，接入帽檐下缘。

| 原图读数 | 米 | 位置／含义 |
|---|---:|---|
| 2½in + 2½in = 5in | 0.0635×2 = 0.127 | A323，端柱轴两侧，投影**总宽**；非单侧5in |
| 7in | 0.1778 | A323 A左侧竖向尺寸，罩面到投影前端深度 |
| 11½in | 0.2921 | 罩面到玻璃／内侧面退距，独立于前凸7in |
| 1ft11⅛in、3ft4in、1ft11⅛in | 0.587375、1.016、0.587375 | G321／E321，角面三分尺寸链，**不等分** |
| 三段总7ft2¼in | 2.19075 | 角面尺寸链；不是把6ft11in再乘√2 |
| 6ft11in | 2.1082 | G321，理论角柱reference到首常规柱轴的正交定位 |

图像研究副本仅在临时目录：`/private/tmp/wtc_edge_annotated_323.png`（增加编号）、`wtc_323_A_jamb_dims.png`（轴两侧2½in原尺寸）、`wtc_crown_floorcorner.png`（7in原尺寸）、`wtc_edge_321_107_plan.png`（三分角板尺寸链）。不随模型发布。

## 当前源码／旧渲染的症结

审阅 `crown_edge_revision.py:corner_frames`、`facade_revision.py:_corners` 及现有 `detail_facade_corner.png`／`detail_crown.png`。以下是修订前源码算值：

| 当前项目量 | 值 |
|---|---:|
| 端柱轴p = 29×40in | 29.464m |
| OUTER_HALF角面折点p | 29.569210m |
| U框中心p | 29.534210m（偏柱轴70.210mm） |
| U框宽／前凸 | 160mm／65mm |
| U框前面p区间 | 29.454210–29.614210m |
| 普通端柱罩p区间 | 29.225875–29.702125m |
| 当前角面展开长度 | 3.191866m |

U框前面全部覆盖在末柱罩范围内；没有分离的洗窗缝／双回折／不锈钢前端。冠部12in末罩右缘29.616400m，几乎与U框右缘重合，仅差2.190mm。旧渲染因此只有弱折线。普通末罩还越过当前45°折点132.915mm，必须与实际回折一起解端部，不能继续加重叠条。

更大的位置问题：当前把角板放在罩前缘 `OUTER_HALF`，并把6ft11in用于45°角面run，生成3.191866m宽角面；原321角板在罩面内侧，尺寸链总2.19075m。应先按原图玻璃／角板层面和柱轴重新定位，随后安放三块，不能只把现有大角面改成三个不同宽度。

## 给实现的截面关系

```text
面内方向u：     -2½in   柱轴／洗窗缝   +2½in
                ┌─SS端面─┐  ┌─SS端面─┐
外侧 front      │AL return│  │AL return│  前凸7in
罩面            └────────┴──┴────────┘
                端柱罩／独立角部折回
                      ╲ 斜回折到内侧角板
                       ╲ [0.587375][1.016][0.587375]
```

塔冠投影对准实际末柱轴，保留中间轨缝；两条回折和两个SS前端可独立选择。角侧回折要按321G／323A连接内侧角板，并在顶部接321E／323E的帽檐／facia return。三板位置和接缝按实际原图尺寸链复核。板厚、轨槽口与普通楼层采用何种前凸型尚未核定；普通层外推应明确标记。

本次只写核读记录。只读Blender启动在读文件前退出139，未修改或保存场景；保存场景的实际对象边界尚待集成验收。

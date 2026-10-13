# 尺寸、出处与不确定度

坐标统一为 Concourse El.310ft = z0。数值换算精确不等于历史测量无误；原资料未给容差时，不编造误差条。全部对象的实际边界、材质与证据继承见 `reports/geometry_manifest.json`；`uncertainty_m=null` 表示未量化。

| 参数 | 模型值 | 原始出处 | 精度边界 |
|---|---:|---|---|
| Plaza 标高 | 22ft / 6.7056m | NIST 1-1 图2-3，Concourse El310、Plaza El332 | 标高有据；场地坐标仍展示布局 |
| WTC1/2 屋面 | 1368/1362ft / 416.9664/415.1376m | NIST 1-5A v1 §4.2.1 | 相对 Concourse；容差未给 |
| 覆面外缘宽 | 208′10″ / 63.6524m | 同上 | 钢柱、外墙和覆面宽的口径不可混用 |
| 角切 | 6′11″ / 2.1082m | 同上 | 角部板、连接和转折剖面尚未转录 |
| 常规外柱 | 59/面，40in轴距，约14in方钢柱 | NIST 1-3 §2.3.1 | 铝包覆厚度、各层变截面未核 |
| 树柱基轴 | 19/面、10ft / 3.048m | NIST 1-1 图2-3、1-2A 图3-6 | 两端/转角专图另核；不能用数量推出直柱形状 |
| 树板下/上拼接 | El363 / El418′11½″，z16.1544 / 33.2105m | 原图2-AB2-2，NIST 1-2A p37 图3-6 | 标高有据；板截面和包覆仍未知 |
| 树板直段/叉段 | 9′4″ / 11′4″，叉起点z18.9992，终点z22.4536m | 同图，已直接读取扫描图 | 三叉曲线按图示插值；宽、厚不是实测值 |
| 叉内凹起点 | 叉起点上6ft，z20.828m | 同图6ft标注 | 弧线控制点仍为视觉插值 |
| 典型 spandrel | 52in / 1.3208m | NIST 1-3 §2.3.1 | 钢板深度；常规层标高插值，样件默认隐藏 |
| 顶部矩形管 | 7×5in / .1778×.127m | NIST 1-2A §3.2.7；1-3 §2.3.4 | 与宽翼缘交替的具体构件表、WF截面未知 |
| 核心 | 约87×137ft；47柱；3楼梯 | NIST 1-3A §2.1、1-1 | 柱网和井道示意；WTC1长轴东西、WTC2南北 |
| 3–6层 | 外侧无楼板，模型仅核心板 | NIST 1-2A pp2–3 | 完整实际各层标高、结构与开洞仍缺 |
| Sky Lobby / MER | 44、78 / 7–8、41–42、75–76、108–109 | NIST 1 表1-1 | 室内/设备平面未核；实际几何是类型参考 |
| 108/109百叶退距 | 4ft / 1.2192m | NIST 1-5A v2 pp417–425，图A-1～A-8 | 分组、条数和开口绝对标高仍示意 |
| AHU系统 | 典型MER12台AHU；高/低压送回风类型 | NIST 1-4C p85；1-4D pp43–46 图4-5～4-8 | 1-4D是75/76层类型图；不能当108/109竣工布置；部件计数口径也不同 |
| 帽桁架 | 107至屋顶，长/短方向各4道；核心框架和伸臂 | NIST 1-2A pp41–42 图3-10/11 | 平面/拓扑按图示参考；节点、杆截面和标高仍简化 |
| WTC1天线 | 约360ft / 109.728m | NIST 1-1、1-5A v1 | 白色分段圆筒及外附发送组件按1981/2001照片解释；半径、连接、振子尺寸及位置推定 |
| WTC2屋顶观景 | 室外屋顶、室内107层 | NIST 1 表1-1 | 栏杆、台阶、配套、内装及路线未经原图核定 |
| WTC3 | 22层、242ft / 73.7616m | CVU/Skyscraper Center building19942；NIST 1-1 | 入口基准对应关系、轮廓、酒店内装未核 |
| WTC4/5/6 | 9/9/8层 | NIST 1-1 §2.1 | 层高3.65m、足迹、立面、位置均推定 |
| WTC7 | 610ft；北329ft、南247ft、两侧约153/149ft | NIST 1A §1.2.3、1-9 | 展示位置、窗带、颜色与内部未核 |
| 广场 | 约5acre；模型铺砖1.5m节距、喷泉周边放射分块 | NIST 1-1 §2.1 | 1.5m不是历史砖尺寸；实际独立mesh数量见最新qa.json |
| Sphere 尺度代理 | 约25ft高、15ft直径 | Smithsonian Art Inventories302674；9/11 Memorial20476 | 底座/喷泉直径推定；通用球体不复刻原作 |

原件仅作研究链接，不随包发布：

- [NIST 1-1](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-1.pdf)
- [NIST 1-2A](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-2a.pdf)：图3-6直接读取；角部专图2-AB2-17～22、截面图2-AB2-4～16仍待获取与逐张转录。
- [NIST 1-3](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-3.pdf)、[1-3A](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-3a.pdf)
- [NIST 1-5A v1](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-5av1.pdf)、[v2](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-5av2.pdf)
- [NIST 1-4C](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-4c.pdf)、[1-4D](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-4d.pdf)
- [NIST 1](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1.pdf)、[1A](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1a.pdf)
- [CVU WTC3](https://www.skyscrapercenter.com/building/wd/19942)
- [Smithsonian Sphere](https://siris-artinventories.si.edu/ipac20/ipac.jsp?uri=full%3D3100001~%21302674~%2111)、[9/11 Memorial](https://collection.911memorial.org/Detail/objects/20476)
- [LOC 1976俯瞰图](https://www.loc.gov/item/2021636620/)、[山崎实设计模型照片](https://www.loc.gov/pictures/resource/ds.14455/)

## 本轮结构、幕墙与WTC7补证

- [NIST NCSTAR1 p72 图5-6](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1.pdf)：铝罩18in宽、中线矩形凹槽；钢柱为箱形。槽宽/深未标；模型.04×.03m及3mm板厚为推定。玻璃位于罩后，当前参考面依据截面关系布置，玻璃厚度仍推定。
- [NIST1-1 pp15、25–26 图2-9/2-10](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-1.pdf)：10×36ft三柱三层预制板；普通层错缝、机械层同高；端板1.375–3in、双拼接板。模型采用三层分件逻辑；层高仍插值，不能把所有模块长度称为真实36ft；壁厚/螺栓/接头构件表未核。钢件与18in铝罩独立，可分别隐藏。
- 钢柱参考线207′2″；覆面外缘208′10″；各侧差10in。6′11″倒角对应参考轮廓，屋面按覆面偏移后的45°角切生成。
- [NIST1-9 ch5 pp98–114 图5-10～5-25](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-9.pdf)：WTC7北63中心窗+两端各2；南45+两端各2；东12+端部各2，西南端另有一对；NS典型窗4′7″×6′6″，3in框、1in玻璃、1.25in石板及5in镀锌挂盒。EW与NS窗列分别建；22/23、46/47机械层、南顶斜玻璃与北顶百叶独立。绝对标高、顶层退距和所有门口仍有推定。
- [FEMA403 ch4 §4.1.1](https://www.fema.gov/pdf/library/fema403_ch4.pdf)：WTC5为L形，包络330×420ft，每层约120000ft²。模型包络有据；等边缺口由约面积推导，缺口比例、方位和现场坐标未经测绘。
- WTC3/4/6新增分格窗、框、窗间墙、入口、基座和屋面部件；这些尺寸未取得完整原图。

## 2026-10-13 塔冠／屋顶／广场照片核查

| 项目 | 本轮几何 | 依据 | 不确定度／限制 |
|---|---|---|---|
| 塔冠顶端 | 每面58尖拱、独立倒Y枝；下部菱形转接；8边斜帽檐面板 | Brian Rose/Edward Fausty 1981原照；NIST1-2A §3.2.7 | 可见形态有据；17m范围、2.4m帽檐落差、1.8m内收和所有枝宽为CG估算，非施工尺寸；重复数量依59轴推演 |
| 窗擦系统 | 双轨、横梁、支腿、角部转盘、小车/轮/电机/吊臂/缆索 | 同照片前景；NIST维护报告提及屋顶窗擦轨 | 类型与可见拓扑有据；轨距、高度、路径及小车机构比例推定 |
| 天线 | 360ft主筒，分段锥形；法兰/螺栓、平台、栏杆、外附竖向发送组件、辅天线 | NIST高度；JWSmythe 2001-09-06原照与1981原照 | 设备清单、频段、所有半径/段界/平台/位置未知；不能称制造图复原 |
| 核心屋顶 | 47轴到屋面，顶部梁、节点板/螺栓；3个分段井壁类型模块 | NIST1-2A §3.2.8帽桁架 | 轴位/梁截面/节点规格/井道位置仍示意；端点达到屋顶是技术验收 |
| 广场 | 方砖1.5m，5圈放射砖；环座、圆花池和灯杆，喷泉coping分96块 | LOC2021636621历史照片 | 中心与场地坐标、各半径、家具尺寸/数量、植栽和年份未核；12.5m水池半径仅估算 |
| 屋顶机电分件 | 检修口/铰链/把手、管/法兰/六螺栓/支座/阀轮、梯式桥架/缆线 | NIST系统类别；原创工业类型模型 | 不具实际设备表；原先无据的大AHU转为默认隐藏的类型模块 |

参考链接：[Rose/Fausty 1981](https://www.brianrose.com/blog/2015/10/new-yorkthe-walk/)、[JWSmythe 2001原照及CC BY3.0](https://commons.wikimedia.org/wiki/File:2WTC_roof_to_1WTC_roof.jpeg)、[LOC广场原照](https://www.loc.gov/item/2021636621/)。照片未作为纹理或源文件随项目发布。

追加：转角铝板覆盖普通柱顶拼接至斜帽檐，外轮廓按8边图形，接缝3.65m节距仍估算。上段钢柱类型改以17m照片解释范围与普通钢段分区。广场11棵树及花池叶簇为原创程序植物类型，位置/种类/季节未测绘；不是原址植物清单。

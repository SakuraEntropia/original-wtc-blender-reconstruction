# 大厅修订与 Sphere 授权记录

核查：2026-10-14。`src/wtc/lobby_revision.py` 为幂等补丁，接在 `tower_completion()` 后运行。原镜头不改；原吊顶、低矮电梯代理隐藏并保留。

## 原始图像与可确认范围

- [Tai Ping / Edward Fields 项目档案](https://www.taipingcarpets.com/projects/twin-towers-at-world-trade-center-ny)：供应商记录1986年港务局委托，原有大厅、夹层与空中大厅地毯的更换方案。文字说明用水磨石分隔地毯，便于局部替换，举出20×40ft区块。此尺寸只证明其设计策略，**模型中的分块没有冒充该尺寸或原始平面**。
- 该页原照 `World-Trade-Center.jpg` 与 `World-Trade-Center-2_2022-04-22-101053_oibm.jpg` 已在浏览器实际观察：可见浅色石材竖框、深色门洞、上部高窄反光面、平滑夹层底面及圆形暗装灯。第二图的上部反射可辨方形斜面凹槽与悬垂方盒。照片不足以确认石材矿种、玻璃镀层、照明型号、吊顶节距和准确数量。
- [9/11 Memorial C.2022.20.10](https://collection.911memorial.org/Detail/objects/121750)：Nicholas Solovioff 1970年大厅/夹层施工版画的馆藏记录。辅助证明研究对象；此次未据其提取尺寸。该项标明版权/相关权利保护，图像不随包发布。
- [LOC ppmsca.50296](https://www.loc.gov/pictures/resource/ppmsca.50296/)：大厅施工照片条目已找到，但本轮网页抓取403；**未把未观察图像当作几何证据**。

## 已实施的范围

1. 独立方形凹槽吊顶模块、斜面收口、可见板缝、悬垂方盒灯和灯罩。
2. 核心筒饰面四面分件：石材分段竖框、石材裙墙/窗间墙、上下层双扇门、门框/门槛/呼叫面板、高窄反光上窗。当前大厅镜头可看到核心筒的东/南面。
3. 核心筒侧廊分件、水磨石色边界、绿色地毯区块、下部暗装圆灯。采用照片中出现的构造语言，具体轮廓、尺寸和塔楼配色归属均为估算。
4. 大厅展示吊顶标高沿用旧场景 `6×12ft`；**不是本轮核实出的建筑标高**。47根核心柱、三楼梯等结构代理不受改动。
5. 模块、材质和收藏集明确带有 `STUDY` / `confidence`。使用共享基础网格但每个组件独立可选；不用外部贴图。照片仅链接，不打包。

核心包络约87×137ft及塔楼朝向沿用项目已登记的NIST依据。[NIST NCSTAR 1](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=909017) 表1-1、图1-9支持44及78层为快速/局部电梯换乘空中大厅；[NCSTAR 1-7](https://nvlpubs.nist.gov/nistpubs/Legacy/NCSTAR/ncstar1-7.pdf) §2.2.3为电梯系统依据。这里只完善元数据，未将原有插值楼板标高升级成测绘数据，也未根据论坛说法指定44/78层的石材颜色。

## Koenig《The Sphere》候选资产

| 候选 | 实际核查结果 | 包内处理 |
|---|---|---|
| [TurboSquid 2224261](https://www.turbosquid.com/FullPreview/2224261) | 产品页明确为 Standard、Editorial Uses Only；列出SketchUp/OBJ/Blender/STL，属于作者重建。页面作者显示名与搜索缓存有变化，不能仅凭署名确认原作授权链。 | 未购买、未下载、未导入。 |
| [3D Warehouse 5cd1dc0d44ea99d4e6901f9a264cdbc0](https://embed-3dwarehouse-classic.sketchup.com/model/5cd1dc0d44ea99d4e6901f9a264cdbc0/Koenig-Sphere) | 搜索记录为“Koenig Sphere”，说明提及修改纹理；详情访问403。没有核实原网格作者和雕塑原作的许可链，也没有取得本条目的开放再分发授权。 | 未下载、未导入。 |

[TurboSquid正式许可](https://blog.turbosquid.com/turbosquid-3d-model-license/)限制模型向第三方再分发，并对Editorial资产限定用途；购买许可不等于允许将可提取网格放入公开 `.blend` / CC BY资产包。该候选可继续研究受许可约束的纪录/教学渲染用途，不能宣称已经获得开放资产授权。

[3D Warehouse条款](https://3dwarehouse.sketchup.com/tou)及[官方FAQ](https://help.sketchup.com/en/3d-warehouse/3d-warehouse-terms-use-faq)区分模型作为作品的一部分与集合再分发；平台可下载本身不能证明上传者拥有雕塑复制权，亦不能自动转换为本项目CC BY4.0。

结论：本轮没有取得可作为开放资产交付的原始Sphere模型。现有通用尺度球体代理不能算作雕塑复原；不改名冒充、不声明使用第三方工业模型。

## 验证状态

补丁仅创建/修改上述模块与元数据，静态语法检查完成。Blender执行、二次apply对象数稳定性、材质检查及大厅渲染由整合流程验证；本文件不预先声称渲染通过。

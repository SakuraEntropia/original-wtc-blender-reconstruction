# 原纽约 WTC｜模块化 CG 研究模型

主文件 `wtc_detailed_cg.blend`；独立资产库 `assets/`；34个检查镜头与渲染 `renders/detail_*.png`。双塔、分段钢柱、核心、大厅、机电类型、帽桁架、天线、WTC3–7、广场分别组织。每块铺砖独立对象/mesh；重复窗框、吊顶、构件复用网格。

最新：一楼收窄梁中央240mm/端部680mm/深180mm；两塔456件凸脊、152个底柱体与144根收窄梁，各件独立对象和单用户mesh，可直接分件编辑。三凸脊两侧高、中间低，分别走向三个叉；尺寸属照片拟合。

恢复楼板/核心筒：两塔各109片原楼板、47轴分段核心柱、井道和屋顶节点在视口/渲染默认开启；Plaza层继续使用已有双挑空曲线平台。旧F002整板保留隐藏，防止封住挑空；不启用核心范围实心代理。此次仅重新渲染overview/core，其他细节图保留前一批状态，逐图版本见render_runtime.json。

2026-10-15修正：渲染隐藏研究钢构同步隐藏视口；大厅按A-AB-252/A-B-22改两处曲线挑空的半开放平台、玻璃栏杆/扶梯与四翼旋转门；三叉柱增加三条凸脊（两侧高、中间低）、嵌套次框与子框，一楼顶横梁改为两端厚/中央薄的上下双曲边实体，细窗框另保留实际横槽；塔冠曲线改2½in宽、6mm厚的连通扁板，据AB302将整个中字框8.0084m改11.176m，增加覆盖楼层。南塔增加照片拟合的蓝色环形观景步道、维修井、双出入口、中央历史小平台、支架/围栏/碟形通信天线；保留原维修机械细件。全部34相机改Perspective，Cycles Metal GPU实际渲染，配置/耗时见`reports/render_runtime.json`。详见[本轮证据及验收](docs/OCT15_FINAL_SOURCE_CORRECTIONS.md)。

追加原建筑A·AB·321/323节点修订：5in×7in分件突出框、不等宽且内退的三分角板、下缘截角/上端收尖的角屋面、共享顶点的斜接及独立翻边。旧通用U框与同宽八角帽檐撤换。新近景：`crown_miter`、`edge_profile`、`edge_top`；源图/推断区分见[执行记录](docs/ORIGINAL_JUNCTION_IMPLEMENTATION.md)。

2026-10-14修正：按NIST1-5Av1增加玻璃退距/凸框、每层三分角板、两跨曲线开合塔冠、44/78层特殊窗带及机械层凸翅；大厅增加模块凹槽顶棚、灯具、核心外饰与门框；WTC7按NIST1-9屋顶平面增加两机房、两屏墙、五个冷却出口及北侧竖百叶；方砖沿喷泉/花盆裁切，接入放射铺装。

**当前未达到完整历史复原的production-ready标准。** 来源明确的尺寸保持原值；照片拟合的曲率、板厚、设备型号、机房高度、绝对楼层标高和布局仍标估算。曲线塔冠是铝饰面，不能当作承重钢施工图。地下商业/PATH、全域机电、真实逐层室内及完整UV/LOD/稳定版导出管线仍未完成。见[生产门槛](docs/PRODUCTION_GATE.md)与[七项记录](docs/SEVEN_ITEM_REVISION_PLAN.md)。

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -t 4 -P build.py
/Applications/Blender.app/Contents/MacOS/Blender -b wtc_detailed_cg.blend -t 4 -P revise.py -- --views=crown,lobby,wtc7_roof,paving_seam
/Applications/Blender.app/Contents/MacOS/Blender -b wtc_detailed_cg.blend -t 4 -P verify.py
/Applications/Blender.app/Contents/MacOS/Blender -b wtc_detailed_cg.blend -t 4 -P verify_repeat.py
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -t 4 -P verify_assets.py
python3 package.py
```

实测Blender5.2.0 Alpha；验证结果与实际数量见`reports/qa.json`、`assets_qa.json`、`repeat_qa.json`。`geometry_manifest.json.gz`逐件记录实际边界、材质、来源与不确定度；未知测量公差不编数值。链接资产库已测试；大量对象本地Append较慢，建议集合实例。`review.py -- --views=...`单独重渲染，`--views=none`可仅保存更新。

全部网格/程序材质由代码生成，无外部贴图或第三方工业资产依赖。Sphere仍是通用尺度代理；找到的TurboSquid与Warehouse候选没有取得开放网格再分发授权，见[授权核查](docs/LOBBY_SPHERE_EVIDENCE.md)。图纸、照片只引用，不打包。

资料：[主提示词](docs/AGENT_PROMPT_ZH.md)、[尺寸表](docs/SOURCES_AND_DIMENSIONS.md)、[立面证据](docs/FACADE_REVISION_EVIDENCE.md)、[大厅](docs/LOBBY_SPHERE_EVIDENCE.md)、[WTC7屋顶](docs/WTC7_ROOF_EVIDENCE.md)、[铺装](docs/PAVING_REVISION_EVIDENCE.md)、[版权](docs/COPYRIGHT.md)。代码MIT；自有几何/材质/渲染贡献CC BY4.0，许可不延伸至第三方原作。

[GitHub public仓库](https://github.com/SakuraEntropia/original-wtc-blender-reconstruction)；实际已推送版本、文件数量和Git blob核验见`reports/publication.json`。本地最新改动是否已发布以该报告为准。

最终重开及技术检查结果以`reports/qa.json`为准；资产链接及重复迁移分别见`assets_qa.json`、`repeat_qa.json`。技术验收不等于完整历史生产精度。

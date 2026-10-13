# 原纽约 WTC｜细节 CG 工程

当前主文件 `wtc_detailed_cg.blend`；独立 Blender 资产在 `assets/`。双塔、树柱/大厅/核心、机电类型模块、帽桁架、WTC3–7、铺砖与球体代理分别组织。`REVIEW_CAMERAS` 保存全部 20 个检查镜头。铺砖数量见 reports/qa.json，每块是独立对象和独立 mesh；重复外柱与楼板复用网格。

本轮修正：统一 Concourse/Plaza 标高；依据 NIST 图3-6 的 9′4″、11′4″和6′标注重做连续三叉；矩形管与宽翼缘顶部构件分开；3–6层外侧留空；大厅基座避免切入；顶部机电百叶退后4ft；机电加入风机叶轮、护栅、风管、圆管与法兰；帽桁架按核心框架与外围伸臂独立建；观景栏改为杆件；天线改为完整四边格构；去除橙色高度代理。

**当前为细节研究模型，尚未达到完整历史复原的 production-ready 标准。** 角部树板、真实核心/井道布局、逐层标高、室内布局、设备型号与布置、完整街区/地下商业/PATH均未完成原图级核定。球体为原创通用尺度代理，未复制 Koenig 原作。详见 [生产门槛与缺口](docs/PRODUCTION_GATE.md)。

```sh
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -t 4 -P build.py
/Applications/Blender.app/Contents/MacOS/Blender -b wtc_detailed_cg.blend -t 4 -P verify.py
```

实测 Blender 5.2.0 Alpha。尚未验证稳定版兼容性。材质均程序生成，无外部图像、工业模型或贴图依赖。脚本先渲染，恢复可见状态后保存总场景，再输出独立资产。`reports/qa.json` 是保存文件重开验收，`reports/geometry_manifest.json.gz` 逐对象记录尺寸、材质、来源标签和未量化的不确定度。

资料：[来源尺寸表](docs/SOURCES_AND_DIMENSIONS.md)；[假设](docs/ASSUMPTIONS.md)；[主提示词](docs/AGENT_PROMPT_ZH.md)；[版权](docs/COPYRIGHT.md)。代码 MIT；原创几何/材质/渲染的贡献部分 CC BY 4.0，见许可文件。GitHub public 已推送：[仓库](https://github.com/SakuraEntropia/original-wtc-blender-reconstruction)。已逐件核对远端与本地Git blob哈希；主.blend、30个资产库、20图、脚本、尺寸引用与许可记录均已公开。参考图纸与照片未上传。详见 reports/publication.json。

本轮新增 `facade_detail.py` 和 `lowrise_detail.py`。钢箱段、端板/拼接件、凹槽铝罩与玻璃分开；屋面/女儿墙为8段含45°角切。WTC7用NIST不同朝向窗列、独立石板/挂盒；WTC5使用FEMA的330×420ft L形包络。新视角：`detail_steel_panels.png`、`detail_section.png`、`detail_wtc7.png`、`detail_lowrise.png`、`detail_roof_plan.png`。

2026-10-13再修：新增 `crown_site_detail.py`，按历史照片重建尖拱/菱形塔冠、8边内收斜帽檐、窗擦双轨及转盘小车；天线换白色分段主筒与外附部件；核心增加屋面连接与分段井壁；广场补放射砖、环座、花池、灯杆；主楼与裙楼屋顶加入独立检修/管线/桥架部件。所有无原注尺寸仍标估算。`detail_crown.png`、`detail_core_top.png`、`detail_plaza.png`、`detail_mep_detail.png`为新增检查视角。

已有保存场景可用 `Blender -b wtc_detailed_cg.blend -P revise.py` 增量更新；`review.py -- --views=crown,core_top`单独复测镜头，节约重建成本。完整重建仍用build.py。

最终保存文件重开：59项技术检查通过；20个1280×1280检查图；30个独立资产库只读加载通过。当前117,610个mesh对象、8,630块独立铺砖、67种程序材质。大量独立钢段和铺砖使对象数高；推荐按集合关闭未使用模块。尺寸清单压缩存储，解压后为JSON；含每件实际边界和未量化的不确定度。

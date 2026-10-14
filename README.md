# 原纽约 WTC｜模块化 CG 研究模型

主文件 `wtc_detailed_cg.blend`；独立资产库 `assets/`；26个检查镜头与渲染 `renders/detail_*.png`。双塔、分段钢柱、核心、大厅、机电类型、帽桁架、天线、WTC3–7、广场分别组织。每块铺砖独立对象/mesh；重复窗框、吊顶、构件复用网格。

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

最终重开：89项技术检查通过；40个资产库、26个镜头；132,643个mesh对象、8,670块独立铺砖、82种材质。连续两次迁移对象/mesh/集合/材质数量一致。技术验收不等于完整历史生产精度。

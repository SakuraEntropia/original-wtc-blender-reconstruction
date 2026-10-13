"""Package only generated deliverables, never cached source photographs/scans."""
from pathlib import Path
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
qa=json.loads((ROOT/'reports/qa.json').read_text())
assets=json.loads((ROOT/'reports/assets_qa.json').read_text())
if not qa['technical_pass'] or not assets['passed']:
    raise RuntimeError('Delivery requires successful saved-scene and asset checks')
files=set(ROOT.glob('*.py'))
files.update(ROOT/n for n in ('README.md','LICENSE','ASSET_LICENSE.md','.gitignore','.gitattributes','wtc_detailed_cg.blend'))
for pattern in ('src/**/*.py','docs/*.md','assets/*.blend','renders/detail_*.png'):
    files.update(ROOT.glob(pattern))
files.update(ROOT/'reports'/n for n in ('qa.json','assets_qa.json','geometry_manifest.json.gz'))
pub=json.loads((ROOT/'reports/publication.json').read_text()) if (ROOT/'reports/publication.json').exists() else {}
if pub:files.add(ROOT/'reports/publication.json')
manifest={'historical_production_ready':False,'github_pushed_files':pub.get('verified_file_count',0),
          'technical_check_count':len(qa['technical_checks']),'asset_libraries':len(assets['libraries']),
          'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,
                    'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]}
index=ROOT/'reports/delivery_manifest.json';index.write_text(json.dumps(manifest,indent=2))
files.add(index)
target=ROOT.parent/'wtc_detailed_cg_delivery.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in sorted(files):archive.write(p,'wtc_reconstruction/'+str(p.relative_to(ROOT)))
with zipfile.ZipFile(target) as archive:
    if archive.testzip():raise RuntimeError('Delivery ZIP CRC failure')
print(json.dumps({'archive':str(target),'files':len(files),'bytes':target.stat().st_size,
                  'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}))

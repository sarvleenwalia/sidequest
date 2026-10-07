"""Embed verified local reports in a portable static evidence viewer."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parent
real=json.loads((ROOT/'real-data-review/real_data_audit.json').read_text())
synthetic=json.loads((ROOT/'release-results-v3/metrics.json').read_text())
sample=pd.read_csv(ROOT/'real-data-review/real_sample_summary.csv').to_dict('records')
embedding=pd.read_csv(ROOT/'real-data-review/real_embedding.csv').sample(n=400,random_state=42)[['svd_1','svd_2','line_group']].to_dict('records')
predictions=pd.read_csv(ROOT/'release-results-v3/held_out_predictions.csv').to_dict('records')
payload={'real':real,'synthetic':synthetic,'samples':sample,'embedding':embedding,'predictions':predictions}
html=(ROOT/'dashboard.template.html').read_text(encoding='utf-8').replace('__EVIDENCE__',json.dumps(payload).replace('<','\\u003c'))
html=html.replace('href="demo-data/counts.csv"','href="counts.example.csv"').replace('href="demo-data/metadata.csv"','href="metadata.example.csv"')
for name in ['PITCH.md','DATASET_REVIEW.md','VALIDATION.md','explore_geo.py']:
    html=html.replace(f'href="{name}"',f'href="https://github.com/sarvleenwalia/sidequest/blob/main/research/stemcell-algorithm/{name}"')
(ROOT/'index.html').write_text(html,encoding='utf-8')
(ROOT/'real-audit.json').write_text(json.dumps(real,indent=2),encoding='utf-8')
(ROOT/'synthetic-benchmark.json').write_text(json.dumps(synthetic,indent=2),encoding='utf-8')
print('Built index.html from real and synthetic reports; no fabricated metrics.')

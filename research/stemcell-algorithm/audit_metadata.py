"""Audit declared metadata for donor-held-out binary/multiclass disease modeling."""
import argparse
import json
from pathlib import Path
import pandas as pd


def audit(frame, label='status', folds=4):
    required = {'cell_id','donor_id','batch_id',label}
    missing = sorted(required - set(frame.columns))
    if missing:
        return {'eligible_for_declared_cv':False,'reasons':[f'Missing columns: {missing}']}
    reasons, warnings = [], []
    if frame.empty:
        reasons.append('No cells.')
    if frame[list(required)].isna().any().any():
        reasons.append('Missing identity, batch, or disease labels.')
    if frame.cell_id.duplicated().any():
        reasons.append('Duplicate cell IDs.')
    clean = frame.dropna(subset=list(required)).astype({c:str for c in required})
    if clean.groupby('donor_id')[label].nunique().max() > 1:
        reasons.append('A declared donor has more than one disease label.')
    counts = clean.groupby(label).donor_id.nunique().to_dict()
    if len(counts) < 2:
        reasons.append('Need at least two disease-label classes.')
    if folds < 2 or any(n < folds for n in counts.values()):
        reasons.append(f'Need at least {folds} independent donors in every class.')
    cross = pd.crosstab(clean.batch_id,clean[label])
    if len(cross)>1 and (cross.gt(0).sum(axis=1)==1).all():
        reasons.append('Complete batch/label confounding: every batch has only one class.')
    if len(cross)>1:
        warnings.append('Review partial batch confounding, time points, protocols and donor covariates manually.')
    warnings.append('Declared donor IDs cannot be verified automatically; technical replicates must share the original donor ID.')
    return {'eligible_for_declared_cv':not reasons,'reasons':reasons,'warnings':warnings,
            'cells':len(frame),'declared_donors':int(clean.donor_id.nunique()),
            'donors_per_class':{str(k):int(v) for k,v in counts.items()},
            'batches':int(clean.batch_id.nunique()),'folds_requested':folds,
            'scope':'Metadata feasibility only; not real-data, biological, clinical, or prospective validation.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--metadata',required=True); p.add_argument('--label',default='status')
    p.add_argument('--folds',type=int,default=4); p.add_argument('--out',required=True)
    args=p.parse_args()
    report=audit(pd.read_csv(args.metadata,dtype=str),args.label,args.folds)
    Path(args.out).write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))
    raise SystemExit(0 if report['eligible_for_declared_cv'] else 2)

"""Exploratory scRNA-seq pipeline. No clinical or prospective validation implied."""
from __future__ import annotations
import argparse
import json
import platform
import hashlib
import os
import tempfile
from pathlib import Path
import importlib.metadata
import numpy as np
import pandas as pd
from scipy import sparse, stats
from scipy.io import mmread
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, roc_auc_score, confusion_matrix
from sklearn.model_selection import StratifiedGroupKFold, StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
os.environ.setdefault('MPLCONFIGDIR', str(Path(tempfile.gettempdir()) / 'stemcell-matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


class VariableGenes(BaseEstimator, TransformerMixin):
    """Select variance-ranked features using training observations only."""
    def __init__(self, n=1000):
        self.n = n

    def fit(self, X, y=None):
        self.indices_ = np.argsort(np.var(X, axis=0))[-min(self.n, X.shape[1]):]
        return self

    def transform(self, X):
        return X[:, self.indices_]


def normalize(X, target=10000):
    X = sparse.csr_matrix(X, dtype=float)
    totals = np.asarray(X.sum(axis=1)).ravel()
    Y = sparse.diags(target / np.maximum(totals, 1)) @ X
    Y = Y.tocsr()
    Y.data = np.log1p(Y.data)
    return Y


def read_data(counts, metadata=None, genes=None):
    path = Path(counts)
    if path.suffix == '.h5ad':
        import anndata
        adata = anndata.read_h5ad(path)
        X = adata.layers['counts'] if 'counts' in adata.layers else adata.X
        meta = adata.obs.copy()
        meta.index = meta.index.astype(str)
        names = np.asarray(adata.var_names.astype(str))
    elif path.suffix == '.mtx':
        if not metadata or not genes:
            raise ValueError('MTX needs --metadata and --genes. Matrix rows must be cells, columns genes.')
        X = mmread(path).tocsr()
        meta = pd.read_csv(metadata, dtype={'cell_id': str}).set_index('cell_id')
        names = pd.read_csv(genes, header=None)[0].astype(str).to_numpy()
    elif path.suffix == '.csv':
        if not metadata:
            raise ValueError('CSV counts need --metadata.')
        frame = pd.read_csv(path, index_col=0)
        frame.index = frame.index.astype(str)
        names = frame.columns.astype(str).to_numpy()
        X = sparse.csr_matrix(frame.to_numpy(dtype=float))
        meta = pd.read_csv(metadata, dtype={'cell_id': str}).set_index('cell_id')
        if meta.index.has_duplicates or frame.index.has_duplicates:
            raise ValueError('Duplicate cell IDs.')
        if set(meta.index) != set(frame.index):
            raise ValueError('Counts and metadata must contain exactly the same cell IDs.')
        meta = meta.loc[frame.index]
    else:
        raise ValueError('Use .csv, .mtx, or .h5ad raw counts.')
    X = sparse.csr_matrix(X, dtype=float)
    if X.shape != (len(meta), len(names)) or meta.index.has_duplicates:
        raise ValueError('Dimensions or cell IDs are invalid.')
    if len(set(names)) != len(names):
        raise ValueError('Gene names must be unique. Sum duplicate symbols upstream.')
    if not np.isfinite(X.data).all() or (X.data < 0).any() or not np.allclose(X.data, np.round(X.data)):
        raise ValueError('Input must be finite, nonnegative, unnormalized integer counts.')
    return X, meta, names


def qc(X, names, min_genes=200, max_mt=20, mt_prefix='MT-'):
    total = np.asarray(X.sum(axis=1)).ravel()
    detected = np.asarray((X > 0).sum(axis=1)).ravel()
    mt = np.array([g.upper().startswith(mt_prefix.upper()) for g in names])
    mt_pct = 100 * np.asarray(X[:, mt].sum(axis=1)).ravel() / np.maximum(total, 1)
    keep = (total > 0) & (detected >= min_genes) & (mt_pct <= max_mt)
    return keep, pd.DataFrame({'total_counts': total, 'detected_genes': detected,
                              'mitochondrial_percent': mt_pct, 'pass_qc': keep})


def pseudobulk(X, meta, label, min_cells=10):
    """One row per donor/label. Sum counts before normalization."""
    rows, records = [], []
    for (donor, value), subset in meta.groupby(['donor_id', label], sort=True):
        indices = meta.index.get_indexer(subset.index)
        if len(indices) < min_cells:
            continue
        rows.append(sparse.csr_matrix(X[indices].sum(axis=0)))
        records.append({'donor_id': donor, 'label': value, 'n_cells': len(indices),
                        'batches': '|'.join(sorted(subset.batch_id.astype(str).unique()))})
    if not rows:
        raise ValueError('No donor/label groups passed --min-cells.')
    return sparse.vstack(rows).tocsr(), pd.DataFrame(records)


def bh(p):
    order = np.argsort(p)
    q = np.minimum.accumulate((p[order] * len(p) / np.arange(1, len(p)+1))[::-1])[::-1]
    result = np.empty_like(q)
    result[order] = np.minimum(q, 1)
    return result


def donor_bootstrap(y, pred, groups, seed=42, iterations=1000):
    """Conditional uncertainty of fixed OOF predictions, resampling whole donors."""
    y, pred, groups = np.asarray(y), np.asarray(pred), np.asarray(groups)
    donors = np.unique(groups)
    classes = np.unique(y)
    rng = np.random.default_rng(seed)
    scores = []
    for _ in range(iterations):
        chosen = rng.choice(donors, size=len(donors), replace=True)
        indices = np.concatenate([np.flatnonzero(groups == donor) for donor in chosen])
        if set(y[indices]) != set(classes):
            continue
        weights = np.concatenate([np.repeat(1/np.sum(groups == donor), np.sum(groups == donor)) for donor in chosen])
        scores.append(float(balanced_accuracy_score(y[indices], pred[indices], sample_weight=weights)))
    if not scores:
        raise ValueError('Bootstrap contains no evaluable draws.')
    return {'metric':'balanced_accuracy','interval_95_percent':np.percentile(scores,[2.5,97.5]).tolist(),
            'valid_draws':len(scores),'requested_draws':iterations,'resampling_unit':'donor',
            'method':'Percentile bootstrap of fixed out-of-fold predictions; models are not refitted. Not external-validation uncertainty.'}


def differential(X, labels, names):
    """Exploratory Welch tests on donor log-normalized pseudobulk, not cell tests."""
    classes = np.unique(labels)
    if len(classes) != 2:
        return None
    A, B = X[labels == classes[1]], X[labels == classes[0]]
    if min(len(A), len(B)) < 3:
        return None
    va, vb = A.var(axis=0, ddof=1), B.var(axis=0, ddof=1)
    denom = va / len(A) + vb / len(B)
    delta = A.mean(axis=0) - B.mean(axis=0)
    p = np.ones(X.shape[1])
    valid = denom > 0
    degrees = denom[valid] ** 2 / ((va[valid]/len(A))**2/(len(A)-1) + (vb[valid]/len(B))**2/(len(B)-1))
    p[valid] = 2 * stats.t.sf(np.abs(delta[valid])/np.sqrt(denom[valid]), degrees)
    # Constant but differing features need a count-based model; don't invent significance.
    return pd.DataFrame({'gene': names, 'contrast': f'{classes[1]} minus {classes[0]}',
                         'mean_log_difference': delta, 'p_value': p, 'q_value': bh(p)}).sort_values('q_value')


def model_evaluation(X, units, folds, features, seed, permutations=0, with_interval=True):
    y = units.label.astype(str).to_numpy()
    groups = units.donor_id.astype(str).to_numpy()
    classes = np.unique(y)
    if len(classes) < 2:
        raise ValueError('Need at least two label classes.')
    donor_counts = {c: len(set(groups[y == c])) for c in classes}
    if min(donor_counts.values()) < folds or folds < 2:
        raise ValueError(f'Need at least {folds} donors in every class; found {donor_counts}.')
    # Split unique donors directly when each donor has one label. Grouped
    # stratification is approximate and can lose a class on small cohorts.
    if units.groupby('donor_id').label.nunique().max() == 1:
        donors = np.unique(groups)
        labels = np.array([y[groups == donor][0] for donor in donors])
        splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
        splits = [(np.flatnonzero(np.isin(groups, donors[train])),
                   np.flatnonzero(np.isin(groups, donors[test])))
                  for train, test in splitter.split(donors, labels)]
    else:
        splitter = StratifiedGroupKFold(n_splits=folds, shuffle=True, random_state=seed)
        splits = list(splitter.split(X, y, groups))
    proba = np.zeros((len(y), len(classes)))
    coefficients, records = [], []
    for i, (train, test) in enumerate(splits):
        if set(groups[train]) & set(groups[test]):
            raise AssertionError('Donor leakage.')
        if set(y[train]) != set(classes) or set(y[test]) != set(classes):
            raise ValueError('A fold lacks a class. Reduce --folds or obtain more balanced donors.')
        pipe = Pipeline([('variable', VariableGenes(min(1000, X.shape[1]))),
                         ('select', SelectKBest(f_classif, k=min(features, X.shape[1], 1000))),
                         ('scale', StandardScaler()),
                         ('model', LogisticRegression(C=0.1, class_weight='balanced', max_iter=3000, random_state=seed))])
        pipe.fit(X[train], y[train])
        proba[test] = pipe.predict_proba(X[test])
        coef = np.zeros(X.shape[1])
        selected = pipe['variable'].indices_[pipe['select'].get_support()]
        coef[selected] = np.abs(pipe['model'].coef_).mean(axis=0)
        coefficients.append(coef)
        records.append({'fold': i+1, 'train_donors': sorted(set(groups[train])),
                        'test_donors': sorted(set(groups[test])), 'train_units': len(train), 'test_units': len(test)})
    pred = classes[proba.argmax(axis=1)]
    # Equal donor weight even when one donor has several fate labels.
    weights = np.array([1 / np.sum(groups == g) for g in groups])
    score = float(balanced_accuracy_score(y, pred, sample_weight=weights))
    summary = {'balanced_accuracy': score, 'majority_baseline_balanced_accuracy': 1/len(classes),
               'classes': list(classes), 'confusion_matrix': confusion_matrix(y, pred, labels=classes).tolist(),
               'confusion_matrix_unit': 'donor/label pseudobulk rows', 'donors_by_class': donor_counts,
               'evaluation_unit': 'held-out donor', 'folds': records}
    if with_interval:
        summary['conditional_bootstrap'] = donor_bootstrap(y,pred,groups,seed,1000)
    if len(classes) == 2:
        summary['roc_auc'] = float(roc_auc_score(y == classes[1], proba[:, 1], sample_weight=weights))
    null_scores = []
    if permutations:
        if units.groupby('donor_id').label.nunique().max() > 1:
            summary['permutation_note'] = 'Skipped: donor-label permutation only supports one label per donor.'
        else:
            R = np.random.default_rng(seed)
            donors = np.unique(groups)
            donor_labels = np.array([y[groups == d][0] for d in donors])
            for _ in range(permutations):
                perm = dict(zip(donors, R.permutation(donor_labels)))
                shuffled = units.copy()
                shuffled['label'] = [perm[d] for d in groups]
                try:
                    null, _, _ = model_evaluation(X, shuffled, folds, features, seed, with_interval=False)
                    null_scores.append(null['balanced_accuracy'])
                except ValueError:
                    continue
            summary['permutation_scores'] = null_scores
            summary['successful_permutations'] = len(null_scores)
            if null_scores:
                summary['permutation_p_value'] = (1+sum(s >= score for s in null_scores))/(1+len(null_scores))
    predictions = units.copy()
    predictions['predicted_label'] = pred
    for i, c in enumerate(classes):
        predictions[f'probability_{c}'] = proba[:, i]
    return summary, predictions, np.mean(coefficients, axis=0)


def pathways(path, X, names, units):
    if not path:
        return None
    sets = json.loads(Path(path).read_text(encoding='utf-8'))
    lookup = {g: i for i, g in enumerate(names)}
    Z = (X-X.mean(axis=0)) / np.maximum(X.std(axis=0), 1e-8)
    result = units[['donor_id', 'label']].copy()
    coverage = []
    for name, genes in sets.items():
        found = sorted(set(genes) & set(lookup))
        coverage.append({'pathway': name, 'matched': len(found), 'requested': len(set(genes)), 'genes': found})
        result[name] = Z[:, [lookup[g] for g in found]].mean(axis=1) if found else np.nan
    return result, coverage


def run(args, progress=None):
    notify = progress or (lambda message: None)
    notify('Reading and validating counts…')
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Output directory is not empty. Use a new directory for each run.')
    out.mkdir(parents=True, exist_ok=True)
    X, meta, names = read_data(args.counts, args.metadata, args.genes)
    required = {'donor_id', 'batch_id', args.label}
    if not required.issubset(meta.columns):
        raise ValueError(f'Metadata requires {sorted(required)}.')
    if meta[list(required)].isna().any().any():
        raise ValueError('Missing donor, batch, or labels.')
    for column in required:
        meta[column] = meta[column].astype(str)
    if args.task == 'pd' and meta.groupby('donor_id')[args.label].nunique().max() > 1:
        raise ValueError('PD status must be consistent within a donor.')
    n_input = X.shape[0]
    notify('Filtering cells and genes…')
    keep, metrics = qc(X, names, args.min_genes, args.max_mt, args.mt_prefix)
    metrics.index = meta.index
    metrics.to_csv(out/'cell_qc.csv', index_label='cell_id')
    X, meta = X[keep], meta.loc[keep].copy()
    if args.cell_type:
        if 'cell_type' not in meta:
            raise ValueError('--cell-type requires cell_type metadata, assigned independently of disease labels.')
        choose = meta.cell_type.astype(str).eq(args.cell_type).to_numpy()
        X, meta = X[choose], meta.loc[choose].copy()
    if X.shape[0] < 4:
        raise ValueError('Too few cells after QC and cell-type filtering.')
    gene_keep = np.asarray((X > 0).sum(axis=0)).ravel() >= args.min_gene_cells
    X, names = X[:, gene_keep], names[gene_keep]
    if X.shape[1] < 3:
        raise ValueError('Too few expressed genes.')
    warning = []
    if not any(g.upper().startswith(args.mt_prefix.upper()) for g in names):
        warning.append('No mitochondrial symbols matched; mitochondrial filtering was ineffective. Map gene IDs or adjust prefix.')
    if args.task == 'pd' and not args.cell_type:
        warning.append('No cell-type subset: PD status may reflect cell composition. Not a dopaminergic-specific result.')
    batch_table = pd.crosstab(meta.batch_id, meta[args.label])
    batch_table.to_csv(out/'batch_label_counts.csv')
    if len(batch_table) > 1 and (batch_table.gt(0).sum(axis=1) == 1).all():
        raise ValueError('Every batch contains only one label: complete batch/label confounding. Obtain overlapping batches before interpreting a classifier.')
    if len(batch_table) > 1:
        warning.append('Multiple batches detected; batch-label overlap alone does not rule out confounding. Review protocol and time-point effects; this model does not adjust batch.')
    notify('Calculating the descriptive embedding…')
    Y = normalize(X)
    # Whole-dataset embedding is descriptive only, never fed to cross-validation.
    dim = min(20, Y.shape[0]-1, Y.shape[1]-1)
    embed = TruncatedSVD(n_components=dim, random_state=args.seed).fit_transform(Y)
    notify('Calculating descriptive cell clusters…')
    cluster = KMeans(n_clusters=min(args.clusters, X.shape[0]), n_init=10, random_state=args.seed).fit_predict(embed)
    cells = meta.copy()
    cells['cluster'] = cluster
    cells['svd_1'], cells['svd_2'] = embed[:, 0], embed[:, 1]
    cells.to_csv(out/'cells_embedding.csv', index_label='cell_id')
    plt.figure(figsize=(8, 6))
    plt.scatter(embed[:, 0], embed[:, 1], c=cluster, s=7, cmap='tab10', alpha=.65)
    plt.xlabel('SVD 1'); plt.ylabel('SVD 2'); plt.title('Descriptive cell clusters (not annotated cell fates)')
    plt.tight_layout(); plt.savefig(out/'clusters.png', dpi=160); plt.close()
    notify('Training and evaluating on separate donors…')
    bulk, units = pseudobulk(X, meta, args.label, args.min_cells)
    bx = normalize(bulk).toarray()
    report, predictions, importance = model_evaluation(bx, units, args.folds, args.features, args.seed, args.permutations)
    predictions.to_csv(out/'held_out_predictions.csv', index=False)
    pd.DataFrame({'gene': names, 'mean_absolute_standardized_coefficient': importance}).sort_values('mean_absolute_standardized_coefficient', ascending=False).to_csv(out/'model_features.csv', index=False)
    de = differential(bx, units.label.to_numpy(), names) if args.task == 'pd' else None
    if de is not None:
        de.to_csv(out/'exploratory_differential_genes.csv', index=False)
        warning.append('Differential tests use donor pseudobulk but do not adjust batch, sex, age, or genotype; use a count-based design model for publication.')
    pathway = pathways(args.pathways, bx, names, units)
    if pathway:
        pathway[0].to_csv(out/'pathway_scores.csv', index=False)
        (out/'pathway_coverage.json').write_text(json.dumps(pathway[1], indent=2), encoding='utf-8')
        warning.append('Pathway scores are descriptive standardized expression averages, not enrichment significance or causal evidence.')
    report.update({'task': args.task, 'label_column': args.label, 'cells_input': n_input,
                   'cells_analyzed': X.shape[0], 'genes_analyzed': X.shape[1], 'donors': units.donor_id.nunique(),
                   'synthetic': args.synthetic, 'warnings': warning,
                   'interpretation': 'Exploratory label classification, not future vulnerability, clinical diagnosis, causal mechanism, or validated treatment guidance.'})
    (out/'metrics.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    notify('Writing results and reproducibility manifest…')
    versions = {}
    for package in ['numpy','pandas','scipy','scikit-learn','matplotlib','anndata']:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = 'not installed (not required for CSV input)'
    hashes = {}
    for source in [args.counts, args.metadata, args.genes, args.pathways]:
        if source:
            digest = hashlib.sha256()
            with open(source, 'rb') as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b''):
                    digest.update(chunk)
            hashes[str(source)] = digest.hexdigest()
    (out/'run_manifest.json').write_text(json.dumps({'arguments': vars(args), 'python': platform.python_version(), 'packages': versions, 'input_sha256': hashes}, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


def demo(directory, seed=42):
    out = Path(directory); out.mkdir(parents=True, exist_ok=True)
    R = np.random.default_rng(seed)
    names = np.array(['MT-ND1','MT-CO1','TH','DDC','SLC6A3','NURR1','LAMP1','LAMP2','CTSD','SQSTM1','HSPA8','PSMB5']+[f'GENE_{i}' for i in range(288)])
    base = R.uniform(.8, 2.5, len(names)); base[:2] = .3
    rows, meta = [], []
    for d in range(16):
        label = 'PD' if d % 2 else 'control'
        donor = f'donor_{d:02}'
        donor_effect = R.lognormal(0, .08, len(names))
        for c in range(35):
            rate = base * donor_effect * R.lognormal(0, .12)
            if label == 'PD':
                rate[6:12] *= 3
            rows.append(R.poisson(rate))
            meta.append({'cell_id': f'{donor}_cell_{c:03}', 'donor_id': donor, 'batch_id': f'batch_{d//4}', 'status': label, 'cell_type': 'dopaminergic'})
    pd.DataFrame(rows, index=[m['cell_id'] for m in meta], columns=names).to_csv(out/'counts.csv', index_label='cell_id')
    pd.DataFrame(meta).to_csv(out/'metadata.csv', index=False)
    print(f'SYNTHETIC demonstration data saved to {out}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    d = sub.add_parser('demo'); d.add_argument('--out', required=True); d.add_argument('--seed', type=int, default=42)
    p = sub.add_parser('run')
    p.add_argument('--counts', required=True); p.add_argument('--metadata'); p.add_argument('--genes'); p.add_argument('--out', required=True)
    p.add_argument('--task', choices=['pd','fate'], default='pd'); p.add_argument('--label', default='status'); p.add_argument('--cell-type')
    p.add_argument('--min-genes', type=int, default=200); p.add_argument('--max-mt', type=float, default=20); p.add_argument('--mt-prefix', default='MT-')
    p.add_argument('--min-gene-cells', type=int, default=3); p.add_argument('--min-cells', type=int, default=10)
    p.add_argument('--folds', type=int, default=4); p.add_argument('--features', type=int, default=50); p.add_argument('--clusters', type=int, default=6)
    p.add_argument('--seed', type=int, default=42); p.add_argument('--permutations', type=int, default=0)
    p.add_argument('--pathways'); p.add_argument('--synthetic', action='store_true')
    args = parser.parse_args()
    if args.command == 'demo':
        demo(args.out, args.seed)
    else:
        if not 0 <= args.max_mt <= 100 or min(args.min_genes, args.min_gene_cells, args.min_cells, args.features, args.clusters) < 1 or args.permutations < 0:
            parser.error('Invalid thresholds or counts.')
        try:
            run(args)
        except ValueError as error:
            parser.exit(2, f'Input error: {error}\n')


if __name__ == '__main__':
    main()

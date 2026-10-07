"""Reproduce a descriptive audit of GSE183248. Never fit a disease classifier."""
import argparse
import hashlib
import json
import urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.decomposition import TruncatedSVD
import stemcell


BASE = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE183nnn/GSE183248/suppl/'
FILES = ['GSE183248_Metadata.csv.gz','GSE183248_Raw_data.csv.gz']


def explore(source, out):
    source, out = Path(source), Path(out)
    if out.exists() and any(out.iterdir()):
        raise ValueError('Choose an empty output directory.')
    out.mkdir(parents=True, exist_ok=True)
    metadata = pd.read_csv(source/FILES[0],index_col=0)
    metadata.index = metadata.index.astype(str)
    if metadata.index.has_duplicates:
        raise ValueError('Duplicate metadata cell IDs.')
    chunks, genes, ids = [], [], None
    for frame in pd.read_csv(source/FILES[1],index_col=0,chunksize=256):
        if ids is None:
            ids = frame.columns.astype(str)
        values = frame.to_numpy(dtype=float)
        if not np.isfinite(values).all() or (values<0).any() or not np.allclose(values,np.round(values)):
            raise ValueError('Downloaded file is not raw counts.')
        genes.extend(frame.index.astype(str))
        chunks.append(sparse.csr_matrix(values))
    if len(set(genes)) != len(genes) or set(ids)!=set(metadata.index):
        raise ValueError('Gene names or cell alignment invalid.')
    X = sparse.vstack(chunks).T.tocsr()
    metadata = metadata.loc[ids].copy()
    genes = np.array(genes)
    keep, qc = stemcell.qc(X,genes,min_genes=200,max_mt=20)
    qc.index=ids
    # Published metadata fractions appear on a 0..1 scale; report observed range.
    total = np.asarray(X.sum(axis=1)).ravel()
    metadata['sample'] = metadata['orig.ident']
    metadata['line_group'] = metadata['orig.ident'].str.split('_').str[0]
    metadata['timepoint'] = metadata['orig.ident'].str.split('_').str[1:].str.join('_')
    qc['sample'] = metadata['sample']
    qc.to_csv(out/'real_cell_qc.csv',index_label='cell_id')
    summary = metadata.groupby(['sample','line_group','timepoint']).size().reset_index(name='cells')
    summary.to_csv(out/'real_sample_summary.csv',index=False)
    Y = stemcell.normalize(X[keep])
    average=np.asarray(Y.mean(axis=0)).ravel()
    variance=np.asarray(Y.power(2).mean(axis=0)).ravel()-average**2
    selected=np.argsort(variance)[-min(2000,len(genes)):]
    embedding=TruncatedSVD(n_components=12,random_state=42).fit_transform(Y[:,selected])
    retained=metadata.loc[keep,['sample','line_group','timepoint']].copy()
    retained['svd_1'],retained['svd_2']=embedding[:,0],embedding[:,1]
    retained.to_csv(out/'real_embedding.csv',index_label='cell_id')
    import matplotlib.pyplot as plt
    figure,axes=plt.subplots(1,2,figsize=(12,5))
    colors={'Control':'#369b8e','PINK1':'#bd7063'}
    for group in retained.line_group.unique():
        mask=retained.line_group.eq(group)
        axes[0].scatter(retained.loc[mask,'svd_1'],retained.loc[mask,'svd_2'],s=6,alpha=.5,label=group,color=colors.get(group))
    axes[0].set(xlabel='SVD 1',ylabel='SVD 2',title='Two cell-line groups; descriptive embedding')
    axes[0].legend()
    axes[1].barh(summary['sample'],summary['cells'],color=[colors.get(g,'gray') for g in summary.line_group])
    axes[1].set(xlabel='Cells in provided matrix',title='Time points are not independent donors')
    figure.suptitle('Real public data: GSE183248 · no disease classifier evaluation',fontsize=12)
    figure.tight_layout(); figure.savefig(out/'real_data_audit.png',dpi=160); plt.close(figure)
    hashes={name:hashlib.sha256((source/name).read_bytes()).hexdigest() for name in FILES}
    report={'accession':'GSE183248','source_urls':{name:BASE+name for name in FILES},'input_sha256':hashes,
            'synthetic':False,'cells':int(X.shape[0]),'genes':int(X.shape[1]),'cells_after_example_qc':int(keep.sum()),
            'sample_categories_in_download':int(metadata['sample'].nunique()),'line_groups':sorted(metadata.line_group.unique()),
            'matrix_totals_match_published_metadata':bool(np.allclose(total,metadata.nCount_RNA)),
            'published_mito_fraction_range':[float(metadata['percent.mito'].min()),float(metadata['percent.mito'].max())],
            'classifier_eligible':False,'disease_prediction_metrics':None,
            'decision':'Two cell-line groups; no independent donor replication within condition. Do not report cross-donor PD accuracy.',
            'limitations':['Public matrix may already reflect upstream filtering; downloaded cells are not all originally sequenced cells.',
                           'GEO lists 12 samples, but this downloaded matrix has 9 sample categories.',
                           'SVD is descriptive; differences may reflect time point, line identity, mutation, protocol or other factors.',
                           'No cell-type annotations were inferred. No early vulnerability or future cell fate was predicted.']}
    (out/'real_data_audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True); p.add_argument('--out',required=True); p.add_argument('--download',action='store_true')
    a=p.parse_args()
    if a.download:
        Path(a.source).mkdir(parents=True,exist_ok=True)
        for name in FILES:
            if not (Path(a.source)/name).exists():
                urllib.request.urlretrieve(BASE+name,Path(a.source)/name)
    explore(a.source,a.out)

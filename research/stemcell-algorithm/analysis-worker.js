/* The existing Python pipeline runs in a worker; uploaded files stay in memory. */
let runtime;
const status = text => postMessage({type:'progress',text});
self.reportProgress = status;
self.onmessage = async ({data}) => {
  try {
    if (!runtime) {
      status('Loading Python and scientific libraries. The first run may take a few minutes.');
      importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js');
      runtime = await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v0.27.7/full/',stdout:()=>{},stderr:()=>{}});
      for (const name of ['numpy','pandas','scipy','scikit-learn','matplotlib']) {
        status('Loading '+name+'… First use downloads scientific libraries.');
        let failure;
        await runtime.loadPackage(name,{messageCallback:text=>status(text),errorCallback:text=>{failure=text;}});
        if(failure) {runtime=null;throw new Error('Library download failed: '+failure+'. Check your connection, then retry.');}
      }
      for (const name of ['stemcell.py','audit_metadata.py']) {
        const response = await fetch(name);
        if (!response.ok) throw new Error('Cannot load '+name+'. Please retry after refreshing.');
        runtime.FS.writeFile('/home/pyodide/'+name,await response.text());
      }
    }
    status('Checking inputs and donor replication…');
    runtime.globals.set('browser_sample',Boolean(data.sample));
    runtime.globals.set('browser_config',JSON.stringify(data.config));
    if (!data.sample) {
      runtime.FS.writeFile('/home/pyodide/upload-counts.csv',data.counts);
      runtime.FS.writeFile('/home/pyodide/upload-metadata.csv',data.metadata);
    }
    status('Running quality checks, donor-separated training and evaluation…');
    const result = await runtime.runPythonAsync(`
import json, shutil, io, zipfile, base64
from pathlib import Path
from argparse import Namespace
import pandas as pd
import stemcell
from js import reportProgress as browser_status
from audit_metadata import audit
cfg=json.loads(browser_config)
out=Path('/home/pyodide/browser-results')
if out.exists(): shutil.rmtree(out)
if browser_sample:
    stemcell.demo('/home/pyodide/browser-sample')
    counts='/home/pyodide/browser-sample/counts.csv'
    metadata='/home/pyodide/browser-sample/metadata.csv'
else:
    counts='/home/pyodide/upload-counts.csv'
    metadata='/home/pyodide/upload-metadata.csv'
check=audit(pd.read_csv(metadata,dtype=str),cfg['label'],cfg['folds'])
if not check['eligible_for_declared_cv']:
    raise ValueError('Cannot evaluate this study: '+ '; '.join(check['reasons']))
stemcell.run(Namespace(counts=counts, metadata=metadata, genes=None, out=str(out), task='pd', label=cfg['label'], cell_type=None, min_genes=cfg['min_genes'], max_mt=20., mt_prefix='MT-', min_gene_cells=3, min_cells=10, folds=cfg['folds'], features=50, clusters=6, seed=42, permutations=0, pathways=None, synthetic=bool(browser_sample)), progress=browser_status)
buf=io.BytesIO()
with zipfile.ZipFile(buf,'w',zipfile.ZIP_DEFLATED) as z:
    for f in out.iterdir(): z.write(f,f.name)
json.dumps({'metrics':json.loads((out/'metrics.json').read_text()),'audit':check,'predictions':pd.read_csv(out/'held_out_predictions.csv').to_dict('records'),'archive':base64.b64encode(buf.getvalue()).decode()})
`);
    postMessage({type:'done',result:JSON.parse(result)});
  } catch (error) { postMessage({type:'error',text:String(error.message||error)}); }
};

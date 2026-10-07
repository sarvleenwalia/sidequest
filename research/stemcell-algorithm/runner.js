'use strict';
(() => {
  const el=id=>document.getElementById(id);
  let worker, timer, downloadURL;
  function finish(message) {
    clearTimeout(timer); el('run-status').textContent=message;
    el('run-own').disabled=el('run-sample').disabled=false;
    el('cancel-run').hidden=true;
  }
  function resetWorker(){if(worker) worker.terminate();worker=null;}
  async function run(sample) {
    el('run-results').hidden=true;
    const counts=el('counts-file').files[0],metadata=el('metadata-file').files[0];
    if(!sample && (!counts||!metadata)) return finish('Choose both a raw-count CSV and a metadata CSV.');
    if(!sample && (counts.size>20*1024*1024||metadata.size>5*1024*1024)) return finish('Browser limit: counts 20 MB, metadata 5 MB. Use the downloadable Python package for larger studies.');
    const config={label:el('label-column').value.trim(),folds:Number(el('run-folds').value),min_genes:Number(el('run-min-genes').value)};
    if(!config.label||!Number.isInteger(config.min_genes)||config.min_genes<1) return finish('Enter a label column and a positive minimum gene count.');
    el('run-own').disabled=el('run-sample').disabled=true;el('cancel-run').hidden=false;
    el('run-status').textContent='Preparing analysis…';
    if(!worker) {
      worker=new Worker('analysis-worker.js');
      worker.onerror=e=>{resetWorker();finish('Analysis engine could not start. Check your connection and retry. '+e.message);};
      worker.onmessage=({data})=>{
        if(data.type==='progress')el('run-status').textContent=data.text;
        if(data.type==='error')finish(data.text);
        if(data.type==='done'){
          const r=data.result,m=r.metrics;
          finish('Analysis complete. Results below were calculated from this run.');
          el('run-results').hidden=false;
          el('run-summary').textContent=`${m.synthetic?'SYNTHETIC SAMPLE':'UPLOADED DATA'} · ${m.cells_analyzed} retained cells · ${m.donors} declared donors · ${(m.balanced_accuracy*100).toFixed(1)}% balanced accuracy · ${(m.majority_baseline_balanced_accuracy*100).toFixed(1)}% majority baseline`;
          el('run-warnings').textContent=m.interpretation+' '+m.warnings.join(' ')+' '+r.audit.warnings.join(' ');
          el('run-report').textContent=JSON.stringify(m,null,2);
          const bytes=Uint8Array.from(atob(r.archive),c=>c.charCodeAt(0));
          if(downloadURL)URL.revokeObjectURL(downloadURL);
          downloadURL=URL.createObjectURL(new Blob([bytes],{type:'application/zip'}));
          el('run-download').href=downloadURL;
        }
      };
    }
    timer=setTimeout(()=>{resetWorker();finish('Run timed out after 10 minutes. Retry with a smaller dataset or use the Python package.');},600000);
    try {worker.postMessage({sample,config,counts:sample?null:await counts.text(),metadata:sample?null:await metadata.text()});}
    catch(e){finish('Could not read the selected files: '+e.message);}
  }
  el('run-own').onclick=()=>run(false);el('run-sample').onclick=()=>run(true);
  el('cancel-run').onclick=()=>{resetWorker();finish('Cancelled. You can start another run.');};
})();

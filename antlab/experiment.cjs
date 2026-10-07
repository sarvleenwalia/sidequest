/* Reproduce the release evidence: node experiment.cjs */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const E=require('./engine.js');
const {performance}=require('node:perf_hooks');
const root=__dirname,started=new Date().toISOString();
const results={protocol:{started_utc:started,seed:20261007,training:{generations:4,candidates_per_generation:3,games_per_candidate:4,ants_per_move:16,max_plies:30,match_seeds:[31000,31001,31002,31003]},validation:{pairs:12,games:24,seeds_start:91000,ants_per_move:16,max_plies:30,colour_swapped:true},maze:{sizes:[10,15,20,28],seeds_per_size:10,ants:25,rounds:40,step_cap:'3 * size * size'},scope:'Simulated search agents; evolutionary hyperparameter search, not neural-network or language-model training.'},training:[],validation:[],greedy_checks:[],mazes:[],tactics:[]};
async function match(w,b,seed,maxPly=30){
 E.seedRandom(seed);const g=new E.Chess();let plies=0;
 while(plies<maxPly&&!g.game_over()){
  const m=await(g.turn()==='w'?w:b)(g);
  if(!m)throw Error('Agent supplied no move before game over');
  if(!g.move(m))throw Error('Agent supplied illegal move: '+m);plies++;
 }
 let score,termination;
 if(g.in_checkmate()){score=g.turn()==='w'?0:1;termination='checkmate';}
 else if(g.game_over()){score=.5;termination='rules_draw';}
 else {const v=E.evalW(g);score=v>200?1:v<-200?0:.5;termination='material_adjudication';}
 return{seed,white_points:score,termination,plies,final_eval_white:E.evalW(g),pgn:g.pgn(),fen:g.fen()};
}
async function score(P){let points=0;const games=[];
 for(let i=0;i<4;i++){
  const white=i%2===0,a=E.antF(P,16),greedy=async g=>E.greedy(g);
  const game=await match(white?a:greedy,white?greedy:a,31000+i);
  game.candidate_white=white;game.candidate_points=white?game.white_points:1-game.white_points;points+=game.candidate_points;games.push(game);
 }return{points_per_game:points/4,games};
}
function quantile(v,q){const a=[...v].sort((x,y)=>x-y);return a[Math.floor((a.length-1)*q)];}
function pairedCI(pairs){const original=randFactory(441);const draws=[];
 for(let k=0;k<10000;k++){let t=0;for(let i=0;i<pairs.length;i++)t+=pairs[Math.floor(original()*pairs.length)];draws.push(t/pairs.length);}
 return[quantile(draws,.025),quantile(draws,.975)];
}
function randFactory(seed){let t=seed>>>0;return()=>{t+=0x6D2B79F5;let x=t;x=Math.imul(x^(x>>>15),x|1);x^=x+Math.imul(x^(x>>>7),x|61);return((x^(x>>>14))>>>0)/4294967296;};}
async function main(){
 let cur={...E.DEF};
 for(let g=0;g<4;g++){
  E.seedRandom(20261007+g);const candidates=[cur,E.mut(cur),E.mut(cur)];let selected=0,best=-1;
  for(let c=0;c<3;c++){const r=await score(candidates[c]);results.training.push({generation:g+1,candidate:c,parameters:{...candidates[c]},...r});if(r.points_per_game>best){best=r.points_per_game;selected=c;}console.log('train',g+1,c,r.points_per_game);}
  cur={...candidates[selected]};
 }
 results.selected_parameters=cur;
 fs.writeFileSync(path.join(root,'trained-settings.json'),JSON.stringify({parameters:cur,training_seed:20261007,training_scope:results.protocol.training,validation_pending:true},null,2));
 for(let i=0;i<12;i++){
  for(const trainedWhite of [true,false]){
   const a=E.antF(cur,16),b=E.antF(E.DEF,16);const r=await match(trainedWhite?a:b,trainedWhite?b:a,91000+i);
   results.validation.push({...r,pair:i+1,trained_white:trainedWhite,trained_points:trainedWhite?r.white_points:1-r.white_points});
  }console.log('held-out pair',i+1);
 }
 for(const label of ['default','selected'])for(let i=0;i<8;i++){
  const white=i%2===0,a=E.antF(label==='default'?E.DEF:cur,16),b=async g=>E.greedy(g);const r=await match(white?a:b,white?b:a,101000+i);
  results.greedy_checks.push({...r,agent:label,agent_white:white,agent_points:white?r.white_points:1-r.white_points});
 }
 for(const n of [10,15,20,28])for(let i=0;i<10;i++){
  const seed=501000+n*100+i;E.seedRandom(seed);E.gen(n);
  const maze=E.mazeSnapshot();let before=performance.now(),shortest=E.bfs();const bfs_ms=performance.now()-before;
  let best=null,reached=0,work=0;before=performance.now();
  for(let r=0;r<40;r++){const x=E.round(25,.12,n*n*3);reached+=x.reached;work+=x.work;if(x.bp&&(!best||x.bp.length<best.length))best=x.bp;}
  const ant_ms=performance.now()-before;
  if(best){if(best[0]!==0||best.at(-1)!==n*n-1)throw Error('Invalid ant endpoints');for(let j=1;j<best.length;j++)if(!E.nbrs(best[j-1]).includes(best[j]))throw Error('Ant route crossed wall');if(best.length<shortest.length)throw Error('Ant route beat exact BFS, impossible');}
  results.mazes.push({size:n,seed,shortest_steps:shortest.length-1,ant_steps:best?best.length-1:null,extra_pct:best?(best.length-shortest.length)/(shortest.length-1)*100:null,reached_of_1000:reached,walk_steps:work,bfs_ms,ant_ms,maze_sha256:crypto.createHash('sha256').update(Buffer.from(maze.G)).digest('hex')});
  console.log('maze',n,i+1,best?best.length-1:'unsolved');
 }
 const tactics=[['white_rook_mate','6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1'],['black_rook_mate','r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 1'],['queen_mate','7k/8/5KQ1/8/8/8/8/8 w - - 0 1'],['stalemate','7k/5K2/6Q1/8/8/8/8/8 b - - 0 1']];
 for(const [name,fen] of tactics){E.seedRandom(771);const g=new E.Chess(fen);const r=await E.think(g,E.DEF,60);let passed;if(!r)passed=g.game_over();else {g.move(r.best.m.san);passed=g.in_checkmate();}results.tactics.push({name,fen,selected_move:r?r.best.m.san:null,passed});}
 const pairs=Array.from({length:12},(_,i)=>results.validation.filter(x=>x.pair===i+1).reduce((a,x)=>a+x.trained_points,0)/2);
 results.summary={trained_validation_points:results.validation.reduce((a,x)=>a+x.trained_points,0),validation_games:24,trained_points_per_game:results.validation.reduce((a,x)=>a+x.trained_points,0)/24,paired_bootstrap_95:pairedCI(pairs),validation_termination_counts:Object.fromEntries(['checkmate','rules_draw','material_adjudication'].map(k=>[k,results.validation.filter(x=>x.termination===k).length])),tactics_passed:results.tactics.filter(x=>x.passed).length,maze_by_size:[10,15,20,28].map(size=>{const rows=results.mazes.filter(x=>x.size===size),solved=rows.filter(x=>x.ant_steps!==null);return{size,mazes:rows.length,solved:solved.length,mean_extra_pct_solved:solved.length?solved.reduce((a,x)=>a+x.extra_pct,0)/solved.length:null,optimal:solved.filter(x=>x.ant_steps===x.shortest_steps).length,mean_goal_rate_pct:rows.reduce((a,x)=>a+x.reached_of_1000/10,0)/rows.length,mean_ant_ms:rows.reduce((a,x)=>a+x.ant_ms,0)/rows.length,mean_bfs_ms:rows.reduce((a,x)=>a+x.bfs_ms,0)/rows.length};})};
 results.protocol.finished_utc=new Date().toISOString();results.protocol.node_version=process.version;results.protocol.source_sha256={};for(const f of ['engine.js','chess.min.js','experiment.cjs'])results.protocol.source_sha256[f]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,f))).digest('hex');
 fs.writeFileSync(path.join(root,'results.json'),JSON.stringify(results,null,2));
 fs.writeFileSync(path.join(root,'trained-settings.json'),JSON.stringify({parameters:cur,training_seed:20261007,summary:results.summary,claim:'Frozen candidate; held-out evidence is in results.json. No strength or improvement claim is certified.'},null,2));
 console.log('DONE',JSON.stringify(results.summary));
}
main().catch(e=>{console.error(e);process.exitCode=1;});

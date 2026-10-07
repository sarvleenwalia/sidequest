/* AntLab core: shared by the website and offline experiments. */
if(typeof module!=='undefined')var Chess=require('./chess.min.js').Chess;
let rand=Math.random;
function seedRandom(seed){let t=Number(seed)>>>0;rand=()=>{t+=0x6D2B79F5;let x=t;x=Math.imul(x^(x>>>15),x|1);x^=x+Math.imul(x^(x>>>7),x|61);return((x^(x>>>14))>>>0)/4294967296;};}
const setRand=f=>{rand=f};
let N=15,W=31,G,tau,sp=null,best=null,run=false,stopA=false;
const DIR=[[1,0],[-1,0],[0,1],[0,-1]];
function gen(n){N=n;W=2*n+1;G=new Uint8Array(W*W).fill(1);G[W+1]=0;const st=[[1,1]];
 while(st.length){const [x,y]=st[st.length-1];const nb=DIR.map(([a,b])=>[x+2*a,y+2*b,x+a,y+b]).filter(([a,b])=>a>0&&b>0&&a<W&&b<W&&G[b*W+a]);
  if(!nb.length){st.pop();continue}const [a,b,mx,my]=nb[rand()*nb.length|0];G[my*W+mx]=0;G[b*W+a]=0;st.push([a,b])}
 for(let i=0,k=n*n/5|0;i<k*4&&k>0;i++){const x=1+rand()*(W-2)|0,y=1+rand()*(W-2)|0;if((x+y)%2==1&&G[y*W+x]){G[y*W+x]=0;k--}}
 tau=new Float32Array(n*n).fill(.1);sp=null;best=null}
const nbrs=(c)=>{const x=c%N,y=c/N|0,o=[];for(const [a,b] of DIR){const nx=x+a,ny=y+b;if(nx>=0&&ny>=0&&nx<N&&ny<N&&!G[(2*y+1+b)*W+(2*x+1+a)])o.push(ny*N+nx)}return o};
function bfs(){const prev=new Int32Array(N*N).fill(-2),q=[0];prev[0]=-1;for(let i=0;i<q.length;i++){const c=q[i];if(c===N*N-1)break;for(const n of nbrs(c))if(prev[n]===-2){prev[n]=c;q.push(n)}}
 const p=[];for(let c=N*N-1;c>=0;c=prev[c]){p.push(c);if(prev[c]<0)break}return p.reverse()}
function erase(path){const out=[],pos=new Map();for(const c of path){if(pos.has(c)){const k=pos.get(c);for(let j=k+1;j<out.length;j++)pos.delete(out[j]);out.length=k+1}else{pos.set(c,out.length);out.push(c)}}return out}
function round(M,rho,cap){let reached=0,work=0,bp=null;const dep=[];const GL=N*N-1,gx=N-1,gy=N-1;
 for(let a=0;a<M;a++){let c=0,prv=-1;const path=[0];for(let s=0;s<cap;s++){work++;let o=nbrs(c);if(o.length>1)o=o.filter(n=>n!==prv);
   const w=o.map(n=>tau[n]*Math.pow(1/(1+Math.abs(gx-n%N)+Math.abs(gy-(n/N|0))),1.5));let t=0;w.forEach(v=>t+=v);let u=rand()*t,i=0;while(i<o.length-1&&(u-=w[i])>0)i++;
   prv=c;c=o[i];path.push(c);if(c===GL){reached++;const e=erase(path);dep.push(e);if(!bp||e.length<bp.length)bp=e;break}}}
 for(let i=0;i<tau.length;i++)tau[i]=Math.max(.02,tau[i]*(1-rho));
 dep.forEach(e=>{const d=3/e.length*N;e.forEach(c=>tau[c]+=d)});return{reached,work,bp}}

const VAL={p:100,n:320,b:330,r:500,q:900,k:0};
const evalW=g=>{let s=0;const b=g.board();for(let r=0;r<8;r++)for(let c=0;c<8;c++){const p=b[r][c];if(!p)continue;const v=VAL[p.type]+(p.type==='k'||p.type==='r'?0:(3.5-Math.max(Math.abs(r-3.5),Math.abs(c-3.5)))*6);s+=p.color==='w'?v:-v}return s};
const val=(g,side)=>{if(g.in_draw())return .5;if(g.in_check()&&g.moves().length===0)return g.turn()===side?0:1;return 1/(1+Math.exp(-(evalW(g)*(side==='w'?1:-1))/300))};
const DEF={a:1,b:3,rho:.08,D:4,T:3};
function pick(g,T){const ms=g.moves(),mv=g.turn();if(!ms.length)return null;let bm=null,bv=-1;for(let k=0;k<T;k++){const m=ms[rand()*ms.length|0];g.move(m);const v=val(g,mv);g.undo();if(v>bv){bv=v;bm=m}}return bm}
/* root value of a move = worst case over every opponent reply (catches hung pieces and mates) */
function rootEta(g,side){if(g.in_checkmate())return 99;const os=g.moves({verbose:true});if(!os.length)return .5;let w=val(g,side);
 for(const o of os){if(o.san.endsWith('#'))return 0;if(!(o.captured||o.promotion))continue;g.move(o);const v=val(g,side);g.undo();if(v<w)w=v}return w}
async function think(g0,P,n,prog,stop,yieldFn){const g=new Chess(g0.fen()),side=g.turn(),ms=g.moves({verbose:true});if(!ms.length)return null;
 const R=ms.map(m=>{g.move(m);const eta=rootEta(g,side);g.undo();return{m,eta,tau:1,n:0,sum:0,line:[m.san],lv:-1}});
 const mate=R.find(r=>r.eta===99);if(mate)return{best:mate,R,mate:true};
 for(let a=0;a<n;a++){const w=R.map(r=>Math.pow(r.tau,P.a)*Math.pow(r.eta+.02,P.b));let t=0;w.forEach(v=>t+=v);let u=rand()*t,i=0;while(i<R.length-1&&(u-=w[i])>0)i++;
  const r=R[i];g.move(r.m);const line=[r.m.san];for(let d=0;d<P.D;d++){const m=pick(g,P.T);if(!m)break;g.move(m);line.push(m)}
  const v=val(g,side);for(let k=0;k<line.length;k++)g.undo();r.n++;r.sum+=v;if(v>r.lv){r.lv=v;r.line=line}
  R.forEach(x=>x.tau=Math.max(.05,x.tau*(1-P.rho)));r.tau+=v*2;
  if(a%8===7){if(prog)prog(a+1,R);if(yieldFn)await yieldFn();if(stop&&stop())break}}
 let bst=R[0],bs=-1;R.forEach(r=>{const s=(r.sum+r.eta*2)/(r.n+2);if(s>bs){bs=s;bst=r}});return{best:bst,R}}
function greedy(g){const ms=g.moves(),mv=g.turn();let bm=[],bv=-1;for(const m of ms){g.move(m);const v=val(g,mv);g.undo();if(v>bv+1e-9){bv=v;bm=[m]}else if(Math.abs(v-bv)<1e-9)bm.push(m)}return bm[rand()*bm.length|0]}
async function playGame(wf,bf,maxPly,stop,yieldFn){const g=new Chess();for(let i=0;i<maxPly&&!g.game_over();i++){if(stop&&stop())return null;const m=await(g.turn()==='w'?wf:bf)(g);if(!m)break;g.move(m);if(yieldFn)await yieldFn()}
 if(g.in_checkmate())return g.turn()==='w'?0:1;if(g.game_over())return .5;const e=evalW(g);return e>200?1:e<-200?0:.5}
const antF=(P,n,y)=>async g=>{const r=await think(g,P,n,null,null,y);return r&&r.best.m.san};

const cl=(v,a,b)=>Math.min(b,Math.max(a,v)),mut=p=>({a:cl(p.a+(rand()-.5)*.6,.5,2),b:cl(p.b+(rand()-.5)*3,1,8),rho:cl(p.rho+(rand()-.5)*.12,.02,.4),D:cl(Math.round(p.D+(rand()<.5?-1:1)*(1+(rand()*2|0))),2,8),T:cl(Math.round(p.T+(rand()<.5?-1:1)),1,8)});

function mazeSnapshot(){return{N,W,G:Array.from(G),tau:Array.from(tau),shortest:bfs()};}
function validParams(p){return p&&Number.isFinite(p.a)&&p.a>=.5&&p.a<=2&&Number.isFinite(p.b)&&p.b>=1&&p.b<=8&&Number.isFinite(p.rho)&&p.rho>=.02&&p.rho<=.4&&Number.isInteger(p.D)&&p.D>=2&&p.D<=8&&Number.isInteger(p.T)&&p.T>=1&&p.T<=8;}
if(typeof module!=='undefined')module.exports={Chess,seedRandom,gen,bfs,nbrs,erase,round,mazeSnapshot,DEF,evalW,val,rootEta,think,greedy,playGame,antF,mut,validParams};

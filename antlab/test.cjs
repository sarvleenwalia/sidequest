const assert=require('node:assert/strict');const E=require('./engine.js');
let passed=0;const tests=[];
async function test(name,fn){const start=Date.now();await fn();passed++;tests.push({name,passed:true,elapsed_ms:Date.now()-start});console.log('PASS',name);}
(async()=>{
 await test('Maze generation reproduces the same seed',()=>{E.seedRandom(11);E.gen(10);const a=E.mazeSnapshot();E.seedRandom(11);E.gen(10);assert.deepEqual(E.mazeSnapshot(),a);});
 await test('Different seeds produce different maze layouts',()=>{E.seedRandom(12);E.gen(10);const a=E.mazeSnapshot().G;E.seedRandom(13);E.gen(10);assert.notDeepEqual(E.mazeSnapshot().G,a);});
 await test('BFS route is connected and legal at every size',()=>{for(const n of [10,15,20,28]){E.seedRandom(41+n);E.gen(n);const p=E.bfs();assert.equal(p[0],0);assert.equal(p.at(-1),n*n-1);assert.equal(new Set(p).size,p.length);for(let i=1;i<p.length;i++)assert(E.nbrs(p[i-1]).includes(p[i]));}});
 await test('Loop erasure preserves a simple connected path',()=>assert.deepEqual(E.erase([0,1,2,1,3,4,3,5]),[0,1,3,5]));
 await test('Pheromones stay positive and finite',()=>{E.seedRandom(17);E.gen(10);E.round(25,.12,300);assert(E.mazeSnapshot().tau.every(x=>Number.isFinite(x)&&x>=.0199));});
 await test('Ant paths do not cross walls or beat exact BFS',()=>{E.seedRandom(12);E.gen(10);const shortest=E.bfs();let p;for(let i=0;i<40;i++){const r=E.round(25,.12,300);if(r.bp)p=r.bp;}assert(p);assert(p.length>=shortest.length);for(let i=1;i<p.length;i++)assert(E.nbrs(p[i-1]).includes(p[i]));});
 await test('Search returns a legal move without mutating the input game',async()=>{const g=new E.Chess(),fen=g.fen();E.seedRandom(4);const r=await E.think(g,E.DEF,16);assert(g.moves().includes(r.best.m.san));assert.equal(g.fen(),fen);assert.equal(g.history().length,0);});
 await test('Chess search reproduces a fixed seed',async()=>{const g=new E.Chess();E.seedRandom(2);const a=await E.think(g,E.DEF,16);E.seedRandom(2);const b=await E.think(g,E.DEF,16);assert.equal(a.best.m.san,b.best.m.san);assert.deepEqual(a.R.map(r=>[r.n,r.sum,r.tau]),b.R.map(r=>[r.n,r.sum,r.tau]));});
 await test('White mate-in-one is detected',async()=>{const g=new E.Chess('6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1');const r=await E.think(g,E.DEF,16);g.move(r.best.m.san);assert(g.in_checkmate());});
 await test('Black mate-in-one is detected',async()=>{const g=new E.Chess('r5k1/5ppp/8/8/8/8/5PPP/6K1 b - - 0 1');const r=await E.think(g,E.DEF,16);g.move(r.best.m.san);assert(g.in_checkmate());});
 await test('Stalemate is neutral and no move is returned',async()=>{const g=new E.Chess('7k/5K2/6Q1/8/8/8/8/8 b - - 0 1');assert(g.in_draw());assert.equal(E.val(g,'w'),.5);assert.equal(await E.think(g,E.DEF,16),null);});
 await test('Insufficient-material draw is neutral',()=>{const g=new E.Chess('7k/8/5K2/8/8/8/8/8 w - - 0 1');assert(g.in_draw());assert.equal(E.val(g,'w'),.5);});
 await test('Mutations are bounded across 1,000 samples',()=>{E.seedRandom(4);let p={...E.DEF};for(let i=0;i<1000;i++){p=E.mut(p);assert(E.validParams(p));}});
 await test('Corrupt persisted settings are rejected',()=>{for(const p of [null,{}, {...E.DEF,a:NaN},{...E.DEF,D:99},{...E.DEF,T:1.5}])assert(!E.validParams(p));});
 await test('Stop is polled without a progress callback',async()=>{let polls=0,yields=0;const r=await E.think(new E.Chess(),E.DEF,150,null,()=>{polls++;return true;},async()=>{yields++;});assert.equal(polls,1);assert.equal(yields,1);assert.equal(r.R.reduce((s,x)=>s+x.n,0),8);});
 await test('Stopped game returns no outcome',async()=>assert.equal(await E.playGame(async()=>null,async()=>null,30,()=>true),null));
 await test('Chess rules library accepts a legal castling move',()=>{const g=new E.Chess('r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1');assert(g.moves().includes('O-O'));assert(g.move('O-O'));assert.equal(g.get('g1').type,'k');});
 await test('Chess rules library enforces en passant',()=>{const g=new E.Chess();for(const m of ['e4','a6','e5','d5'])assert(g.move(m));assert(g.move('exd6'));assert.equal(g.get('d5'),null);});
 await test('Chess rules library supports queen promotion',()=>{const g=new E.Chess('7k/P7/8/8/8/8/8/7K w - - 0 1');assert(g.move({from:'a7',to:'a8',promotion:'q'}));assert.equal(g.get('a8').type,'q');});
 require('node:fs').writeFileSync(require('node:path').join(__dirname,'tests.json'),JSON.stringify({passed,failed:0,tests},null,2));console.log(passed+' tests passed');
})().catch(e=>{console.error(e);process.exitCode=1;});

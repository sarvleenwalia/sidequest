import http from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=fileURLToPath(new URL('./',import.meta.url));
const allowed=new Set(['index.html','style.css','app.js']);
const types={'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8'};
http.createServer(async(req,res)=>{const name=new URL(req.url,'http://localhost').pathname.slice(1)||'index.html';if(!allowed.has(name)){res.writeHead(404);res.end('Not found');return;}try{const body=await readFile(path.join(root,name));res.writeHead(200,{'Content-Type':types[path.extname(name)],'X-Content-Type-Options':'nosniff'});res.end(body);}catch{res.writeHead(500);res.end('Unable to serve file');}}).listen(4173,'127.0.0.1',()=>console.log('Sidequest preview: http://127.0.0.1:4173'));

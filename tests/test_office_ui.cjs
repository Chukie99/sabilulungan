// Exercise native pixel assets and navigation without an installed browser.
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8');
const code=html.slice(html.indexOf('const staff='),html.indexOf('const el=id'));
const canvas={fillRect(){},fillText(){}};
const context={matchMedia:()=>({matches:false}),performance:{now:()=>0},el:()=>({getContext:()=>canvas})};
vm.createContext(context);
vm.runInContext(code+`;globalThis.test={staff,pixelAvatar,drawMap,pathTo,homes,blocked};`,context);
const t=context.test;t.drawMap();
const sprites=Object.entries(t.staff).map(([role,info])=>t.pixelAvatar(role,info[1]));
assert.equal(new Set(sprites).size,13,'Each character needs a distinct asset');
for(const home of t.homes){for(const target of [[15,6],[15,12],[10,16],[5,16],[25,12],[27,16],[16,16],[2,11]]){const path=t.pathTo({x:home[0],y:home[1]},target);assert(path.length,'Every desk needs access to each lounge waypoint');let last=home;for(const tile of path){assert(!t.blocked.has(tile.join(',')),'Path crosses furniture');assert.equal(Math.abs(tile[0]-last[0])+Math.abs(tile[1]-last[1]),1,'Movement must follow adjacent tiles');last=tile;}}}
console.log('PASS: 13 distinct sprites and 104 paths avoid furniture');

const fs=require('fs'),vm=require('vm'),assert=require('assert');
const code=fs.readFileSync('office.js','utf8');
const canvas={fillRect(){},fillText(){},beginPath(){},moveTo(){},lineTo(){},closePath(){},fill(){},save(){},restore(){},clip(){}};
const context={matchMedia:()=>({matches:false}),performance:{now:()=>0},el:()=>({getContext:()=>canvas})};
vm.createContext(context);vm.runInContext(code+`;globalThis.test={staff,pixelAvatar,drawMap,pathTo,homes,blocked,roamPoints};`,context);
const t=context.test;t.drawMap();const agents=JSON.parse(fs.readFileSync('agents.json','utf8'));
assert.equal(Object.keys(agents).length,t.homes.length,'Each agent needs its own desk');
const sprites=Object.entries(t.staff).map(([role,info])=>t.pixelAvatar(role,info[1]));
assert.equal(new Set(sprites).size,Object.keys(agents).length,'Each character needs a distinct asset');
for(const role of Object.keys(agents))assert(t.staff[role],'Each agent needs a named avatar');
for(const home of t.homes){for(const target of t.roamPoints){const path=t.pathTo({x:home[0],y:home[1]},target);assert(path.length,'Every desk needs access to each waypoint');let last=home;for(const tile of path){assert(!t.blocked.has(tile.join(',')),'Path crosses furniture');assert.equal(Math.abs(tile[0]-last[0])+Math.abs(tile[1]-last[1]),1,'Movement must follow adjacent tiles');last=tile;}const back=t.pathTo({x:target[0],y:target[1]},home);assert(back.length,'Every character must be able to return to work');}}
console.log('PASS: 20 unique characters, 140 outward and 140 return routes');

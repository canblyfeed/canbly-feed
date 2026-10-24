// usage: node template/shot.js <slides.html> <outdir>  -> outdir/01.png, 02.png ...
const {chromium}=require('playwright');const path=require('path');const fs=require('fs');
const [html,out]=process.argv.slice(2);
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1400}});
await p.goto('file://'+path.resolve(html));await p.evaluate(()=>document.fonts.ready);
fs.mkdirSync(out,{recursive:true});const s=await p.$$('section');
for(let i=0;i<s.length;i++)await s[i].screenshot({path:path.join(out,String(i+1).padStart(2,'0')+'.png')});await b.close();})();

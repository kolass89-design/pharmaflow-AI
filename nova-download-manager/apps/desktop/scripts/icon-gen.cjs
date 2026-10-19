// Generates build/icon.png (512x512) with zero dependencies.
const zlib = require('node:zlib'); const fs = require('node:fs'); const path = require('node:path');
const S = 512;
const crcTable = []; for (let n=0;n<256;n++){let c=n;for(let k=0;k<8;k++)c=c&1?0xedb88320^(c>>>1):c>>>1;crcTable[n]=c;}
function crc32(buf){let c=0xffffffff;for(let i=0;i<buf.length;i++)c=crcTable[(c^buf[i])&0xff]^(c>>>8);return (c^0xffffffff)>>>0;}
function chunk(type,data){const len=Buffer.alloc(4);len.writeUInt32BE(data.length);const td=Buffer.concat([Buffer.from(type),data]);const crc=Buffer.alloc(4);crc.writeUInt32BE(crc32(td));return Buffer.concat([len,td,crc]);}
const px = Buffer.alloc(S*S*4);
function setP(x,y,r,g,b,a){const i=(y*S+x)*4;px[i]=r;px[i+1]=g;px[i+2]=b;px[i+3]=a;}
const R=110; // corner radius
for(let y=0;y<S;y++)for(let x=0;x<S;x++){
  const cx=Math.max(R-x,0,x-(S-1-R)), cy=Math.max(R-y,0,y-(S-1-R));
  const outside=Math.hypot(cx,cy)>R;
  if(outside){setP(x,y,0,0,0,0);continue;}
  const t=(x+y)/(2*S);
  let r=Math.round(109+(34-109)*t), g=Math.round(124+(195-124)*t), b=Math.round(255+(230-255)*t);
  // white download arrow: shaft + head + tray
  const inShaft = x>226&&x<286&&y>110&&y<300;
  const head = y>=300&&y<384 ? Math.abs(x-256) < (84-(y-300)) : false;
  const tray = x>140&&x<372&&y>396&&y<428;
  const trayL = x>=140&&x<168&&y>360&&y<428, trayR = x>344&&x<=372&&y>360&&y<428;
  if(inShaft||head||tray||trayL||trayR){r=255;g=255;b=255;}
  setP(x,y,r,g,b,255);
}
const rows=[]; for(let y=0;y<S;y++){const row=Buffer.alloc(1+S*4);row[0]=0;px.copy(row,1,y*S*4,(y+1)*S*4);rows.push(row);}
const ihdr=Buffer.alloc(13); ihdr.writeUInt32BE(S,0); ihdr.writeUInt32BE(S,4); ihdr[8]=8; ihdr[9]=6;
const png=Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ihdr),chunk('IDAT',zlib.deflateSync(Buffer.concat(rows),{level:9})),chunk('IEND',Buffer.alloc(0))]);
const out=path.join(__dirname,'..','build','icon.png'); fs.writeFileSync(out,png);
console.log('wrote',out,png.length,'bytes');

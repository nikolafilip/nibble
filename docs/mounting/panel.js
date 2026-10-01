// The two-sided panel (D065): where every card stands, the rails, the ribbons' routes and their lengths.
// panel.html draws it; `node panel.js` prints the slot plan, the rail heights and the lengths that docs/mounting.md quotes,
// so the document and the model come from one place. Lengths in mm. "y" in a face's plan is measured DOWN from the top of
// the uprights (the way a drawing is read); heights above the table are HEIGHT + FOOT - y.
'use strict';
const CARD=100, PITCH=110, COLS=5, SIDE=20, TOP=10;        // card, slot pitch, columns a face, margin inside the uprights' outer edges, top margin
const UP=20, HEIGHT=800, FOOT=300, FOOT_H=20;              // 2020 extrusion: its section, the uprights' length, the feet (laid flat under the uprights)
const WIDTH=2*SIDE+COLS*PITCH-10;                          // 580: five cards, four gaps and the margins; also every rail's length
const STANDOFF=12;                                         // card to rail; open until the pilot's socket is measured (docs/mounting.md)
const SEQ={w:245,h:255,holes:231,hole_y:20,link_x:115};    // the sequencer: size, its rails' spacing, its upper holes below its top edge, its link header's x
const HDR_Y=7.5, LINK_Y=95, LINK_IN=14, LINK_OUT=80, CHAIN_X=40;   // on a card: the bus header below the top edge; the link headers along the bottom edge
const RIBBON_W=64*1.27;                                    // 81.3: the bus ribbon's width
const SLACK=300;                                           // per bus ribbon: the loose end at the hub and the fold-backs

// ---- the rows: y of each rail (a card's holes are mid-height, so the rail runs through the middle of its row) ----
const FRONT_RAILS=[60,170,280,390,500,610,731];            // rows 1-4 at the pitch; rows 5-7 are the band: the sequencer's two rails (231 apart) and one between
const BACK_RAILS=[60,170,280,390,500,610,720];             // seven rows at the pitch
const rail_y=(face,row)=>(face==='front'?FRONT_RAILS:BACK_RAILS)[row-1];
const card_top=(face,row)=>rail_y(face,row)-CARD/2;
const col_x=c=>SIDE+(c-1)*PITCH;                           // a column's left edge
const SEQ_X=col_x(1), SEQ_Y=rail_y('front',5)-SEQ.hole_y;  // the sequencer: left edge on column 1 (its bus header then sits in column 1's ribbon), top edge 20 above its upper rail

// ---- the slot plan: face -> row -> column -> card. The front as the front sees it, the back as the back sees it (its column 1 stands behind the front's column 5) ----
const KINDS={alu:['ALU bit',1],ctr:['counter bit',2],reg:['register bit',3],memctl:['memory control',4],mem:['memory slots',8],prog:['program',5],
             clock:['clock',2],panela:['panel A',24],panelb:['panel B',16],panelc:['panel C',16],hub:['hub',1],seq:['sequencer',19]};
const FRONT={1:{1:'alu0',2:'ctr0',3:'ctr7',4:'reg0',5:'reg1'},
             2:{1:'alu1',2:'ctr1',3:'ctr6',4:'reg2',5:'reg3'},
             3:{1:'alu2',2:'ctr2',3:'ctr5'},
             4:{1:'alu3',2:'ctr3',3:'ctr4'},
             5:{4:'clock'},
             6:{4:'panela',5:'panelb'},
             7:{4:'panelc',5:'hub'}};
const BACK= {1:{1:'memctl'},
             2:{1:'mem0'},
             3:{1:'mem1'},
             4:{1:'mem2'},
             5:{1:'mem3'},
             6:{1:'mem4',2:'mem7'},
             7:{1:'mem5',2:'mem6'}};
// program cards fill the back along ribbon B, so a longer program is more cards at the ribbon's end: column 2 downward, 3 upward, 4 downward, 5 upward
const PROG_SLOTS=[[2,1],[2,2],[2,3],[2,4],[2,5],[3,7],[3,6],[3,5],[3,4],[3,3],[3,2],[3,1],[4,1],[4,2],[4,3],[4,4],[4,5],[4,6],[4,7],[5,7],[5,6],[5,5],[5,4],[5,3],[5,2],[5,1]];
const PROG_MAX=PROG_SLOTS.length;

function plan(nprog){
  const back={}; for(const r in BACK){ back[r]={...BACK[r]}; }
  PROG_SLOTS.slice(0,nprog).forEach(([c,r],i)=>{ back[r]=back[r]||{}; back[r][c]='prog'+(i+1); });
  return {front:FRONT,back};
}
const kind=name=>name.replace(/\d+$/,'');
function cards(face,P){ const out=[]; for(const r in P[face]) for(const c in P[face][r]) out.push({name:P[face][r][c],row:+r,col:+c,x:col_x(+c),y:card_top(face,+r)}); return out; }

// ---- the bus ribbons: a route is a list of points behind the face, [x, y]; a socket wherever a column's card has its header ----
const hdr=(face,row)=>card_top(face,row)+HDR_Y;
const HOP=40, TURN_IN=28;                                  // a turn is three folds (mounting.md); the ribbon doubled back costs about this much over the sideways step; the sideways band's centre lies this far inside the last socket
function route_front(P){
  // from the hub's top header (column 5, row 7) up column 5, down 4, up 3, down 2, a sideways step to column 1 above the sequencer, down through its socket, back up column 1
  // a turn's sideways run lies just inside the last socket: the 45 degree fold starts past the socket and the 81 mm band lies back over the column (TURN_IN)
  const cx=c=>col_x(c)+CARD/2, F=cards('front',P), top=hdr('front',1)+TURN_IN;
  const pts=[[cx(5),hdr('front',7)],[cx(5),top],[cx(4),top],[cx(4),hdr('front',7)],[cx(3),hdr('front',7)],[cx(3),top],[cx(2),top],[cx(2),SEQ_Y-60],[cx(1),SEQ_Y-60],[cx(1),SEQ_Y+HDR_Y+12],[cx(1),top]];
  return {name:'A',pts,sockets:F.length+1,hops:4};
}
function route_back(P){
  // from the hub's bottom header, under the panel, up the back's column 1 (behind the hub), then down 2, up 3, down 4, up 5 as far as its cards go
  const cx=c=>col_x(c)+CARD/2, B=cards('back',P);
  const high=c=>{ const ys=B.filter(k=>k.col===c).map(k=>hdr('back',k.row)); return ys.length?Math.min(...ys):hdr('back',7); };
  const under=HEIGHT+FOOT_H-5, top=hdr('back',1)+TURN_IN;         // 5 mm above the table, between the feet
  const hub_bottom=card_top('front',7)+CARD-7;                    // the hub's second header, 7 mm above its bottom edge (HY2 = 93)
  const pts=[[cx(1),hub_bottom],[cx(1),under],[cx(1),top],[cx(2),top],[cx(2),hdr('back',7)],[cx(3),hdr('back',7)],[cx(3),top],[cx(4),top],[cx(4),hdr('back',7)],[cx(5),hdr('back',7)],[cx(5),high(5)]];
  return {name:'B',pts,sockets:B.length+1,hops:4+1};              // the fifth turn: the ribbon arrives mirrored from under the panel
}
const length=pts=>pts.slice(1).reduce((s,p,i)=>s+Math.hypot(p[0]-pts[i][0],p[1]-pts[i][1]),0);
function ribbons(P){
  return [route_front(P),route_back(P)].map(r=>({...r,mm:Math.round(length(r.pts)+r.hops*HOP+SLACK)}));
}

// ---- the link cables along the bottom edges: OUT (x 80) to the next card's IN (x 14); the chained 12-way over a column's fronts at x 40 ----
function links(P){
  const F=cards('front',P), at=n=>F.find(k=>k.name===n);
  const six=[]; const chain=(a,b)=>{ const A=at(a), B=at(b); const side=A.row===B.row&&B.col===A.col+1;
    // side by side: a U under the gap, three folds, about 80 mm. One above the other: out to the column gap on the right, along it, back in under the next card: about 230 mm
    six.push({from:a,to:b,mm:side?80:230,how:side?'U, side by side':'round the column gap'}); };
  for(let i=0;i<3;i++) chain('alu'+i,'alu'+(i+1));
  for(let i=0;i<7;i++) chain('ctr'+i,'ctr'+(i+1));
  // the 12-way chains: the sequencer's link header up column 2 over the counter cards, a U at the top, down column 3; memory control down column 1 of the back, a U, up column 2
  const twelve=[{what:'sequencer to the eight counter cards',sockets:9,mm:Math.round((SEQ_Y-(card_top('front',1)+LINK_Y))+35+PITCH+HOP+(card_top('front',4)+LINK_Y)-(card_top('front',1)+LINK_Y)+100)},
                {what:'memory control to the eight slot cards',sockets:9,mm:Math.round((card_top('back',7)-card_top('back',1))+PITCH+HOP+PITCH+100)}];
  return {six,twelve};
}

// ---- the frame's parts ----
function parts(P){
  const rails=FRONT_RAILS.length+BACK_RAILS.length;
  const n=cards('front',P).length+cards('back',P).length;
  return [['2020 extrusion, 800 mm',2,'the uprights'],
          [`2020 extrusion, ${WIDTH} mm`,rails,`${FRONT_RAILS.length} rails on the front face, ${BACK_RAILS.length} on the back; ${(rails*WIDTH/1000).toFixed(1)} m`],
          [`2020 extrusion, ${FOOT} mm`,2,'the feet, flat under the uprights, across the panel'],
          ['2020 corner brackets with their screws and T-nuts',rails*2+4,'one at each rail end, two per foot'],
          ['M3 T-nuts for the 6 mm slot',2*n+4+10,`two per card, four for the sequencer, ten over`],
          [`M3 male-female standoffs, ${STANDOFF} mm or what the pilot says`,2*n+4+10,'brass; the sequencer may want longer ones (its upper rail runs under its header)'],
          ['M3 x 6 mm screws',2*(2*n+4)+20,'card to standoff, standoff to T-nut; no washers (the mounting pads are 6.4 mm)'],
          ['Rubber feet, self-adhesive',4,'under the feet']];
}

function report(nprog=20){
  const P=plan(nprog); const H=HEIGHT+FOOT_H;
  const lines=[`Panel ${WIDTH} wide, ${HEIGHT} tall on ${FOOT_H} mm feet, ${COLS} columns a face at ${PITCH}: column left edges ${[1,2,3,4,5].map(col_x).join(', ')}`];
  for(const face of ['front','back']){
    lines.push(`\n${face.toUpperCase()} (${cards(face,P).length} cards)`);
    const R=face==='front'?FRONT_RAILS:BACK_RAILS;
    R.forEach((y,i)=>{ const row=P[face][i+1]||{}; lines.push(`  row ${i+1}: rail ${y} from the top, ${H-y} above the table; card tops at ${y-50}: `+[1,2,3,4,5].map(c=>row[c]||'-').join(' ')); });
  }
  lines.push(`  sequencer: left edge ${SEQ_X}, top ${SEQ_Y} from the top (${H-SEQ_Y} above the table), rails at ${rail_y('front',5)} and ${rail_y('front',7)}; bus header centred on column 1; link header at x ${SEQ_X+SEQ.link_x}`);
  for(const r of ribbons(P)) lines.push(`ribbon ${r.name}: ${r.sockets} sockets, ${r.hops} turns, ${r.mm} mm with ${SLACK} slack; route ${r.pts.map(p=>`(${p[0]},${p[1]})`).join(' ')}`);
  const L=links(P); lines.push(`6-way links: `+L.six.map(l=>`${l.from}>${l.to} ${l.mm} (${l.how})`).join('; '));
  for(const t of L.twelve) lines.push(`12-way chain, ${t.what}: ${t.sockets} sockets, about ${t.mm} mm`);
  lines.push('parts:'); for(const [p,q,n] of parts(P)) lines.push(`  ${q} x ${p}: ${n}`);
  return lines.join('\n');
}

const api={CARD,PITCH,COLS,SIDE,TOP,UP,HEIGHT,FOOT,FOOT_H,WIDTH,STANDOFF,SEQ,SEQ_X,SEQ_Y,HDR_Y,LINK_Y,LINK_IN,LINK_OUT,CHAIN_X,RIBBON_W,FRONT_RAILS,BACK_RAILS,KINDS,PROG_MAX,rail_y,card_top,col_x,plan,kind,cards,hdr,ribbons,links,parts,report};
if(typeof module!=='undefined') module.exports=api; else window.PANEL=api;
if(typeof require!=='undefined' && require.main===module) console.log(report(+(process.argv[2]||20)));

"""KiCad 10 schematic writer for Nibble boards. Draws nmos.Design gate lists as cells,
plus the board frame (bus header, decoupling, indicators) and a testbench sub-sheet."""
import uuid as _uuid, re, os
KLIB='/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols'
G=2.54
def U(): return str(_uuid.uuid4())
def f(x):
    s=f"{x:.4f}".rstrip('0').rstrip('.'); return s if s!='-0' else '0'

def libsym(lib,name):
    """Extract a symbol from KiCad's shared libraries as an embedded lib_symbols block."""
    s=open(f'{KLIB}/{lib}.kicad_sym').read()
    i=s.find(f'\t(symbol "{name}"\n'); assert i>=0,(lib,name)
    j=s.find('\n\t(symbol "',i+10)
    if j<0: j=s.rfind('\n)')
    b=s[i:j].replace(f'(symbol "{name}"',f'(symbol "{lib}:{name}"',1)
    return "\n".join("\t"+l for l in b.split("\n"))+"\n"

class Writer:
    def __init__(self,project,root_uuid,sheet_uuid=None):
        self.project=project; self.root_uuid=root_uuid
        self.sheet_uuid=sheet_uuid or root_uuid
        self.path=f"/{root_uuid}" if sheet_uuid is None else f"/{root_uuid}/{sheet_uuid}"
        self.place={}; self.silk=[]; self.pwr=[]; self.rails=[]; self.vias=[]; self.body=''; self.n={'Q':1,'R':1,'D':1,'C':1,'J':1,'H':1,'V':1,'#PWR':1,'#FLG':1,'TP':1,'SW':1,'F':1,'U':1}
        self.router_exclude=[]; self.keepouts=[]     # parts and areas the autorouter does not see (pcb.py): the diode matrix
        self.libs={}
    def ref(self,p):
        r=f"{p}{self.n[p]}"; self.n[p]+=1; return r
    def prop(self,name,val,x,y,rot=0,hide=False,justify=None):
        eff="(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)"+(f"\n\t\t\t\t(justify {justify})" if justify else "")+"\n\t\t\t)"
        return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {f(x)} {f(y)} {rot})\n'+("\t\t\t(hide yes)\n" if hide else "")+
                "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t"+eff+"\n\t\t)\n")
    def symbol(self,lib,name,ref,value,x,y,rot,pins,footprint="",props=(),mirror=None,in_bom=True,on_board=True,sim=True,hide_value=False,dnp=False):
        if int(re.sub(r'\D','',ref) or 0)>=9000: in_bom=on_board=False     # testbench parts (refs 9000 and up) never reach the board or the BOM
        if dnp: in_bom=sim=False                                          # do not populate: pads on the board, nothing in the BOM or the simulation
        self.libs.setdefault(f"{lib}:{name}",libsym(lib,name))
        s=f'\t(symbol\n\t\t(lib_id "{lib}:{name}")\n\t\t(at {f(x)} {f(y)} {rot})\n'
        if mirror: s+=f'\t\t(mirror {mirror})\n'
        s+=f'\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim {"no" if sim else "yes"})\n\t\t(in_bom {"yes" if in_bom else "no"})\n\t\t(on_board {"yes" if on_board else "no"})\n\t\t(in_pos_files yes)\n\t\t(dnp {"yes" if dnp else "no"})\n\t\t(fields_autoplaced yes)\n\t\t(uuid "{U()}")\n'
        s+=self.prop("Reference",ref,x+2.54,y-1.27,0,hide=ref.startswith('#'),justify="left")
        s+=self.prop("Value",value,x+2.54,y+1.27,0,hide=hide_value,justify="left")
        s+=self.prop("Footprint",footprint,x,y,0,hide=True)
        s+=self.prop("Datasheet","",x,y,0,hide=True)
        for nm,val,hide in props: s+=self.prop(nm,val,x,y,0,hide=hide)
        for p in pins: s+=f'\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
        s+=f'\t\t(instances\n\t\t\t(project "{self.project}"\n\t\t\t\t(path "{self.path}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n'
        self.body+=s; return ref
    # ---- parts ----
    R_FOOT="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical"
    Q_FOOT="Package_TO_SOT_THT:TO-92_Inline_Wide"
    LED_FOOT="LED_THT:LED_D3.0mm"
    C_FOOT="Capacitor_THT:C_Disc_D5.0mm_W2.5mm_P2.50mm"
    CP_FOOT="Capacitor_THT:CP_Radial_D5.0mm_P2.00mm"
    J_FOOT="Connector_IDC:IDC-Header_2x32_P2.54mm_Vertical"
    H_FOOT="MountingHole:MountingHole_3.2mm_M3_Pad"
    LIB_PREFIX="${KIPRJMOD}/../../lib"      # boards/<name>/ -> repo lib/; builders one level up set "${KIPRJMOD}/../lib"
    @property
    def MODEL_LIB(self): return self.LIB_PREFIX+"/2N7000.lib"
    @property
    def LED_LIB(self): return self.LIB_PREFIX+"/led.lib"
    def R(self,value,x,y,rot=0,**kw):
        """pins: 1 at top (y-3.81), 2 at bottom (y+3.81) for rot 0"""
        return self.symbol("Device","R",self.ref('R'),value,x,y,rot,('1','2'),self.R_FOOT,[("Description","Resistor",True)],**kw)
    def Q(self,x,y):
        """2N7000: D at (x+2.54,y-5.08), G at (x-5.08,y), S at (x+2.54,y+5.08)"""
        props=[("Description","N-Channel MOSFET, TO-92",True),("Sim.Device","NMOS",True),("Sim.Type","VDMOS",True),
               ("Sim.Pins","1=S 2=G 3=D",True),("Sim.Library",self.MODEL_LIB,True),("Sim.Name","2N7000",True)]
        return self.symbol("Transistor_FET","2N7000",self.ref('Q'),"2N7000",x,y,0,('1','2','3'),self.Q_FOOT,props)
    def LED(self,x,y):
        """rot 90: A at top (y-3.81), K at bottom (y+3.81)"""
        props=[("Description","Light emitting diode",True),("Sim.Device","D",True),("Sim.Pins","1=K 2=A",True),
               ("Sim.Library",self.LED_LIB,True),("Sim.Name","LEDRED",True)]
        return self.symbol("Device","LED",self.ref('D'),"LED",x,y,90,('1','2'),self.LED_FOOT,props)
    def C(self,value,x,y,polar=False):
        return self.symbol("Device","C_Polarized" if polar else "C",self.ref('C'),value,x,y,0,('1','2'),self.CP_FOOT if polar else self.C_FOOT,[("Description","Capacitor",True)])
    def PW(self,name,x,y):
        lib="power:GND" if name=="GND" else "power:+5V"
        return self.symbol("power","GND" if name=="GND" else "+5V",self.ref('#PWR'),name,x,y,0,('1',),"",[("Description",f'Power symbol creates a global label with name \\"{name}\\"',True)])
    def pwr_flag(self,x,y):
        return self.symbol("power","PWR_FLAG",self.ref('#FLG'),"PWR_FLAG",x,y,0,('1',),"",[("Description","Special symbol for telling ERC where power comes from",True)])
    def header(self,x,y):
        """2x32 header; odd pins at x-5.08, even at x+7.62; pin1 at y-38.1, step 2.54 down."""
        return self.symbol("Connector_Generic","Conn_02x32_Odd_Even",self.ref('J'),"BUS",x,y,0,tuple(str(i) for i in range(1,65)),self.J_FOOT,[("Description","Nibble bus header",True)],sim=False)
    TP_FOOT="TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm"
    def testpoint(self,name,x,y):
        """pin 1 at (x, y+2.54)?? -> Connector:TestPoint pin is at (0,-2.54) symbol coords = (x, y+2.54)?? see libsym"""
        return self.symbol("Connector","TestPoint",self.ref('TP'),name,x,y,0,('1',),self.TP_FOOT,[("Description","test point",True)],in_bom=True,sim=False)
    def pinheader(self,n,x,y,value):
        return self.symbol("Connector_Generic",f"Conn_01x{n:02d}",self.ref('J'),value,x,y,0,tuple(str(i) for i in range(1,n+1)),f"Connector_PinHeader_2.54mm:PinHeader_1x{n:02d}_P2.54mm_Vertical",[("Description","pin header",True)],sim=False)
    def dipswitch(self,n,x,y,value):
        """SW_DIP_x08 etc: pins 1..n on the left at x-7.62?, n+1..2n on the right"""
        return self.symbol("Switch",f"SW_DIP_x{n:02d}",self.ref('SW'),value,x,y,0,tuple(str(i) for i in range(1,2*n+1)),f"Button_Switch_THT:SW_DIP_SPSTx{n:02d}_Slide_9.78x{ {1:'4.72',2:'7.26',4:'12.34',8:'22.5'}[n]}mm_W7.62mm_P2.54mm",[("Description","DIP switch",True)],sim=False)
    def button(self,x,y,value):
        return self.symbol("Switch","SW_Push",self.ref('SW'),value,x,y,0,('1','2'),"Button_Switch_THT:SW_PUSH_6mm",[("Description","push button",True)],sim=False)
    D_FOOT="Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal"
    D_FOOT_V="Diode_THT:D_DO-35_SOD27_P2.54mm_Vertical_AnodeUp"    # standing on its cathode pad, anode lead down to a pad 2.54 away
    def diode(self,x,y,rot=0,dnp=False,foot=None):
        """1N4148: pin 1 K, pin 2 A. dnp: the pads are on the board, the part is not (an empty matrix crossing)"""
        return self.symbol("Device","D",self.ref('D'),"1N4148",x,y,rot,('1','2'),foot or self.D_FOOT,[("Description","small signal diode",True),("Sim.Device","D",True),("Sim.Pins","1=K 2=A",True),("Sim.Library",self.LED_LIB,True),("Sim.Name","D1N4148",True)],dnp=dnp)
    def hole(self,x,y):
        return self.symbol("Mechanical","MountingHole",self.ref('H'),"M3",x,y,0,(),self.H_FOOT,[],in_bom=False,sim=False)
    def vsource(self,kind,params,x,y):
        lib={"PULSE":"VPULSE","PWL":"VPWL","DC":"VDC"}[kind]
        props=[("Description","Voltage source",True),("Sim.Pins","1=+ 2=-",True),("Sim.Type",kind,True),("Sim.Device","V",True)]
        if kind!="DC": props.append(("Sim.Params",params,False))
        return self.symbol("Simulation_SPICE",lib,self.ref('V'),lib if kind!="DC" else params,x,y,0,('1','2'),"",props,in_bom=False,on_board=False)
    # ---- graphics ----
    def W(self,x1,y1,x2,y2):
        self.body+=f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n'
    def J(self,x,y):
        self.body+=f'\t(junction\n\t\t(at {f(x)} {f(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)\n'
    def L(self,name,x,y,rot=0,shape="input"):
        just="left" if rot==0 else "right"
        self.body+=(f'\t(global_label "{name}"\n\t\t(shape {shape})\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(fields_autoplaced yes)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {f(x)} {f(y)} 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify {just})\n\t\t\t)\n\t\t)\n\t)\n')
    def T(self,s,x,y,size=1.27,bold=False):
        s=s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
        b="\n\t\t\t\t(bold yes)" if bold else ""
        self.body+=f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {f(size)} {f(size)}){b}\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n'
    def sheet(self,name,file,x,y,w,h,page,sheet_uuid):
        self.body+=(f'\t(sheet\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(w)} {f(h)})\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
            f'\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n\t\t(uuid "{sheet_uuid}")\n'
            f'\t\t(property "Sheetname" "{name}"\n\t\t\t(at {f(x)} {f(y-0.7116)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
            f'\t\t(property "Sheetfile" "{file}"\n\t\t\t(at {f(x)} {f(y+h+0.5846)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "{self.project}"\n\t\t\t\t(path "/{self.root_uuid}"\n\t\t\t\t\t(page "{page}")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    def at(self,ref,x,y,rot=0):
        """PCB placement (mm) for a part."""
        self.place[ref]=(x,y,rot); return ref
    def label(self,text,x,y,size=1.0):
        self.silk.append((text,x,y,size))
    # ---- cells ----
    CELL_W=15*G   # 38.1 schematic
    PCB_COL=10.16 # PCB tile pitch
    HCOL=None     # usable tile column height on the board (None: unlimited)
    def tile_h(self,g):
        n=len(g['ins']); k=g['kind']
        if k=='LED': return 25.4
        if k=='BUS': return 10.16
        if k=='PD': return 10.16
        if k=='PULL': return 5.08*n+5.08
        return 10.16+5.08*n+5.08
    def pu_rot(self,pcb): return 0     # schematic rotation of a cell's pull-up (pin 1 at the top when 0)
    def gate(self,g,x0,y0,pcb=None):
        """Draw one NAND/NOR/INV/BUS/LED cell at (x0,y0) and, with pcb=(x,y,column), place its tile. Returns height used."""
        ins=g['ins']; n=len(ins); kind=g['kind']
        xq=x0+8*G; xc=xq+G; xbus=xq+3*G; xout=x0+14*G; xin=x0+2*G
        yr=y0+3*G          # pull-up resistor centre
        yc0=yr+3*G         # output node
        r=d=None; qs=[]
        if kind=='LED':
            self.PW('+5V',xc,yr-1.5*G)
            r=self.R(g['pu'],xc,yr,self.pu_rot(pcb))   # pins yr-1.5G / yr+1.5G
            d=self.LED(xc,yr+3.5*G)              # A at yr+2G, K at yr+5G
            self.W(xc,yr+1.5*G,xc,yr+2*G)
            yq=yr+7*G                          # D at yq-2G = yr+5G
            qs.append(self.Q(xq,yq)); self.PW('GND',xc,yq+2*G)
            self.W(xq-2*G,yq,xin,yq); self.L(ins[0],xin,yq,180,'input')
            self.T(g['out'],xc+1.5*G,yr+3.5*G,1.0)
            if pcb: self.place_tile(g,pcb,r,d,qs)
            return 10*G
        if kind=='BUS':
            yq=y0+4*G
            qs.append(self.Q(xq,yq)); self.PW('GND',xc,yq+2*G)
            self.W(xc,yq-2*G,xc,yq-3*G); self.W(xc,yq-3*G,xout,yq-3*G); self.L(g['out'],xout,yq-3*G,0,'bidirectional')
            self.W(xq-2*G,yq,xin,yq); self.L(ins[0],xin,yq,180,'input')
            if pcb: self.place_tile(g,pcb,r,d,qs)
            return 8*G
        if kind=='PD':                         # pull-down resistor from a line to ground (a panel line reads 0 when nothing drives it)
            self.L(g['out'],xc,yr-2*G,90,'input'); self.W(xc,yr-2*G,xc,yr-1.5*G)
            r=self.R(g['pu'],xc,yr,180 if (pcb and pcb[2]%2==0) else 0)      # pin 1 at the ground end in an even column: on the board the body pad meets the GND rail there
            self.W(xc,yr+1.5*G,xc,yr+2*G); self.PW('GND',xc,yr+2*G)
            if pcb: self.place_tile(g,pcb,r,None,[])
            return 6*G
        if kind=='PULL':                       # extra pull-down stack on a node that has its pull-up elsewhere: no resistor
            self.W(xc,yc0,xout,yc0); self.L(g['out'],xout,yc0,0,'bidirectional')
        else:
            self.PW('+5V',xc,yr-1.5*G)
            r=self.R(g['pu'],xc,yr,self.pu_rot(pcb))
            self.W(xc,yr+1.5*G,xc,yc0); self.W(xc,yc0,xout,yc0); self.L(g['out'],xout,yc0,0,'output')
        if n>1: self.J(xc,yc0)
        for k,inp in enumerate(ins):
            yq=yc0+2*G+6*G*k                   # D at yq-2G, S at yq+2G
            qs.append(self.Q(xq,yq))
            self.W(xq-2*G,yq,xin,yq); self.L(inp,xin,yq,180,'input')
            if kind in ('NAND','PULL'):
                if k<n-1: self.W(xc,yq+2*G,xc,yq+4*G)
                else: self.PW('GND',xc,yq+2*G)
            else:
                self.PW('GND',xc,yq+2*G)
                if k>0:
                    self.W(xc,yq-2*G,xbus,yq-2*G)
                    ytop=yc0 if k==1 else yq-2*G-6*G
                    self.W(xbus,ytop,xbus,yq-2*G); self.J(xbus,ytop)
        if pcb: self.place_tile(g,pcb,r,d,qs)
        return 6*G*n+8*G
    def place_tile(self,g,pcb,r,d,qs):
        """Classic tile (the nine boards): pull-up standing at the top of a 10.16 mm column, transistors below it at 5.08,
        GND rail on B.Cu at x-1.27 and +5V at x+6.35 of every column, stubs recorded in self.pwr."""
        px,py=pcb[0],pcb[1]; kind=g['kind']; n=len(qs)
        if kind=='LED':
            self.at(r,px+2.54,py,270); self.at(d,px+1.27,py+10.16,0); self.at(qs[0],px,py+15.24,0); self.label(g['out'].replace('LED_',''),px+3.8,py+12.9,1.0)
            self.pwr.append(('+5V',px+2.54,py)); self.pwr.append(('GND',px,py+15.24)); return
        if kind=='BUS': self.at(qs[0],px,py+2.54,0); self.pwr.append(('GND',px,py+2.54)); return
        if kind=='PD': self.at(r,px+2.54,py,270); self.pwr.append(('GND',px+2.54,py+5.08)); return
        if kind=='PULL': qy0=py+2.54
        else: self.at(r,px+2.54,py,270); self.pwr.append(('+5V',px+2.54,py)); qy0=py+10.16
        for k,q in enumerate(qs):
            self.at(q,px,qy0+5.08*k,0)
            if kind=='NOR' or k==n-1: self.pwr.append(('GND',px,qy0+5.08*k))
    def pack(self,gates,fields,mode,pre=None):
        """PCB tile positions over the tile fields [(x, y, columns, height or None)], filled in order.
        'skyline': each gate goes to the lowest column of the first field with room (ties left to right). 'column': fill a
        column top to bottom in gate order, next column (next field) when a tile no longer fits. Returns [(g,(x,y,col))], [column heights per field].
        pre: [(g, field, column)] placed first, stacked in the given column (the sequencer puts the matrix's drivers under
        their columns and the row buffers beside the row tails, D051); the rest packs around them."""
        colh=[[f[1]]*f[2] for f in fields]; tiles=[]; fi=0; j=0
        def fits(fi,j,h): return fields[fi][3] is None or colh[fi][j]+h<=fields[fi][1]+fields[fi][3]
        def col(fi,j): return j+(fields[fi][4] if len(fields[fi])>4 else 0)      # a field's optional fifth element: the global column index of its first column, so the
        # rail parity (GND/+5V alternate at the column boundaries) continues across a seam where two fields share a boundary (the sequencer's split left field)
        done=set()
        for g,pf,pj in pre or []:
            h=self.tile_h(g)
            if not fits(pf,pj,h): raise SystemExit(f"pre-placed tile {g['out']} does not fit in field {pf} column {pj}")
            tiles.append((g,(fields[pf][0]+pj*self.PCB_COL,colh[pf][pj],col(pf,pj)))); colh[pf][pj]+=h; done.add(id(g))
        for g in gates:
            if id(g) in done: continue
            h=self.tile_h(g)
            if mode=='skyline':
                for fi in range(len(fields)):
                    ok=[c for c in range(fields[fi][2]) if fits(fi,c,h)]
                    if ok: j=min(ok,key=lambda c:(round(colh[fi][c],3),c)); break
                else: raise SystemExit(f"tile {g['out']} does not fit: every column of every field is full")
            else:
                while fi<len(fields) and not fits(fi,j,h):
                    j+=1
                    if j>=fields[fi][2]: fi+=1; j=0
                if fi>=len(fields):      # every column passed: the tile goes to the lowest column with room anywhere (the remainders under the pre-placed tiles)
                    ok=[(f,c) for f in range(len(fields)) for c in range(fields[f][2]) if fits(f,c,h)]
                    if not ok: raise SystemExit(f"tile {g['out']} does not fit: every column of every field is full")
                    fi,j=min(ok,key=lambda fc:(round(colh[fc[0]][fc[1]],3),fc)); tiles.append((g,(fields[fi][0]+j*self.PCB_COL,colh[fi][j],col(fi,j)))); colh[fi][j]+=h; fi=len(fields); continue
            tiles.append((g,(fields[fi][0]+j*self.PCB_COL,colh[fi][j],col(fi,j)))); colh[fi][j]+=h
        return tiles,colh
    def layout(self,gates,titles,x0,y0,cols,pcb_origin=(10.0,10.0),pcb_cols=None,pack='skyline',fields=None,pack_order=None,pre=None):
        """Draw all gates group by group (schematic) and assign PCB tiles: one field of pcb_cols columns at pcb_origin, or the
        given fields [(x, y, columns, height or None)] filled in order. pack_order: the gates in the order they are packed (default: as drawn)."""
        y=y0; groups=[]
        fields=fields or [(pcb_origin[0],pcb_origin[1],pcb_cols or cols,self.HCOL)]
        for g in gates:
            if not groups or groups[-1][0]!=g['group']: groups.append((g['group'],[]))
            groups[-1][1].append(g)
        tiles,colh=self.pack(pack_order or gates,fields,pack,pre); self.tiles=tiles     # kept: a board can draw spines over its tile positions
        pos={id(g):t for g,t in tiles}
        for name,gs in groups:
            self.T(titles.get(name,name),x0,y-G,2.0,True); y+=2*G
            for i in range(0,len(gs),cols):
                rw=gs[i:i+cols]; h=0
                for j,g in enumerate(rw): h=max(h,self.gate(g,x0+j*self.CELL_W,y,pcb=pos[id(g)]))
                y+=h+2*G
            y+=2*G
        self.pcb_extent=(max(f[0]+f[2]*self.PCB_COL for f in fields),max(max(c) for c in colh))
        self.trunks=[]
        for f,ch in zip(fields,colh): self.rails_for(f[0],f[1],f[2],ch,f[4] if len(f)>4 else 0)
        return y
    def rails_for(self,pxo,pyo,pcb_cols,colh,phase=0):
        """Power rails: per column, GND on B.Cu at x-1.27 and +5V on B.Cu at x+6.35, from the trunks above the tiles to the column bottom."""
        yg=pyo-6.0; yv=pyo-3.0; xs=[pxo+j*self.PCB_COL for j in range(pcb_cols)]
        for j,x in enumerate(xs):
            if colh[j]==pyo: continue
            yg_end=max([y for n,px_,y in self.pwr if n=='GND' and abs(px_-x)<0.01 and pyo<=y<=colh[j]],default=None)          # this field's stubs only: another field may share the column x (the sequencer's spine band splits a field)
            yv_end=max([y for n,px_,y in self.pwr if n=='+5V' and abs(px_-(x+2.54))<0.01 and pyo<=y<=colh[j]],default=None)
            if yg_end: self.rails.append(('GND','B.Cu',x-1.27,yg,x-1.27,yg_end,0.5)); self.vias.append(('GND',x-1.27,yg))
            if yv_end: self.rails.append(('+5V','B.Cu',x+6.35,yv,x+6.35,yv_end,0.5)); self.vias.append(('+5V',x+6.35,yv))
        used=[x for j,x in enumerate(xs) if colh[j]>pyo]
        self.trunks.append(((used[0]-1.27,used[-1]-1.27,yg),(used[0]+6.35,used[-1]+6.35,yv)))
        self.rails.append(('GND','F.Cu',used[0]-1.27,yg,used[-1]-1.27,yg,0.8))
        self.rails.append(('+5V','F.Cu',used[0]+6.35,yv,used[-1]+6.35,yv,0.8))
        for net,sx,sy in self.pwr:
            if net=='GND': self.rails.append(('GND','B.Cu',sx,sy,sx-1.27,sy,0.5))
            else: self.rails.append(('+5V','B.Cu',sx,sy,sx+3.81,sy,0.5))
    def file(self,paper_w,paper_h,extra_libs=()):
        libs="".join(self.libs.values())+"".join(extra_libs)
        return (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{self.sheet_uuid}")\n\t(paper "User" {f(paper_w)} {f(paper_h)})\n'
                "\t(lib_symbols\n"+libs+"\t)\n"+self.body+
                ('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n' if self.sheet_uuid==self.root_uuid else '')+'\t(embedded_fonts no)\n)\n')

class DenseWriter(Writer):
    """The card tile (D045, docs/cards.md): about 70 mm2 per transistor against 200 to 300 on the nine boards.
    Columns at P = 7.68 mm holding one TO-92 per 5.08 mm row (pads S G D at 2.54, or D G S in the odd columns, which
    are mirrored). The pull-up lies along the row above its stack, one pad on the source column and one on the drain
    column (P is 7.68 and not 7.62 because the vertical 0207 footprint's courtyard is 7.63 long). Power runs on B.Cu
    between the columns, alternately a GND and a +5V rail, each shared by the two columns beside it: sources face the
    GND rail, pull-ups reach the +5V rail with a 1.27 mm stub. Tile heights: 3.175 + 5.08 n for a gate of n
    transistors (the R row plus courtyard gaps), 5.08 n for a bare stack (BUS, PULL), 15.24 for an LED.
    The trunks above the tiles are on F.Cu: GND at y0 - 3.5, +5V at y0 - 2.0, one via per rail."""
    PCB_COL=7.68
    RAIL=0.5
    def __init__(self,*a,**k):
        super().__init__(*a,**k); self.rail_end={}     # rail x -> lowest y a stub reaches
    def tile_h(self,g):
        n=len(g['ins']); k=g['kind']
        if k=='LED': return 15.24
        if k=='PD': return 5.08
        if k in ('BUS','PULL'): return 5.08*n
        return 3.175+5.08*n
    def pu_rot(self,pcb):
        # all pull-ups lie rot 0 on the board, body on the left pad: in an even column the left pad is the source
        # column (the output), in an odd (mirrored) column it is the drain column (+5V). Pad 1 is the body pad.
        return 180 if (pcb and pcb[2]%2==0) else 0
    def R(self,value,x,y,rot=0,**kw):
        """Resistor symbol; rot 180 puts pin 1 at the bottom (the pins land on the same wire ends either way)."""
        return self.symbol("Device","R",self.ref('R'),value,x,y,rot,('1','2'),self.R_FOOT,[("Description","Resistor",True)],**kw)
    def place_tile(self,g,pcb,r,d,qs):
        px,py,j=pcb; m=j%2; P=self.PCB_COL; kind=g['kind']; n=len(qs)
        xs,xg,xd=(px,px+2.54,px+5.08) if m==0 else (px+5.08,px+2.54,px)
        xgnd,x5v=(px-1.27,px+P-1.27) if m==0 else (px+P-1.27,px-1.27)
        def use(x,y): self.rail_end[round(x,3)]=max(self.rail_end.get(round(x,3),0),y)
        def Q(q,y): self.at(q,xs,y,0 if m==0 else 180)
        def gnd(y): self.rails.append(('GND','B.Cu',xs,y,xgnd,y,self.RAIL)); use(xgnd,y)
        if kind=='PD':      # the pull-down resistor lying along its row, the ground pad on the rail side, the other pad the line
            self.at(r,px,py+2.54,0); xg_=px if m==0 else px+5.08
            self.rails.append(('GND','B.Cu',xg_,py+2.54,xgnd,py+2.54,self.RAIL)); use(xgnd,py+2.54); return
        if kind in ('BUS','PULL'):
            y0=py+(1.27 if m==0 else 0.635)
            for k,q in enumerate(qs): Q(q,y0+5.08*k)
            gnd(y0+5.08*(n-1)); return
        self.at(r,px,py,0); self.rails.append(('+5V','B.Cu',xd,py,x5v,py,self.RAIL)); use(x5v,py)   # body on the left pad; +5V pad on the drain column
        if kind=='LED':
            self.at(d,xg,py+6.35,90); Q(qs[0],py+10.795); gnd(py+10.795)
            self.label(g['out'].replace('LED_',''),xg+2.4,py+5.7,0.8); return
        y0=py+(4.445 if m==0 else 3.81)
        for k,q in enumerate(qs):
            Q(q,y0+5.08*k)
            if kind=='NOR' or k==n-1: gnd(y0+5.08*k)
    def rails_for(self,pxo,pyo,pcb_cols,colh,phase=0):
        """phase: the global column index of the field's first column (the parity of a boundary's net must agree with the field next door)."""
        yg=pyo-3.5; yv=pyo-2.0; P=self.PCB_COL
        xr=[pxo-1.27+P*k for k in range(pcb_cols+1)]
        for k,x in enumerate(xr):
            end=self.rail_end.get(round(x,3))
            if not end: continue
            net,yt=('GND',yg) if (k+phase)%2==0 else ('+5V',yv)
            self.rails.append((net,'B.Cu',x,yt,x,end,self.RAIL)); self.vias.append((net,x,yt))
        ug=[x for k,x in enumerate(xr) if (k+phase)%2==0 and self.rail_end.get(round(x,3))]
        uv=[x for k,x in enumerate(xr) if (k+phase)%2==1 and self.rail_end.get(round(x,3))]
        self.trunks.append(((min(ug),max(ug),yg),(min(uv),max(uv),yv)))
        self.rails.append(('GND','F.Cu',min(ug),yg,max(ug),yg,0.8))
        self.rails.append(('+5V','F.Cu',min(uv),yv,max(uv),yv,0.8))

def project_file(name):
    return '{\n  "board": {"design_settings": {"defaults": {}, "rules": {}}},\n  "meta": {"filename": "%s.kicad_pro", "version": 3},\n  "schematic": {"drawing": {}, "legacy_lib_dir": "", "legacy_lib_list": []},\n  "sheets": [],\n  "text_variables": {}\n}\n' % name

def write_plan(w,path,outline,extra=None):
    """PCB placement plan consumed by pcb.py (run with KiCad's python)."""
    import json
    extra=dict(extra or {})
    if w.router_exclude or w.keepouts: extra['router']=dict(extra.get('router',{}),exclude_refs=w.router_exclude,keepout=w.keepouts)
    json.dump(dict(place=w.place,silk=w.silk,rails=w.rails,vias=w.vias,outline=list(outline),extra=extra),open(path,'w'),indent=0)

def matrix(w,rows,cols,diodes,x0,y0,pcb,pd='1Meg',caption=lambda c:c,note=None,vertical=False,tails='right'):
    """Diode control matrix. rows: [(net, caption)], cols: [net], diodes: [(row_net, col_net)] fitted; every other
    crossing gets a DNP diode (pads on the board, nothing fitted) so an instruction can be added by soldering (D040).
    Schematic: columns are vertical wires (label at the top, pull-down at the bottom), rows horizontal wires
    (label at the left); a diode at a crossing has its anode on the row and its cathode on the column.
    PCB (origin pcb=(x,y)), transposed to keep the board short: rows are vertical B.Cu tracks at 2.54 mm pitch
    (left to right), columns horizontal F.Cu tracks at 10.16 mm pitch (top to bottom). The diode stands along its
    row, centred between row tracks: cathode pad on the column track, anode pad 7.62 below with a short stub to the
    row track. The pull-downs stand at the right end of the columns with a GND rail 2.5 mm beside them.
    vertical (D045): the diodes stand up (DO-35 on a 2.54 mm pad pair), columns at 5.08 mm, the anode pad 2.54 below the
    crossing; the pull-downs lie along the columns at the right end with the GND rail through their far pads.
    Returns (schematic height used, pcb extent (x, y))."""
    CW,RH=5*G,4*G; xl=x0+8*G; yt=y0+6*G
    CP,RP=(5.08 if vertical else 10.16),2.54; AP=2.54 if vertical else 7.62; px0,py0=pcb; pxl=px0+8; pyt=py0+12
    colx={c:xl+k*CW for k,c in enumerate(cols)}; rowy={r:yt+k*RH for k,(r,cap) in enumerate(rows)}
    pcy={c:pyt+k*CP for k,c in enumerate(cols)}; prx={r:pxl+k*RP for k,(r,cap) in enumerate(rows)}
    ybot=yt+len(rows)*RH; xr=xl+len(cols)*CW; pxr=pxl+len(rows)*RP+(3.0 if vertical else 2)       # pxr: where the pull-downs stand
    for c in cols:
        x=colx[c]; w.W(x,yt-2*G,x,ybot+G); w.L(c,x,yt-2*G,90,'output')
        r=w.R(pd,x,ybot+2.5*G); w.W(x,ybot+4*G,x,ybot+5*G); w.PW('GND',x,ybot+5*G)
        if vertical:
            w.at(r,pxr,pcy[c],0); w.rails.append(('GND','B.Cu',pxr+5.08,pcy[c],pxr+5.08+2.5,pcy[c],0.5))  # rot 0: pad 1 on the column track, pad 2 (GND) 5.08 to the right, stub to the rail
        else:
            w.at(r,pxr,pcy[c],270); w.pwr.append(('GND',pxr,pcy[c]+5.08))     # rot 270: pad 1 at (x,y) on the column track, pad 2 (GND) at (x,y+5.08)
            w.rails.append(('GND','B.Cu',pxr,pcy[c]+5.08,pxr+2.5,pcy[c]+5.08,0.5))   # stub to the GND rail beside the pull-downs (a rail through them would cross their signal pads)
        if vertical and tails=='left':      # D051: the tail sticks out of the keepout's left edge, toward the buffers beside the matrix; the pull-down at the right end sits on the hidden track, so the router does not see it either
            # the tail: a fixed via 4.5 mm before the keepout and a 3.5 mm In2 stub from it, so the router reaches the column on its vertical
            # layer straight from the buffer's drain pad (an F.Cu tail beside the keepout was boxed in by the corridor's vertical tracks: 23 of 23 open)
            # the 1.5 mm of F.Cu tail between the via and the keepout's edge stays visible to the router (hidden, v8 routed PCL_m across PCR_m's tail there)
            w.rails.append((c,'F.Cu',pxl-4.5,pcy[c],pxl-3.0,pcy[c],0.5)); w.rails.append((c,'F.Cu',pxl-3.0,pcy[c],pxr,pcy[c],0.5,True)); w.vias.append((c,pxl-4.5,pcy[c])); w.rails.append((c,'In2.Cu',pxl-4.5,pcy[c],pxl-8.0,pcy[c],0.5)); w.router_exclude.append(r)
        elif vertical:    # the column track inside the matrix is hidden from the router; its tail past the keepout's edge to the pull-down is not, so the router neither crosses it nor misses it
            xk=prx[rows[-1][0]]+2.6
            w.rails.append((c,'F.Cu',pxl-2,pcy[c],xk,pcy[c],0.5,True)); w.rails.append((c,'F.Cu',xk,pcy[c],pxr,pcy[c],0.5))
        else: w.rails.append((c,'F.Cu',pxl-4,pcy[c],pxr,pcy[c],0.5))
        w.label(caption(c),px0,pcy[c]-0.9,0.9)
    if vertical:
        xg=pxr+5.08+2.5; w.rails.append(('GND','B.Cu',xg,pcy[cols[0]],xg,pcy[cols[-1]],0.5))      # joined by the pour
    else:
        w.rails.append(('GND','B.Cu',pxr+2.5,pcy[cols[0]]+5.08,pxr+2.5,pcy[cols[-1]]+5.08,0.5)); w.vias.append(('GND',pxr+2.5,pcy[cols[-1]]+5.08))
    ybot_in=pcy[cols[-1]]+AP+1.0                   # the matrix's copper ends here; vertical: a 2.2 mm tail per row sticks out for the router
    for k,(r,cap) in enumerate(rows):
        y=rowy[r]; w.W(xl-4*G,y,xr,y); w.L(r,xl-4*G,y,180,'input'); w.L(r,xr,y,0,'input'); w.T(cap,xl-4*G,y-0.6*G,1.0)   # a label at both ends: no dangling wire
        if vertical:
            w.rails.append((r,'B.Cu',prx[r],pyt-1.0,prx[r],ybot_in,0.4,True)); w.rails.append((r,'B.Cu',prx[r],ybot_in,prx[r],ybot_in+2.2,0.4))
        else: w.rails.append((r,'B.Cu',prx[r],pyt-4,prx[r],ybot_in,0.4))
    for k,(r,cap) in enumerate(rows):      # row captions along the top, three heights so they stay legible at 2.54 pitch
        w.label(cap.replace(' (free)',''),prx[r]-0.9,pyt-5.0-(k%3)*3.0,0.8)     # (1.5 mm lower than before: the top row touched the sequencer's link header outline)
    fitted=set(diodes)
    for rn,cap in rows:                    # a diode symbol at every crossing (D040): fitted where the design has one, DNP (pads only) elsewhere
        for cn in cols:
            x,y=colx[cn],rowy[rn]; dnp=(rn,cn) not in fitted
            d=w.diode(x+2*G,y+1.5*G,90,dnp=dnp,foot=w.D_FOOT_V if vertical else None); w.J(x+2*G,y); w.W(x+2*G,y+3*G,x,y+3*G); w.J(x,y+3*G)   # A on the row wire, K to the column wire
            w.at(d,prx[rn]+1.27,pcy[cn],270); w.rails.append((rn,"B.Cu",prx[rn]+1.27,pcy[cn]+AP,prx[rn],pcy[cn]+AP,0.4)+((True,) if vertical else ()))   # rot 270: K at (x,y) on the column track, A at (x,y+AP) with a stub to the row track
            if vertical: w.router_exclude.append(d)
    if vertical:   # the router never enters the matrix: its diodes and tracks are hidden from it (pcb.py), a keepout fences the area
        w.keepouts.append((pxl-3.0,pyt-1.5,prx[rows[-1][0]]+2.6,ybot_in+0.2))
    w.T(note or "Rows are driven by the NOR gates on the left (10k pull-ups); a diode pulls its column high while the row is high; columns have 1 Meg pull-downs and a buffer to the bus header.\n"
        "Every crossing has a pad pair on the board; a crossed-out diode is not fitted.  Add an instruction: solder diodes on a free row.",x0,y0+2*G,1.4)
    return ybot+8*G-y0, ((pxr+5.08+2.5+3 if vertical else pxr+8), pcy[cols[-1]]+(AP+6 if vertical else 12))

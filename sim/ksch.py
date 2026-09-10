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
        self.libs={}
    def ref(self,p):
        r=f"{p}{self.n[p]}"; self.n[p]+=1; return r
    def prop(self,name,val,x,y,rot=0,hide=False,justify=None):
        eff="(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)"+(f"\n\t\t\t\t(justify {justify})" if justify else "")+"\n\t\t\t)"
        return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {f(x)} {f(y)} {rot})\n'+("\t\t\t(hide yes)\n" if hide else "")+
                "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t"+eff+"\n\t\t)\n")
    def symbol(self,lib,name,ref,value,x,y,rot,pins,footprint="",props=(),mirror=None,in_bom=True,on_board=True,sim=True,hide_value=False):
        self.libs.setdefault(f"{lib}:{name}",libsym(lib,name))
        s=f'\t(symbol\n\t\t(lib_id "{lib}:{name}")\n\t\t(at {f(x)} {f(y)} {rot})\n'
        if mirror: s+=f'\t\t(mirror {mirror})\n'
        s+=f'\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim {"no" if sim else "yes"})\n\t\t(in_bom {"yes" if in_bom else "no"})\n\t\t(on_board {"yes" if on_board else "no"})\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(uuid "{U()}")\n'
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
        return self.symbol("Switch",f"SW_DIP_x{n:02d}",self.ref('SW'),value,x,y,0,tuple(str(i) for i in range(1,2*n+1)),f"Button_Switch_THT:SW_DIP_SPSTx{n:02d}_Slide_9.78x{'22.5' if n==8 else '12.34'}mm_W7.62mm_P2.54mm",[("Description","DIP switch",True)],sim=False)
    def button(self,x,y,value):
        return self.symbol("Switch","SW_Push",self.ref('SW'),value,x,y,0,('1','2'),"Button_Switch_THT:SW_PUSH_6mm",[("Description","push button",True)],sim=False)
    def diode(self,x,y,rot=0):
        """1N4148: pin 1 K, pin 2 A"""
        return self.symbol("Device","D",self.ref('D'),"1N4148",x,y,rot,('1','2'),"Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",[("Description","small signal diode",True),("Sim.Device","D",True),("Sim.Pins","1=K 2=A",True),("Sim.Library",self.LED_LIB,True),("Sim.Name","D1N4148",True)])
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
    @staticmethod
    def tile_h(g):
        n=len(g['ins']); k=g['kind']
        if k=='LED': return 25.4
        if k=='BUS': return 10.16
        return 10.16+5.08*n+5.08
    def gate(self,g,x0,y0,pcb=None):
        """Draw one NAND/NOR/INV/BUS/LED cell at (x0,y0). Returns height used."""
        ins=g['ins']; n=len(ins); kind=g['kind']
        xq=x0+8*G; xc=xq+G; xbus=xq+3*G; xout=x0+14*G; xin=x0+2*G
        yr=y0+3*G          # pull-up resistor centre
        yc0=yr+3*G         # output node
        px,py=pcb if pcb else (None,None)
        if kind=='LED':
            self.PW('+5V',xc,yr-1.5*G)
            r=self.R(g['pu'],xc,yr)              # pins yr-1.5G / yr+1.5G
            d=self.LED(xc,yr+3.5*G)              # A at yr+2G, K at yr+5G
            self.W(xc,yr+1.5*G,xc,yr+2*G)
            yq=yr+7*G                          # D at yq-2G = yr+5G
            q=self.Q(xq,yq); self.PW('GND',xc,yq+2*G)
            if pcb: self.at(r,px+2.54,py,270); self.at(d,px+1.27,py+10.16,0); self.at(q,px,py+15.24,0); self.label(g['out'].replace('LED_',''),px+3.8,py+12.9,1.0); self.pwr.append(('+5V',px+2.54,py)); self.pwr.append(('GND',px,py+15.24))
            self.W(xq-2*G,yq,xin,yq); self.L(ins[0],xin,yq,180,'input')
            self.T(g['out'],xc+1.5*G,yr+3.5*G,1.0)
            return 10*G
        if kind=='BUS':
            yq=y0+4*G
            q=self.Q(xq,yq); self.PW('GND',xc,yq+2*G)
            if pcb: self.at(q,px,py+2.54,0); self.pwr.append(('GND',px,py+2.54))
            self.W(xc,yq-2*G,xc,yq-3*G); self.W(xc,yq-3*G,xout,yq-3*G); self.L(g['out'],xout,yq-3*G,0,'bidirectional')
            self.W(xq-2*G,yq,xin,yq); self.L(ins[0],xin,yq,180,'input')
            return 8*G
        self.PW('+5V',xc,yr-1.5*G)
        r=self.R(g['pu'],xc,yr)
        if pcb: self.at(r,px+2.54,py,270); self.pwr.append(('+5V',px+2.54,py))
        self.W(xc,yr+1.5*G,xc,yc0); self.W(xc,yc0,xout,yc0); self.L(g['out'],xout,yc0,0,'output')
        if n>1: self.J(xc,yc0)
        for k,inp in enumerate(ins):
            yq=yc0+2*G+6*G*k                   # D at yq-2G, S at yq+2G
            q=self.Q(xq,yq)
            if pcb:
                self.at(q,px,py+10.16+5.08*k,0)
                if kind=='NOR' or k==n-1: self.pwr.append(('GND',px,py+10.16+5.08*k))
            self.W(xq-2*G,yq,xin,yq); self.L(inp,xin,yq,180,'input')
            if kind=='NAND':
                if k<n-1: self.W(xc,yq+2*G,xc,yq+4*G)
                else: self.PW('GND',xc,yq+2*G)
            else:
                self.PW('GND',xc,yq+2*G)
                if k>0:
                    self.W(xc,yq-2*G,xbus,yq-2*G); self.J(xc,yq-2*G) if False else None
                    ytop=yc0 if k==1 else yq-2*G-6*G
                    self.W(xbus,ytop,xbus,yq-2*G); self.J(xbus,ytop)
        return 6*G*n+8*G
    def layout(self,gates,titles,x0,y0,cols,pcb_origin=(10.0,10.0),pcb_cols=None):
        """Draw all gates group by group (schematic) and assign PCB tiles in a grid of pcb_cols columns."""
        y=y0; groups=[]
        pcb_cols=pcb_cols or cols; pxo,pyo=pcb_origin; py=pyo; tiles=[]
        for g in gates:
            if not groups or groups[-1][0]!=g['group']: groups.append((g['group'],[]))
            groups[-1][1].append(g)
        # pcb tile positions: fill columns left to right in gate order, each column packed independently
        # (skyline packing: next gate goes to the lowest column, ties broken left to right)
        colh=[pyo]*pcb_cols
        for g in gates:
            j=min(range(pcb_cols),key=lambda c:(round(colh[c],3),c))
            tiles.append((g,(pxo+j*self.PCB_COL,colh[j]))); colh[j]+=self.tile_h(g)
        py=max(colh)
        pos={id(g):t for g,t in tiles}
        for name,gs in groups:
            self.T(titles.get(name,name),x0,y-G,2.0,True); y+=2*G
            for i in range(0,len(gs),cols):
                rw=gs[i:i+cols]; h=0
                for j,g in enumerate(rw): h=max(h,self.gate(g,x0+j*self.CELL_W,y,pcb=pos[id(g)]))
                y+=h+2*G
            y+=2*G
        self.pcb_extent=(pxo+pcb_cols*self.PCB_COL,py)
        # power rails: per column, GND on B.Cu at x-1.27 and +5V on B.Cu at x+6.35, from the trunks above the tiles to the column bottom
        yg=pyo-6.0; yv=pyo-3.0; xs=[pxo+j*self.PCB_COL for j in range(pcb_cols)]
        for j,x in enumerate(xs):
            if colh[j]==pyo: continue
            yg_end=max([y for n,px_,y in self.pwr if n=='GND' and abs(px_-x)<0.01],default=None)
            yv_end=max([y for n,px_,y in self.pwr if n=='+5V' and abs(px_-(x+2.54))<0.01],default=None)
            if yg_end: self.rails.append(('GND','B.Cu',x-1.27,yg,x-1.27,yg_end,0.5)); self.vias.append(('GND',x-1.27,yg))
            if yv_end: self.rails.append(('+5V','B.Cu',x+6.35,yv,x+6.35,yv_end,0.5)); self.vias.append(('+5V',x+6.35,yv))
        used=[x for j,x in enumerate(xs) if colh[j]>pyo]
        self.rails.append(('GND','F.Cu',used[0]-1.27,yg,used[-1]-1.27,yg,0.8))
        self.rails.append(('+5V','F.Cu',used[0]+6.35,yv,used[-1]+6.35,yv,0.8))
        for net,sx,sy in self.pwr:
            if net=='GND': self.rails.append(('GND','B.Cu',sx,sy,sx-1.27,sy,0.5))
            else: self.rails.append(('+5V','B.Cu',sx,sy,sx+3.81,sy,0.5))
        return y
    def file(self,paper_w,paper_h,extra_libs=()):
        libs="".join(self.libs.values())+"".join(extra_libs)
        return (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{self.sheet_uuid}")\n\t(paper "User" {f(paper_w)} {f(paper_h)})\n'
                "\t(lib_symbols\n"+libs+"\t)\n"+self.body+
                ('\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n' if self.sheet_uuid==self.root_uuid else '')+'\t(embedded_fonts no)\n)\n')

def project_file(name):
    return '{\n  "board": {"design_settings": {"defaults": {}, "rules": {}}},\n  "meta": {"filename": "%s.kicad_pro", "version": 3},\n  "schematic": {"drawing": {}, "legacy_lib_dir": "", "legacy_lib_list": []},\n  "sheets": [],\n  "text_variables": {}\n}\n' % name

def write_plan(w,path,outline,extra=None):
    """PCB placement plan consumed by pcb.py (run with KiCad's python)."""
    import json
    json.dump(dict(place=w.place,silk=w.silk,rails=w.rails,vias=w.vias,outline=list(outline),extra=extra or {}),open(path,'w'),indent=0)

"""Emit KiCad 10 schematic S-expressions."""
import uuid as _uuid, re
ROOT_UUID="dcea6538-d2e0-47f4-9689-37c811b1c565"
PROJECT="Untitled"
def U(): return str(_uuid.uuid4())
def f(x): 
    s=f"{x:.4f}".rstrip('0').rstrip('.'); return s if s!='-0' else '0'

def prop(name,val,x,y,rot=0,hide=False,justify=None,italic=False):
    eff="(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)"+("\n\t\t\t\t\t(italic yes)" if italic else "")+"\n\t\t\t\t)"+(f"\n\t\t\t\t(justify {justify})" if justify else "")+"\n\t\t\t)"
    return (f'\t\t(property "{name}" "{val}"\n\t\t\t(at {f(x)} {f(y)} {rot})\n'+("\t\t\t(hide yes)\n" if hide else "")+
            "\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t"+eff+"\n\t\t)\n")

def symbol(lib_id, ref, value, x, y, rot, path, extra_props=(), pins=('1','2'), footprint="", sim=False, mirror=None, in_bom=True):
    """extra_props: list of (name,val,hide)"""
    s=f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {f(x)} {f(y)} {rot})\n'
    if mirror: s+=f'\t\t(mirror {mirror})\n'
    s+=f'\t\t(unit 1)\n\t\t(body_style 1)\n\t\t(exclude_from_sim no)\n\t\t(in_bom {"yes" if in_bom else "no"})\n\t\t(on_board {"yes" if in_bom else "no"})\n\t\t(in_pos_files yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(uuid "{U()}")\n'
    hide_ref=ref.startswith('#')
    s+=prop("Reference",ref,x+2.54,y-1.27,0,hide=hide_ref,justify="left")
    s+=prop("Value",value,x+2.54,y+1.27,0,justify="left")
    s+=prop("Footprint",footprint,x,y,0,hide=True)
    s+=prop("Datasheet","",x,y,0,hide=True)
    for name,val,hide in extra_props: s+=prop(name,val,x,y,0,hide=hide)
    for p in pins: s+=f'\t\t(pin "{p}"\n\t\t\t(uuid "{U()}")\n\t\t)\n'
    s+=f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "{path}"\n\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n'
    return s

Q_PROPS=[("Description","0.2A Ic, 40V Vce, Small Signal NPN Transistor, TO-92",True),("Sim.Device","NPN",True),("Sim.Pins","1=E 2=B 3=C",True),
         ("Sim.Library","${KIPRJMOD}/../../lib/2N3904.lib",True),("Sim.Name","2N3904",True),("Sim.Type","GUMMELPOON",True)]
R_FOOT="Resistor_THT:R_Axial_DIN0207_L6.3mm_D2.5mm_P5.08mm_Vertical"
Q_FOOT="Package_TO_SOT_THT:TO-92_Inline"
def resistor(ref,value,x,y,rot,path):
    return symbol("Device:R",ref,value,x,y,rot,path,[("Description","Resistor",True)],footprint=R_FOOT)
def transistor(ref,x,y,rot,path):
    return symbol("Transistor_BJT:2N3904",ref,"2N3904",x,y,rot,path,Q_PROPS,pins=('3','2','1'),footprint=Q_FOOT)
def power(ref,name,x,y,rot,path):
    lib="power:GND" if name=="GND" else "power:+5V"
    return symbol(lib,ref,name,x,y,rot,path,[("Description",f'Power symbol creates a global label with name \\"{name}\\"',True)],pins=('1',))
def vsource(ref,kind,params,x,y,path):
    """kind: PULSE / PWL / DC"""
    lib={"PULSE":"Simulation_SPICE:VPULSE","PWL":"Simulation_SPICE:VPWL","DC":"Simulation_SPICE:VDC"}[kind]
    val={"PULSE":"VPULSE","PWL":"VPWL","DC":params}[kind]
    props=[("Description","Voltage source",True),("Sim.Pins","1=+ 2=-",True),("Sim.Type",kind,True),("Sim.Device","V",True)]
    if kind!="DC": props.append(("Sim.Params",params,False))
    return symbol(lib,ref,val,x,y,0,path,props,in_bom=False)

def wire(x1,y1,x2,y2):
    return f'\t(wire\n\t\t(pts\n\t\t\t(xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n'
def junction(x,y):
    return f'\t(junction\n\t\t(at {f(x)} {f(y)})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n\t\t(uuid "{U()}")\n\t)\n'
def glabel(name,x,y,rot=0,shape="input"):
    just="left" if rot==0 else "right"
    return (f'\t(global_label "{name}"\n\t\t(shape {shape})\n\t\t(at {f(x)} {f(y)} {rot})\n\t\t(fields_autoplaced yes)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n\t\t(uuid "{U()}")\n'
            f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}"\n\t\t\t(at {f(x)} {f(y)} 0)\n\t\t\t(hide yes)\n\t\t\t(show_name no)\n\t\t\t(do_not_autoplace no)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify {just})\n\t\t\t)\n\t\t)\n\t)\n')
def text(s,x,y,size=1.27,bold=False):
    s=s.replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
    b="\n\t\t\t\t(bold yes)" if bold else ""
    return f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {f(size)} {f(size)}){b}\n\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{U()}")\n\t)\n'
def sheet(name,file,x,y,w,h,page,sheet_uuid):
    return (f'\t(sheet\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(w)} {f(h)})\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n'
            f'\t\t(stroke\n\t\t\t(width 0.1524)\n\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n\t\t(uuid "{sheet_uuid}")\n'
            f'\t\t(property "Sheetname" "{name}"\n\t\t\t(at {f(x)} {f(y-0.7116)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n'
            f'\t\t(property "Sheetfile" "{file}"\n\t\t\t(at {f(x)} {f(y+h+0.5846)} 0)\n\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n'
            f'\t\t(instances\n\t\t\t(project "{PROJECT}"\n\t\t\t\t(path "/{ROOT_UUID}"\n\t\t\t\t\t(page "{page}")\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')

def lib_symbol_block(root_text, name):
    """extract an embedded lib symbol block from the root schematic text"""
    i=root_text.find(f'\t\t(symbol "{name}"\n')
    assert i>=0, name
    j=root_text.find('\n\t\t(symbol "', i+10)
    k=root_text.find('\n\t)\n', i)          # end of lib_symbols
    if j<0 or k<j: j=k
    return root_text[i:j]+"\n"

def sheet_file(sheet_uuid, paper_w, paper_h, lib_blocks, body):
    return (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n\t(uuid "{sheet_uuid}")\n\t(paper "User" {f(paper_w)} {f(paper_h)})\n'
            "\t(lib_symbols\n"+"".join(lib_blocks)+"\t)\n"+body+'\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n')

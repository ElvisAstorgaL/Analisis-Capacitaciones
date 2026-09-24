"""Lectura del registro HC y cruce por persona, área y turnos reales."""
import zipfile, xml.etree.ElementTree as ET, re, unicodedata
from collections import defaultdict
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
def norm(v):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(v or '').upper()) if not unicodedata.combining(c)).split())
def read_hc(file):
    with zipfile.ZipFile(file) as z:
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            ss=[''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in root.findall('m:si',NS)]
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
        rows=[]
        for row in root.findall('.//m:sheetData/m:row',NS):
            values={}
            for c in row.findall('m:c',NS):
                ref=c.get('r'); col=re.match(r'[A-Z]+',ref).group()
                v=c.find('m:v',NS); ins=c.find('m:is',NS)
                val=v.text if v is not None else ''.join(t.text or '' for t in ins.findall('.//m:t',NS)) if ins is not None else ''
                if c.get('t')=='s' and val: val=ss[int(val)]
                values[col]=str(val or '').strip()
            rows.append(values)
    if not rows: raise ValueError('El registro HC no tiene datos.')
    headings=rows[0]
    for col,expected in {'A':'AREA','B':'SUPERVISOR','C':'NOMBRE'}.items():
        if norm(headings.get(col))!=expected: raise ValueError(f'No se encontró la columna {expected} en {col}.')
    courses={c:headings[c] for c in 'EFGHIJKL' if headings.get(c)}
    technicians=[]
    for n,r in enumerate(rows[1:],2):
        if not r.get('C'): continue
        technicians.append({'area':r.get('A',''),'supervisor':r.get('B',''),'nombre':r['C'],'cargo':r.get('D',''),'estados':{c:norm(r.get(c)) for c in courses},'fila':n})
    return courses,technicians

def _possible_supervisors(person, mapping):
    original=norm(person['supervisor']); area=norm(person['area'])
    if original=='SUP NUEVO' and 'RECONSTRU' in area: return ['PATRICIO PONCE']
    if original in mapping: return [norm(x) for x in re.split(r'\s*[;,]\s*',mapping[original]) if x.strip()]
    # Supervisores emparejados en el Excel HC; cada uno conserva su propio turno.
    if ' Y ' in original: return [x.strip() for x in original.split(' Y ')]
    return [original]

def cross_hc(records,technicians,course,day,mapping=None):
    mapping=mapping or {}
    on_date=defaultdict(list); known=defaultdict(list)
    for r in records:
        known[norm(r['supervisor'])].append(r)
        if r['fecha']==day: on_date[norm(r['supervisor'])].append(r)
    result=[]
    for t in technicians:
        if t['estados'].get(course)!='PENDIENTE': continue
        name=norm(t['nombre']); cargo=norm(t['cargo']); boss=norm(t['supervisor'])
        # Jefes de operaciones figuran como responsables de sus supervisores, no como turno.
        # Si el participante es supervisor, usar su propio turno en el calendario.
        if 'SUPERVISOR' in cargo and name in known:
            options=[name]; mode='Turno propio del supervisor participante'
        else:
            options=_possible_supervisors(t,mapping); mode='Turno del supervisor responsable'
        existing=[s for s in options if s in known]
        working=[s for s in existing if any(r['estado']=='Día' for r in on_date[s])]
        if working: status='Candidato · confirmar turno del participante'
        elif not existing: status='Sin correspondencia en calendario'
        elif not any(on_date[s] for s in existing): status='Sin turno registrado ese día'
        else: status='Supervisor sin turno día'
        result.append({'Técnico / participante':t['nombre'],'Cargo':t['cargo'],'Supervisor HC':t['supervisor'],
            'Supervisores calendario':', '.join(options),'Supervisores de día':', '.join(working),
            'Área HC':t['area'],'Estado HC':'PENDIENTE','Criterio':mode,'Situación':status,'Fila HC':t['fila']})
    result.sort(key=lambda x:(not x['Situación'].startswith('Candidato'),norm(x['Supervisor HC']),norm(x['Técnico / participante'])))
    return result

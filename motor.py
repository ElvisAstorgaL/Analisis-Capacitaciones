"""Motor determinista de lectura de calendarios Excel 2026, sin dependencias externas."""
import zipfile, xml.etree.ElementTree as ET, re, calendar
from collections import defaultdict
from datetime import date
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
BASE='{'+NS['m']+'}'
MONTHS={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
AREAS={'Calendario Rodados':'Rodados','Calendario Tolvas':'Tolvas','Calendario P&P':'P&P','Calendario EqAp':'Equipos de Apoyo','Calendario 798':'798','Calendario Reco':'Reconstrucción','Calendario R&D':'R&D'}

def _col(ref):
    s=re.match(r'[A-Z]+',ref).group(); n=0
    for ch in s:n=n*26+ord(ch)-64
    return n

def read_calendar(path,month=10,year=2026):
    records=[];warnings=[]
    with zipfile.ZipFile(path) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in si.findall('.//m:t',NS)) for si in root.findall('m:si',NS)]
        styles=ET.fromstring(z.read('xl/styles.xml'))
        fills=styles.find('m:fills',NS); xfs=styles.find('m:cellXfs',NS)
        def fill(style):
            try:
                f=fills[int(xfs[int(style)].get('fillId','0'))]
                fg=f.find('.//m:fgColor',NS)
                if fg is None:return None
                rgb=fg.get('rgb','').upper()
                if rgb.endswith('FFFF00'):return 'Día'
                if fg.get('theme')=='3' and fg.get('tint','').startswith('0.499'):return 'Noche'
                if fg.get('theme')=='5' and fg.get('tint','').startswith('0.599'):return 'Descanso'
                return None
            except (ValueError,IndexError,TypeError):return None
        for index,(sheet,area) in enumerate(AREAS.items(),start=3):
            root=ET.fromstring(z.read(f'xl/worksheets/sheet{index}.xml'))
            rows=[]
            for r in root.findall('.//m:sheetData/m:row',NS):
                cells={}
                for c in r.findall('m:c',NS):
                    v=c.find('m:v',NS); ins=c.find('m:is',NS)
                    value=v.text if v is not None else ''.join(t.text or '' for t in ins.findall('.//m:t',NS)) if ins is not None else ''
                    if c.get('t')=='s' and value:value=shared[int(value)]
                    cells[_col(c.get('r'))]={'value':value,'status':fill(c.get('s','0')),'ref':c.get('r')}
                rows.append((int(r.get('r')),cells))
            # Every month is a separate 7-column block, sometimes repeated vertically for different crews.
            for ri,(rownum,cells) in enumerate(rows):
                for start in (4,12,20):
                    heading=cells.get(start,{}).get('value','').strip().lower()
                    if MONTHS.get(heading)!=month:continue
                    # Locate the crew heading within the next two rows, then weekday heading.
                    crewrow=None;weekday=None
                    for k in range(ri+1,min(ri+5,len(rows))):
                        rc=rows[k][1];v=rc.get(start,{}).get('value','').lower()
                        if 'turno' in v and crewrow is None:crewrow=k
                        if v in ('lunes','martes'):weekday=k;break
                    if crewrow is None or weekday is None:continue
                    rc=rows[crewrow][1];crew=rc.get(start,{}).get('value','').strip()
                    # Names can be in E and G; collect text in crew heading, excluding labels.
                    names=[]
                    for col in range(start+1,start+7):
                        val=rc.get(col,{}).get('value','').strip()
                        if val and not re.match(r'^(turno|lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|octubre|noviembre|diciembre)',val,re.I) and not val.isdigit():names.append(val)
                    if not names:
                        warnings.append(f'{sheet} {crew} {month}: sin nombres detectados ({rows[crewrow][0]}).');continue
                    end=min(weekday+7,len(rows))
                    for k in range(weekday+1,end):
                        dayrow=rows[k][1]
                        for col in range(start,start+7):
                            c=dayrow.get(col)
                            if not c:continue
                            try:d=int(c['value'])
                            except (ValueError,TypeError):continue
                            if not 1<=d<=calendar.monthrange(year,month)[1]:continue
                            status=c['status']
                            if not status:
                                warnings.append(f'{sheet}!{c["ref"]}: fecha {d} sin color reconocido.');continue
                            for name in names:
                                records.append({'fecha':date(year,month,d),'area':area,'supervisor':name,'turno':crew,'estado':status,'celda':f'{sheet}!{c["ref"]}'})
    # Reject contradictory duplicates rather than silently choosing one.
    unique={}; conflicts=[]
    for r in records:
        key=(r['fecha'],r['area'],r['supervisor'])
        if key in unique and unique[key]['estado']!=r['estado']:conflicts.append(f'{key}: {unique[key]["estado"]} / {r["estado"]}')
        else:unique[key]=r
    if conflicts:raise ValueError('Estados contradictorios: '+'; '.join(conflicts[:12]))
    return list(unique.values()),warnings

def coincidences(records,reference='Luis Cortes'):
    days=sorted({r['fecha'] for r in records if r['supervisor'].casefold()==reference.casefold() and r['estado']=='Día'})
    if not days:raise ValueError(f'No se encontraron fechas de día para {reference}.')
    result=[]
    for day in days:
        active=sorted([r for r in records if r['fecha']==day and r['estado']=='Día' and r['supervisor'].casefold()!=reference.casefold()],key=lambda x:(x['area'],x['supervisor']))
        result.append({'fecha':day,'coincidentes':active,'supervisores':len(active),'areas':len({r['area'] for r in active})})
    return result

import io
from datetime import date
from collections import defaultdict
import pandas as pd
import streamlit as st
from motor import read_calendar
from hc_motor import read_hc,cross_hc,norm

st.header('Herramientas críticas')
st.caption('Cruce del registro HC con los turnos de día de los supervisores. La disponibilidad individual de los técnicos requiere confirmación.')
a,b=st.columns(2)
cal=a.file_uploader('Calendario de turnos 2026',type=['xlsx'],key='hc_calendar')
hc=b.file_uploader('Registro de capacitaciones HC',type=['xlsx'],key='hc_registry')
if not cal or not hc:
    st.info('Carga ambos Excel para realizar el cruce. Los archivos no se guardan de forma permanente en esta versión.')
    st.stop()
try:
    courses,technicians=read_hc(io.BytesIO(hc.getvalue()))
except Exception as e:
    st.error(f'Error al leer registro HC: {e}');st.stop()
selected_date=st.date_input('Fecha propuesta',value=date(2026,10,2),min_value=date(2026,1,1),max_value=date(2026,12,31))
course=st.selectbox('Herramienta crítica',list(courses),index=next((i for i,c in enumerate(courses) if 'HYTORC' in norm(courses[c])),0),format_func=lambda c:courses[c])
try:
    records,warnings=read_calendar(io.BytesIO(cal.getvalue()),selected_date.month,selected_date.year)
except Exception as e:
    st.error(f'Error al leer calendario: {e}');st.stop()

# Explicit equivalence only; names in HC may refer to a different managerial level.
hc_names=sorted({norm(t['supervisor']) for t in technicians if t['estados'].get(course)=='PENDIENTE' and t['supervisor']})
calendar_names=sorted({r['supervisor'] for r in records})
calendar_index={norm(n):n for n in calendar_names}
mapping={}
with st.expander('Correspondencia entre supervisores HC y calendario (revisar si difieren)'):
    st.caption('Las parejas de supervisores se separan automáticamente; SUP NUEVO en Reconstrucción equivale a Patricio Ponce. Los jefes de operaciones no requieren turno propio: sus supervisores participantes se cruzan por su nombre.')
    for name in hc_names:
        if name in calendar_index or ' Y ' in name or name in ('SUP NUEVO','ALDO SANCHEZ','CLAUDIO ESTRADA','HUGO ESCOBAR'):continue
        choice=st.selectbox(f'{name} → supervisor del calendario', ['Sin correspondencia confirmada']+calendar_names,key='map_'+name)
        if choice!='Sin correspondencia confirmada':mapping[name]=choice
rows=cross_hc(records,technicians,course,selected_date,mapping)
matched=[r for r in rows if r['Situación'].startswith('Candidato')]
unmatched=[r for r in rows if r['Situación']=='Sin correspondencia en calendario']
m1,m2,m3=st.columns(3)
m1.metric('Técnicos con HC pendiente',len(rows))
m2.metric('Candidatos por turno del supervisor',len(matched))
m3.metric('Sin correspondencia de turno',len(unmatched))
if warnings:st.warning(f'{len(warnings)} advertencias de lectura del calendario. Revisa el detalle al final.')
st.subheader('Técnicos propuestos para la fecha')
if matched:
    st.dataframe(pd.DataFrame(matched).drop(columns=['Fila HC']),hide_index=True,use_container_width=True)
else:st.info('No hay candidatos verificables con las correspondencias actuales.')
with st.expander('Pendientes no propuestos / por revisar'):
    other=[r for r in rows if r not in matched]
    if other:st.dataframe(pd.DataFrame(other),hide_index=True,use_container_width=True)
    else:st.success('Todos los pendientes tienen supervisor de día en el calendario.')
st.download_button('Descargar cruce HC (CSV)',pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig'),file_name='cruce_hc.csv',mime='text/csv')
st.subheader('Preparar invitación')
if selected_date.weekday() != 4: st.caption('Puedes elegir cualquier fecha; viernes a lunes es una modalidad habitual, no una restricción.')
start=st.time_input('Hora de inicio',value=__import__('datetime').time(15,0))
end=st.time_input('Hora de término',value=__import__('datetime').time(18,0))
if end <= start: st.error('La hora de término debe ser posterior a la hora de inicio.')
location=st.text_input('Lugar','Sala de capacitaciones C5')
trainer=st.text_input('Relator (confirmar)','')
selected=st.multiselect('Participantes a proponer (confirmar con supervisores)',[f"{r['Técnico / participante']} (fila {r['Fila HC']})" for r in matched],default=[f"{r['Técnico / participante']} (fila {r['Fila HC']})" for r in matched])
selected_rows=[r for r in matched if f"{r['Técnico / participante']} (fila {r['Fila HC']})" in selected]
by_supervisor=defaultdict(list)
for r in selected_rows:by_supervisor[r['Supervisores de día']].append(r['Técnico / participante'])
listing='\n'.join(f"- {s}: {', '.join(names)}" for s,names in sorted(by_supervisor.items())) or '- Sin técnicos seleccionados.'
email=(f'Asunto: Confirmación de participantes HC – {courses[course]} – {selected_date:%d/%m/%Y}\n\n'
       f'Estimados/as:\n\nEstamos coordinando la capacitación {courses[course]} para el {selected_date:%d/%m/%Y}, '
       f'de {start:%H:%M} a {end:%H:%M}, en {location}.\n'
       +(f'Relator propuesto: {trainer}.\n' if trainer else '')+
       '\nSegún el registro HC cargado, los siguientes trabajadores figuran con la capacitación pendiente y '
       'sus supervisores aparecen programados de día en esa fecha:\n\n'+listing+'\n\n'
       'Favor confirmar la disponibilidad individual de cada técnico, la vigencia del registro y su participación. '
       'Este listado es una propuesta, no una inscripción confirmada.\n\nSaludos,\nElvis Astorga')
st.text_area('Borrador para Outlook',email,height=320)
st.download_button('Descargar borrador (.txt)',email.encode('utf-8'),disabled=end<=start,file_name='invitacion_hc.txt',mime='text/plain')
with st.expander('Advertencias y trazabilidad'):
    st.write(warnings if warnings else 'Sin advertencias de calendario.')
    st.caption('El registro HC puede estar desactualizado respecto de SharePoint; confirma antes de enviar.')

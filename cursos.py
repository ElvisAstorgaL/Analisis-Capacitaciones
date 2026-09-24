import io
from collections import defaultdict
import pandas as pd
import streamlit as st
from motor import read_calendar, coincidences
from extra import excel_bytes, pdf_bytes, month_heatmap, save_history

st.title('Planificación general de cursos')
st.caption('Fechas sugeridas según coincidencias reales de turno día. La cantidad de supervisores no equivale a participantes disponibles.')
upload = st.file_uploader('Cargar calendario de turnos (.xlsx)', type='xlsx')
if upload is None:
    st.info('Carga tu calendario para comenzar. El archivo se procesa durante esta sesión.')
    st.stop()
months = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
month = st.selectbox('Mes', list(range(1,13)), index=9, format_func=lambda n: months[n-1])
try:
    records, warnings = read_calendar(io.BytesIO(upload.getvalue()), month)
except Exception as exc:
    st.error(f'No se pudo leer el archivo: {exc}')
    st.stop()
names = sorted({r['supervisor'] for r in records})
supervisor = st.selectbox('Supervisor solicitante', names, index=names.index('Luis Cortes') if 'Luis Cortes' in names else 0)
curso = st.text_input('Curso', 'Trabajo en Altura')
c1, c2 = st.columns(2)
minimo = c1.number_input('Mínimo de participantes', min_value=1, value=6)
propios = c2.number_input('Participantes confirmados del solicitante', min_value=0, value=1)
try:
    days = coincidences(records, supervisor)
except ValueError as exc:
    st.warning(str(exc))
    st.stop()

remaining = max(0, minimo - propios)
all_contacts = {r['supervisor'] for d in days for r in d['coincidentes']}
m1,m2,m3 = st.columns(3)
m1.metric('Días de turno día',len(days))
m2.metric('Supervisores distintos que coinciden',len(all_contacts))
m3.metric('Participantes adicionales requeridos',remaining)

# Ranking is an opportunity indicator, never a probability or confirmation.
ranked = sorted(days, key=lambda d:(-d['supervisores'],-d['areas'],d['fecha']))
top = ranked[:4]
st.subheader('Calendario visual de coincidencias')
month_heatmap(2026,month,{d['fecha']:d['supervisores'] for d in days})
st.subheader('Fechas para consultar primero')
st.caption('Ordenadas por número de supervisores y, en empate, áreas que coinciden de día; ante empates se muestra primero la fecha más próxima dentro del mes. No indica probabilidad real de conseguir cupos.')
for idx,d in enumerate(top,1):
    with st.container(border=True):
        left,right=st.columns([1,3])
        left.markdown(f'### Opción {idx}')
        left.markdown(f"**{d['fecha'].strftime('%d/%m/%Y')}**")
        right.write(f"**{d['areas']} áreas** · **{d['supervisores']} supervisores** coinciden con {supervisor}.")
        right.caption(' · '.join(f"{r['supervisor']} ({r['area']})" for r in d['coincidentes']))

st.subheader('Selecciona las fechas que quieres proponer')
options = [d['fecha'] for d in ranked]
selected = st.multiselect('Fechas para el correo', options, default=[d['fecha'] for d in top[:2]], format_func=lambda dt:dt.strftime('%d/%m/%Y'))
selected_days=[d for d in days if d['fecha'] in selected]
selected_days.sort(key=lambda d:d['fecha'])
if selected_days:
    contact_dates=defaultdict(lambda:{'area':'','fechas':[]})
    for d in selected_days:
        for r in d['coincidentes']:
            contact_dates[r['supervisor']]['area']=r['area']
            contact_dates[r['supervisor']]['fechas'].append(d['fecha'].strftime('%d/%m'))
    contact_rows=[{'Supervisor':name,'Área':v['area'],'Fechas en turno día':', '.join(v['fechas']),'Días coincidentes':len(v['fechas'])} for name,v in contact_dates.items()]
    contact_rows.sort(key=lambda x:(-x['Días coincidentes'],x['Área'],x['Supervisor']))
    st.dataframe(pd.DataFrame(contact_rows),hide_index=True,use_container_width=True)
    dates_txt=', '.join(d.strftime('%d/%m') for d in selected)
    by_area=defaultdict(list)
    for r in contact_rows:
        by_area[r['Área']].append(f"{r['Supervisor']} ({r['Fechas en turno día']})")
    listing='\n'.join(f"- {area}: {'; '.join(people)}" for area,people in sorted(by_area.items()))
    email=(f'Asunto: Consulta de participantes – {curso} – {months[month-1]} 2026\n\n'
           f'Estimados/as:\n\n{supervisor} solicita gestionar el curso {curso} y actualmente cuenta con {propios} participante(s) confirmado(s). '
           f'Para completar el mínimo de {minimo}, necesitamos {remaining} participante(s) adicionales.\n\n'
           f'Según el calendario de turnos, estas son las fechas propuestas: {dates_txt}. '
           'Los siguientes supervisores coinciden en turno día en una o más de esas fechas:\n\n'
           f'{listing}\n\n'
           'Agradeceré confirmar si tienen técnicos con esta capacitación pendiente y cuántos podrían asistir en cada fecha. '
           'La disponibilidad indicada corresponde únicamente al turno programado y debe confirmarse antes de inscribir.\n\nSaludos.')
    st.subheader('Correo listo para adaptar')
    if st.button('Guardar esta programación en historial',key='save_general'):
        save_history({'Módulo':'Cursos','Fecha':', '.join(x.strftime('%d/%m/%Y') for x in selected),'Capacitación':curso,'Supervisor solicitante':supervisor,'Candidatos por turno':len(contact_rows),'Estado':'Propuesta, pendiente de confirmación'})
        st.success('Guardada en el historial temporal.')
    st.download_button('Exportar supervisores y fechas (Excel)',excel_bytes({'Supervisores':contact_rows}),file_name='planificacion_cursos.xlsx')
    st.download_button('Exportar propuesta (PDF)',pdf_bytes('Planificación: '+curso,{'Supervisores coincidentes':contact_rows}),file_name='planificacion_cursos.pdf')
    st.text_area('Copia este texto a Outlook o Teams',value=email,height=350,disabled=True)
    st.caption('Vista previa regenerada según las fechas seleccionadas. Copia el texto o descarga el borrador.')
    st.download_button('Descargar borrador de correo (.txt)',email.encode('utf-8'),file_name='consulta_capacitacion.txt',mime='text/plain')
else:
    st.info('Selecciona al menos una fecha para generar el listado y el correo.')

with st.expander('Todas las fechas, sin filtrar'):
    rows=[{'Fecha':d['fecha'].strftime('%d/%m/%Y'),'Áreas coincidentes':d['areas'],'Supervisores coincidentes':d['supervisores'],'Supervisores de día':' · '.join(f"{r['supervisor']} ({r['area']})" for r in d['coincidentes'])} for d in ranked]
    st.dataframe(pd.DataFrame(rows),hide_index=True,use_container_width=True)
    st.download_button('Descargar coincidencias CSV',pd.DataFrame(rows).to_csv(index=False).encode('utf-8-sig'),file_name=f'coincidencias_{month}_2026.csv',mime='text/csv')
with st.expander(f'Advertencias de lectura ({len(warnings)})'):
    st.write(warnings if warnings else 'Sin advertencias.')
with st.expander('Trazabilidad: celdas originales'):
    st.dataframe(pd.DataFrame(records),hide_index=True,use_container_width=True)
st.info('Próxima versión: cruce con un Excel de técnicos y vigencia de cursos, para distinguir personal pendiente, vigente y por vencer. No se asumen postulaciones sin ese archivo.')

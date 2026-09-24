"""Interfaz de planificación de una o varias herramientas críticas."""
import io
from collections import defaultdict
from datetime import date, time
import pandas as pd
import streamlit as st
from motor import read_calendar
from hc_motor import read_hc, cross_hc, norm
from extra import excel_bytes, pdf_bytes, month_heatmap, save_history

st.header('Herramientas críticas')
st.caption('Selecciona una o varias HC. Se cruzan los pendientes de cada curso con los turnos de día de los supervisores; la asistencia individual debe confirmarse.')
a, b = st.columns(2)
cal = a.file_uploader('Calendario de turnos 2026', type=['xlsx'], key='hc_calendar')
hc = b.file_uploader('Registro de capacitaciones HC', type=['xlsx'], key='hc_registry')
if not cal or not hc:
    st.info('Carga ambos Excel para realizar el cruce. Esta versión no almacena los archivos permanentemente.')
    st.stop()

@st.cache_data(show_spinner=False)
def load_hc(raw):
    return read_hc(io.BytesIO(raw))

@st.cache_data(show_spinner=False)
def load_calendar(raw, month, year):
    return read_calendar(io.BytesIO(raw), month, year)

try:
    courses, technicians = load_hc(hc.getvalue())
except Exception as e:
    st.error(f'No se pudo leer el registro HC: {e}')
    st.stop()

selected_date = st.date_input('Fecha propuesta', value=date(2026, 10, 2), min_value=date(2026, 1, 1), max_value=date(2026, 12, 31), key='hc_date')
try:
    records, warnings = load_calendar(cal.getvalue(), selected_date.month, selected_date.year)
except Exception as e:
    st.error(f'No se pudo leer el calendario: {e}')
    st.stop()

st.subheader('Calendario visual de supervisores de día')
month_counts={}
for record in records:
    if record['estado']=='Día':
        month_counts.setdefault(record['fecha'],set()).add((record['supervisor'],record['area']))
month_heatmap(selected_date.year,selected_date.month,{d:len(v) for d,v in month_counts.items()})
st.subheader('Selecciona las herramientas críticas')
initial = next((key for key, name in courses.items() if 'HYTORC' in norm(name)), next(iter(courses), None))
selected_courses = st.multiselect(
    'Puedes agregar varios cursos o quitarlos con la X',
    options=list(courses), default=[initial] if initial else [],
    format_func=lambda key: courses[key], key='hc_selected_courses',
    placeholder='Selecciona una o más HC',
)
if not selected_courses:
    st.info('Selecciona al menos una herramienta crítica para ver los candidatos.')
    st.stop()

# Los nombres del calendario y HC pueden contener varias personas en una celda.
# Se ofrecen correspondencias manuales solo para los nombres no reconocidos.
calendar_names = sorted({r['supervisor'] for r in records})
calendar_index = {norm(n) for n in calendar_names}
hc_names = sorted({norm(t['supervisor']) for t in technicians
                   if any(t['estados'].get(c) == 'PENDIENTE' for c in selected_courses)
                   and t['supervisor']})
mapping = {}
missing_names = [n for n in hc_names if n not in calendar_index and ' Y ' not in n
                 and n not in ('SUP NUEVO', 'ALDO SANCHEZ', 'CLAUDIO ESTRADA', 'HUGO ESCOBAR')]
if missing_names:
    with st.expander('Correspondencias de supervisores por revisar'):
        st.caption('SUP NUEVO en Reconstrucción se interpreta como Patricio Ponce. Los jefes de operaciones no se consideran turnos de sus supervisores participantes.')
        for name in missing_names:
            choice = st.selectbox(f'{name} → calendario', ['Sin correspondencia confirmada'] + calendar_names, key='hc_map_'+name)
            if choice != 'Sin correspondencia confirmada':
                mapping[name] = choice

st.divider()
st.subheader('Resultados por capacitación')
# La fecha de cada HC es editable; para cruzar otros meses se requiere recargar su calendario.
course_dates={}
all_rows = []
proposals = []
for i, course in enumerate(selected_courses):
    label = courses[course]
    course_day=st.date_input('Fecha de esta HC',value=selected_date,min_value=date(2026,1,1),max_value=date(2026,12,31),key=f'hc_day_{course}')
    course_dates[course]=course_day
    if course_day.month!=selected_date.month or course_day.year!=selected_date.year:
        course_records,_=load_calendar(cal.getvalue(),course_day.month,course_day.year)
    else:course_records=records
    rows = cross_hc(course_records, technicians, course, course_day, mapping)
    for r in rows:
        all_rows.append({'Capacitación': label, **r})
    candidates = [r for r in rows if r['Situación'].startswith('Candidato')]
    unmatched = [r for r in rows if r['Situación'] == 'Sin correspondencia en calendario']
    with st.container(border=True):
        st.markdown(f'#### {i+1}. {label}')
        m1, m2, m3 = st.columns(3)
        m1.metric('Pendientes', len(rows))
        m2.metric('Candidatos por turno', len(candidates))
        m3.metric('Sin correspondencia', len(unmatched))
        if candidates:
            st.dataframe(pd.DataFrame(candidates).drop(columns=['Fila HC']), hide_index=True, use_container_width=True)
        elif rows:
            st.warning('Esta HC tiene pendientes, pero ninguno coincide con un supervisor de día en la fecha seleccionada. Revisa los demás pendientes o cambia la fecha.')
        else:
            st.info('No hay participantes marcados como PENDIENTE para esta HC en el Excel cargado.')
        with st.expander(f'Otros pendientes / por revisar ({len(rows)-len(candidates)})'):
            other = [r for r in rows if r not in candidates]
            if other:
                st.dataframe(pd.DataFrame(other), hide_index=True, use_container_width=True)
            else:
                st.caption('No hay otros pendientes.')

        st.markdown('**Horario y participantes de esta capacitación**')
        left, right = st.columns(2)
        start = left.time_input('Inicio', value=time(9 if i % 2 == 0 else 15, 0), key=f'hc_start_{course}')
        end = right.time_input('Término', value=time(14 if i % 2 == 0 else 18, 0), key=f'hc_end_{course}')
        if end <= start:
            st.error('La hora de término debe ser posterior a la de inicio.')
        options = {f"{r['Técnico / participante']} · {r['Supervisor HC']} · fila {r['Fila HC']}": r for r in candidates}
        chosen = st.multiselect('Participantes propuestos', options=list(options), default=list(options), key=f'hc_people_{course}')
        proposals.append({'name': label, 'date': course_day, 'start': start, 'end': end, 'people': [options[k] for k in chosen], 'valid': end > start})

if len(proposals) > 1:
    for i, first in enumerate(proposals):
        for second in proposals[i+1:]:
            if first['date']==second['date'] and first['valid'] and second['valid'] and first['start'] < second['end'] and second['start'] < first['end']:
                same = {r['Fila HC'] for r in first['people']} & {r['Fila HC'] for r in second['people']}
                if same:
                    st.warning(f'Conflicto de horario: {len(same)} participante(s) están propuestos para «{first["name"]}» y «{second["name"]}» en horarios superpuestos.')

st.download_button('Descargar cruce de todas las HC (CSV)', pd.DataFrame(all_rows).to_csv(index=False).encode('utf-8-sig'), file_name=f'cruce_hc_{selected_date:%Y%m%d}.csv', mime='text/csv')
st.download_button('Exportar cruce completo (Excel)',excel_bytes({'Pendientes':all_rows}),file_name='cruce_hc.xlsx')
st.download_button('Exportar cruce completo (PDF)',pdf_bytes('Planificación de herramientas críticas',{'Pendientes y situación':all_rows}),file_name='cruce_hc.pdf')
st.divider()
st.subheader('Correo conjunto para Outlook')
location = st.text_input('Lugar', 'Sala de capacitaciones C5', key='hc_location')
trainer = st.text_input('Relator (opcional)', '', key='hc_trainer')

sections = []
for p in proposals:
    grouped = defaultdict(list)
    for r in p['people']:
        grouped[r['Supervisores de día'] or r['Supervisor HC']].append(r['Técnico / participante'])
    listing = '\n'.join(f'  - {supervisor}: {", ".join(sorted(set(names)))}' for supervisor, names in sorted(grouped.items())) or '  - Sin participantes propuestos.'
    sections.append(f'{p["name"]}\nFecha: {p["date"]:%d/%m/%Y}\nHorario: {p["start"]:%H:%M} a {p["end"]:%H:%M}\nParticipantes propuestos por supervisor:\n{listing}')

subject = f'Coordinación de {len(proposals)} capacitación(es) HC – {selected_date:%d/%m/%Y}'
email = (f'Asunto: {subject}\n\nEstimados/as:\n\n'
         f'Estamos organizando las siguientes capacitaciones de herramientas críticas, en {location}.\n'
         + (f'Relator: {trainer}.\n' if trainer else '') + '\n'
         + '\n\n'.join(sections)
         + '\n\nLos participantes se proponen según sus HC pendientes y el turno de día registrado de sus supervisores. '
         'Favor confirmar disponibilidad individual, vigencia de los registros y asistencia. '
         'Esta propuesta no constituye una inscripción confirmada.\n\nSaludos,\nElvis Astorga')
if st.button('Guardar programación HC en historial'):
    for p in proposals:
        save_history({'Módulo':'HC','Fecha':p['date'].strftime('%d/%m/%Y'),'Capacitación':p['name'],'Supervisor solicitante':'Planificación general','Candidatos por turno':len(p['people']),'Estado':'Propuesta, pendiente de confirmación'})
    st.success('Programación guardada en historial temporal.')
st.text_area('Borrador (incluye todas las HC seleccionadas)', value=email, height=380, key='hc_email_preview')
st.download_button('Descargar correo conjunto (.txt)', email.encode('utf-8'), file_name=f'invitacion_hc_{selected_date:%Y%m%d}.txt', mime='text/plain', disabled=not all(p['valid'] for p in proposals))
with st.expander('Advertencias y trazabilidad'):
    if warnings:
        st.write(warnings)
    else:
        st.caption('Sin advertencias del calendario.')
    st.caption('El registro se carga manualmente; puede estar desactualizado respecto de SharePoint.')

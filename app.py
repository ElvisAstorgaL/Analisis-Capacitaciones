import io, calendar
from collections import defaultdict
import pandas as pd
import streamlit as st
from motor import read_calendar,coincidences
st.set_page_config(page_title='Planificador de capacitaciones CSAR',layout='wide',page_icon='📅')
st.title('Planificador de capacitaciones CSAR')
st.caption('Cruce verificable de turnos de día. Los resultados provienen de los colores de las celdas, no de inferencias de IA.')
upload=st.file_uploader('Cargar Calendario Turnos 2026.xlsx',type='xlsx')
if upload is None:
    st.info('Carga el Excel para comenzar. Se incluye el archivo original en este paquete.');st.stop()
month=st.selectbox('Mes',list(range(1,13)),index=9,format_func=lambda n:['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'][n-1])
try:
    records,warnings=read_calendar(io.BytesIO(upload.getvalue()),month)
except Exception as e:
    st.error(f'No se pudo leer el archivo: {e}');st.stop()
names=sorted({r['supervisor'] for r in records});supervisor=st.selectbox('Supervisor solicitante',names,index=names.index('Luis Cortes') if 'Luis Cortes' in names else 0)
curso=st.text_input('Curso','Trabajo en Altura');minimo=st.number_input('Mínimo de participantes',min_value=1,value=6);propios=st.number_input('Participantes confirmados del supervisor solicitante',min_value=0,value=1)
try: days=coincidences(records,supervisor)
except ValueError as e:st.warning(str(e));st.stop()
a,b,c=st.columns(3);a.metric('Días de turno día',len(days));b.metric('Supervisores distintos que coinciden',len({r['supervisor'] for d in days for r in d['coincidentes']}));c.metric('Participantes adicionales requeridos',max(0,minimo-propios))
st.subheader('Coincidencias por fecha')
summary=[]
for d in days:
    summary.append({'Fecha':d['fecha'].strftime('%d/%m/%Y'),'Supervisores coincidentes':d['supervisores'],'Áreas coincidentes':d['areas'],'Supervisores de día':' · '.join(f"{r['supervisor']} ({r['area']})" for r in d['coincidentes'])})
st.dataframe(pd.DataFrame(summary),hide_index=True,use_container_width=True)
st.subheader('Supervisores que puedes consultar')
contacts=defaultdict(lambda:{'area':'','dias':[]})
for d in days:
    for r in d['coincidentes']:
        item=contacts[r['supervisor']];item['area']=r['area'];item['dias'].append(d['fecha'].day)
contact_rows=[{'Supervisor':name,'Área':v['area'],'Días coincidentes':len(v['dias']),'Fechas de día':', '.join(map(str,v['dias']))} for name,v in contacts.items()]
st.dataframe(pd.DataFrame(sorted(contact_rows,key=lambda x:(-x['Días coincidentes'],x['Supervisor']))),hide_index=True,use_container_width=True)
st.info('Coincidencia de supervisores ≠ participantes confirmados. Registra las postulaciones antes de asegurar el mínimo del curso.')
st.download_button('Descargar coincidencias CSV',pd.DataFrame(summary).to_csv(index=False).encode('utf-8-sig'),file_name=f'coincidencias_{month}_2026.csv',mime='text/csv')
with st.expander(f'Advertencias de lectura ({len(warnings)})'):
    st.write(warnings if warnings else 'No se encontraron advertencias.')
with st.expander('Trazabilidad: celdas originales'):
    st.dataframe(pd.DataFrame(records),hide_index=True,use_container_width=True)

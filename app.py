import streamlit as st
st.set_page_config(page_title='Gestión de capacitaciones CSAR',page_icon='📚',layout='wide')
st.title('Gestión de capacitaciones CSAR')
st.caption('Planificación de cursos y herramientas críticas · prototipo sin conexión automática a SharePoint')
module=st.radio('Módulo',['Planificación de cursos','Herramientas críticas'],horizontal=True)
if module=='Planificación de cursos':
    import cursos
else:
    import hc

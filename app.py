import streamlit as st
st.set_page_config(page_title='CSAR | Gestión de capacitaciones',page_icon='🟡',layout='wide')
st.markdown('''<style>
.stApp{background:linear-gradient(155deg,#20262D 0%,#151A20 100%);color:#F2F4F5}
[data-testid="stSidebar"]{background:#252C33}
h1,h2,h3{color:#FFCD11!important}
.stButton>button[kind="primary"],.stDownloadButton>button{background:#FFCD11!important;color:#20252A!important;border:0;border-radius:9px;font-weight:700}
[data-testid="stMetric"]{background:#303840;padding:13px;border-radius:12px;border-left:4px solid #FFCD11}
[data-testid="stVerticalBlockBorderWrapper"]{border-color:#555C63!important}
</style>''',unsafe_allow_html=True)
st.markdown('### 🟡 CSAR  /  GESTIÓN DE CAPACITACIONES')
st.caption('Planificación de cursos y herramientas críticas · versión 6 · datos cargados manualmente')
module=st.sidebar.radio('Módulo',['🏠 Inicio','📅 Planificación de cursos','🔧 Herramientas críticas','📚 Historial e indicadores','☁️ SharePoint'],key='csar_module')
if module=='🏠 Inicio':
    st.title('Centro de planificación')
    st.write('Selecciona un módulo desde el menú lateral. Los archivos se cargan en cada módulo; los registros personales no se guardan en GitHub.')
    c1,c2=st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader('📅 Planificación de cursos')
            st.write('Encuentra las fechas con más supervisores de día, consulta cupos y genera un correo general.')
            if st.button('Abrir planificación',use_container_width=True):st.session_state.csar_module='📅 Planificación de cursos';st.rerun()
    with c2:
        with st.container(border=True):
            st.subheader('🔧 Herramientas críticas')
            st.write('Cruza HC pendientes con turnos; programa varias capacitaciones y genera un correo conjunto.')
            if st.button('Abrir HC',use_container_width=True):st.session_state.csar_module='🔧 Herramientas críticas';st.rerun()
elif module=='📅 Planificación de cursos':import cursos
elif module=='🔧 Herramientas críticas':import hc
elif module=='📚 Historial e indicadores':
    from extra import history_panel
    history_panel()
    history=st.session_state.get('csar_history',[])
    a,b,c=st.columns(3)
    a.metric('Programaciones guardadas',len(history))
    b.metric('Cursos generales',sum(r.get('Módulo')=='Cursos' for r in history))
    c.metric('Programaciones HC',sum(r.get('Módulo')=='HC' for r in history))
    st.caption('Los indicadores reflejan únicamente el historial cargado en esta sesión, no la ejecución real ni toda la dotación.')
else:
    st.title('Conexión con SharePoint')
    st.warning('Aún no está conectada. La V6 utiliza carga manual; no se almacenan credenciales ni archivos de personal en el repositorio.')
    st.write('Para la conexión real se requiere autorización de TI, permisos de Microsoft Entra/Graph y una ubicación de SharePoint autorizada. La configuración debe guardarse en los secretos de Streamlit, nunca en GitHub.')
    st.write('Hasta entonces, exporta los Excel autorizados desde SharePoint y súbelos en el módulo correspondiente.')

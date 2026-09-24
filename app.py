import streamlit as st
st.set_page_config(page_title='CSAR | Gestión de capacitaciones',page_icon='🟡',layout='wide')
st.markdown("""<style>
/* Alto contraste: fondo oscuro, textos y controles legibles */
.stApp {background:linear-gradient(155deg,#20262D 0%,#151A20 100%);color:#F4F5F7}
[data-testid="stSidebar"] {background:#252C33!important}
[data-testid="stSidebar"] * {color:#F4F5F7!important}
h1,h2,h3 {color:#FFCD11!important}
p,span,label,small,li,[data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"] {color:#F4F5F7}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {color:#CBD3DA!important}
/* Streamlit button text inherits theme and is always readable */
.stButton>button, .stDownloadButton>button, .stFormSubmitButton>button {
 background:#FFCD11!important;color:#161B20!important;border:1px solid #FFCD11!important;
 border-radius:9px!important;font-weight:750!important;opacity:1!important;
}
.stButton>button *, .stDownloadButton>button *, .stFormSubmitButton>button * {color:#161B20!important;opacity:1!important}
.stButton>button:hover,.stDownloadButton>button:hover {background:#FFE16B!important;border-color:#FFE16B!important}
.stButton>button:disabled {background:#626A72!important;color:#F5F5F5!important;border-color:#626A72!important}
.stButton>button:disabled * {color:#F5F5F5!important}
[data-testid="stMetric"] {background:#303840;padding:13px;border-radius:12px;border-left:4px solid #FFCD11}
[data-testid="stMetric"] * {color:#F5F6F7!important}
[data-testid="stVerticalBlockBorderWrapper"] {border-color:#58636C!important}
[data-baseweb="input"] input,[data-baseweb="textarea"] textarea {background:#313A43!important;color:#FFFFFF!important}
[data-baseweb="select"]>div {background:#313A43!important;color:#FFFFFF!important}
[data-baseweb="select"] span {color:#FFFFFF!important}
[data-testid="stRadio"] label,[data-testid="stCheckbox"] label {color:#F5F5F5!important}
</style>""",unsafe_allow_html=True)
st.markdown('### 🟡 CSAR  /  GESTIÓN DE CAPACITACIONES')
st.caption('Planificación de cursos y herramientas críticas · versión 6 · datos cargados manualmente')
# Procesar navegación antes de crear el widget; nunca modificar su estado después.
if '_csar_next_module' in st.session_state:
    st.session_state['csar_module'] = st.session_state.pop('_csar_next_module')
module=st.sidebar.radio('Módulo',['🏠 Inicio','📅 Planificación de cursos','🔧 Herramientas críticas','📚 Historial e indicadores','☁️ SharePoint'],key='csar_module')
if module=='🏠 Inicio':
    st.title('Centro de planificación')
    st.write('Selecciona un módulo desde el menú lateral. Los archivos se cargan en cada módulo; los registros personales no se guardan en GitHub.')
    c1,c2=st.columns(2)
    with c1:
        with st.container(border=True):
            st.subheader('📅 Planificación de cursos')
            st.write('Encuentra las fechas con más supervisores de día, consulta cupos y genera un correo general.')
            if st.button('Abrir planificación',key='home_courses',use_container_width=True):
                st.session_state['_csar_next_module']='📅 Planificación de cursos'
                st.rerun()
    with c2:
        with st.container(border=True):
            st.subheader('🔧 Herramientas críticas')
            st.write('Cruza HC pendientes con turnos; programa varias capacitaciones y genera un correo conjunto.')
            if st.button('Abrir HC',key='home_hc',use_container_width=True):
                st.session_state['_csar_next_module']='🔧 Herramientas críticas'
                st.rerun()
elif module == '📅 Planificación de cursos':
    import runpy
    runpy.run_module('cursos', run_name='_main_')

elif module == '🔧 Herramientas críticas':
    import runpy
    runpy.run_module('hc', run_name='_main_')
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

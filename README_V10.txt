CSAR V10 — versión estable de carga manual

- Carga ambos Excel desde la barra lateral, que permanece visible en todos los módulos.
- Los archivos se conservan en st.session_state como bytes durante la sesión, incluso al navegar a Inicio, Historial o SharePoint.
- Cada Excel puede sustituirse individualmente en la barra lateral cuando se actualice en SharePoint.
- Planificación general mantiene el análisis y calendario existentes.
- HC mantiene comparación de 1–4 fechas, correo automático y copia directa desde st.code.
- No existe sincronización automática ni almacenamiento persistente; tras reiniciar el servidor hay que volver a cargar.
- No subir Excel con datos de personal al repositorio público.

Instalación: reemplazar app.py, cursos.py y hc.py de V9 por los de V10; el ZIP incluye todos los archivos por comodidad.

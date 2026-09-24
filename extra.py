"""Exportación, historial temporal y calendario visual para Streamlit."""
import io
import calendar
from datetime import date
from html import escape
import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

YELLOW='#FFCD11'

def excel_bytes(tables):
    buffer=io.BytesIO()
    with pd.ExcelWriter(buffer,engine='xlsxwriter') as writer:
        for sheet,rows in tables.items():
            df=pd.DataFrame(rows)
            if df.empty: df=pd.DataFrame({'Información':['Sin registros']})
            df.to_excel(writer,sheet_name=sheet[:31],index=False)
            ws=writer.sheets[sheet[:31]]
            ws.freeze_panes(1,0)
            ws.autofilter(0,0,len(df),len(df.columns)-1)
            header=writer.book.add_format({'bold':True,'bg_color':'#FFCD11','font_color':'#222222','border':0})
            for i,col in enumerate(df.columns):
                ws.write(0,i,col,header)
                ws.set_column(i,i,min(58,max(16,len(str(col))+3)))
    return buffer.getvalue()

def pdf_bytes(title,sections):
    b=io.BytesIO(); doc=SimpleDocTemplate(b,pagesize=(595,842),leftMargin=38,rightMargin=38)
    sty=getSampleStyleSheet(); flow=[Paragraph(escape(title),sty['Title']),Spacer(1,16)]
    for heading,rows in sections.items():
        flow.extend([Paragraph(escape(heading),sty['Heading2']),Spacer(1,8)])
        for item in rows[:200]:
            flow.append(Paragraph(escape(' | '.join(f'{k}: {v}' for k,v in item.items())),sty['BodyText']))
            flow.append(Spacer(1,5))
        if not rows: flow.append(Paragraph('Sin registros',sty['BodyText']))
        flow.append(Spacer(1,12))
    doc.build(flow)
    return b.getvalue()

def month_heatmap(year,month,counts):
    """counts: date -> int, colores según coincidencias reales."""
    maximum=max(counts.values(),default=0)
    st.caption('Amarillo intenso: más supervisores de día; gris: sin coincidencias. Los valores son supervisores, no cupos confirmados.')
    head=''.join(f'<th>{d}</th>' for d in ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'])
    lines=[f'<table class="heatmap"><thead><tr>{head}</tr></thead><tbody>']
    for week in calendar.monthcalendar(year,month):
        lines.append('<tr>')
        for day in week:
            if not day: lines.append('<td class="blank"></td>');continue
            value=counts.get(date(year,month,day),0)
            opacity=(0.15+0.85*value/maximum) if maximum else 0.08
            bg=f'rgba(255,205,17,{opacity:.2f})' if value else '#333B43'
            lines.append(f'<td style="background:{bg};color:{"#111" if value else "#9BA5AF"}"><b>{day}</b><small>{value} sup.</small></td>')
        lines.append('</tr>')
    lines.append('</tbody></table>')
    st.markdown('<style>.heatmap{width:100%;border-spacing:5px}.heatmap td{border-radius:9px;padding:9px;height:56px;text-align:center}.heatmap th{color:#FFCD11}.heatmap small{display:block;font-size:11px}.heatmap .blank{background:transparent}</style>'+''.join(lines),unsafe_allow_html=True)

def save_history(entry):
    st.session_state.setdefault('csar_history',[]).append(entry)

def history_panel():
    st.subheader('Historial de programaciones')
    st.caption('Historial temporal de esta sesión. Exporta el archivo antes de cerrar; aún no hay almacenamiento central.')
    incoming=st.file_uploader('Importar historial anterior (CSV, opcional)',type='csv',key='history_import')
    if incoming and st.button('Incorporar historial importado'):
        try:
            rows=pd.read_csv(incoming).fillna('').to_dict('records')
            st.session_state.setdefault('csar_history',[]).extend(rows)
            st.success(f'{len(rows)} registros incorporados.')
        except Exception as exc:st.error(str(exc))
    history=st.session_state.get('csar_history',[])
    if history:
        st.dataframe(pd.DataFrame(history),hide_index=True,use_container_width=True)
        st.download_button('Descargar historial (Excel)',excel_bytes({'Historial':history}),file_name='historial_csar.xlsx')
    else: st.info('Todavía no has guardado programaciones en esta sesión.')

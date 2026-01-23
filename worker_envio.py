import os
import pandas as pd
from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
import io
from datetime import datetime, timedelta

# --- FUNÇÃO PARA GERAR O PDF COM ALERTAS ---
def gerar_pdf_completo(logs, estoque, equipamentos, org_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho
    pdf.set_fill_color(41, 128, 185) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, f"AUDITORIA INTELIGENTE - {org_name.upper()}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.ln(5)

    # SEÇÃO 1: ALERTAS CRÍTICOS (NOVIDADE)
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(190, 10, "!!! ALERTAS DE ATENÇÃO IMEDIATA !!!", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(0, 0, 0)
    
    alertas = 0
    for item in estoque:
        if float(item.get('quantidade', 0)) <= float(item.get('estoque_minimo', 0)):
            pdf.cell(190, 7, f"- STOCK CRÍTICO: {item['nome']} (Qtd: {item['quantidade']} / Mín: {item['estoque_minimo']})", ln=True)
            alertas += 1
    
    if alertas == 0:
        pdf.cell(190, 7, "Nenhum item abaixo do stock mínimo.", ln=True)
    pdf.ln(5)

    # SEÇÃO 2: ESTADO DOS EQUIPAMENTOS
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. Inventário de Equipamentos", ln=True)
    pdf.set_font("Arial", size=9)
    for eq in equipamentos:
        status = eq.get('status', 'Ativo')
        pdf.cell(190, 7, f"- {eq['nome']}: {status}", ln=True)
    pdf.ln(5)

    # SEÇÃO 3: HISTÓRICO DE LOGS (TABELA)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "3. Registro de Movimentações Recentes", ln=True)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 8, "Data/Hora", 1, 0, 'C', True)
    pdf.cell(35, 8, "Usuário", 1, 0, 'C', True)
    pdf.cell(85, 8, "Ação / Item", 1, 0, 'C', True)
    pdf.cell(35, 8, "Qtd Nova", 1, 1, 'C', True)

    pdf.set_font("Arial", size=8)
    for log in logs:
        data = log['created_at'][:16].replace('T', ' ')
        pdf.cell(35, 8, data, 1)
        pdf.cell(35, 8, str(log.get('usuario', 'N/A'))[:18], 1)
        pdf.cell(85, 8, str(log.get('substancia', 'N/A'))[:45], 1)
        pdf.cell(35, 8, str(log.get('quantidade_nova', '0')), 1, 1)

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 10, "Relatório Automático - Sistema de Gestão de Laboratórios", align='C')
    return pdf.output(dest='S')

def executar_robo():
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        
        # Coleta de Dados
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs_data = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).limit(50).execute().data

        # Identificação de itens críticos para o corpo do e-mail
        itens_criticos = [i['nome'] for i in estoque_data if float(i.get('quantidade', 0)) <= float(i.get('estoque_minimo', 0))]
        status_alerta = "⚠️ ATENÇÃO: Itens em Stock Crítico" if itens_criticos else "✅ Tudo em conformidade"

        # Geração do Excel com abas
        df_estoque = pd.DataFrame(estoque_data)
        df_equip = pd.DataFrame(equip_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_estoque.to_excel(writer, index=False, sheet_name='Substâncias')
            df_equip.to_excel(writer, index=False, sheet_name='Equipamentos')
        
        # Geração do PDF
        pdf_bytes = gerar_pdf_completo(logs_data, estoque_data, equip_data, org)

        # E-mail
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"{status_alerta} | Relatório: {org}"

        lista_criticos_html = "".join([f"<li style='color: red;'>{item}</li>" for item in itens_criticos])
        if not lista_criticos_html: lista_criticos_html = "<li>Nenhum item abaixo do mínimo.</li>"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #2980b9; color: white; padding: 20px; text-align: center;">
                <h1>Auditoria de Laboratório Inteligente</h1>
                <p>Status Atual: <strong>{status_alerta}</strong></p>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <h3>Resumo de Alertas:</h3>
                <ul>{lista_criticos_html}</ul>
                <hr>
                <p>Em anexo, enviamos os detalhes técnicos das últimas 50 movimentações e a folha de inventário completa.</p>
                <p style="font-size: 11px;">Relatório gerado em: {datetime.now().strftime('%d/%m/%Y')}</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        # Anexos
        for content, name in [(excel_buffer.getvalue(), f"Inventario_{org}.xlsx"), 
                              (pdf_bytes, f"Auditoria_{org}.pdf")]:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{name}"')
            msg.attach(part)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(ag['smtp_user'], ag['smtp_pass'])
                server.send_message(msg)
                print(f"✅ Relatório enviado para {org}")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    executar_robo()

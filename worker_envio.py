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
from datetime import datetime
from sklearn.linear_model import LinearRegression

# --- FUNÇÃO IA PARA PREVISÃO ---
def calcular_previsao_ia(logs, item_nome, qtd_atual):
    if not logs: return "Sem histórico"
    try:
        df_logs = pd.DataFrame(logs)
        df_item = df_logs[df_logs['substancia'] == item_nome].copy()
        if len(df_item) < 3: return "IA: Dados insuficientes"
        
        df_item['created_at'] = pd.to_datetime(df_item['created_at'])
        df_item['dias'] = (df_item['created_at'] - df_item['created_at'].min()).dt.days
        
        X = df_item[['dias']].values
        y = df_item['quantidade_nova'].values
        model = LinearRegression().fit(X, y)
        
        if model.coef_[0] >= 0: return "Stock Estável"
        
        dias_restantes = abs(float(qtd_atual) / model.coef_[0])
        return f"Previsão IA: Esgota em ~{int(dias_restantes)} dias"
    except:
        return "IA: Análise pendente"

# --- GERADOR DE PDF ---
def gerar_pdf_completo(logs, estoque, org_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho Azul (Mantendo seu estilo)
    pdf.set_fill_color(41, 128, 185) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, f"RELATÓRIO DE AUDITORIA - {org_name.upper()}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.ln(5)

    # Seção 1: Resumo + IA
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "1. Resumo e Inteligência Preditiva", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(190, 7, f"A organização {org_name} possui {len(estoque)} itens ativos. Abaixo, os insights de consumo gerados pela IA:")
    pdf.ln(2)
    
    # Lista de Previsões IA
    pdf.set_font("Arial", 'I', 9)
    for item in estoque[:5]: # Analisa os 5 primeiros
        previsao = calcular_previsao_ia(logs, item['nome'], item.get('quantidade', 0))
        pdf.cell(190, 7, f"> {item['nome']}: {previsao}", ln=True)
    pdf.ln(5)

    # Seção 2: Tabela de Logs (Seu Layout Original)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. Registro de Movimentações (Logs)", ln=True)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 8, "Data/Hora", 1, 0, 'C', True)
    pdf.cell(35, 8, "Usuário", 1, 0, 'C', True)
    pdf.cell(30, 8, "Ação", 1, 0, 'C', True)
    pdf.cell(55, 8, "Substância", 1, 0, 'C', True)
    pdf.cell(35, 8, "Qtd Nova", 1, 1, 'C', True)

    pdf.set_font("Arial", size=8)
    if not logs:
        pdf.cell(190, 10, "Sem registros recentes.", 1, 1, 'C')
    else:
        for log in logs[:25]:
            data = log['created_at'][:16].replace('T', ' ')
            pdf.cell(35, 8, data, 1)
            pdf.cell(35, 8, str(log.get('usuario', 'N/A'))[:18], 1)
            pdf.cell(30, 8, "Alteração", 1)
            pdf.cell(55, 8, str(log.get('substancia', 'N/A'))[:25], 1)
            pdf.cell(35, 8, str(log.get('quantidade_nova', '0')), 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- FUNÇÃO PRINCIPAL ---
def executar_robo():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        print(f"Processando: {org}")
        
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs_data = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).limit(50).execute().data

        # Excel com duas abas
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(estoque_data).to_excel(writer, index=False, sheet_name='Estoque')
            pd.DataFrame(equip_data).to_excel(writer, index=False, sheet_name='Equipamentos')
        
        pdf_bytes = gerar_pdf_completo(logs_data, estoque_data, org)

        # E-mail (Seu HTML Original)
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"🧪 Relatório de Auditoria Inteligente: {org}"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <div style="background-color: #2980b9; color: white; padding: 20px; text-align: center;">
                <h1>Relatório Semanal de Atividades</h1>
                <p>Organização: <strong>{org}</strong></p>
            </div>
            <div style="padding: 20px; border: 1px solid #ddd;">
                <p>Olá,</p>
                <p>O relatório do seu laboratório foi gerado. Incluímos as previsões de consumo da <strong>IA</strong>.</p>
                <ul>
                    <li><strong>PDF:</strong> Auditoria e tendências de stock.</li>
                    <li><strong>Excel:</strong> Base completa de itens e equipamentos.</li>
                </ul>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        for content, name in [(excel_buffer.getvalue(), f"Dados_{org}.xlsx"), (pdf_bytes, f"Auditoria_{org}.pdf")]:
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
                print(f"✅ Enviado: {org}")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    executar_robo()

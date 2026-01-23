import os
import pandas as pd
import numpy as np
from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from fpdf import FPDF
import io
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression

# --- FUNÇÃO DE INTELIGÊNCIA PREDITIVA ---
def calcular_previsao(logs, item_nome, qtd_atual):
    # Filtra logs específicos do item que foram reduções (consumo)
    df_logs = pd.DataFrame(logs)
    if df_logs.empty: return "Dados insuficientes"
    
    df_item = df_logs[df_logs['substancia'] == item_nome].copy()
    if len(df_item) < 2: return "Estável"

    # Converter datas para numérico (dias passados)
    df_item['created_at'] = pd.to_datetime(df_item['created_at'])
    min_date = df_item['created_at'].min()
    df_item['dias'] = (df_item['created_at'] - min_date).dt.days
    
    # Treinar mini-regressão: Dias vs Quantidade Nova
    X = df_item[['dias']].values
    y = df_item['quantidade_nova'].values
    
    try:
        model = LinearRegression().fit(X, y)
        taxa_consumo = model.coef_[0] # Qtd consumida por dia (negativo se estiver descendo)
        
        if taxa_consumo >= 0: return "Consumo estável ou em alta"
        
        dias_restantes = abs(qtd_atual / taxa_consumo)
        return f"Esgota em aprox. {int(dias_restantes)} dias"
    except:
        return "Análise pendente"

# --- FUNÇÃO PARA GERAR O PDF COM IA ---
def gerar_pdf_completo(logs, estoque, equipamentos, org_name):
    pdf = FPDF()
    pdf.add_page()
    
    pdf.set_fill_color(41, 128, 185) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, f"RELATÓRIO PREDITIVO - {org_name.upper()}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Análise de IA gerada em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='R')
    pdf.ln(5)

    # SEÇÃO IA: PREVISÕES DE ESTOQUE
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(190, 10, "1. Inteligência Preditiva (Projeção de Consumo)", ln=True)
    pdf.set_font("Arial", size=9)
    pdf.set_text_color(0, 0, 0)
    
    for item in estoque:
        previsao = calcular_previsao(logs, item['nome'], float(item['quantidade']))
        cor_alerta = (200, 0, 0) if "Esgota" in previsao else (0, 0, 0)
        pdf.set_text_color(*cor_alerta)
        pdf.cell(190, 7, f"- {item['nome']}: {previsao} (Atual: {item['quantidade']})", ln=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # SEÇÃO 2: EQUIPAMENTOS E MANUTENÇÃO
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. Status de Equipamentos", ln=True)
    pdf.set_font("Arial", size=9)
    for eq in equipamentos:
        pdf.cell(190, 7, f"- {eq['nome']}: {eq.get('status', 'Ativo')}", ln=True)
    pdf.ln(10)

    # SEÇÃO 3: HISTÓRICO (MANTIDO)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "3. Últimas 50 Movimentações", ln=True)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 8)
    pdf.cell(35, 8, "Data", 1, 0, 'C', True)
    pdf.cell(35, 8, "Usuário", 1, 0, 'C', True)
    pdf.cell(85, 8, "Item", 1, 0, 'C', True)
    pdf.cell(35, 8, "Qtd", 1, 1, 'C', True)

    pdf.set_font("Arial", size=8)
    for log in logs[:50]:
        pdf.cell(35, 8, log['created_at'][:10], 1)
        pdf.cell(35, 8, str(log.get('usuario', 'N/A'))[:15], 1)
        pdf.cell(85, 8, str(log.get('substancia', 'N/A'))[:40], 1)
        pdf.cell(35, 8, str(log.get('quantidade_nova', '0')), 1, 1)

    return pdf.output(dest='S')

# --- EXECUÇÃO PRINCIPAL ---
def executar_robo():
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs_data = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).execute().data

        # PDF e Excel
        pdf_bytes = gerar_pdf_completo(logs_data, estoque_data, equip_data, org)
        
        df_est = pd.DataFrame(estoque_data)
        df_eq = pd.DataFrame(equip_data)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_est.to_excel(writer, index=False, sheet_name='Substâncias')
            df_eq.to_excel(writer, index=False, sheet_name='Equipamentos')

        # E-mail com Insight de IA
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"🤖 INSIGHTS DE IA: Relatório de Auditoria {org}"

        corpo_html = f"""
        <html>
        <body style="font-family: sans-serif;">
            <div style="background-color: #2c3e50; color: white; padding: 20px; text-align: center;">
                <h2>Análise Preditiva de Laboratório</h2>
            </div>
            <div style="padding: 20px;">
                <p>Olá, aplicamos algoritmos de <strong>Regressão Linear</strong> sobre os seus dados de consumo.</p>
                <p>O relatório em anexo agora contém a estimativa de <strong>dias restantes</strong> para cada item do seu estoque baseado no histórico real.</p>
                <div style="background: #f9f9f9; padding: 15px; border-left: 5px solid #2980b9;">
                    <strong>Destaque do Sistema:</strong> Verifique no PDF os itens marcados em vermelho; eles podem acabar antes da sua próxima compra.
                </div>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        # Anexos
        for content, name in [(excel_buffer.getvalue(), f"Dados_{org}.xlsx"), (pdf_bytes, f"IA_Auditoria_{org}.pdf")]:
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
                print(f"✅ Robô IA enviado para {org}!")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    executar_robo()

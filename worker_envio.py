import matplotlib
# ESSENCIAL: Força o modo 'Agg' (sem interface gráfica) para o deploy não travar
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

import os
import pandas as pd
import numpy as np
import base64
import io
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from supabase import create_client
from jinja2 import Environment, FileSystemLoader
from xhtml2pdf import pisa
from sklearn.linear_model import LinearRegression

# --- 1. INTELIGÊNCIA ARTIFICIAL: REGRESSÃO LINEAR ---
def calcular_previsao_ia(logs, item_nome, qtd_atual):
    if not logs: return "Sem histórico"
    df_logs = pd.DataFrame(logs)
    if df_logs.empty: return "Sem dados de log"
    
    df_item = df_logs[df_logs['substancia'] == item_nome].copy()
    if len(df_item) < 3: return "IA: Dados insuficientes"

    try:
        df_item['created_at'] = pd.to_datetime(df_item['created_at'])
        min_date = df_item['created_at'].min()
        df_item['dias'] = (df_item['created_at'] - min_date).dt.days
        
        X = df_item[['dias']].values
        y = df_item['quantidade_nova'].values
        
        model = LinearRegression().fit(X, y)
        taxa_consumo = model.coef_[0] 
        
        if taxa_consumo >= 0: return "Stock Estável"
        
        dias_restantes = abs(qtd_atual / taxa_consumo)
        return f"Esgota em aprox. {int(dias_restantes)} dias"
    except:
        return "Análise pendente"

# --- 2. GERAÇÃO DE GRÁFICO PARA O PDF ---
def gerar_grafico_base64(estoque_data):
    if not estoque_data: return None
    try:
        df = pd.DataFrame(estoque_data)
        plt.figure(figsize=(7, 3))
        # Pegamos os top 10 itens para o gráfico não ficar poluído
        df_top = df.head(10)
        plt.bar(df_top['nome'].str[:12], df_top['quantidade'], color='#1E3A8A')
        plt.title("Níveis de Stock por Item")
        plt.xticks(rotation=30)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close() # Libera a memória do servidor
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except:
        return None

# --- 3. CONVERSOR HTML -> PDF ---
def gerar_pdf_pelo_html(dados_template):
    try:
        # Resolve problema de pastas no Linux (case-sensitive)
        folder = 'HTML' if os.path.exists('HTML') else 'html'
        env = Environment(loader=FileSystemLoader(folder))
        template = env.get_template('template_pdf.html')
        html_final = template.render(dados_template)
        
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.StringIO(html_final), dest=pdf_buffer)
        
        if pisa_status.err: return None
        return pdf_buffer.getvalue()
    except Exception as e:
        print(f"Erro na geração do PDF: {e}")
        return None

# --- 4. EXECUÇÃO DO ROBÔ ---
def executar_robo():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Erro: SUPABASE_URL ou KEY não encontradas.")
        return

    supabase = create_client(url, key)
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        print(f"🤖 Auditoria em curso: {org}")
        
        # Busca no Banco
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs_all = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).execute().data

        # Lógica de Alertas e IA
        alertas = sum(1 for i in estoque_data if float(i.get('quantidade', 0)) <= float(i.get('estoque_minimo', 0)))
        img_64 = gerar_grafico_base64(estoque_data)
        
        insight_ia = "IA pronta para análise."
        if estoque_data:
            previsao = calcular_previsao_ia(logs_all, estoque_data[0]['nome'], float(estoque_data[0]['quantidade']))
            insight_ia = f"Insight IA: {estoque_data[0]['nome']} -> {previsao}."

        dados_pdf = {
            "org_name": org,
            "data_atual": datetime.now().strftime('%d/%m/%Y'),
            "total_sub": len(estoque_data),
            "total_equ": len(equip_data),
            "total_alertas": alertas,
            "grafico_base64": img_64,
            "insight_ia": insight_ia
        }

        # Anexos
        pdf_bytes = gerar_pdf_pelo_html(dados_pdf)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(estoque_data).to_excel(writer, index=False, sheet_name='Estoque')
            pd.DataFrame(equip_data).to_excel(writer, index=False, sheet_name='Equipamentos')

        # E-mail
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"📊 RELATÓRIO 360° | {org}"
        msg.attach(MIMEText(f"<h2>Auditoria {org}</h2><p>Relatórios gerados em anexo.</p>", 'html'))

        for content, name in [(pdf_bytes, f"Auditoria_{org}.pdf"), (excel_buffer.getvalue(), f"Dados_{org}.xlsx")]:
            if content:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{name}"')
                msg.attach(part)

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as s:
                s.starttls()
                s.login(ag['smtp_user'], ag['smtp_pass'])
                s.send_message(msg)
                print(f"✅ Enviado: {org}")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    executar_robo()

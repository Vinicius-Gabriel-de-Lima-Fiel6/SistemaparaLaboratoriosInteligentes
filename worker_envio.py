import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
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
    df_logs = pd.DataFrame(logs)
    if df_logs.empty: return "Sem histórico suficiente"
    
    df_item = df_logs[df_logs['substancia'] == item_nome].copy()
    if len(df_item) < 3: return "Dados insuficientes para IA"

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
        plt.bar(df['nome'].str[:12], df['quantidade'], color='#1E3A8A')
        plt.title("Níveis de Stock por Item")
        plt.xticks(rotation=30)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    except:
        return None

# --- 3. CONVERSOR HTML -> PDF (xhtml2pdf) ---
def gerar_pdf_pelo_html(dados_template):
    try:
        # Carrega o seu arquivo da pasta HTML/template_pdf.html
        env = Environment(loader=FileSystemLoader('HTML'))
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
    # Conexão Supabase
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    # Busca agendamentos ativos
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        print(f"🤖 Processando Auditoria: {org}")
        
        # Coleta de Dados
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs_all = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).execute().data

        # Cálculos e IA
        total_sub = len(estoque_data)
        total_equ = len(equip_data)
        alertas = sum(1 for i in estoque_data if float(i.get('quantidade', 0)) <= float(i.get('estoque_minimo', 0)))
        
        img_base64 = gerar_grafico_base64(estoque_data)
        
        # Gera o insight dinâmico para a caixa de IA do seu HTML
        previsoes = [f"{i['nome']} ({calcular_previsao_ia(logs_all, i['nome'], float(i['quantidade']))})" for i in estoque_data[:3]]
        insight_ia = f"Análise preditiva concluída. Destaque para: {', '.join(previsoes)}. No total, {alertas} itens exigem atenção imediata por estoque baixo."

        # Dados que preenchem o seu template_pdf.html
        dados_pdf = {
            "org_name": org,
            "data_atual": datetime.now().strftime('%d/%m/%Y'),
            "total_sub": total_sub,
            "total_equ": total_equ,
            "total_alertas": alertas,
            "grafico_base64": img_base64,
            "insight_ia": insight_ia
        }

        # Geração dos Anexos
        pdf_bytes = gerar_pdf_pelo_html(dados_pdf)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(estoque_data).to_excel(writer, index=False, sheet_name='Substâncias')
            pd.DataFrame(equip_data).to_excel(writer, index=False, sheet_name='Equipamentos')

        # Montagem do E-mail
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"📊 AUDITORIA INTELIGENTE 360° | {org}"
        
        corpo_email = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Relatório de Auditoria Gerado com Sucesso</h2>
            <p>Olá, o relatório da organização <b>{org}</b> foi processado pela nossa IA.</p>
            <p>O <b>PDF em anexo</b> contém o layout 360° com os cards indicadores e análise gráfica.</p>
            <p>O <b>Excel em anexo</b> contém a base de dados completa para conferência manual.</p>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo_email, 'html'))

        # Anexar arquivos
        for content, name in [(pdf_bytes, f"Auditoria_{org}.pdf"), (excel_buffer.getvalue(), f"Base_Dados_{org}.xlsx")]:
            if content:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(content)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f'attachment; filename="{name}"')
                msg.attach(part)

        # Envio SMTP
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(ag['smtp_user'], ag['smtp_pass'])
                server.send_message(msg)
                print(f"✅ Sucesso total para {org}")
        except Exception as e:
            print(f"❌ Erro no envio para {org}: {e}")

if __name__ == "__main__":
    executar_robo()

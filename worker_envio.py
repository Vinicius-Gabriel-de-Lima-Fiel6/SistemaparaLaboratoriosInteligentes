import matplotlib
# ESSENCIAL para rodar no GitHub Actions sem erro de "display"
matplotlib.use('Agg') 
import matplotlib.pyplot as plt

import os
import pandas as pd
import numpy as np
import io
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from supabase import create_client
from fpdf import FPDF
from sklearn.linear_model import LinearRegression

# --- 1. INTELIGÊNCIA ARTIFICIAL: REGRESSÃO LINEAR ---
def calcular_previsao_ia(logs, item_nome, qtd_atual):
    if not logs: return "Sem historico"
    try:
        df_logs = pd.DataFrame(logs)
        df_item = df_logs[df_logs['substancia'] == item_nome].copy()
        if len(df_item) < 3: return "Dados insuficientes"
        
        df_item['created_at'] = pd.to_datetime(df_item['created_at'])
        df_item['dias'] = (df_item['created_at'] - df_item['created_at'].min()).dt.days
        
        model = LinearRegression().fit(df_item[['dias']].values, df_item['quantidade_nova'].values)
        taxa = model.coef_[0]
        
        if taxa >= 0: return "Stock Estavel"
        dias_restantes = abs(qtd_atual / taxa)
        return f"Esgota em aprox. {int(dias_restantes)} dias"
    except:
        return "Analise pendente"

# --- 2. GERAÇÃO DE GRÁFICO ---
def gerar_grafico_buffer(estoque_data):
    if not estoque_data: return None
    try:
        df = pd.DataFrame(estoque_data).head(10)
        plt.figure(figsize=(7, 3.5))
        plt.bar(df['nome'].str[:12], df['quantidade'], color='#1E3A8A')
        plt.title("Niveis de Stock - Top 10 Itens")
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        return buf
    except:
        return None

# --- 3. CONSTRUTOR DO PDF COM FPDF ---
class PDF_Report(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'RELATORIO DE AUDITORIA INTELIGENTE', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 10, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 0, 1, 'C')
        self.ln(5)

def gerar_pdf_final(dados):
    pdf = PDF_Report()
    pdf.add_page()
    
    # Seção Organizacao
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Organizacao: {dados['org_name']}", ln=True)
    pdf.ln(5)

    # Indicadores em Grid (Simulando os cards)
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(60, 10, " Total Substancias", 1, 0, 'L', True)
    pdf.cell(60, 10, " Equipamentos", 1, 0, 'L', True)
    pdf.cell(60, 10, " Alertas Criticos", 1, 1, 'L', True)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(60, 10, f" {dados['total_sub']}", 1, 0, 'L')
    pdf.cell(60, 10, f" {dados['total_equ']}", 1, 0, 'L')
    pdf.cell(60, 10, f" {dados['total_alertas']}", 1, 1, 'L')
    pdf.ln(10)

    # Insight IA
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 10, "Analise Preditiva (IA):", ln=True)
    pdf.set_font('Arial', '', 10)
    pdf.multi_cell(0, 7, dados['insight_ia'])
    pdf.ln(10)

    # Inserir Gráfico
    if dados['grafico_buf']:
        with open("temp_graph.png", "wb") as f:
            f.write(dados['grafico_buf'].getvalue())
        pdf.image("temp_graph.png", x=15, w=180)
        os.remove("temp_graph.png")

    return pdf.output(dest='S').encode('latin-1')

# --- 4. EXECUÇÃO PRINCIPAL ---
def executar_robo():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key: return

    supabase = create_client(url, key)
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        print(f"🤖 Auditoria: {org}")
        
        estoque = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs = supabase.table("logs_estoque").select("*").eq("org_name", org).execute().data

        # Cálculos
        alertas = sum(1 for i in estoque if float(i.get('quantidade', 0)) <= float(i.get('estoque_minimo', 0)))
        grafico_buf = gerar_grafico_buffer(estoque)
        
        # Insights IA (Pega os 2 primeiros itens)
        ia_insights = []
        for i in estoque[:2]:
            res = calcular_previsao_ia(logs, i['nome'], float(i['quantidade']))
            ia_insights.append(f"{i['nome']}: {res}")
        
        texto_ia = " | ".join(ia_insights) if ia_insights else "Sem dados para previsao."

        # Gerar Arquivos
        pdf_content = gerar_pdf_final({
            "org_name": org, "total_sub": len(estoque), "total_equ": len(equip),
            "total_alertas": alertas, "insight_ia": texto_ia, "grafico_buf": grafico_buf
        })
        
        excel_buf = io.BytesIO()
        with pd.ExcelWriter(excel_buf, engine='xlsxwriter') as writer:
            pd.DataFrame(estoque).to_excel(writer, index=False, sheet_name='Estoque')

        # Enviar E-mail
        msg = MIMEMultipart()
        msg['Subject'] = f"📊 Auditoria IA - {org}"
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg.attach(MIMEText(f"Segue auditoria automatizada para {org}.", 'plain'))

        for content, name in [(pdf_content, f"Auditoria_{org}.pdf"), (excel_buf.getvalue(), f"Dados_{org}.xlsx")]:
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
            print(f"✅ Sucesso: {org}")
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    executar_robo()

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
    if not logs: return "Sem historico"
    try:
        df_logs = pd.DataFrame(logs)
        df_item = df_logs[df_logs['substancia'] == item_nome].copy()
        if len(df_item) < 3: return "IA: Dados insuficientes"
        
        df_item['created_at'] = pd.to_datetime(df_item['created_at'])
        df_item['dias'] = (df_item['created_at'] - df_item['created_at'].min()).dt.days
        
        X = df_item[['dias']].values
        y = df_item['quantidade_nova'].values
        model = LinearRegression().fit(X, y)
        
        if model.coef_[0] >= 0: return "Stock Estavel"
        
        dias_restantes = abs(float(qtd_atual) / model.coef_[0])
        return f"Previsao IA: Esgota em ~{int(dias_restantes)} dias"
    except:
        return "IA: Analise pendente"

# --- GERADOR DE PDF ---
def gerar_pdf_completo(logs, estoque, org_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho Azul
    pdf.set_fill_color(41, 128, 185) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    
    org_txt = org_name.upper().encode('latin-1', 'replace').decode('latin-1')
    pdf.cell(190, 15, f"RELATORIO DE AUDITORIA - {org_txt}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.ln(5)

    # Seção 1: Resumo + IA
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "1. Resumo e Inteligencia Preditiva", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(190, 7, f"Relatorio de itens ativos para {org_txt}. Analise preditiva de consumo:")
    pdf.ln(2)
    
    pdf.set_font("Arial", 'I', 9)
    for item in estoque[:5]:
        previsao = calcular_previsao_ia(logs, item['nome'], item.get('quantidade', 0))
        nome_item = str(item['nome']).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(190, 7, f"> {nome_item}: {previsao}", ln=True)
    pdf.ln(5)

    # Seção 2: Tabela de Logs
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. Registro de Movimentacoes (Logs)", ln=True)
    
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 8, "Data/Hora", 1, 0, 'C', True)
    pdf.cell(35, 8, "Usuario", 1, 0, 'C', True)
    pdf.cell(30, 8, "Acao", 1, 0, 'C', True)
    pdf.cell(55, 8, "Substancia", 1, 0, 'C', True)
    pdf.cell(35, 8, "Qtd Nova", 1, 1, 'C', True)

    pdf.set_font("Arial", size=8)
    if not logs:
        pdf.cell(190, 10, "Sem registros recentes.", 1, 1, 'C')
    else:
        for log in logs[:25]:
            data = str(log.get('created_at', ''))[:16].replace('T', ' ')
            user = str(log.get('usuario', 'N/A'))[:18].encode('latin-1', 'replace').decode('latin-1')
            subst = str(log.get('substancia', 'N/A'))[:25].encode('latin-1', 'replace').decode('latin-1')
            pdf.cell(35, 8, data, 1)
            pdf.cell(35, 8, user, 1)
            pdf.cell(30, 8, "Alteracao", 1)
            pdf.cell(55, 8, subst, 1)
            pdf.cell(35, 8, str(log.get('quantidade_nova', '0')), 1, 1)

    # Retorno seguro em bytes
    out = pdf.output(dest='S')
    return out.encode('latin-1') if isinstance(out, str) else out

# --- FUNÇÃO PRINCIPAL ---
def executar_robo():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # --- LÓGICA DE TRADUÇÃO DO DIA (Para bater com seu campo 'text') ---
    dias_traducao = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo"
    }
    dia_hoje_texto = dias_traducao[datetime.now().weekday()]
    print(f"Hoje é {dia_hoje_texto}. Buscando agendamentos...")

    # Busca bots ativos para o dia específico (Texto exato do banco)
    agendamentos = supabase.table("bot_scheduler")\
        .select("*")\
        .eq("ativo", True)\
        .eq("dia_semana", dia_hoje_texto)\
        .execute()

    if not agendamentos.data:
        print(f"Fim da execução: Ninguém configurado para {dia_hoje_texto}.")
        return

    for ag in agendamentos.data:
        org = ag['org_name']
        print(f"Gerando relatorio: {org}")
        
        # Coleta de Dados
        estoque = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).limit(50).execute().data

        # Arquivo Excel
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(estoque).to_excel(writer, index=False, sheet_name='Estoque')
            pd.DataFrame(equip).to_excel(writer, index=False, sheet_name='Equipamentos')
        excel_data = excel_buffer.getvalue()
        
        # Arquivo PDF
        pdf_data = gerar_pdf_completo(logs, estoque, org)

        # Configuração do E-mail
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"🧪 Auditoria Inteligente - {org} ({dia_hoje_texto})"

        corpo = f"""
        <html>
        <body style="font-family: sans-serif;">
            <h2 style="color: #2980b9;">Relatório de Atividades: {org}</h2>
            <p>Olá, seguem em anexo os documentos de auditoria e estoque atualizados.</p>
            <ul>
                <li><strong>PDF:</strong> Logs de movimentação e previsões de IA.</li>
                <li><strong>Excel:</strong> Inventário completo de substâncias e equipamentos.</li>
            </ul>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo, 'html'))

        # Anexos
        for (conteudo, nome) in [(excel_data, f"Dados_{org}.xlsx"), (pdf_data, f"Auditoria_{org}.pdf")]:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(conteudo)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{nome}"')
            msg.attach(part)

        # Envio
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(ag['smtp_user'], ag['smtp_pass'])
                server.send_message(msg)
                print(f"✅ Enviado com sucesso para: {org}")
        except Exception as e:
            print(f"❌ Erro no envio ({org}): {e}")

if __name__ == "__main__":
    executar_robo()

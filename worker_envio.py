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
import matplotlib
# Configura o backend para 'Agg' para funcionar em servidores (GitHub Actions/Heroku)
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
from datetime import datetime
from sklearn.linear_model import LinearRegression

# --- FUNÇÃO IA (ATUALIZADA COM ALERTAS E DETECÇÃO DE ANOMALIAS) ---
# Mantive a lógica de regressão, mas agora ela retorna mais dados para o PDF usar cores
def calcular_previsao_ia(logs, item_nome, qtd_atual):
    # Padrão de retorno caso não tenha dados
    resultado_padrao = {"texto": "Sem historico", "cor": (0, 0, 0), "alerta": False}
    
    if not logs: return resultado_padrao
    try:
        df_logs = pd.DataFrame(logs)
        df_item = df_logs[df_logs['substancia'] == item_nome].copy()
        
        if len(df_item) < 3: 
            return {"texto": "IA: Dados insuficientes", "cor": (128, 128, 128), "alerta": False}
        
        df_item['created_at'] = pd.to_datetime(df_item['created_at'])
        df_item['dias'] = (df_item['created_at'] - df_item['created_at'].min()).dt.days
        
        X = df_item[['dias']].values
        y = df_item['quantidade_nova'].values
        model = LinearRegression().fit(X, y)
        
        # Se a inclinação (coef_[0]) for positiva ou zero, o estoque não está caindo
        if model.coef_[0] >= 0: 
            return {"texto": "Stock Estavel", "cor": (0, 128, 0), "alerta": False} # Verde
        
        taxa_consumo = abs(model.coef_[0])
        dias_restantes = float(qtd_atual) / taxa_consumo
        
        # --- LÓGICA NOVA: ALERTAS E ANOMALIAS ---
        msg_extra = ""
        # Verifica se o último consumo foi muito brusco (Anomalia)
        if len(y) > 2 and abs(y[-2] - y[-1]) > (taxa_consumo * 5):
            msg_extra = " [ANOMALIA]"

        texto_final = f"Previsao IA: Esgota em ~{int(dias_restantes)} dias{msg_extra}"
        
        # Definição de Cores (R, G, B)
        if dias_restantes < 5:
            return {"texto": "CRITICO: " + texto_final, "cor": (220, 20, 60), "alerta": True} # Vermelho
        elif dias_restantes < 10:
            return {"texto": "ATENCAO: " + texto_final, "cor": (255, 140, 0), "alerta": False} # Laranja
        else:
            return {"texto": texto_final, "cor": (0, 0, 0), "alerta": False} # Preto

    except:
        return {"texto": "IA: Analise pendente", "cor": (0, 0, 0), "alerta": False}

# --- NOVA FUNÇÃO: GERADOR DE GRÁFICO ---
def gerar_grafico_tendencia(estoque):
    try:
        # Pega os top 5 itens com maior quantidade para não poluir o gráfico
        itens_top = sorted(estoque, key=lambda x: x.get('quantidade', 0), reverse=True)[:5]
        
        nomes = [str(i['nome'])[:10] for i in itens_top] # Abrevia nomes longos
        qtds = [float(i.get('quantidade', 0)) for i in itens_top]
        
        plt.figure(figsize=(6, 4))
        plt.bar(nomes, qtds, color='#2980b9')
        plt.title('Top 5 Itens em Estoque')
        plt.ylabel('Quantidade Atual')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        plt.close() # Importante fechar para liberar memória
        img_buffer.seek(0)
        return img_buffer.getvalue()
    except Exception as e:
        print(f"Erro ao gerar gráfico: {e}")
        return None

# --- GERADOR DE PDF (ATUALIZADO COM CORES) ---
def gerar_pdf_completo(logs, estoque, org_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Tratamento de string para evitar erro latin-1 no título
    org_clean = org_name.upper().encode('latin-1', 'replace').decode('latin-1')
    
    # Cabeçalho
    pdf.set_fill_color(41, 128, 185) 
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, f"RELATORIO DE AUDITORIA - {org_clean}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.ln(5)

    # Seção 1: IA (Agora com Cores)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "1. Analise Preditiva e Alertas", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.ln(2)
    
    # Analisa os primeiros 8 itens (aumentei um pouco o limite)
    for item in estoque[:8]:
        resultado = calcular_previsao_ia(logs, item['nome'], item.get('quantidade', 0))
        
        # Aplica a cor retornada pela função IA
        r, g, b = resultado['cor']
        pdf.set_text_color(r, g, b)
        
        # Se for alerta crítico, coloca em Negrito
        estilo = 'B' if resultado['alerta'] else ''
        pdf.set_font("Arial", estilo, 9)
        
        item_nome_clean = str(item['nome']).encode('latin-1', 'replace').decode('latin-1')
        txt = f"> {item_nome_clean}: {resultado['texto']}".encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(190, 7, txt, ln=True)
    
    # Reseta cor para preto
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Seção 2: Tabela de Logs (Mantida idêntica)
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
            qtd = str(log.get('quantidade_nova', '0'))
            
            pdf.cell(35, 8, data, 1)
            pdf.cell(35, 8, user, 1)
            pdf.cell(30, 8, "Alteracao", 1)
            pdf.cell(55, 8, subst, 1)
            pdf.cell(35, 8, qtd, 1, 1)

    return pdf.output(dest='S').encode('latin-1')

# --- FUNÇÃO PRINCIPAL (Mantendo a lógica de dias) ---
def executar_robo():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)
    
    # Mantendo sua lógica exata de tradução de dias
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
    print(f"Iniciando para: {dia_hoje_texto}")

    agendamentos = supabase.table("bot_scheduler")\
        .select("*")\
        .eq("ativo", True)\
        .eq("dia_semana", dia_hoje_texto)\
        .execute()

    if not agendamentos.data:
        print("Nenhum bot agendado para hoje.")
        return

    for ag in agendamentos.data:
        org = ag['org_name']
        print(f"Processando: {org}")
        
        # Coleta de dados
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        logs_data = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).limit(50).execute().data

        # 1. Excel (Mantido)
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            pd.DataFrame(estoque_data).to_excel(writer, index=False, sheet_name='Estoque')
            pd.DataFrame(equip_data).to_excel(writer, index=False, sheet_name='Equipamentos')
        excel_bytes = excel_buffer.getvalue()
        
        # 2. PDF (Agora colorido via função atualizada)
        pdf_bytes = gerar_pdf_completo(logs_data, estoque_data, org)

        # 3. Gráfico (NOVIDADE)
        grafico_bytes = gerar_grafico_tendencia(estoque_data)

        # E-mail
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"🧪 Relatorio Completo: {org} ({dia_hoje_texto})"

        corpo_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #2c3e50; color: white; padding: 20px;">
                <h2>Relatório de Auditoria: {org}</h2>
            </div>
            <div style="padding: 20px;">
                <p>Olá,</p>
                <p>Seu relatório semanal foi gerado com novas métricas de segurança.</p>
                <ul>
                    <li><strong>PDF:</strong> Agora com alertas de cor (Vermelho = Crítico).</li>
                    <li><strong>Gráfico:</strong> Visualização rápida do top 5 estoque (anexo).</li>
                    <li><strong>Excel:</strong> Base completa.</li>
                </ul>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        # Anexar Arquivos (Adicionado o Gráfico na lista)
        anexos = [
            (excel_bytes, f"Dados_{org}.xlsx"),
            (pdf_bytes, f"Auditoria_{org}.pdf"),
            (grafico_bytes, f"Grafico_Stock_{org}.png") # Novo anexo
        ]

        for content, name in anexos:
            if content: # Proteção caso o gráfico falhe e venha None
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
            print(f"❌ Erro envio {org}: {e}")

if __name__ == "__main__":
    executar_robo()

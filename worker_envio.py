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

# --- FUNÇÃO PARA GERAR O PDF BONITO ---
def gerar_pdf_completo(logs, estoque, org_name):
    pdf = FPDF()
    pdf.add_page()
    
    # Cabeçalho Estilizado
    pdf.set_fill_color(41, 128, 185) # Azul Profissional
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(190, 15, f"RELATÓRIO DE AUDITORIA - {org_name.upper()}", ln=True, align='C', fill=True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.cell(190, 10, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", ln=True, align='R')
    pdf.ln(5)

    # Seção 1: Resumo do Estoque Atual
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "1. Resumo de Itens em Estoque", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(190, 7, f"Atualmente, a organização {org_name} possui {len(estoque)} itens ativos cadastrados no sistema.")
    pdf.ln(5)

    # Seção 2: Histórico de Alterações (Tabela de Logs)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(190, 10, "2. Registro Detalhado de Movimentações", ln=True)
    
    # Cabeçalho da Tabela
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(35, 8, "Data/Hora", 1, 0, 'C', True)
    pdf.cell(35, 8, "Usuário", 1, 0, 'C', True)
    pdf.cell(30, 8, "Ação", 1, 0, 'C', True) 
    pdf.cell(55, 8, "Item/Substância", 1, 0, 'C', True) # Nome ajustado para cobrir ambos
    pdf.cell(35, 8, "Qtd/Status", 1, 1, 'C', True)

    # Dados dos Logs
    pdf.set_font("Arial", size=8)
    if not logs:
        pdf.cell(190, 10, "Nenhuma movimentação registrada no período.", 1, 1, 'C')
    else:
        for log in logs:
            data = log['created_at'][:16].replace('T', ' ')
            pdf.cell(35, 8, data, 1)
            pdf.cell(35, 8, str(log.get('usuario', 'N/A'))[:18], 1)
            pdf.cell(30, 8, "Alteração", 1) 
            pdf.cell(55, 8, str(log.get('substancia', 'N/A'))[:25], 1)
            pdf.cell(35, 8, str(log.get('quantidade_nova', '0')), 1, 1)

    pdf.ln(10)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(190, 10, "Este relatório é gerado automaticamente pelo Sistema de Laboratórios Inteligentes.", align='C')
    
    return pdf.output(dest='S')

# --- FUNÇÃO PRINCIPAL ---
def executar_robo():
    supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_KEY"))
    
    # Busca os agendamentos ativos
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute()

    for ag in agendamentos.data:
        org = ag['org_name']
        
        # Coleta dados das duas tabelas para o Excel
        estoque_data = supabase.table("substancias").select("*").eq("org_name", org).execute().data
        equip_data = supabase.table("equipamentos").select("*").eq("org_name", org).execute().data
        
        # Conexão com a tabela de logs (Puxa tudo: Substâncias e Equipamentos)
        logs_data = supabase.table("logs_estoque").select("*").eq("org_name", org).order('created_at', desc=True).limit(50).execute().data

        # Prepara o arquivo EXCEL COM DUAS ABAS
        df_estoque = pd.DataFrame(estoque_data)
        df_equip = pd.DataFrame(equip_data)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df_estoque.to_excel(writer, index=False, sheet_name='Substâncias')
            df_equip.to_excel(writer, index=False, sheet_name='Equipamentos')
        
        # PDF foca no resumo das substâncias (conforme seu original) mas traz logs de tudo
        pdf_bytes = gerar_pdf_completo(logs_data, estoque_data, org)

        # Montagem do E-mail HTML (Bonito - Exatamente seu original)
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
                <p>Segue em anexo o relatório completo do seu laboratório referente às últimas atividades detectadas no sistema.</p>
                <ul>
                    <li><strong>Arquivo PDF:</strong> Histórico detalhado de quem alterou, retirou ou cadastrou itens (Substâncias e Equipamentos).</li>
                    <li><strong>Arquivo Excel:</strong> Planilha com abas separadas para Estoque e Equipamentos atualizados.</li>
                </ul>
                <p>Caso precise de suporte, entre em contato com a administração do sistema.</p>
                <br>
                <p style="font-size: 12px; color: #777;">Este é um e-mail automático. Por favor, não responda.</p>
            </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, 'html'))

        # Anexos
        for content, name, mime in [(excel_buffer.getvalue(), f"Inventario_Completo_{org}.xlsx", "application/vnd.ms-excel"), 
                                    (pdf_bytes, f"Auditoria_{org}.pdf", "application/pdf")]:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{name}"')
            msg.attach(part)

        # Disparo
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(ag['smtp_user'], ag['smtp_pass'])
                server.send_message(msg)
                print(f"✅ Relatório Completo enviado para {org}!")
        except Exception as e:
            print(f"❌ Erro ao enviar para {org}: {e}")

if __name__ == "__main__":
    executar_robo()

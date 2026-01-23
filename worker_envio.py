import os
import pandas as pd
from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import io

def executar_robo():
    # 1. Conecta usando as chaves que você acabou de configurar no GitHub
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 2. Busca na tabela bot_scheduler QUEM deve receber o e-mail
    res_agendamentos = supabase.table("bot_scheduler").select("*").execute()
    
    if not res_agendamentos.data:
        print("Nenhum agendamento encontrado.")
        return

    for ag in res_agendamentos.data:
        org = ag['org_name']
        print(f"📦 Gerando relatório para {org}...")

        # 3. BUSCA OS DADOS REAIS DO LABORATÓRIO (A conexão mágica)
        res_dados = supabase.table("substancias").select("*").eq("org_name", org).execute()
        df = pd.DataFrame(res_dados.data)

        # 4. CRIA O EXCEL EM MEMÓRIA
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Inventário', index=False)
        
        # 5. CONFIGURA O E-MAIL COM O ANEXO
        msg = MIMEMultipart()
        msg['From'] = ag['smtp_user']
        msg['To'] = ag['email_destino']
        msg['Subject'] = f"🧪 Relatório de Auditoria Inteligente - {org}"
        
        corpo = f"Olá,\n\nSegue em anexo o relatório de estoque atualizado para a organização {org}.\n\nEste é um envio automático agendado para as quintas-feiras."
        msg.attach(MIMEText(corpo, 'plain'))

        # Anexando o arquivo
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(excel_buffer.getvalue())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="Relatorio_{org}.xlsx"')
        msg.attach(part)

        # 6. DISPARA O E-MAIL USANDO O SMTP QUE VOCÊ SALVOU NO STREAMLIT
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(ag['smtp_user'], ag['smtp_pass'])
                server.send_message(msg)
                print(f"✅ E-mail com anexo enviado para {ag['email_destino']}")
        except Exception as e:
            print(f"❌ Erro ao enviar e-mail para {org}: {e}")

if __name__ == "__main__":
    executar_robo()

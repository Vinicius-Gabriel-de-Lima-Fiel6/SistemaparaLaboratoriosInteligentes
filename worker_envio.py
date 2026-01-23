import os
import pandas as pd
from supabase import create_client
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def executar_robo():
    # Pega as chaves dos Secrets do GitHub
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Chaves de ambiente não encontradas!")
        return
        
    supabase = create_client(url, key)

    # LENDO A TABELA NOVA (A que não tem erro de RLS)
    try:
        res = supabase.table("bot_scheduler").select("*").execute()
        agendamentos = res.data
    except Exception as e:
        print(f"❌ Erro ao acessar a tabela bot_scheduler: {e}")
        return

    if not agendamentos:
        print("ℹ️ Nenhuma configuração encontrada na bot_scheduler.")
        return

    for ag in agendamentos:
        print(f"📧 Enviando para: {ag['email_destino']}...")
        try:
            msg = MIMEMultipart()
            msg['From'] = ag['smtp_user']
            msg['To'] = ag['email_destino']
            msg['Subject'] = f"🧪 Relatório Automático - {ag['org_name']}"
            
            corpo = f"Relatório agendado para {ag['dia_semana']} às {ag['horario']}."
            msg.attach(MIMEText(corpo, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(ag['smtp_user'], ag['smtp_pass'])
            server.send_message(msg)
            server.quit()
            print(f"✅ E-mail enviado com sucesso!")
        except Exception as e:
            print(f"❌ Erro no SMTP: {e}")

if __name__ == "__main__":
    executar_robo()

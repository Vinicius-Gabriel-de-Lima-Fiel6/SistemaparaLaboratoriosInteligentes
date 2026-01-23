import os
import pandas as pd
from supabase import create_client
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import io

def executar_robo():
    # Conecta ao banco
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    supabase = create_client(url, key)

    # 1. Busca quem agendou para hoje
    # Nota: Em Python, Thursday = Quinta-feira
    agendamentos = supabase.table("bot_scheduler").select("*").eq("ativo", True).execute().data

    for ag in agendamentos:
        print(f"Verificando agendamento para {ag['org_name']}...")
        
        # Envio de e-mail simples para teste
        try:
            msg = MIMEMultipart()
            msg['From'] = ag['smtp_user']
            msg['To'] = ag['email_destino']
            msg['Subject'] = f"🧪 Relatório LabSmartAI - {ag['org_name']}"
            
            corpo = f"Relatório automático disparado para {ag['dia_semana']} às {ag['horario']}"
            msg.attach(MIMEText(corpo, 'plain'))

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(ag['smtp_user'], ag['smtp_pass'])
            server.send_message(msg)
            server.quit()
            print(f"✅ E-mail enviado para {ag['email_destino']}")
        except Exception as e:
            print(f"❌ Erro ao enviar: {e}")

if __name__ == "__main__":
    executar_robo()

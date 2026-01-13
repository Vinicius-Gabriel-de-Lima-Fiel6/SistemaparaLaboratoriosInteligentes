import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
import datetime


def conectar_supabase():

    import streamlit as st 
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def processar_relatorio_por_empresa(org_name):
    supabase = conectar_supabase()
    
  

    users = supabase.table("usuarios").select("*").eq("org_name", org_name).execute().data

 
    logs = supabase.table("logs_estoque").select("*").eq("org_name", org_name).order("created_at", desc=True).limit(20).execute().data
    
  
    estoque = supabase.table("substancias").select("*").eq("org_name", org_name).execute().data
    itens_criticos = [i for i in estoque if i['quantidade'] <= i.get('estoque_minimo', 0)]
  
    equips = supabase.table("equipamentos").select("*").eq("org_name", org_name).execute().data
    pendentes = [e for e in equips if e['status'] != 'Operacional']

    # --- MONTAGEM DO CORPO DO RELATÓRIO ---
    corpo = f"<h2>📊 Relatório Absoluto: {org_name}</h2><hr>"
    
    corpo += f"<h3>👥 Tráfego de Equipe</h3><p>Total de colaboradores ativos: {len(users)}</p>"
    
    corpo += "<h3>⚠️ Alertas de Inventário</h3><ul>"
    for item in itens_criticos:
        corpo += f"<li><strong>{item['nome']}</strong>: Apenas {item['quantidade']} restando.</li>"
    corpo += "</ul>" if itens_criticos else "<p>✅ Estoque em dia.</p>"

    corpo += "<h3>🔄 Últimas Alterações no Sistema</h3><ul>"
    for l in logs:
        corpo += f"<li>{l['usuario']} alterou {l['substancia']} (Para: {l['quantidade_nova']})</li>"
    corpo += "</ul>"

    corpo += f"<h3>🛠️ Equipamentos</h3><p>{len(pendentes)} equipamentos aguardando manutenção.</p>"

    return corpo

def disparar_email_final(config, html_content):
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 Inteligência de Dados - {config['org_name']}"
    msg['From'] = config['smtp_user']
    msg['To'] = config['email_destino']
    msg.attach(MIMEText(html_content, 'html'))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config['smtp_user'], config['smtp_pass'])
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Erro no disparo: {e}")
        return False


def rodar_bot_completo():
    supabase = conectar_supabase()

    agendamentos = supabase.table("config_automacao").select("*").execute().data
    
    for ag in agendamentos:
        conteudo = processar_relatorio_por_empresa(ag['org_name'])
        disparar_email_final(ag, conteudo)

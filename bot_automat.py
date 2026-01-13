import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
import datetime

def conectar_supabase(st):
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def processar_relatorio_por_empresa(org_name, st):
    supabase = conectar_supabase(st)
    
    # Coleta de todas as tabelas para o relatório completo
    logs = supabase.table("logs_estoque").select("*").eq("org_name", org_name).order("created_at", desc=True).limit(10).execute().data
    estoque = supabase.table("substancias").select("*").eq("org_name", org_name).execute().data
    equips = supabase.table("equipamentos").select("*").eq("org_name", org_name).execute().data
    
    criticos = [i for i in estoque if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]
    manutencao = [e for e in equips if e.get('status') != 'Operacional']

    corpo = f"""
    <div style="font-family: sans-serif; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
        <h2 style="color: #1E3A8A;">Relatório de Inteligência - {org_name}</h2>
        <hr>
        <h3 style="color: #B91C1C;">Alertas de Estoque</h3>
        <ul>{''.join([f"<li>{i['nome']}: {i['quantidade']}</li>" for i in criticos]) if criticos else "<li>✅ Estoque em dia</li>"}</ul>
        <h3 style="color: #1E40AF;">Atividade Recente</h3>
        <ul>{''.join([f"<li>{l.get('usuario')}: {l.get('substancia')}</li>" for l in logs]) if logs else "<li>Sem movimentações recentes.</li>"}</ul>
        <h3 style="color: #03543F;">Status de Equipamentos</h3>
        <p>Ativos em manutenção: {len(manutencao)} de um total de {len(equips)}.</p>
    </div>
    """
    return corpo

def disparar_email_manual(config, st):
    html_content = processar_relatorio_por_empresa(config['org_name'], st)
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 Inteligência de Dados - {config['org_name']}"
    msg['From'] = config['smtp_user']
    msg['To'] = config['email_destino']
    msg.attach(MIMEText(html_content, 'html'))

    try:
        lista = [e.strip() for e in config['email_destino'].split(",")]
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config['smtp_user'], config['smtp_pass'])
            server.sendmail(config['smtp_user'], lista, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erro SMTP: {e}")
        return False

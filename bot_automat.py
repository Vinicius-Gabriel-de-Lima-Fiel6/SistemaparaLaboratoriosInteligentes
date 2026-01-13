import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
import datetime

def conectar_supabase(st):

    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def processar_relatorio_por_empresa(org_name, st):
    """Gera o HTML do relatório com dados filtrados por empresa"""
    supabase = conectar_supabase(st)
    
    # 1. Busca Movimentações (Logs)
    try:
        logs = supabase.table("logs_estoque").select("*").eq("org_name", org_name).order("created_at", desc=True).limit(10).execute().data
    except:
        logs = []
    
    # 2. Busca Estoque Crítico
    try:
        estoque = supabase.table("substancias").select("*").eq("org_name", org_name).execute().data
        itens_criticos = [i for i in estoque if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]
    except:
        itens_criticos = []
    
    # 3. Busca Equipamentos
    try:
        equips = supabase.table("equipamentos").select("*").eq("org_name", org_name).execute().data
        pendentes = [e for e in equips if e.get('status') != 'Operacional']
    except:
        pendentes = []

    # Construção do HTML
    corpo = f"""
    <div style="font-family: sans-serif; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        <h2 style="color: #1E3A8A;">📊 Relatório de Inteligência: {org_name}</h2>
        <hr>
        <p><b>Data:</b> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <h3 style="color: #B91C1C;">⚠️ Alertas de Estoque Crítico</h3>
        <ul>
            {''.join([f"<li>{i['nome']}: {i['quantidade']} unidades (Mín: {i['estoque_minimo']})</li>" for i in itens_criticos]) if itens_criticos else "<li>✅ Todos os itens com estoque em dia.</li>"}
        </ul>

        <h3 style="color: #1E40AF;">🔄 Últimas Movimentações</h3>
        <ul>
            {''.join([f"<li>{l.get('usuario', 'Sistema')}: {l.get('substancia', 'Item')} ({l.get('tipo_operacao', 'Alteração')})</li>" for l in logs]) if logs else "<li>Nenhuma movimentação recente.</li>"}
        </ul>

        <h3 style="color: #03543F;">🛠️ Equipamentos</h3>
        <p>Existem {len(pendentes)} equipamentos fora do status operacional.</p>
    </div>
    """
    return corpo

def disparar_email_manual(config, st):
    """Executa o envio para múltiplos destinatários"""
    if not config.get('smtp_user') or not config.get('smtp_pass'):
        st.error("Erro: Credenciais SMTP não configuradas.")
        return False

    destinatarios_str = config.get('email_destino', "")
    if not destinatarios_str:
        st.warning("Aviso: Nenhum receptor selecionado.")
        return False

    html_content = processar_relatorio_por_empresa(config['org_name'], st)
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 Relatório Automatizado - {config['org_name']}"
    msg['From'] = config['smtp_user']
    msg['To'] = destinatarios_str
    msg.attach(MIMEText(html_content, 'html'))

    try:
  
        lista_emails = [e.strip() for e in destinatarios_str.split(",") if e.strip()]
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config['smtp_user'], config['smtp_pass'])
            server.sendmail(config['smtp_user'], lista_emails, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Falha no envio SMTP: {e}")
        return False

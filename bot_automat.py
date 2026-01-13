import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
import datetime

# Função de conexão usando as secrets do Streamlit
def conectar_supabase(st):
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def processar_relatorio_por_empresa(org_name, st):
    supabase = conectar_supabase(st)
    
    # 1. Busca usuários da empresa específica
    users = supabase.table("users").select("*").eq("org_name", org_name).execute().data
    
    # 2. Busca movimentações recentes (logs_estoque)
    logs = supabase.table("logs_estoque").select("*").eq("org_name", org_name).order("created_at", desc=True).limit(10).execute().data
    
    # 3. Busca estoque crítico (substancias)
    estoque = supabase.table("substancias").select("*").eq("org_name", org_name).execute().data
    itens_criticos = [i for i in estoque if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]
    
    # 4. Equipamentos com problema
    equips = supabase.table("equipamentos").select("*").eq("org_name", org_name).execute().data
    pendentes = [e for e in equips if e.get('status') != 'Operacional']

    # Montagem do HTML do Relatório
    corpo = f"""
    <div style="font-family: sans-serif; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
        <h2 style="color: #1E3A8A;">📊 Relatório de Inteligência: {org_name}</h2>
        <hr>
        <p><b>Data:</b> {datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <h3 style="color: #B91C1C;">⚠️ Alertas de Estoque</h3>
        <ul>
            {''.join([f"<li>{i['nome']}: {i['quantidade']} unidades</li>" for i in itens_criticos]) if itens_criticos else "<li>✅ Estoque regularizado.</li>"}
        </ul>

        <h3 style="color: #1E40AF;">🔄 Atividade Recente</h3>
        <ul>
            {''.join([f"<li>{l.get('usuario', 'Sistema')}: {l.get('substancia', 'Item')} -> {l.get('quantidade_nova', 'Alterado')}</li>" for l in logs]) if logs else "<li>Nenhuma movimentação registrada.</li>"}
        </ul>

        <h3 style="color: #03543F;">🛠️ Status de Equipamentos</h3>
        <p>{len(pendentes)} equipamentos necessitam de atenção.</p>
    </div>
    """
    return corpo

def disparar_email_manual(config, st):
    # Verifica se as configurações básicas existem
    if not config.get('smtp_user') or not config.get('smtp_pass'):
        return False

    html_content = processar_relatorio_por_empresa(config['org_name'], st)
    
    msg = MIMEMultipart()
    msg['Subject'] = f"🚀 Inteligência de Dados - {config['org_name']}"
    msg['From'] = config['smtp_user']
    msg['To'] = config['email_destino']
    msg.attach(MIMEText(html_content, 'html'))

    try:
        # Configuração para Gmail (padrão)
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config['smtp_user'], config['smtp_pass'])
            server.send_message(msg)
        return True
    except Exception as e:
        # Mostra o erro no console do Streamlit para debug
        st.error(f"Erro de Conexão SMTP: {e}")
        return False

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client
import datetime

def conectar_supabase(st):
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def processar_relatorio_por_empresa(org_name, st):
    supabase = conectar_supabase(st)
    
    # --- COLETA TOTAL DE DADOS ---
    try:
        # 1. Equipe
        users = supabase.table("users").select("*").eq("org_name", org_name).execute().data
        # 2. Movimentações Recentes
        logs = supabase.table("logs_estoque").select("*").eq("org_name", org_name).order("created_at", desc=True).limit(15).execute().data
        # 3. Estoque Completo
        estoque = supabase.table("substancias").select("*").eq("org_name", org_name).execute().data
        itens_criticos = [i for i in estoque if i.get('quantidade', 0) <= i.get('estoque_minimo', 0)]
        # 4. Equipamentos
        equips = supabase.table("equipamentos").select("*").eq("org_name", org_name).execute().data
        manutencao = [e for e in equips if e.get('status') != 'Operacional']
    except Exception as e:
        return f"<h2>Erro ao processar dados: {e}</h2>"

    # --- MONTAGEM DO CORPO DO RELATÓRIO ---
    corpo = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto; border: 1px solid #eee; padding: 20px; border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <div style="text-align: center; border-bottom: 2px solid #1E3A8A; padding-bottom: 10px;">
            <h1 style="color: #1E3A8A; margin: 0;">Relatório Executivo</h1>
            <p style="color: #666;">{org_name} | {datetime.datetime.now().strftime('%d/%m/%Y')}</p>
        </div>

        <h3 style="color: #B91C1C; border-left: 4px solid #B91C1C; padding-left: 10px; margin-top: 25px;">⚠️ Alertas de Estoque Crítico</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="background: #f8f8f8;">
                <th style="text-align: left; padding: 8px;">Item</th>
                <th style="text-align: right; padding: 8px;">Qtd Atual</th>
            </tr>
            {''.join([f"<tr><td style='padding: 8px; border-bottom: 1px solid #eee;'>{i['nome']}</td><td style='padding: 8px; border-bottom: 1px solid #eee; text-align: right; color: red;'>{i['quantidade']}</td></tr>" for i in itens_criticos]) if itens_criticos else "<tr><td colspan='2' style='padding: 8px;'>✅ Tudo regularizado.</td></tr>"}
        </table>

        <h3 style="color: #1E40AF; border-left: 4px solid #1E40AF; padding-left: 10px; margin-top: 25px;">🔄 Resumo de Movimentações</h3>
        <ul style="list-style: none; padding: 0;">
            {''.join([f"<li style='padding: 5px 0; border-bottom: 1px dotted #ccc; font-size: 0.9em;'><b>{l.get('usuario', 'Sist.')}:</b> {l.get('substancia', 'Item')} ({l.get('tipo_operacao', 'Alt.')})</li>" for l in logs]) if logs else "<li>Sem atividades recentes.</li>"}
        </ul>

        <h3 style="color: #03543F; border-left: 4px solid #03543F; padding-left: 10px; margin-top: 25px;">🛠️ Infraestrutura</h3>
        <p style="font-size: 0.9em;"><b>Equipamentos em manutenção:</b> {len(manutencao)}<br>
        <b>Total de ativos monitorados:</b> {len(equips)}</p>

        <div style="margin-top: 30px; padding: 15px; background: #F3F4F6; border-radius: 8px; text-align: center; font-size: 0.8em; color: #555;">
            Este é um relatório gerado automaticamente pelo Sistema Absolute.
        </div>
    </div>
    """
    return corpo

def disparar_email_manual(config, st):
    if not config.get('smtp_user') or not config.get('smtp_pass'):
        st.error("Credenciais SMTP faltando.")
        return False
    
    destinatarios = config.get('email_destino', "")
    if not destinatarios:
        st.warning("Nenhum destinatário definido.")
        return False

    html_content = processar_relatorio_por_empresa(config['org_name'], st)
    
    msg = MIMEMultipart()
    msg['Subject'] = f"📊 Relatório Completo - {config['org_name']}"
    msg['From'] = config['smtp_user']
    msg['To'] = destinatarios
    msg.attach(MIMEText(html_content, 'html'))

    try:
        lista_envio = [e.strip() for e in destinatarios.split(",") if e.strip()]
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(config['smtp_user'], config['smtp_pass'])
            server.sendmail(config['smtp_user'], lista_envio, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erro SMTP: {e}")
        return False

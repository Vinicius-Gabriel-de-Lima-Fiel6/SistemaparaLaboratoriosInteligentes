import streamlit as st
import serial
import pandas as pd
import time
from datetime import datetime

# Configuração da Página
st.set_page_config(page_title="LabControl V10 - Dashboard", layout="wide")

st.title("🔬 Monitoramento de Laboratório de Pesquisa")
st.markdown("---")

# --- CONEXÃO SERIAL ---
# Nota: Substitua 'COM3' pela porta onde seu Arduino estiver conectado
@st.cache_resource
def conectar_arduino():
    try:
        return serial.Serial('COM3', 9600, timeout=1)
    except:
        return None

arduino = conectar_arduino()

# --- ESTADO DO SISTEMA (Session State) ---
if 'dados' not in st.session_state:
    st.session_state.dados = pd.DataFrame(columns=["Tempo", "Temp", "pH", "Turbidez", "Gas", "Distancia"])

# --- INTERFACE: COLUNA LATERAL (CONTROLES) ---
with st.sidebar:
    st.header("⚙️ Controles do Sistema")
    if arduino:
        st.success("Arduino Conectado!")
    else:
        st.error("Arduino não detectado.")
        
    if st.button("🚨 DESLIGAR SISTEMA FÍSICO", type="primary"):
        if arduino:
            arduino.write(b'X') # Envia o caractere de parada
            st.warning("Comando de Emergência enviado!")

    st.download_button(
        label="📥 Exportar Dados (CSV)",
        data=st.session_state.dados.to_csv(index=False),
        file_name=f"log_laboratorio_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

# --- CORPO PRINCIPAL: VISUALIZAÇÃO ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📟 Display do Sistema (LCD)")
    # Simulador do LCD 16x2
    lcd_placeholder = st.empty()
    
    st.subheader("📋 Porta Serial (Raw)")
    serial_placeholder = st.empty()

with col2:
    st.subheader("📈 Gráficos Dinâmicos")
    chart_placeholder = st.empty()

# --- LOOP DE ATUALIZAÇÃO EM TEMPO REAL ---
while True:
    if arduino and arduino.in_waiting > 0:
        linha = arduino.readline().decode('utf-8').strip()
        
        # Ignorar o cabeçalho se ele aparecer
        if "Tempo" not in linha:
            try:
                # Quebrar a linha CSV recebida
                valores = linha.split(',')
                if len(valores) >= 6:
                    nova_linha = {
                        "Tempo": datetime.now().strftime('%H:%M:%S'),
                        "Temp": float(valores[1]),
                        "pH": int(valores[2]),
                        "Turbidez": int(valores[3]),
                        "Gas": int(valores[4]),
                        "Distancia": int(valores[5])
                    }
                    
                    # Atualizar base de dados
                    st.session_state.dados = pd.concat([st.session_state.dados, pd.DataFrame([nova_linha])], ignore_index=True)
                    st.session_state.dados = st.session_state.dados.tail(20) # Manter apenas os últimos 20 pontos
                    
                    # Atualizar Gráfico
                    chart_placeholder.line_chart(st.session_state.dados.set_index("Tempo")[["Temp", "pH", "Gas"]])
                    
                    # Atualizar "LCD" Virtual
                    lcd_placeholder.info(f"TEMP: {valores[1]}°C | PH: {valores[2]}\n\nDIST: {valores[5]}cm | GAS: {valores[4]}")
                    
                    # Mostrar Log Serial
                    serial_placeholder.code(linha)
            except:
                pass
                
    time.sleep(0.1) # Frequência de atualização

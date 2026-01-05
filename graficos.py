import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import statistics
from scipy.interpolate import make_interp_spline
import webbrowser

def show_graficos():
    st.title("📊 Laboratório Gráfico Inteligente")

    # --- 1. LINKS EXTERNOS ---
    col_links = st.columns(4)
    with col_links[0]:
        if st.button("🌐 GeoGebra", use_container_width=True):
            webbrowser.open("https://www.geogebra.org/graphing")
    with col_links[1]:
        if st.button("🧠 WolframAlpha", use_container_width=True):
            webbrowser.open("https://www.wolframalpha.com/")
    with col_links[2]:
        if st.button("📈 Weibull", use_container_width=True):
            webbrowser.open("https://www-acsu-buffalo-edu.translate.goog/~adamcunn/probability/weibull.html")
    with col_links[3]:
        if st.button("💻 Matlab Web", use_container_width=True):
            webbrowser.open("https://matlab.mathworks.com/")

    st.divider()

    # --- 2. SELEÇÃO DO TIPO DE GRÁFICO ---
    tipo_grafico = st.selectbox(
        "Selecione a análise físico-química:",
        [
            "Solubilidade", "Titulação", "Calibração", "Dispersão", "Histograma",
            "UV-Vis", "Diagrama de Fases", "Cromatograma", "Barras", "Regressão Linear", 
            "Barras com Erro", "Cinética Química", "Arrhenius", "Michaelis-Menten", 
            "Lineweaver-Burk", "pKa Curve", "Isoterma Adsorção", "Capacidade Térmica", 
            "RMN Spectrum", "Mass Spectrum", "TGA", "Adsorção Cinética", "Polarização"
        ]
    )

    # --- 3. INPUTS DINÂMICOS (Na Barra Lateral) ---
    inputs = {}
    with st.sidebar.expander("📝 Configurar Dados", expanded=True):
        if tipo_grafico == "Solubilidade":
            inputs['name'] = st.text_input("Composto", "NaCl")
            inputs['x'] = st.text_input("Temperaturas (K)", "273, 298, 323, 348")
            inputs['y'] = st.text_input("Solubilidade (g/100g H2O)", "35.7, 36.0, 36.3, 37.0")
        
        elif tipo_grafico == "Barras" or tipo_grafico == "Barras com Erro":
            inputs['x_label'] = st.text_input("Categorias (Nomes)", "A, B, C")
            inputs['y'] = st.text_input("Valores numéricos", "10, 20, 15")
        
        else:
            # Padrão para os demais gráficos (X e Y numéricos)
            inputs['x'] = st.text_input("Eixo X (Valores separados por vírgula)", "")
            inputs['y'] = st.text_input("Eixo Y (Valores separados por vírgula)", "")

    # --- 4. LÓGICA DE PLOTAGEM COM AJUSTE DE ERRO ---
    try:
        # Trava 1: Verifica se os campos estão vazios
        if (tipo_grafico != "Histograma" and (not inputs.get('x') or not inputs.get('y'))) or \
           (tipo_grafico == "Histograma" and not inputs.get('x')):
            st.info("💡 Por favor, insira os dados na barra lateral para gerar o gráfico.")
            return # Sai da função sem tentar plotar

        # Trava 2: Conversão de strings para listas numéricas
        def parse_data(txt):
            return np.array([float(i.strip()) for i in txt.split(',') if i.strip()])

        # Processamento dos dados
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if "x" in inputs:
            x_data = parse_data(inputs['x'])
        if "y" in inputs:
            y_data = parse_data(inputs['y'])

        # Validação de dimensão
        if tipo_grafico not in ["Histograma", "Barras", "Barras com Erro"] and len(x_data) != len(y_data):
            st.warning("⚠️ Atenção: A quantidade de valores em X deve ser igual à de Y.")
            return

        # --- Execução dos Gráficos (Lógica Original Adaptada) ---
        if tipo_grafico == "Solubilidade":
            if len(x_data) >= 3:
                xs = np.linspace(x_data.min(), x_data.max(), 300)
                ys = make_interp_spline(x_data, y_data, k=2)(xs)
                ax.plot(xs, ys, label=inputs.get('name', 'Composto'), color='cyan', linewidth=2)
                ax.scatter(x_data, y_data, color='red')
            else:
                ax.plot(x_data, y_data, '-o')
            ax.set_ylabel("Solubilidade (g/100g H₂O)")

        elif tipo_grafico == "Regressão Linear":
            coef = np.polyfit(x_data, y_data, 1)
            f = np.poly1d(coef)
            ax.scatter(x_data, y_data, color='magenta', label='Dados')
            ax.plot(x_data, f(x_data), '--', color='red', label=f'y={coef[0]:.2f}x + {coef[1]:.2f}')

        elif tipo_grafico == "Histograma":
            ax.hist(x_data, bins='auto', color='orange', edgecolor='black')

        elif tipo_grafico == "Barras":
            cats = inputs['x_label'].split(',')
            ax.bar(cats, y_data, color='skyblue')

        # Fallback para todos os outros (X, Y lineares)
        else:
            ax.plot(x_data, y_data, '-o', label=tipo_grafico, markersize=8)

        # Estilização Geral (Padrão LabSmart)
        ax.set_title(f"Gráfico: {tipo_grafico}", fontsize=16, fontweight='bold')
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.legend()
        
        # Exibe no Streamlit
        st.pyplot(fig)

    except ValueError:
        st.error("❌ Erro de Formato: Certifique-se de usar apenas números e vírgulas.")
    except Exception as e:
        st.error(f"⚠️ Erro ao processar gráfico: {e}")
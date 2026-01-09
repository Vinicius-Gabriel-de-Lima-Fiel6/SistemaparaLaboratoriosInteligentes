import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
from sklearn.metrics import r2_score
import io

def show_graficos():
    st.title("📊 Laboratório Gráfico de Alta Precisão")

    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    # --- 1. CABEÇALHO TÉCNICO ---
    with st.expander("🌐 Ecossistema de Recursos Científicos", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.link_button("🌐 GeoGebra", "https://www.geogebra.org/graphing", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("📈 Weibull", "https://www-acsu-buffalo-edu.translate.goog/~adamcunn/probability/weibull.html", use_container_width=True)
        col4 = c4.link_button("💻 Matlab Web", "https://matlab.mathworks.com/", use_container_width=True)
        
        c5, c6, c7 = st.columns(3)
        c5.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/chemistry/", use_container_width=True)
        c6.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)
        c7.link_button("📚 IUPAC Gold", "https://goldbook.iupac.org/", use_container_width=True)

    st.divider()

    # --- 2. CONTROLE LATERAL (BIBLIOTECA EXPANDIDA) ---
    with st.sidebar:
        st.header("📥 Entrada de Dados")
        
        with st.container(border=True):
            tipo_grafico = st.selectbox(
                "Tipo de Gráfico / Análise:",
                [
                    "Linhas e Pontos", "Barras", "Dispersão (Scatter)", "Histograma",
                    "Solubilidade", "Titulação", "Calibração", "UV-Vis", "Cromatograma",
                    "Diagrama de Fases", "TGA (Degradação)", "RMN / Mass Spectrum",
                    "Regressão Linear (R²)", "Regressão Polinomial", "Suavização Savitzky-Golay", 
                    "Spline Cubic (Suave)", "Cinética Química", "Arrhenius", 
                    "Michaelis-Menten", "Isoterma de Adsorção", "Capacidade Térmica"
                ]
            )
            nome = st.text_input("ID da Amostra", f"Amostra_{len(st.session_state.series_graficas)+1}")
            in_x = st.text_input("Eixo X (Valores)", "10, 20, 30, 40")
            in_y = st.text_input("Eixo Y (Valores)", "1.5, 2.8, 4.2, 5.9")
            cor = st.color_picker("Cor da Série", "#1f77b4") # Azul padrão científico
            nota = st.text_input("Nota no Ponto Máximo", "")

        col_add, col_reset = st.columns(2)
        if col_add.button("➕ Adicionar", use_container_width=True):
            try:
                x = np.array([float(i.strip()) for i in in_x.split(',') if i.strip()])
                y = np.array([float(i.strip()) for i in in_y.split(',') if i.strip()])
                if len(x) == len(y) or tipo_grafico == "Histograma":
                    st.session_state.series_graficas.append({
                        "nome": nome, "x": x, "y": y, "cor": cor, "tipo": tipo_grafico, "nota": nota
                    })
                    st.toast(f"Série {nome} integrada!")
                else:
                    st.error("X e Y devem ter o mesmo tamanho!")
            except:
                st.error("Erro no formato. Use números separados por vírgula.")

        if col_reset.button("🗑️ Limpar Workspace", use_container_width=True):
            st.session_state.series_graficas = []
            st.rerun()

    # --- 3. RENDERIZAÇÃO INTERATIVA (TEMA BRANCO) ---
    if not st.session_state.series_graficas:
        st.info("💡 Selecione o modelo químico/matemático e adicione os dados para começar.")
    else:
        fig = go.Figure()

        for s in st.session_state.series_graficas:
            x, y = s['x'], s['y']
            
            if s['tipo'] == "Regressão Linear (R²)":
                coef = np.polyfit(x, y, 1)
                p = np.poly1d(coef)
                r2 = r2_score(y, p(x))
                fig.add_trace(go.Scatter(x=x, y=p(x), mode='lines', name=f"{s['nome']} (R²:{r2:.3f})", line=dict(color=s['cor'], dash='dash')))
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name=s['nome'], marker=dict(color=s['cor'])))

            elif s['tipo'] in ["Spline Cubic (Suave)", "Solubilidade", "Cinética Química"]:
                x_new = np.linspace(x.min(), x.max(), 300)
                spl = make_interp_spline(x, y, k=3)
                fig.add_trace(go.Scatter(x=x_new, y=spl(x_new), mode='lines', name=s['nome'], line=dict(color=s['cor'], width=2.5)))
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name=f"{s['nome']} (Pontos)", marker=dict(color=s['cor'])))

            elif s['tipo'] == "Suavização Savitzky-Golay":
                window = 5 if len(y) > 5 else 3
                y_smooth = savgol_filter(y, window, 2)
                fig.add_trace(go.Scatter(x=x, y=y_smooth, mode='lines+markers', name=f"{s['nome']} (Filtrado)", line=dict(color=s['cor'])))

            elif s['tipo'] == "Barras":
                fig.add_trace(go.Bar(x=x, y=y, name=s['nome'], marker_color=s['cor']))

            elif s['tipo'] == "Histograma":
                fig.add_trace(go.Histogram(x=x, name=s['nome'], marker_color=s['cor'], opacity=0.6))

            elif s['tipo'] in ["UV-Vis", "Cromatograma", "RMN / Mass Spectrum"]:
                fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=s['nome'], line=dict(color=s['cor'], width=1.5), fill='tozeroy'))

            else:
                fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=s['nome'], line=dict(color=s['cor'])))

            if s['nota']:
                ymax = np.max(y)
                xmax = x[np.argmax(y)]
                fig.add_annotation(x=xmax, y=ymax, text=s['nota'], showarrow=True, arrowhead=1, bgcolor=s['cor'], font=dict(color="white"))

        # CONFIGURAÇÃO DO TEMA BRANCO
        fig.update_layout(
            template="plotly_white", # Fundo branco padrão
            paper_bgcolor="white",
            plot_bgcolor="white",
            font=dict(color="#333333"),
            title=dict(text="Análise Multivariada", font=dict(size=20, color="black")),
            xaxis=dict(
                gridcolor="#eeeeee", 
                linecolor="#333", 
                title="Eixo X", 
                zerolinecolor="#ccc"
            ),
            yaxis=dict(
                gridcolor="#eeeeee", 
                linecolor="#333", 
                title="Eixo Y", 
                zerolinecolor="#ccc"
            ),
            hovermode="x unified",
            dragmode="pan",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displaylogo': False})

        # --- 4. EXPORTAÇÃO E ESTATÍSTICA ---
        st.markdown("---")
        c_exp, c_tab = st.columns([1, 2])
        with c_exp:
            st.subheader("📂 Saída de Dados")
            csv = pd.DataFrame([{"Série": s['nome'], "X": xi, "Y": yi} for s in st.session_state.series_graficas for xi, yi in zip(s['x'], s['y'])])
            st.download_button("📊 Exportar CSV", csv.to_csv(index=False).encode('utf-8'), "lab_export.csv", use_container_width=True)
        
        with c_tab:
            st.subheader("📉 Estatísticas")
            stats = [{"Amostra": s['nome'], "Média": f"{np.mean(s['y']):.2f}", "Máximo": np.max(s['y']), "D. Padrão": f"{np.std(s['y']):.2f}"} for s in st.session_state.series_graficas]
            st.dataframe(pd.DataFrame(stats), use_container_width=True)

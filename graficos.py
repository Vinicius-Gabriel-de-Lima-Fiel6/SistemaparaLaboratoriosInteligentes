import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
from sklearn.metrics import r2_score
import io

def show_graficos():
    st.title("📊 Estação Gráfica Dinâmica e Interativa")

    # Inicialização do container de memória
    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    # --- 1. CABEÇALHO TÉCNICO ---
    with st.expander("🔬 Recursos de Apoio", expanded=False):
        c1, c2, c3 = st.columns(3)
        c1.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/chemistry/", use_container_width=True)
        c2.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)
        c3.link_button("📚 IUPAC Gold", "https://goldbook.iupac.org/", use_container_width=True)

    st.divider()

    # --- 2. CONTROLE LATERAL (Input e Gestão) ---
    with st.sidebar:
        st.header("📥 Entrada de Dados")
        
        with st.container(border=True):
            tipo_ajuste = st.selectbox(
                "Modelo Matemático:",
                ["Padrão (Linhas e Pontos)", "Regressão Linear", "Suavização (Savitzky-Golay)", "Spline Cubic"]
            )
            nome = st.text_input("ID da Amostra", f"Amostra_{len(st.session_state.series_graficas)+1}")
            in_x = st.text_input("Eixo X (Valores)", "0, 5, 10, 15, 20, 25")
            in_y = st.text_input("Eixo Y (Valores)", "1.5, 3.2, 7.8, 12.1, 19.5, 28.3")
            cor = st.color_picker("Cor da Série", "#00F2FF")
            nota = st.text_input("Anotação de Ponto", "")

        col_add, col_reset = st.columns(2)
        if col_add.button("➕ Adicionar", use_container_width=True):
            try:
                x = np.array([float(i.strip()) for i in in_x.split(',') if i.strip()])
                y = np.array([float(i.strip()) for i in in_y.split(',') if i.strip()])
                if len(x) == len(y):
                    st.session_state.series_graficas.append({
                        "nome": nome, "x": x, "y": y, "cor": cor, "tipo": tipo_ajuste, "nota": nota
                    })
                    st.toast(f"Série {nome} integrada!")
                else:
                    st.error("X e Y incompatíveis.")
            except:
                st.error("Use apenas números e vírgulas.")

        if col_reset.button("🗑️ Limpar Tudo", use_container_width=True):
            st.session_state.series_graficas = []
            st.rerun()

        # Gestão de Séries Individuais
        if st.session_state.series_graficas:
            st.markdown("---")
            st.subheader("📋 Séries Ativas")
            for i, s in enumerate(st.session_state.series_graficas):
                if st.button(f"Remover {s['nome']}", key=f"del_{i}", use_container_width=True):
                    st.session_state.series_graficas.pop(i)
                    st.rerun()

    # --- 3. RENDERIZAÇÃO INTERATIVA (PLOTLY) ---
    if not st.session_state.series_graficas:
        st.info("💡 Arraste e explore seus dados: Adicione uma série no menu lateral para começar.")
    else:
        # Criamos a figura do Plotly
        fig = go.Figure()

        for s in st.session_state.series_graficas:
            x, y = s['x'], s['y']
            
            # --- Lógica de Modelagem ---
            if s['tipo'] == "Regressão Linear":
                coef = np.polyfit(x, y, 1)
                p = np.poly1d(coef)
                r2 = r2_score(y, p(x))
                # Linha de tendência
                fig.add_trace(go.Scatter(x=x, y=p(x), mode='lines', name=f"{s['nome']} (R²:{r2:.3f})", 
                                         line=dict(color=s['cor'], dash='dash')))
                # Pontos originais
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name=f"{s['nome']} (Dados)", 
                                         marker=dict(color=s['cor'], size=10), text=s['nota']))

            elif s['tipo'] == "Suavização (Savitzky-Golay)":
                window = 5 if len(y) > 5 else 3
                y_smooth = savgol_filter(y, window, 2)
                fig.add_trace(go.Scatter(x=x, y=y_smooth, mode='lines+markers', name=s['nome'], 
                                         line=dict(color=s['cor'], width=3), text=s['nota']))

            elif s['tipo'] == "Spline Cubic" and len(x) > 3:
                x_new = np.linspace(x.min(), x.max(), 200)
                spl = make_interp_spline(x, y, k=3)
                fig.add_trace(go.Scatter(x=x_new, y=spl(x_new), mode='lines', name=s['nome'], 
                                         line=dict(color=s['cor'], width=2), text=s['nota']))
                fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name=f"{s['nome']} (Pontos)", 
                                         marker=dict(color=s['cor'])))

            else: # Padrão
                fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=s['nome'], 
                                         line=dict(color=s['cor']), marker=dict(size=8), text=s['nota']))

        # Configuração de Layout para Interatividade Máxima
        fig.update_layout(
            title="Análise Multivariada Interativa",
            template="plotly_dark",
            paper_bgcolor="#0E1117",
            plot_bgcolor="#161B22",
            xaxis=dict(title="Eixo X", gridcolor="#333", zerolinecolor="#444"),
            yaxis=dict(title="Eixo Y", gridcolor="#333", zerolinecolor="#444"),
            hovermode="x unified", # Mostra todos os valores de Y para um mesmo X ao passar o mouse
            dragmode="pan", # Permite o arraste por padrão
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        # Exibe o gráfico interativo
        st.plotly_chart(fig, use_container_width=True, config={'scrollZoom': True, 'displaylogo': False})

        # --- 4. EXPORTAÇÃO E ESTATÍSTICA ---
        st.markdown("---")
        c_exp, c_tab = st.columns([1, 2])
        
        with c_exp:
            st.subheader("📂 Saída")
            csv = pd.DataFrame([{"Série": s['nome'], "X": xi, "Y": yi} for s in st.session_state.series_graficas for xi, yi in zip(s['x'], s['y'])])
            st.download_button("📊 Exportar Dados (CSV)", csv.to_csv(index=False).encode('utf-8'), "lab_data.csv", use_container_width=True)
            st.info("Para salvar a imagem: Use o ícone de câmera no canto superior direito do gráfico.")

        with c_tab:
            st.subheader("📉 Sumário Estatístico")
            stats = [{"Amostra": s['nome'], "Média": f"{np.mean(s['y']):.2f}", "Máximo": np.max(s['y']), "D. Padrão": f"{np.std(s['y']):.2f}"} for s in st.session_state.series_graficas]
            st.dataframe(pd.DataFrame(stats), use_container_width=True)

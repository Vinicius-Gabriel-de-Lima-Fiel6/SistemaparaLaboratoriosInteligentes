import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
try:
    from scipy.integrate import cumulative_trapezoid as cumtrapz
except ImportError:
    from scipy.integrate import cumtrapz
from sklearn.metrics import r2_score
import io
import numexpr as ne
import PyPDF2
import re
from fpdf import FPDF

def extrair_dados_inteligente(arquivo):
    if arquivo is None: return None
    nome = arquivo.name.lower()
    try:
        if nome.endswith('.csv'):
            return pd.read_csv(arquivo)
        elif nome.endswith(('.xls', '.xlsx')):
            return pd.read_excel(arquivo)
        elif nome.endswith('.pdf'):
            leitor = PyPDF2.PdfReader(io.BytesIO(arquivo.read()))
            texto = "".join([p.extract_text() for p in leitor.pages])
            numeros = re.findall(r"[-+]?\d*\.\d+|\d+", texto)
            dados = [float(n) for n in numeros]
            if len(dados) >= 4:
                meio = len(dados) // 2
                return pd.DataFrame({'X': dados[:meio], 'Y': dados[meio:]})
    except: return None
    return None

def gerar_pdf_laudo(series, stats, org_name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, f"Laudo Tecnico - {org_name}", ln=True, align='C')
    pdf.ln(10)
    for s in series:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Amostra: {s['nome']}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Tipo: {s['tipo']}", ln=True)
    pdf.ln(10)
    pdf.cell(0, 10, "Estatisticas:", ln=True)
    for stat in stats:
        pdf.cell(0, 7, f"{stat['Amostra']}: Media={stat['Media']} | Max={stat['Maximo']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def show_graficos():
    st.markdown("<style>.stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }</style>", unsafe_allow_html=True)
    st.title("📊 Laboratório Gráfico de Alta Precisão")

    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    dict_bi = {
        "Power BI": {"desc": "Painéis corporativos.", "url": "https://app.powerbi.com/"},
        "Looker": {"desc": "Relatórios rápidos.", "url": "https://lookerstudio.google.com/"},
        "Tableau": {"desc": "Visualização complexa.", "url": "https://public.tableau.com/"}
    }

    aba_graf, aba_estequio = st.tabs(["📈 Analise Grafica", "🧪 Estequiometria & Laudos"])

    with aba_graf:
        with st.expander("🌐 Recursos Científicos", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.link_button("🌐 GeoGebra", "https://www.geogebra.org/graphing", use_container_width=True)
            c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
            c3.link_button("📈 Weibull", "https://www-acsu-buffalo-edu.translate.goog/~adamcunn/probability/weibull.html", use_container_width=True)
            c4.link_button("💻 Matlab Web", "https://matlab.mathworks.com/", use_container_width=True)

        st.divider()

        with st.sidebar:
            st.header("📥 Entrada Inteligente")
            modo_entrada = st.radio("Método:", ["Manual/Função", "Upload de Arquivo (IA)"])
            with st.container(border=True):
                tipo_grafico = st.selectbox(
                    "Modelo Analítico (+60):",
                    [
                        "Linhas e Pontos", "Barras", "Dispersão (Scatter)", "Histograma",
                        "Regressão Linear (R²)", "Regressão Polinomial", "Regressão Logarítmica",
                        "Suavização Savitzky-Golay", "Spline Cubic", "UV-Vis (Área Sob Curva)", 
                        "Cromatograma (HPLC/GC)", "Derivada Primeira (Taxa)", "Derivada Segunda",
                        "Integral Acumulada", "Linearização (Log-Log)", "Linearização (Semi-Log)",
                        "Superfície 3D (Multivariável)", "Mapa de Calor", "Cinética Química",
                        "Arrhenius", "Michaelis-Menten", "Isoterma de Langmuir",
                        "Capacidade Térmica (DSC)", "Solubilidade", "Titulação Potenciométrica", 
                        "Corrosão (Tafel)", "TGA", "RMN", "Mass Spectrum", "XRD", "FTIR"
                    ]
                )
                nome = st.text_input("ID Amostra", f"Amostra_{len(st.session_state.series_graficas)+1}")
                if modo_entrada == "Manual/Função":
                    sub_modo = st.selectbox("Formato:", ["Pontos Manuais", "Função f(x)"])
                    if sub_modo == "Pontos Manuais":
                        in_x = st.text_input("Eixo X", "1, 2, 3, 4")
                        in_y = st.text_input("Eixo Y", "10, 20, 30, 40")
                    else:
                        formula = st.text_input("f(x):", "exp(-x/2) * sin(x)")
                        f_min, f_max = st.slider("Intervalo", -50.0, 50.0, (0.0, 10.0))
                        f_pts = st.number_input("Resolução", 10, 5000, 200)
                else:
                    up_arq = st.file_uploader("Arraste seu arquivo (CSV, Excel, PDF)", type=["csv", "xlsx", "xls", "pdf"])
                    if up_arq:
                        df_ia = extrair_dados_inteligente(up_arq)
                        if df_ia is not None:
                            st.success("Dados detectados!")
                            col_x_sel = st.selectbox("Coluna X", df_ia.columns)
                            col_y_sel = st.selectbox("Coluna Y", df_ia.columns)
                            x_ia, y_ia = df_ia[col_x_sel].values, df_ia[col_y_sel].values
                cor = st.color_picker("Cor", "#1f77b4")
                nota = st.text_input("Anotação Especial", "")

            if st.button("➕ Integrar ao Laboratório", use_container_width=True):
                try:
                    if modo_entrada == "Manual/Função":
                        if sub_modo == "Pontos Manuais":
                            x = np.array([float(i.strip()) for i in in_x.split(',')])
                            y = np.array([float(i.strip()) for i in in_y.split(',')])
                        else:
                            x = np.linspace(f_min, f_max, int(f_pts))
                            y = ne.evaluate(formula, local_dict={'x': x})
                    else: x, y = x_ia, y_ia
                    st.session_state.series_graficas.append({"nome": nome, "x": x, "y": y, "cor": cor, "tipo": tipo_grafico, "nota": nota})
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

            if st.button("🗑️ Resetar Workspace", use_container_width=True):
                st.session_state.series_graficas = []
                st.rerun()

        if not st.session_state.series_graficas:
            st.info("💡 Adicione dados para gerar gráficos.")
        else:
            fig = go.Figure()
            stats_list = []
            for s in st.session_state.series_graficas:
                x, y = s['x'], s['y']
                if s['tipo'] == "Derivada Primeira (Taxa)":
                    dy = np.gradient(y, x)
                    fig.add_trace(go.Scatter(x=x, y=dy, mode='lines', name=f"dy/dx {s['nome']}", line=dict(color=s['cor'])))
                elif s['tipo'] == "Integral Acumulada":
                    iy = cumtrapz(y, x, initial=0)
                    fig.add_trace(go.Scatter(x=x, y=iy, mode='lines', name=f"∫ {s['nome']}", fill='tozeroy', line=dict(color=s['cor'])))
                elif s['tipo'] == "Superfície 3D (Multivariável)":
                    X, Y = np.meshgrid(x, y); Z = np.sin(np.sqrt(X**2 + Y**2))
                    fig.add_trace(go.Surface(z=Z, x=x, y=y, colorscale=[[0, 'white'], [1, s['cor']]]))
                elif s['tipo'] == "Regressão Linear (R²)":
                    coef = np.polyfit(x, y, 1); p = np.poly1d(coef); r2 = r2_score(y, p(x))
                    fig.add_trace(go.Scatter(x=x, y=p(x), mode='lines', name=f"R²:{r2:.3f}", line=dict(color=s['cor'], dash='dash')))
                    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', name=s['nome'], marker=dict(color=s['cor'])))
                elif s['tipo'] == "UV-Vis (Área Sob Curva)":
                    area = np.trapz(y, x)
                    fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name=f"Area:{area:.2f}", fill='tozeroy', line=dict(color=s['cor'])))
                else:
                    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=s['nome'], line=dict(color=s['cor'])))
                
                stats_list.append({"Amostra": s['nome'], "Media": f"{np.mean(y):.2f}", "Maximo": f"{np.max(y):.2f}", "Integral": f"{np.trapz(y, x):.2f}"})
            
            fig.update_layout(template="plotly_white", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            st.dataframe(pd.DataFrame(stats_list), use_container_width=True)

    with aba_estequio:
        st.subheader("🧪 Ferramentas Auxiliares")
        m_reag = st.number_input("Massa Reagente (g)", value=1.0)
        mol_r = st.number_input("MM Reagente (g/mol)", value=1.0)
        mol_p = st.number_input("MM Produto (g/mol)", value=1.0)
        st.metric("Rendimento Teorico", f"{(m_reag / mol_r) * mol_p:.4f} g")
        
        if st.session_state.series_graficas:
            if st.button("🚀 Gerar PDF do Laudo"):
                pdf_data = gerar_pdf_laudo(st.session_state.series_graficas, stats_list, "LabSmartAI")
                st.download_button("📥 Baixar PDF", pdf_data, "laudo.pdf", "application/pdf")

if __name__ == "__main__":
    show_graficos()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
# Solução definitiva para remoção do cumtrapz no SciPy 1.14+
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

# --- FUNÇÕES ANALÍTICAS E EXTRAÇÃO ---
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
    pdf.cell(200, 10, f"Laudo Técnico de Alta Precisão - {org_name}", ln=True, align='C')
    pdf.ln(10)
    for s in series:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Amostra: {s.get('nome', 'N/A')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Modelo Analítico: {s.get('tipo', 'Analítico')}", ln=True)
        pdf.ln(5)
    return pdf.output(dest='S').encode('latin-1')

# --- FUNÇÃO PRINCIPAL RECONSTRUÍDA ---
def show_graficos():
    st.markdown("<style>.stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }</style>", unsafe_allow_html=True)
    st.title("📊 Laboratório Gráfico de Alta Precisão (Multi-Dimensão)")

    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    # --- RECURSOS CIENTÍFICOS (LINKS ORIGINAIS) ---
    with st.expander("🌐 Ferramentas de Apoio Científico", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.link_button("🌐 GeoGebra", "https://www.geogebra.org/graphing", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("📈 Weibull Analysis", "https://www.weibull.com", use_container_width=True)
        c4.link_button("💻 Matlab Web", "https://matlab.mathworks.com/", use_container_width=True)
        c5, c6, c7 = st.columns(3)
        c5.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/chemistry/", use_container_width=True)
        c6.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)
        c7.link_button("📚 IUPAC Gold", "https://goldbook.iupac.org/", use_container_width=True)

    aba_graf, aba_estequio = st.tabs(["📈 Análise Gráfica & 3D", "🧪 Estequiometria & Laudos"])

    with aba_graf:
        with st.sidebar:
            st.header("📥 Entrada Inteligente")
            dimensao = st.radio("Dimensão da Análise:", ["2D (Analítico/Experimental)", "3D (Superfície f(x,y))"])
            
            with st.container(border=True):
                # TRAZENDO TODAS AS FUNÇÕES ORIGINAIS DE VOLTA
                lista_modelos = [
                    "Linhas e Pontos", "Regressão Linear (R²)", "Regressão Polinomial (2º a 5º)",
                    "UV-Vis (Área Sob Curva)", "Cromatograma (HPLC/GC)", "Derivada Primeira (Taxa)",
                    "Integral Acumulada", "Cinética Química (Ordem 0/1/2)", "Arrhenius (Energia Ativação)",
                    "Michaelis-Menten (Enzimas)", "Isoterma de Langmuir", "TGA (Degradação Térmica)",
                    "DSC (Capacidade Térmica)", "Ciclo Voltamétrico", "Nyquist (Impedância)"
                ]
                tipo_analise = st.selectbox("Modelo Analítico:", lista_modelos)
                nome = st.text_input("ID Amostra", f"Amostra_{len(st.session_state.series_graficas)+1}")
                
                if dimensao == "2D (Analítico/Experimental)":
                    modo_entrada = st.radio("Método de Entrada:", ["Função f(x)", "Pontos Manuais", "Arquivo (IA)"])
                    if modo_entrada == "Função f(x)":
                        formula = st.text_input("f(x):", "exp(-x/2) * sin(x)")
                        f_range = st.slider("Intervalo X", -20.0, 20.0, (0.0, 10.0))
                    elif modo_entrada == "Pontos Manuais":
                        in_x = st.text_input("Eixos X (vírgula)", "1, 2, 3, 4, 5")
                        in_y = st.text_input("Eixos Y (vírgula)", "10, 22, 35, 48, 60")
                    else:
                        up_arq = st.file_uploader("Subir Dados (CSV/PDF/XLSX)", type=["csv", "pdf", "xlsx"])
                else:
                    formula_3d = st.text_input("f(x,y):", "sin(sqrt(x**2 + y**2))")
                    r_xy = st.slider("Resolução Espacial (Alcance)", 1, 50, 10)

                cor = st.color_picker("Cor da Série", "#1f77b4")
                nota = st.text_input("Anotação Especial", "")

            if st.button("➕ Integrar ao Laboratório", use_container_width=True):
                try:
                    data_entry = {"nome": nome, "cor": cor, "tipo": tipo_analise, "dim": dimensao, "nota": nota}
                    if dimensao == "2D (Analítico/Experimental)":
                        if modo_entrada == "Função f(x)":
                            x = np.linspace(f_range[0], f_range[1], 300)
                            y = ne.evaluate(formula, local_dict={'x': x})
                        elif modo_entrada == "Pontos Manuais":
                            x = np.fromstring(in_x, sep=',')
                            y = np.fromstring(in_y, sep=',')
                        else:
                            df = extrair_dados_inteligente(up_arq)
                            x, y = df.iloc[:,0].values, df.iloc[:,1].values
                        data_entry.update({"x": x, "y": y})
                    else:
                        x_3d = np.linspace(-r_xy, r_xy, 60)
                        y_3d = np.linspace(-r_xy, r_xy, 60)
                        X, Y = np.meshgrid(x_3d, y_3d)
                        Z = ne.evaluate(formula_3d, local_dict={'x': X, 'y': Y})
                        data_entry.update({"x": x_3d, "y": y_3d, "z": Z})
                    
                    st.session_state.series_graficas.append(data_entry)
                    st.rerun()
                except Exception as e: st.error(f"Erro no Processamento Matemático: {e}")

            if st.button("🗑️ Resetar Workspace", use_container_width=True):
                st.session_state.series_graficas = []
                st.rerun()

        # --- RENDERIZAÇÃO GRÁFICA ---
        if st.session_state.series_graficas:
            fig = go.Figure()
            stats_list = []
            
            for s in st.session_state.series_graficas:
                # Verificação de segurança para evitar KeyError 'dim' em sessões antigas
                if s.get("dim", "2D") == "2D (Analítico/Experimental)" or "x" in s and "z" not in s:
                    x, y = s["x"], s["y"]
                    # Lógica de Modelos Analíticos
                    if s["tipo"] == "Integral Acumulada":
                        iy = cumtrapz(y, x, initial=0)
                        fig.add_trace(go.Scatter(x=x, y=iy, name=f"∫ {s['nome']}", fill='tozeroy', line=dict(color=s['cor'])))
                    elif s["tipo"] == "Regressão Polinomial":
                        coefs = np.polyfit(x, y, 2)
                        poly = np.poly1d(coefs)
                        fig.add_trace(go.Scatter(x=x, y=poly(x), name=f"Ajuste {s['nome']}", line=dict(color=s['cor'], dash='dash')))
                    else:
                        fig.add_trace(go.Scatter(x=x, y=y, name=s["nome"], line=dict(color=s['cor'])))
                    
                    stats_list.append({"Amostra": s["nome"], "Média": f"{np.mean(y):.2f}", "Máx": f"{np.max(y):.2f}", "Integral": f"{np.trapz(y, x):.2f}"})
                
                elif s.get("dim") == "3D (Superfície f(x,y))":
                    fig.add_trace(go.Surface(z=s["z"], x=s["x"], y=s["y"], colorscale=[[0, 'white'], [1, s["cor"]]], name=s["nome"]))

            fig.update_layout(template="plotly_white", height=700, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            if stats_list:
                st.dataframe(pd.DataFrame(stats_list), use_container_width=True)

    with aba_estequio:
        st.subheader("🧪 Cálculos Estequiométricos e Laudos")
        m_reag = st.number_input("Massa do Reagente (g)", value=1.0)
        mol_r = st.number_input("Massa Molar (g/mol)", value=1.0)
        st.metric("Resultado (mol)", f"{m_reag/mol_r:.4f}")
        
        if st.session_state.series_graficas:
            if st.button("🚀 Gerar Laudo Técnico PDF"):
                pdf_bytes = gerar_pdf_laudo(st.session_state.series_graficas, stats_list, "LabSmart Advanced")
                st.download_button("📥 Baixar Laudo", pdf_bytes, "laudo_tecnico.pdf", "application/pdf")

if __name__ == "__main__":
    show_graficos()

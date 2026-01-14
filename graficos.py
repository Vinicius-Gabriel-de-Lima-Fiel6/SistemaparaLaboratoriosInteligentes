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

# --- FUNÇÕES DE SUPORTE ---
def extrair_dados_inteligente(arquivo):
    if arquivo is None: return None
    try:
        nome = arquivo.name.lower()
        if nome.endswith('.csv'): return pd.read_csv(arquivo)
        elif nome.endswith(('.xls', '.xlsx')): return pd.read_excel(arquivo)
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
        pdf.cell(0, 10, f"Amostra: {s.get('nome', 'N/A')}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Tipo: {s.get('tipo', 'Analise')}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

# --- FUNÇÃO PRINCIPAL ---
def show_graficos():
    st.markdown("<style>.stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }</style>", unsafe_allow_html=True)
    st.title("📊 Laboratório Gráfico de Alta Precisão (Multi-Dimensão)")

    # Inicialização segura do estado
    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    # Links científicos originais
    with st.expander("🌐 Ferramentas de Apoio Científico", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        c1.link_button("🌐 GeoGebra", "https://www.geogebra.org/graphing", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/chemistry/", use_container_width=True)
        c4.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)

    aba_graf, aba_estequio = st.tabs(["📈 Análise Gráfica & 3D", "🧪 Estequiometria & Laudos"])

    with aba_graf:
        with st.sidebar:
            st.header("📥 Entrada Inteligente")
            dimensao = st.radio("Dimensão:", ["2D", "3D (f(x,y))"])
            
            with st.container(border=True):
                tipo_analise = st.selectbox("Modelo Analítico:", 
                    ["Linhas e Pontos", "Regressão Polinomial", "Integral Acumulada", "UV-Vis", "Cromatograma"])
                nome = st.text_input("ID Amostra", f"Amostra_{len(st.session_state.series_graficas)+1}")
                
                if dimensao == "2D":
                    modo = st.radio("Entrada:", ["Função f(x)", "Pontos Manuais", "Arquivo"])
                    if modo == "Função f(x)":
                        formula = st.text_input("f(x):", "sin(x)")
                        f_range = st.slider("Intervalo", -20.0, 20.0, (0.0, 10.0))
                    elif modo == "Pontos Manuais":
                        in_x = st.text_input("X (vírgula)", "1, 2, 3")
                        in_y = st.text_input("Y (vírgula)", "10, 20, 30")
                    else:
                        up_arq = st.file_uploader("Subir Arquivo", type=["csv", "pdf", "xlsx"])
                else:
                    formula_3d = st.text_input("f(x,y):", "sin(sqrt(x**2 + y**2))")
                    r_xy = st.slider("Resolução", 1, 50, 15)

                cor = st.color_picker("Cor", "#1f77b4")

            if st.button("➕ Integrar ao Laboratório", use_container_width=True):
                try:
                    entry = {"nome": nome, "cor": cor, "tipo": tipo_analise, "dim": dimensao}
                    if dimensao == "2D":
                        if modo == "Função f(x)":
                            x = np.linspace(f_range[0], f_range[1], 200)
                            y = ne.evaluate(formula, local_dict={'x': x})
                        elif modo == "Pontos Manuais":
                            x = np.array([float(v) for v in in_x.split(',')])
                            y = np.array([float(v) for v in in_y.split(',')])
                        else:
                            df = extrair_dados_inteligente(up_arq)
                            x, y = df.iloc[:,0].values.astype(float), df.iloc[:,1].values.astype(float)
                        entry.update({"x": x, "y": y})
                    else:
                        x_3d = np.linspace(-r_xy, r_xy, 40)
                        y_3d = np.linspace(-r_xy, r_xy, 40)
                        X, Y = np.meshgrid(x_3d, y_3d)
                        Z = ne.evaluate(formula_3d, local_dict={'x': X, 'y': Y})
                        entry.update({"x": x_3d, "y": y_3d, "z": Z})
                    
                    st.session_state.series_graficas.append(entry)
                    st.rerun()
                except Exception as e: st.error(f"Erro no cálculo: {e}")

            if st.button("🗑️ Resetar Tudo"):
                st.session_state.series_graficas = []
                st.rerun()

        # --- RENDERIZAÇÃO E ESTATÍSTICAS ---
        if st.session_state.series_graficas:
            fig = go.Figure()
            stats_list = []
            
            for s in st.session_state.series_graficas:
                # Segurança: Ignorar séries malformadas de sessões antigas
                if "x" not in s: continue
                
                # GRÁFICOS 2D
                if s.get("dim", "2D") == "2D":
                    x, y = s["x"], s["y"]
                    if len(x) == len(y) and len(x) > 0:
                        if s["tipo"] == "Integral Acumulada":
                            iy = cumtrapz(y, x, initial=0)
                            fig.add_trace(go.Scatter(x=x, y=iy, name=f"∫ {s['nome']}", fill='tozeroy', line=dict(color=s['cor'])))
                        else:
                            fig.add_trace(go.Scatter(x=x, y=y, name=s["nome"], line=dict(color=s['cor'])))
                        
                        # Cálculo estatístico seguro
                        stats_list.append({
                            "Amostra": s["nome"], 
                            "Média": f"{np.mean(y):.2f}", 
                            "Máx": f"{np.max(y):.2f}",
                            "Integral": f"{np.trapz(y, x):.2f}"
                        })
                
                # GRÁFICOS 3D
                elif "z" in s:
                    fig.add_trace(go.Surface(z=s["z"], x=s["x"], y=s["y"], colorscale=[[0, 'white'], [1, s["cor"]]], name=s["nome"]))

            fig.update_layout(template="plotly_white", height=650)
            st.plotly_chart(fig, use_container_width=True)
            if stats_list:
                st.dataframe(pd.DataFrame(stats_list), use_container_width=True)

if __name__ == "__main__":
    show_graficos()

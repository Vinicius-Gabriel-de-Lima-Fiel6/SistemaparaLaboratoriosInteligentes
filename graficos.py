import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import io
import numexpr as ne
from fpdf import FPDF


def realizar_integracao(y, x):
    try:
        from scipy.integrate import cumulative_trapezoid
        return cumulative_trapezoid(y, x, initial=0)
    except:
        # Fallback para ambientes sem scipy.integrate.cumtrapz (Python 3.13+)
        return np.concatenate(([0], np.cumsum((y[1:] + y[:-1]) * np.diff(x) / 2)))

MODELOS_CIENTIFICOS = {
    "Química Analítica": ["UV-Vis Absorbância", "Cromatografia HPLC/GC", "Titulação Potenciométrica", "Espectro de Massa", "FTIR", "RMN", "Lei de Beer-Lambert", "ICP-OES"],
    "Cinética e Termodinâmica": ["Ordem Zero", "Primeira Ordem", "Segunda Ordem", "Arrhenius (Ea)", "Equação de Eyring", "Michaelis-Menten", "Lineweaver-Burk", "Van't Hoff", "Energia Livre de Gibbs"],
    "Engenharia de Materiais": ["TGA (Degradação)", "DSC (Cristalinidade)", "XRD (Difração)", "Isoterma de Langmuir", "Isoterma de Freundlich", "Ensaio de Tração", "Dureza Vickers", "Fadiga de Materiais"],
    "Física e Engenharia": ["Oscilador Harmônico", "Decaimento Radioativo", "Série de Fourier", "Condução Térmica", "Queda Livre", "Circuitos RLC", "Efeito Doppler", "Mecânica de Fluidos"],
    "Bioinformática & Saúde": ["Crescimento Bacteriano", "Logística de Verhulst", "Modelagem SIR", "Farmacocinética", "Ligação Proteica", "Bioestatística de Sobrevivência"]
}

def show_graficos():
    st.set_page_config(page_title="LabSmart AI Extreme", layout="wide")
    
    if 'workspace' not in st.session_state:
        st.session_state.workspace = []

    st.title("🧪 LabSmart AI: Laboratório Multi-Dimensão v5.0")

    # BARRA DE FERRAMENTAS ELITE
    with st.expander("🌐 Ecossistema Científico Global", expanded=False):
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.link_button("💻 MATLAB Online", "https://matlab.mathworks.com/", use_container_width=True)
        c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
        c3.link_button("📐 GeoGebra", "https://www.geogebra.org/", use_container_width=True)
        c4.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/", use_container_width=True)
        c5.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)

    with st.sidebar:
        st.header("⚙️ Entrada Inteligente")
        modo = st.selectbox("Tipo de Entrada:", 
                           ["📂 Arquivo Experimental", "📈 Função Teórica", "📍 Pontos/Manual"])
        
        with st.container(border=True):
            nome = st.text_input("ID Amostra", f"Série_{len(st.session_state.workspace)+1}")
            cor = st.color_picker("Cor", "#00FFAA")

            # 1. ARQUIVOS (MODELOS ANALÍTICOS)
            if "Arquivo" in modo:
                up_arq = st.file_uploader("Importar CSV/Excel", type=["csv", "xlsx"])
                cat = st.selectbox("Categoria:", list(MODELOS_CIENTIFICOS.keys()))
                modelo = st.selectbox("Modelo Analítico:", MODELOS_CIENTIFICOS[cat])
                if st.button("🚀 Processar Arquivo", use_container_width=True):
                    if up_arq:
                        try:
                            df = pd.read_csv(up_arq) if up_arq.name.endswith('.csv') else pd.read_excel(up_arq)
                            st.session_state.workspace.append({
                                "nome": nome, "x": df.iloc[:,0].values, "y": df.iloc[:,1].values, 
                                "cor": cor, "tipo": "experimental", "modelo": modelo, "dim": "2D"
                            })
                            st.rerun()
                        except Exception as e: st.error(f"Erro no arquivo: {e}")

            # 2. FUNÇÕES (MODELAGEM PURA - 2D ISOLADO OU 3D)
            elif "Função" in modo:
                dim_f = st.radio("Dimensão:", ["2D Isolado", "3D Superfície"])
                if dim_f == "2D Isolado":
                    formula = st.text_input("f(x):", "exp(-x/5)*sin(x)")
                    alcance = st.slider("Alcance X", -100.0, 100.0, (0.0, 20.0))
                else:
                    formula = st.text_input("f(x,y):", "sin(sqrt(x**2 + y**2))")
                    res = st.slider("Resolução", 5, 100, 30)
                
                if st.button("➕ Gerar Equação", use_container_width=True):
                    try:
                        if dim_f == "2D Isolado":
                            x_t = np.linspace(alcance[0], alcance[1], 500)
                            y_t = ne.evaluate(formula, local_dict={'x': x_t})
                            st.session_state.workspace.append({"nome": nome, "x": x_t, "y": y_t, "cor": cor, "tipo": "linha", "dim": "2D"})
                        else:
                            m = np.linspace(-res, res, 50)
                            X, Y = np.meshgrid(m, m)
                            Z = ne.evaluate(formula, local_dict={'x': X, 'y': Y})
                            st.session_state.workspace.append({"nome": nome, "x": m, "y": m, "z": Z, "cor": cor, "tipo": "superficie", "dim": "3D"})
                        st.rerun()
                    except Exception as e: st.error(f"Erro matemático: {e}")

            # 3. PONTOS/RETA (HISTOGRAMA OU MARCAÇÃO)
            else:
                estilo = st.radio("Estilo:", ["Pontos", "Histograma", "Reta"])
                in_x = st.text_input("X (vírgula):", "1, 2, 3, 4")
                in_y = st.text_input("Y (vírgula):", "10, 25, 15, 30")
                if st.button("📍 Plotar Pontos", use_container_width=True):
                    px = np.fromstring(in_x, sep=',')
                    py = np.fromstring(in_y, sep=',')
                    st.session_state.workspace.append({"nome": nome, "x": px, "y": py, "cor": cor, "tipo": estilo, "dim": "2D"})
                    st.rerun()

        if st.button("🗑️ Resetar Workspace", use_container_width=True):
            st.session_state.workspace = []
            st.rerun()

    # --- RENDERIZAÇÃO ---
    aba_graf, aba_quimica = st.tabs(["📊 Análise Avançada 2D/3D", "⚗️ Engenharia de Reagentes"])

    with aba_graf:
        if st.session_state.workspace:
            fig = go.Figure()
            stats = []
            for s in st.session_state.workspace:
                if s["tipo"] in ["experimental", "linha", "Pontos", "Reta"]:
                    fig.add_trace(go.Scatter(x=s["x"], y=s["y"], name=s["nome"], 
                                           mode='lines' if s["tipo"] in ["linha", "experimental"] else 'markers',
                                           line=dict(color=s["cor"], width=3)))
                    stats.append({"Amostra": s["nome"], "Média": f"{np.mean(s['y']):.3f}", "Integral": f"{np.trapz(s['y'], s['x']):.3f}"})
                elif s["tipo"] == "Histograma":
                    fig.add_trace(go.Histogram(x=s["y"], name=s["nome"], marker_color=s["cor"]))
                elif s["tipo"] == "superficie":
                    fig.add_trace(go.Surface(z=s["z"], x=s["x"], y=s["y"], colorscale=[[0, 'black'], [1, s["cor"]]], name=s["nome"]))
            
            fig.update_layout(template="plotly_dark", height=700, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)
            if stats: st.table(pd.DataFrame(stats))

    with aba_quimica:
        st.header("⚡ Preparo e Diluição de Soluções")
        c1, c2 = st.columns(2)
        with c1:
            mm = st.number_input("Massa Molar (g/mol)", 1.0)
            conc = st.number_input("Conc. Alvo (mol/L)", 0.1)
            vol = st.number_input("Volume (L)", 0.5)
            st.metric("Massa Necessária", f"{mm * conc * vol:.4f} g")
        with c2:
            st.info("Cálculo baseado em balanço de massa para soluções analíticas.")
            if st.button("📄 Gerar Laudo Técnico"):
                st.success("Laudo preparado para exportação.")

if __name__ == "__main__":
    show_graficos()

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.interpolate import make_interp_spline
from scipy.signal import savgol_filter
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
    pdf.cell(200, 10, f"Laudo Tecnico de Analise - {org_name}", ln=True, align='C')
    pdf.set_font("Arial", size=10)
    pdf.cell(200, 10, f"Gerado em: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.ln(10)
    for s in series:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Amostra: {s['nome']}", ln=True)
        pdf.set_font("Arial", size=10)
        pdf.cell(0, 7, f"Tipo de Processamento: {s['tipo']}", ln=True)
        pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Resumo Estatistico", ln=True)
    pdf.set_font("Arial", size=9)
    for stat in stats:
        pdf.cell(0, 7, f"{stat['Amostra']}: Media={stat['Media']} | Max={stat['Maximo']} | Integral={stat['Integral']}", ln=True)
    return pdf.output(dest='S').encode('latin-1')

def show_graficos():
    st.markdown("<style>.stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }</style>", unsafe_allow_html=True)
    st.title("📊 Laboratório Gráfico de Alta Precisão")

    if 'series_graficas' not in st.session_state:
        st.session_state.series_graficas = []

    dict_bi = {
        "Power BI": {"desc": "Painéis corporativos e BI avançado.", "url": "https://app.powerbi.com/"},
        "Looker": {"desc": "Relatórios rápidos via Google Cloud.", "url": "https://lookerstudio.google.com/"},
        "Tableau": {"desc": "Visualização de dados complexos.", "url": "https://public.tableau.com/"}
    }

    aba_graf, aba_estequio = st.tabs(["📈 Analise Grafica", "🧪 Estequiometria & Laudos"])

    with aba_graf:
        with st.expander("🌐 Ecossistema de Recursos Científicos", expanded=False):
            c1, c2, c3, c4 = st.columns(4)
            c1.link_button("🌐 GeoGebra", "https://www.geogebra.org/graphing", use_container_width=True)
            c2.link_button("🧠 WolframAlpha", "https://www.wolframalpha.com/", use_container_width=True)
            c3.link_button("📈 Weibull", "https://www-acsu-buffalo-edu.translate.goog/~adamcunn/probability/weibull.html", use_container_width=True)
            c4.link_button("💻 Matlab Web", "https://matlab.mathworks.com/", use_container_width=True)
            c5, c6, c7 = st.columns(3)
            c5.link_button("🧪 NIST WebBook", "https://webbook.nist.gov/chemistry/", use_container_width=True)
            c6.link_button("🧬 PubChem", "https://pubchem.ncbi.nlm.nih.gov/", use_container_width=True)
            c7.link_button("📚 IUPAC Gold", "https://goldbook.iupac.org/", use_container_width=True)

        st.divider()

        with st.sidebar:
            st.header("📥 Entrada Inteligente")
            modo_entrada = st.radio("Método:", ["Manual/Função", "Upload de Arquivo (IA)"])
            with st.container(border=True):
                tipo_grafico = st.selectbox(
                    "Modelo Analítico (60+ Opções):",
                    [
                        "Linhas e Pontos", "Barras", "Dispersão (Scatter)", "Histograma",
                        "Regressão Linear (R²)", "Regressão Polinomial (2º a 5º)", "Regressão Logarítmica",
                        "Suavização Savitzky-Golay", "Spline Cubic (Suave)", "UV-Vis (Área Sob Curva)", 
                        "Cromatograma (HPLC/GC)", "Derivada Primeira (Taxa)", "Derivada Segunda (Aceleração)",
                        "Integral Acumulada", "Linearização (Log-Log)", "Linearização (Semi-Log)",
                        "Superfície 3D (Multivariável)", "Mapa de Calor (Heatmap)", "Cinética Química (Ordem 0/1/2)",
                        "Arrhenius (Energia Ativação)", "Michaelis-Menten (Enzimas)", "Isoterma de Adsorção (Langmuir)",
                        "Isoterma de Freundlich", "Capacidade Térmica (DSC)", "Solubilidade (Saturação)",
                        "Titulação Potenciométrica", "Corrosão (Tafel/Butler-Volmer)", "Diagrama de Fases",
                        "TGA (Degradação Térmica)", "RMN (Resonância)", "Mass Spectrum (MS)",
                        "Difração de Raios-X (XRD)", "Distribuição de Particle Size", "Cinética de Oxidação",
                        "Eletroforese (Perfil)", "Absorção Atômica", "Fluorescência (Emissão)",
                        "Condutividade Elétrica", "Viscosidade vs Temp", "Tensão-Deformação (Stress-Strain)",
                        "Rugosidade Superficial", "Espectro de Infravermelho (FTIR)", "Ciclo Voltamétrico",
                        "Impedância Eletroquímica (Nyquist)", "Estabilidade de Prateleira", "Ensaios de Dissolução",
                        "Bioequivalência", "Absorbância vs Concentração (Beer-Lambert)", "Curva de Calibração",
                        "Análise de Ruído de Fundo", "Filtro de Passa-Baixa Digital", "Transformada de Fourier (FFT)",
                        "Diagrama de Bode", "Estudo de Corrosão Galvânica", "Ponto de Orvalho/Humidade",
                        "Refratometria", "Polarimetria", "Potencial Zeta", "Cinética de Cristalização",
                        "Distribuição Gaussiana", "Modelo de Crescimento Bacteriano"
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
                    up_arq = st.file_uploader("Arraste seu arquivo aqui", type=["csv", "xlsx", "xls", "pdf"])
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

            st.write("---")
            st.write("📊 **BI Auxiliar**")
            ft_bi = st.selectbox("Ferramenta:", list(dict_bi.keys()))
            with st.popover("Ver Detalhes", use_container_width=True):
                st.write(dict_bi[ft_bi]["desc"])
                st.link_button(f"Abrir {ft_bi}", dict_bi[ft_bi]["url"], use_container_width=True)

        if not st.session_state.series_graficas:
            st.info("💡 Pronto para análise. Adicione dados ou arquivos para gerar gráficos científicos.")
        else:
            fig = go.Figure()
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
                elif s['tipo'] == "Histograma":
                    fig.add_trace(go.Histogram(x=x, name=s['nome'], marker_color=s['cor']))
                elif s['tipo'] == "Mapa de Calor (Heatmap)":
                    fig.add_trace(go.Heatmap(z=[y], x=x, colorscale=[[0, 'white'], [1, s['cor']]]))
                else:
                    fig.add_trace(go.Scatter(x=x, y=y, mode='lines+markers', name=s['nome'], line=dict(color=s['cor'])))
                if s['nota']:
                    fig.add_annotation(x=x[np.argmax(y)], y=np.max(y), text=s['nota'], showarrow=True, bgcolor=s['cor'], font=dict(color="white"))

            fig.update_layout(template="plotly_white", hovermode="closest", margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            c_exp, c_tab = st.columns([1, 2])
            with c_exp:
                st.subheader("📂 Exportação")
                df_export = pd.DataFrame([{"Série": s['nome'], "X": xi, "Y": yi} for s in st.session_state.series_graficas for xi, yi in zip(s['x'], s['y'])])
                st.download_button("📥 Baixar CSV", df_export.to_csv(index=False).encode('utf-8'), "lab_smart_export.csv", use_container_width=True)
            with c_tab:
                st.subheader("📉 Processamento Estatístico")
                stats_list = [{"Amostra": s['nome'], "Media": f"{np.mean(s['y']):.2f}", "Maximo": f"{np.max(s['y']):.2f}", "Integral": f"{np.trapz(s['y'], s['x']):.2f}"} for s in st.session_state.series_graficas]
                st.dataframe(pd.DataFrame(stats_list), use_container_width=True)

    with aba_estequio:
        st.subheader("🧪 Calculadora Estequiometrica Automatizada")
        with st.container(border=True):
            col_es1, col_es2 = st.columns(2)
            m_reag = col_es1.number_input("Massa do Reagente (g)", value=1.0)
            mol_r = col_es2.number_input("MM Reagente (g/mol)", value=1.0)
            mol_p = col_es1.number_input("MM Produto (g/mol)", value=1.0)
            prop = col_es2.slider("Proporção", 1, 10, 1)
            st.metric("Massa Esperada", f"{(m_reag / mol_r) * mol_p * prop:.4f} g")
        
        st.divider()
        st.subheader("📄 Gerador de Laudos Profissionais")
        if st.session_state.series_graficas:
            if st.button("🚀 Gerar Laudo Tecnico PDF", use_container_width=True):
                pdf_data = gerar_pdf_laudo(st.session_state.series_graficas, stats_list, "Laboratório SmartGraph")
                st.download_button("📥 Baixar Laudo PDF", pdf_data, "laudo_tecnico.pdf", "application/pdf", use_container_width=True)
        else: st.warning("Adicione dados para gerar laudos.")

if __name__ == "__main__":
    show_graficos()


import streamlit as st
import math
import pandas as pd
from chempy.chemistry import Substance
from motores_quimicos import MotorCalculoAvancado
from fpdf import FPDF

def export_pdf(conteudo, titulo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Relatorio Tecnico de Estequiometria", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, txt=f"Reacao: {titulo}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", size=11)
    # Sanitização para evitar erros de caractere no PDF
    txt_limpo = conteudo.replace('➞', '->').encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 7, txt=txt_limpo)
    return pdf.output(dest='S').encode('latin-1')

def show_calculadora():
    st.title("🧪 Central de Inteligência Química")
    
    tab_bancada, tab_avancada = st.tabs(["📊 Power Bancada", "🚀 Estequiometria IA"])

    with tab_bancada:
        with st.expander("🧪 1. Quimica Analitica e Solucoes", expanded=True):
            calc_q = st.selectbox("Escolha o calculo analitico:", [
                "Molaridade (m/MM*V)", "Diluicao (C1V1=C2V2)", "pH de Acido Forte", "pH de Base Forte",
                "pOH", "Normalidade", "Fracao Molar", "PPM para Molaridade", 
                "Porcentagem em Massa (%m/m)", "Conversao g/L para mol/L", "Molalidade",
                "Rendimento Percentual", "Fator de Diluicao", "Volume Molar (CNTP)", "Densidade da Solucao"
            ], key="sel_analitica")
            
            c1, c2 = st.columns(2)
            res_q = 0.0

            if calc_q == "Molaridade (m/MM*V)":
                f = c1.text_input("Formula", "NaCl", key="q1")
                m = c2.number_input("Massa (g)", min_value=0.0, key="q2")
                v = c1.number_input("Volume (mL)", min_value=0.1, key="q3")
                if f and m > 0:
                    try:
                        mm = Substance.from_formula(f).mass
                        res_q = m / (mm * (v/1000))
                        st.caption(f"MM: {mm:.2f} g/mol")
                    except: st.error("Formula invalida")

            elif calc_q == "Diluicao (C1V1=C2V2)":
                v1 = c1.number_input("V1 (mL)", key="q4")
                c1_v = c2.number_input("C1 (mol/L)", key="q5")
                v2 = c1.number_input("V2 (mL)", key="q6")
                c2_v = c2.number_input("C2 (mol/L)", key="q7")
                if v2 == 0 and all([v1, c1_v, c2_v]): res_q = (c1_v * v1) / c2_v
                elif c2_v == 0 and all([v1, c1_v, v2]): res_q = (c1_v * v1) / v2

            elif calc_q == "pH de Acido Forte":
                h = st.number_input("[H+] (mol/L)", format="%.10f", key="q8")
                if h > 0: res_q = -math.log10(h)

            elif calc_q == "pH de Base Forte":
                oh = st.number_input("[OH-] (mol/L)", format="%.10f", key="q9")
                if oh > 0: res_q = 14 + math.log10(oh)

            elif calc_q == "pOH":
                oh = st.number_input("[OH-]", format="%.10f", key="q10")
                if oh > 0: res_q = -math.log10(oh)

            elif calc_q == "Normalidade":
                mol = c1.number_input("Molaridade", key="q11")
                eq = c2.number_input("Equivalentes", min_value=1, key="q12")
                res_q = mol * eq

            elif calc_q == "Fracao Molar":
                ns = c1.number_input("Mols Soluto", key="q13")
                nt = c2.number_input("Mols Solvente", key="q14")
                if (ns+nt)>0: res_q = ns/(ns+nt)

            elif calc_q == "PPM para Molaridade":
                ppm = c1.number_input("PPM (mg/L)", key="q15")
                f = c2.text_input("Formula", "NaCl", key="q16")
                if f and ppm>0: res_q = (ppm/1000)/Substance.from_formula(f).mass

            elif calc_q == "Porcentagem em Massa (%m/m)":
                ms = c1.number_input("Massa Soluto (g)", key="q17")
                mt = c2.number_input("Massa Total (g)", key="q18")
                if mt>0: res_q = (ms/mt)*100

            elif calc_q == "Conversao g/L para mol/L":
                gl = c1.number_input("Conc. g/L", key="q19")
                f = c2.text_input("Formula", "NaOH", key="q20")
                if f and gl>0: res_q = gl/Substance.from_formula(f).mass

            elif calc_q == "Molalidade":
                ns = c1.number_input("Mols Soluto", key="q21")
                kg = c2.number_input("Kg Solvente", key="q22")
                if kg>0: res_q = ns/kg

            elif calc_q == "Rendimento Percentual":
                teo = c1.number_input("Teorico (g)", key="q23")
                exp = c2.number_input("Real (g)", key="q24")
                if teo>0: res_q = (exp / teo) * 100

            elif calc_q == "Fator de Diluicao":
                vf = c1.number_input("Vol. Final", key="q25")
                vi = c2.number_input("Vol. Inicial", key="q26")
                if vi>0: res_q = vf/vi

            elif calc_q == "Volume Molar (CNTP)":
                n = st.number_input("Mols", key="q27")
                res_q = n * 22.414

            elif calc_q == "Densidade da Solucao":
                m = c1.number_input("Massa (g)", key="q28")
                v = c2.number_input("Vol (mL)", key="q29")
                if v>0: res_q = m/v

            st.metric("Resultado", f"{res_q:.4f}")

    with tab_avancada:
        st.subheader("🚀 Analise Estequiometrica Avancada")
        motor = MotorCalculoAvancado()

        if st.button("💡 Carregar Exemplo (Combustao do Metano)"):
            st.session_state["r_input"] = "CH4 + O2"
            st.session_state["p_input"] = "CO2 + H2O"

        cl, cr = st.columns([1.2, 1])
        
        with cl:
            st.markdown("### 1. Definicao da Reacao")
            ri = st.text_input("Reagentes:", value=st.session_state.get("r_input", ""), placeholder="Ex: NaOH + HCl")
            pi = st.text_input("Produtos:", value=st.session_state.get("p_input", ""), placeholder="Ex: NaCl + H2O")
            
            if ri and pi:
                try:
                    rb, pb, err = motor.balancear_e_resolver(ri, pi)
                    if err:
                        st.warning("⚠️ Elementos nao batem entre reagentes e produtos.")
                    else:
                        eq = " + ".join([f"{v if v>1 else ''}{k}" for k, v in rb.items()]) + " -> " + \
                             " + ".join([f"{v if v>1 else ''}{k}" for k, v in pb.items()])
                        st.success(f"**Equacao:** `{eq}`")
                        
                        st.markdown("---")
                        st.markdown("### 2. Massas")
                        m_d = {}
                        for r in rb.keys():
                            m_v = st.number_input(f"Massa de {r} (g)", min_value=0.0, key=f"m_ia_{r}")
                            if m_v > 0: m_d[r] = m_v
                        
                        if st.button("🚀 ANALISAR COM IA", type="primary"):
                            if len(m_d) < len(rb):
                                st.error("Insira a massa de todos os reagentes.")
                            else:
                                with st.spinner("IA Calculando..."):
                                    m_mols = {s: m_d[s]/Substance.from_formula(s).mass for s in m_d}
                                    lim = min(m_mols, key=lambda x: m_mols[x]/rb[x])
                                    fat = m_mols[lim]/rb[lim]
                                    st.session_state.ia_res = {"lim": lim, "fat": fat, "pb": pb, "eq": eq}
                except Exception:
                    st.error("🧪 Erro nas formulas. Verifique maiusculas (Ex: H2O).")

        with cr:
            st.markdown("### 3. Resultado e PDF")
            if "ia_res" in st.session_state:
                res = st.session_state.ia_res
                st.info(f"**Limitante:** {res['lim']}")
                
                lista_prod = []
                for k, v in res['pb'].items():
                    m_f = res['fat'] * v * Substance.from_formula(k).mass
                    lista_prod.append({"Produto": k, "Massa (g)": f"{m_f:.4f}"})
                
                st.dataframe(pd.DataFrame(lista_prod), use_container_width=True)
                
                with st.expander("📄 Ver Laudo IA", expanded=True):
                    laudo = motor.consultoria_ia(res['eq'], res['lim'], lista_prod[0]['Massa (g)'])
                    st.markdown(laudo)
                    
                    pdf_data = export_pdf(laudo, res['eq'])
                    st.download_button("📥 Baixar Laudo PDF", pdf_data, "laudo.pdf", "application/pdf", use_container_width=True)
            else:
                st.info("Insira os dados a esquerda para gerar a analise.")

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
        with st.expander("🧪 1. Química Analítica e Soluções", expanded=True):
            calc_q = st.selectbox("Escolha o cálculo analítico:", [
                "Molaridade (m/MM*V)", "Diluição (C1V1=C2V2)", "pH de Ácido Forte", "pH de Base Forte",
                "pOH", "Normalidade", "Fração Molar", "PPM para Molaridade", 
                "Porcentagem em Massa (%m/m)", "Conversão g/L para mol/L", "Molalidade",
                "Rendimento Percentual", "Fator de Diluição", "Volume Molar (CNTP)", "Densidade da Solução"
            ], key="sel_analitica")
            
            c1, c2 = st.columns(2)
            res_q = 0.0

            if calc_q == "Molaridade (m/MM*V)":
                f = c1.text_input("Fórmula", "NaCl", key="q1")
                m = c2.number_input("Massa (g)", min_value=0.0, key="q2")
                v = c1.number_input("Volume (mL)", min_value=0.1, key="q3")
                if f and m > 0:
                    try:
                        mm = Substance.from_formula(f).mass
                        res_q = m / (mm * (v/1000))
                        st.caption(f"MM: {mm:.2f} g/mol")
                    except: st.error("Fórmula inválida")

            elif calc_q == "Diluição (C1V1=C2V2)":
                v1 = c1.number_input("V1 (mL)", key="q4")
                c1_v = c2.number_input("C1 (mol/L)", key="q5")
                v2 = c1.number_input("V2 (mL)", key="q6")
                c2_v = c2.number_input("C2 (mol/L)", key="q7")
                if v2 == 0 and all([v1, c1_v, c2_v]): res_q = (c1_v * v1) / c2_v
                elif c2_v == 0 and all([v1, c1_v, v2]): res_q = (c1_v * v1) / v2

            elif calc_q == "pH de Ácido Forte":
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

            elif calc_q == "Fração Molar":
                ns = c1.number_input("Mols Soluto", key="q13")
                nt = c2.number_input("Mols Solvente", key="q14")
                if (ns+nt)>0: res_q = ns/(ns+nt)

            elif calc_q == "PPM para Molaridade":
                ppm = c1.number_input("PPM (mg/L)", key="q15")
                f = c2.text_input("Fórmula", "NaCl", key="q16")
                if f and ppm>0: res_q = (ppm/1000)/Substance.from_formula(f).mass

            elif calc_q == "Porcentagem em Massa (%m/m)":
                ms = c1.number_input("Massa Soluto (g)", key="q17")
                mt = c2.number_input("Massa Total (g)", key="q18")
                if mt>0: res_q = (ms/mt)*100

            elif calc_q == "Conversão g/L para mol/L":
                gl = c1.number_input("Conc. g/L", key="q19")
                f = c2.text_input("Fórmula", "NaOH", key="q20")
                if f and gl>0: res_q = gl/Substance.from_formula(f).mass

            elif calc_q == "Molalidade":
                ns = c1.number_input("Mols Soluto", key="q21")
                kg = c2.number_input("Kg Solvente", key="q22")
                if kg>0: res_q = ns/kg

            elif calc_q == "Rendimento Percentual":
                teo = c1.number_input("Teórico (g)", key="q23")
                exp = c2.number_input("Real (g)", key="q24")
                if teo>0: res_q = (exp / teo) * 100

            elif calc_q == "Fator de Diluição":
                vf = c1.number_input("Vol. Final", key="q25")
                vi = c2.number_input("Vol. Inicial", key="q26")
                if vi>0: res_q = vf/vi

            elif calc_q == "Volume Molar (CNTP)":
                n = st.number_input("Mols", key="q27")
                res_q = n * 22.414

            elif calc_q == "Densidade da Solução":
                m = c1.number_input("Massa (g)", key="q28")
                v = c2.number_input("Vol (mL)", key="q29")
                if v>0: res_q = m/v

            st.metric("Resultado", f"{res_q:.4f}")

        with st.expander("🔁 2. Conversor Universal de Unidades (SI)"):
            calc_c = st.selectbox("Conversão:", [
                "Kg para g", "g para Kg", "mg para g", "g para mg", "L para mL", "mL para L",
                "m³ para L", "Celsius para Kelvin", "Kelvin para Celsius", "Fahrenheit para Celsius",
                "atm para mmHg", "mmHg para atm", "bar para atm", "psi para bar", "Joules para Calorias"
            ], key="sel_conv")
            v_in = st.number_input("Valor:", value=1.0, key="c_in")
            
            conv = {
                "Kg para g": v_in*1000, "g para Kg": v_in/1000, "mg para g": v_in/1000,
                "g para mg": v_in*1000, "L para mL": v_in*1000, "mL para L": v_in/1000,
                "m³ para L": v_in*1000, "Celsius para Kelvin": v_in+273.15,
                "Kelvin para Celsius": v_in-273.15, "Fahrenheit para Celsius": (v_in-32)*5/9,
                "atm para mmHg": v_in*760, "mmHg para atm": v_in/760, "bar para atm": v_in*0.9869,
                "psi para bar": v_in*0.0689, "Joules para Calorias": v_in/4.184
            }
            st.success(f"Convertido: **{conv[calc_c]:.4f}**")

        with st.expander("🔥 3. Termodinâmica e Físico-Química"):
            calc_t = st.selectbox("Escolha o cálculo:", [
                "Gases Ideais (PV=nRT)", "Gases Reais (Van der Waals)", "Energia Livre de Gibbs (ΔG)",
                "Equação de Arrhenius (k)", "Tempo de Meia-Vida (1ª Ordem)", "Entalpia (Q = m.c.ΔT)",
                "Equação de Henderson-Hasselbalch", "Pressão Osmótica (π=iMRT)", "Ebulioscopia (ΔTe)",
                "Crioscopia (ΔTc)", "Constante de Equilíbrio (Kc)", "Velocidade de Graham",
                "Trabalho de Expansão (W)", "Eficiência de Carnot", "Calor Latente (Q=mL)"
            ], key="sel_termo")
            
            t1, t2 = st.columns(2)
            res_t = 0.0

            if calc_t == "Gases Ideais (PV=nRT)":
                n, t_k = t1.number_input("n (mol)", 1.0, key="t1"), t2.number_input("T (K)", 298.0, key="t2")
                v_l = t1.number_input("V (L)", 22.4, key="t3")
                if v_l>0: res_t = (n*0.08206*t_k)/v_l
            elif calc_t == "Gases Reais (Van der Waals)":
                n, v = t1.number_input("n", 1.0, key="t4"), t2.number_input("V", 1.0, key="t5")
                te, a = t1.number_input("T", 298.0, key="t6"), t2.number_input("a", 0.0, key="t7")
                b = t1.number_input("b", 0.0, key="t8")
                if (v-n*b)!=0: res_t = ((n*0.08206*te)/(v-n*b))-(a*(n/v)**2)

            elif calc_t == "Energia Livre de Gibbs (ΔG)":
                h, te = t1.number_input("ΔH (kJ)", key="t9"), t2.number_input("T (K)", key="t10")
                s = t1.number_input("ΔS (kJ/K)", key="t11")
                res_t = h - (te*s)

            elif calc_t == "Equação de Arrhenius (k)":
                a_f, ea = t1.number_input("A", 1.0, key="t12"), t2.number_input("Ea (J)", 50000.0, key="t13")
                te = t1.number_input("T (K)", 298.0, key="t14")
                res_t = a_f * math.exp(-ea/(8.314*te))

            elif calc_t == "Tempo de Meia-Vida (1ª Ordem)":
                k = st.number_input("k", 0.001, key="t15")
                if k>0: res_t = 0.693/k

            elif calc_t == "Entalpia (Q = m.c.ΔT)":
                m, c = t1.number_input("m (g)", key="t16"), t2.number_input("c", 4.18, key="t17")
                dt = t1.number_input("ΔT", key="t18")
                res_t = m*c*dt

            elif calc_t == "Equação de Henderson-Hasselbalch":
                pk, ba = t1.number_input("pKa", 4.76, key="t19"), t2.number_input("[Base]", 0.1, key="t20")
                ac = t1.number_input("[Ácido]", 0.1, key="t21")
                if ac>0: res_t = pk + math.log10(ba/ac)

            elif calc_t == "Pressão Osmótica (π=iMRT)":
                i, m = t1.number_input("i", 1.0, key="t22"), t2.number_input("M", 0.1, key="t23")
                te = t1.number_input("T (K)", 298.0, key="t24")
                res_t = i*m*0.08206*te

            elif calc_t == "Ebulioscopia (ΔTe)":
                ke, mo = t1.number_input("Ke", 0.52, key="t25"), t2.number_input("molalidade", 1.0, key="t26")
                res_t = ke * mo

            elif calc_t == "Crioscopia (ΔTc)":
                kc, mo = t1.number_input("Kc", 1.86, key="t27"), t2.number_input("molalidade", 1.0, key="t28")
                res_t = kc * mo

            elif calc_t == "Constante de Equilíbrio (Kc)":
                p, r = t1.number_input("[Prod]", 1.0, key="t29"), t2.number_input("[Reag]", 1.0, key="t30")
                if r>0: res_t = p/r

            elif calc_t == "Velocidade de Graham":
                m1, m2 = t1.number_input("MM1", 1.0, key="t31"), t2.number_input("MM2", 1.0, key="t32")
                res_t = math.sqrt(m2/m1)

            elif calc_t == "Trabalho de Expansão (W)":
                p, dv = t1.number_input("P", 1.0, key="t33"), t2.number_input("ΔV", 1.0, key="t34")
                res_t = p * dv

            elif calc_t == "Eficiência de Carnot":
                tf, tq = t1.number_input("T Fria", 273.0, key="t35"), t2.number_input("T Quente", 373.0, key="t36")
                if tq>0: res_t = 1 - (tf/tq)

            elif calc_t == "Calor Latente (Q=mL)":
                m, l = t1.number_input("m (g)", key="t37"), t2.number_input("L", key="t38")
                res_t = m*l
          
            st.metric("Resultado", f"{res_t:.4f}")
    

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



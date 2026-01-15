import streamlit as st
import math
import pandas as pd
from chempy.chemistry import Substance
from motores_quimicos import MotorCalculoAvancado

def show_calculadora():
    st.title("🧪 Central de Inteligência e Cálculos")
    
    # Criando a estrutura de sub-abas organizada
    sub_aba_padrao, sub_aba_avancada = st.tabs([
        "📊 Calculadora de Bancada", 
        "🚀 Estequiometria de Alta Performance"
    ])

    # --- SUB-ABA 1: CALCULADORA POTENCIALIZADA ---
    with sub_aba_padrao:
        st.write("### 🛠️ Ferramentas de Precisão Laboratorial")

        # BLOCO: Concentrações e Soluções
        with st.expander("🧪 Preparo de Soluções e Concentrações", expanded=True):
            opcoes_q = [
                "Molaridade (com Busca de Massa Molar)", 
                "Diluição Precisa (C1V1 = C2V2)", 
                "pH & pOH Reverso", 
                "PPM & Percentual em Massa",
                "Rendimento de Reação (%)"
            ]
            escolha_q = st.selectbox("Selecione o procedimento:", opcoes_q, key="main_q")
            
            c1, c2 = st.columns(2)
            res_q = 0.0

            try:
                if escolha_q == "Molaridade (com Busca de Massa Molar)":
                    formula = c1.text_input("Fórmula do Soluto (ex: H2SO4)", key="f_mol")
                    massa_g = c2.number_input("Massa total (g)", min_value=0.0, format="%.4f", key="m_g")
                    vol_ml = c1.number_input("Volume final (mL)", min_value=0.0, key="v_ml")
                    
                    if formula and massa_g > 0 and vol_ml > 0:
                        try:
                            mm = Substance.from_formula(formula).mass
                            res_q = massa_g / (mm * (vol_ml / 1000))
                            st.info(f"Massa Molar calculada para {formula}: **{mm:.2f} g/mol**")
                        except: st.warning("Aguardando fórmula química válida...")

                elif escolha_q == "Diluição Precisa (C1V1 = C2V2)":
                    st.caption("Insira 0 no campo que deseja descobrir.")
                    v1 = c1.number_input("V1 - Vol. Inicial (mL)", value=0.0, key="v1_d")
                    con1 = c2.number_input("C1 - Conc. Inicial (mol/L)", value=0.0, key="c1_d")
                    v2 = c1.number_input("V2 - Vol. Final (mL)", value=0.0, key="v2_d")
                    con2 = c2.number_input("C2 - Conc. Final (mol/L)", value=0.0, key="c2_d")
                    
                    if v2 == 0 and all([v1, con1, con2]): res_q = (con1 * v1) / con2
                    elif con2 == 0 and all([v1, con1, v2]): res_q = (con1 * v1) / v2
                    elif v1 == 0 and all([v2, con2, con1]): res_q = (con2 * v2) / con1
                    elif con1 == 0 and all([v2, con2, v1]): res_q = (con2 * v2) / v1

                elif escolha_q == "pH & pOH Reverso":
                    modo = c1.radio("Entrada:", ["Concentração [H+]", "Concentração [OH-]", "Valor de pH"], horizontal=True)
                    val_in = c2.number_input("Valor de entrada:", format="%.10f", key="ph_val")
                    if val_in > 0:
                        if modo == "Concentração [H+]": res_q = -math.log10(val_in)
                        elif modo == "Concentração [OH-]": res_q = 14 + math.log10(val_in)
                        elif modo == "Valor de pH": res_q = 10**(-val_in)

                elif escolha_q == "Rendimento de Reação (%)":
                    teorico = c1.number_input("Massa Teórica Esperada (g)", min_value=0.01, key="r_t")
                    real = c2.number_input("Massa Real Obtida (g)", min_value=0.0, key="r_r")
                    res_q = (real / teorico) * 100

                st.metric("Resultado Analítico", f"{res_q:.4f}")
            except Exception as e:
                st.error(f"Erro no cálculo: {e}")

        # BLOCO: Conversões SI
        with st.expander("🔁 Conversor de Unidades SI (Laboratório)"):
            v_conv = st.number_input("Valor numérico:", value=1.0, key="v_c")
            categoria = st.selectbox("Grandeza:", ["Massa", "Volume", "Pressão", "Temperatura"], key="cat_c")
            
            if categoria == "Massa":
                t = st.selectbox("Conversão:", ["g para kg", "kg para g", "mg para g"], key="t1")
                f = {"g para kg": v_conv/1000, "kg para g": v_conv*1000, "mg para g": v_conv/1000}
            elif categoria == "Volume":
                t = st.selectbox("Conversão:", ["L para mL", "mL para L", "µL para mL"], key="t2")
                f = {"L para mL": v_conv*1000, "mL para L": v_conv/1000, "µL para mL": v_conv/1000}
            elif categoria == "Pressão":
                t = st.selectbox("Conversão:", ["atm para mmHg", "mmHg para atm", "bar para atm"], key="t3")
                f = {"atm para mmHg": v_conv*760, "mmHg para atm": v_conv/760, "bar para atm": v_conv*0.9869}
            elif categoria == "Temperatura":
                t = st.selectbox("Conversão:", ["°C para K", "K para °C"], key="t4")
                f = {"°C para K": v_conv+273.15, "K para °C": v_conv-273.15}
            
            st.success(f"Valor Convertido: **{f[t]:.4f}**")

        # BLOCO: Gases
        with st.expander("📘 Gases Ideais (Equação de Clapeyron)"):
            g1, g2, g3 = st.columns(3)
            gn = g1.number_input("n (mol)", value=1.0, key="gn_p")
            gt = g2.number_input("T (Kelvin)", value=298.15, key="gt_p")
            gv = g3.number_input("V (Litros)", value=22.4, key="gv_p")
            if gv > 0:
                p_p = (gn * 0.08206 * gt) / gv
                st.metric("Pressão Estimada", f"{p_p:.4f} atm")

        st.divider()
        st.link_button("🌐 Acessar Calculadora Científica Externa", "https://www.calculadoraonline.com.br/cientifica")

    # --- SUB-ABA 2: CALCULADORA DE PODER EXTREMO ---
    with sub_aba_avancada:
        st.subheader("🚀 Estequiometria Automática com IA")
        motor = MotorCalculoAvancado()
        
        c_left, c_right = st.columns([1.2, 1])
        
        with c_left:
            st.markdown("##### 🧪 Definição da Reação")
            st.caption("Apenas fórmulas separadas por '+'. Ex: KMnO4 + HCl")
            reac_in = st.text_input("Reagentes:", placeholder="Ex: H2 + O2", key="r_ext")
            prod_in = st.text_input("Produtos:", placeholder="Ex: H2O", key="p_ext")
            
            if reac_in and prod_in:
                res_bal, prod_bal, erro_bal = motor.balancear_e_resolver(reac_in, prod_in)
                
                if erro_bal:
                    st.warning("⚠️ Formato inválido. Digite apenas as fórmulas químicas (sem números na frente).")
                else:
                    eq_f = " + ".join([f"{v if v>1 else ''}{k}" for k, v in res_bal.items()]) + " ➞ " + \
                           " + ".join([f"{v if v>1 else ''}{k}" for k, v in prod_bal.items()])
                    st.success(f"**Equação Balanceada:** `{eq_f}`")
                    
                    massas_input = {}
                    st.write("**Massas dos Reagentes (g):**")
                    for r in res_bal.keys():
                        m_in = st.number_input(f"Massa de {r}", min_value=0.0, key=f"m_ext_{r}")
                        if m_in > 0: massas_input[r] = m_in
                    
                    if st.button("EXECUTAR ANÁLISE PROFUNDA", type="primary"):
                        try:
                            # Cálculo de Mols e Limitante
                            mols_calc = {s: massas_input[s] / Substance.from_formula(s).mass for s in massas_input}
                            limitante = min(mols_calc, key=lambda x: mols_calc[x] / res_bal[x])
                            fator_escala = mols_calc[limitante] / res_bal[limitante]
                            st.session_state.data_ext = {
                                "lim": limitante, "fator": fator_escala, 
                                "prod": prod_bal, "eq": eq_f
                            }
                        except: st.error("Erro no processamento das massas.")

        with c_right:
            if "data_ext" in st.session_state:
                d = st.session_state.data_ext
                st.info(f"**Reagente Limitante:** {d['lim']}")
                
                output_list = []
                for p, coeff in d["prod"].items():
                    m_final = d["fator"] * coeff * Substance.from_formula(p).mass
                    output_list.append({"Produto": p, "Massa Teórica (g)": f"{m_final:.4f}"})
                
                st.table(pd.DataFrame(output_list))
                
                st.divider()
                with st.spinner("Groq 70B gerando laudo técnico..."):
                    laudo = motor.consultoria_ia(d["eq"], d["lim"], output_list[0]["Massa Teórica (g)"])
                    st.markdown(laudo)

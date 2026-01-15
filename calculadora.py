import streamlit as st
import math
import pandas as pd
from chempy.chemistry import Substance
from motores_quimicos import MotorCalculoAvancado

def show_calculadora():
    st.title("🧪 Calculadora Química e Conversor SI")
    
    sub_aba_padrao, sub_aba_avancada = st.tabs(["📊 Calculadora Padrão", "🚀 Estequiometria Avançada (IA)"])

    # --- SUB-ABA 1: CALCULADORA PADRÃO (LOGICA CORRIGIDA) ---
    with sub_aba_padrao:
        st.write("Realize cálculos de concentração, diluição e gases.")

        with st.expander("🧪 Fórmulas de Concentração e Química", expanded=True):
            opcoes_quimica = [
                "Molaridade", "Diluição (C1V1 = C2V2)", "pH", "PPM"
            ]
            escolha_q = st.selectbox("Selecione o Cálculo:", opcoes_quimica, key="sel_q_principal")
            
            col1, col2 = st.columns(2)
            res_q = 0.0

            if escolha_q == "Molaridade":
                mol = col1.number_input("Moles do soluto (mol)", format="%.4f", key="input_mol")
                vol = col2.number_input("Volume da solução (L)", min_value=0.0, format="%.4f", key="input_vol")
                if vol > 0: res_q = mol / vol

            elif escolha_q == "Diluição (C1V1 = C2V2)":
                st.info("Digite os três valores conhecidos e deixe 0.0 naquele que deseja descobrir.")
                c1 = col1.number_input("C1 (Conc. Inicial)", value=0.0, format="%.4f", key="d1")
                v1 = col2.number_input("V1 (Vol. Inicial)", value=0.0, format="%.4f", key="d2")
                c2 = col1.number_input("C2 (Conc. Final)", value=0.0, format="%.4f", key="d3")
                v2 = col2.number_input("V2 (Vol. Final)", value=0.0, format="%.4f", key="d4")
                
                # Lógica de isolamento da variável
                if c2 == 0 and all([c1, v1, v2]): res_q = (c1 * v1) / v2
                elif v2 == 0 and all([c1, v1, c2]): res_q = (c1 * v1) / c2
                elif c1 == 0 and all([c2, v2, v1]): res_q = (c2 * v2) / v1
                elif v1 == 0 and all([c2, v2, c1]): res_q = (c2 * v2) / c1

            elif escolha_q == "pH":
                h = st.number_input("Concentração de H⁺ (mol/L)", format="%.10f", min_value=0.0, key="input_ph")
                if h > 0: res_q = -math.log10(h)

            elif escolha_q == "PPM":
                m_soluto = col1.number_input("Massa soluto (mg)", key="input_ppm_m")
                m_solucao = col2.number_input("Massa solução (kg)", min_value=0.0001, key="input_ppm_s")
                res_q = m_soluto / m_solucao

            st.metric("Resultado Final", f"{res_q:.4f}")

        with st.expander("🔁 Conversões de Unidades"):
            c_val, c_tipo = st.columns([2, 1])
            valor_conv = c_val.number_input("Valor:", value=1.0, key="v_conv")
            tipo_conv = c_tipo.selectbox("De/Para:", [
                "g para kg", "kg para g", "L para mL", "mL para L", "°C para K"
            ], key="t_conv")
            
            f_conv = {
                "g para kg": valor_conv / 1000, "kg para g": valor_conv * 1000,
                "L para mL": valor_conv * 1000, "mL para L": valor_conv / 1000,
                "°C para K": valor_conv + 273.15
            }
            st.success(f"Convertido: **{f_conv[tipo_conv]:.4f}**")

        with st.expander("📘 Termodinâmica e Gases"):
            n = st.number_input("n (mol)", value=1.0, key="g1")
            t = st.number_input("T (K)", value=298.15, key="g2")
            v = st.number_input("V (L)", value=22.4, key="g3")
            if v > 0:
                res_p = (n * 0.0821 * t) / v
                st.metric("Pressão (PV=nRT)", f"{res_p:.4f} atm")

    # --- SUB-ABA 2: CALCULADORA AVANÇADA (AMIGÁVEL) ---
    with sub_aba_avancada:
        st.subheader("🚀 Estequiometria Avançada")
        motor = MotorCalculoAvancado()
        
        c_l, c_r = st.columns(2)
        with c_l:
            st.markdown("##### 🧪 Reação")
            st.caption("Dica: Digite apenas as fórmulas (ex: H2 + O2). O sistema balanceia para você.")
            r_in = st.text_input("Reagentes", placeholder="Ex: NaOH + HCl", key="r_adv")
            p_in = st.text_input("Produtos", placeholder="Ex: NaCl + H2O", key="p_adv")
            
            if r_in and p_in:
                # O TRATAMENTO AMIGÁVEL ACONTECE AQUI
                reac_b, prod_b, err = motor.balancear_e_resolver(r_in, p_in)
                
                if err:
                    st.warning("⚠️ Formato inválido. Use apenas as fórmulas separadas por '+'. Não inclua números antes das fórmulas.")
                else:
                    eq_f = " + ".join([f"{v if v>1 else ''}{k}" for k, v in reac_b.items()]) + " ➞ " + \
                           " + ".join([f"{v if v>1 else ''}{k}" for k, v in prod_b.items()])
                    st.success(f"Equação: {eq_f}")
                    
                    massas = {}
                    for r in reac_b.keys():
                        m = st.number_input(f"Massa de {r} (g)", min_value=0.0, key=f"m_ad_{r}")
                        if m > 0: massas[r] = m
                    
                    if st.button("CALCULAR IMPACTO", type="primary"):
                        try:
                            mols = {s: massas[s] / Substance.from_formula(s).mass for s in massas}
                            lim = min(mols, key=lambda x: mols[x] / reac_b[x])
                            fator = mols[lim] / reac_b[lim]
                            st.session_state.res_adv = {"lim": lim, "fator": fator, "prod_b": prod_b, "eq": eq_f}
                        except:
                            st.error("Erro ao processar massas. Verifique as fórmulas.")

        with c_r:
            if "res_adv" in st.session_state:
                res = st.session_state.res_adv
                st.info(f"**Reagente Limitante:** {res['lim']}")
                
                tab = []
                for p, c in res["prod_b"].items():
                    m_p = res["fator"] * c * Substance.from_formula(p).mass
                    tab.append({"Produto": p, "Massa (g)": f"{m_p:.4f}"})
                
                st.table(pd.DataFrame(tab))
                with st.spinner("IA Analisando..."):
                    st.markdown(motor.consultoria_ia(res["eq"], res["lim"], tab[0]["Massa (g)"]))

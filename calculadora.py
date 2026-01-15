import streamlit as st
import math
import pandas as pd
from chempy.chemistry import Substance
from motores_quimicos import MotorCalculoAvancado

def show_calculadora():
    st.title("🧪 Calculadora Química e Conversor SI")
    
    sub_aba_padrao, sub_aba_avancada = st.tabs(["📊 Calculadora Padrão", "🚀 Estequiometria Avançada (IA)"])

    with sub_aba_padrao:
        st.write("Realize cálculos de molaridade, diluição, conversões e termodinâmica.")

        with st.expander("🧪 Fórmulas de Concentração e Química", expanded=True):
            opcoes_quimica = [
                "Molaridade", "Molalidade", "Diluição (C1V1 = C2V2)", "pH", "pOH",
                "Densidade", "% em massa", "PPM", "Volume molar (CNTP)", "Rendimento"
            ]
            escolha_q = st.selectbox("Selecione o Cálculo:", opcoes_quimica)
            col1, col2 = st.columns(2)
            res_q = 0.0

            try:
                if escolha_q == "Molaridade":
                    mol = col1.number_input("Moles do soluto (mol)", format="%.4f", key="q1")
                    vol = col2.number_input("Volume da solução (L)", min_value=0.0001, key="q2")
                    if vol > 0: res_q = mol / vol

                elif escolha_q == "Diluição (C1V1 = C2V2)":
                    st.info("Deixe em 0 o valor que deseja descobrir")
                    c1 = col1.number_input("C1 (Conc. Inicial)", format="%.4f", key="q3")
                    v1 = col2.number_input("V1 (Vol. Inicial)", format="%.4f", key="q4")
                    c2 = col1.number_input("C2 (Conc. Final)", format="%.4f", key="q5")
                    v2 = col2.number_input("V2 (Vol. Final)", format="%.4f", key="q6")
                    if c2 == 0 and v2 != 0: res_q = (c1 * v1) / v2
                    elif v2 == 0 and c2 != 0: res_q = (c1 * v1) / c2

                elif escolha_q == "pH":
                    h = st.number_input("Concentração de H⁺ (mol/L)", format="%.10f", min_value=0.0, key="q7")
                    if h > 0: res_q = -math.log10(h)

                elif escolha_q == "PPM":
                    m_soluto = col1.number_input("Massa soluto (mg)", key="q8")
                    m_solucao = col2.number_input("Massa solução (kg)", min_value=0.0001, key="q9")
                    res_q = m_soluto / m_solucao

                st.metric("Resultado", f"{res_q:.4f}")
            except Exception as e:
                st.error(f"Erro: {e}")

        with st.expander("🔁 Conversões de Unidades"):
            col_c1, col_c2 = st.columns([2, 1])
            valor_conv = col_c1.number_input("Valor para converter:", value=1.0, key="c1")
            tipo_conv = col_c2.selectbox("Conversão:", [
                "g para kg", "kg para g", "L para mL", "mL para L", 
                "°C para K", "atm para mmHg", "cal para J"
            ], key="c2")
            f_conv = {
                "g para kg": valor_conv / 1000, "kg para g": valor_conv * 1000,
                "L para mL": valor_conv * 1000, "mL para L": valor_conv / 1000,
                "°C para K": valor_conv + 273.15, "atm para mmHg": valor_conv * 760,
                "cal para J": valor_conv * 4.184
            }
            st.success(f"Resultado: **{f_conv[tipo_conv]:.4f}**")

        with st.expander("📘 Termodinâmica e Gases"):
            op_avancada = st.selectbox("Cálculo Avançado:", ["Gases Ideais (PV=nRT)", "Energia de Gibbs"], key="t1")
            if op_avancada == "Gases Ideais (PV=nRT)":
                n = st.number_input("n (mol)", value=1.0, key="t2")
                t = st.number_input("T (K)", value=298.15, key="t3")
                v = st.number_input("V (L)", value=22.4, key="t4")
                res_p = (n * 0.0821 * t) / v
                st.metric("Pressão Estimada (atm)", f"{res_p:.4f}")

        st.divider()
        if st.button("🌐 Abrir Calculadora Científica Online"):
            st.link_button("Ir para Calculadora Online", "https://www.calculadoraonline.com.br/cientifica")

    with sub_aba_avancada:
        st.subheader("🚀 Estequiometria Avançada (Poder Extremo)")
        motor = MotorCalculoAvancado()
        c_left, c_right = st.columns([1, 1])
        
        with c_left:
            r_in = st.text_input("Reagentes (ex: NaOH + HCl)", key="adv_1")
            p_in = st.text_input("Produtos (ex: NaCl + H2O)", key="adv_2")
            if r_in and p_in:
                reac_b, prod_b, err = motor.balancear_e_resolver(r_in, p_in)
                if err: st.error(err)
                else:
                    eq_f = " + ".join([f"{v if v>1 else ''}{k}" for k, v in reac_b.items()]) + " ➞ " + \
                           " + ".join([f"{v if v>1 else ''}{k}" for k, v in prod_b.items()])
                    st.code(eq_f)
                    massas = {}
                    for r in reac_b.keys():
                        m = st.number_input(f"Massa {r} (g)", min_value=0.0, key=f"ma_{r}")
                        if m > 0: massas[r] = m
                    
                    if st.button("CALCULAR COM IA", type="primary", key="btn_adv"):
                        mols = {s: massas[s] / Substance.from_formula(s).mass for s in massas}
                        lim = min(mols, key=lambda x: mols[x] / reac_b[x])
                        fator = mols[lim] / reac_b[lim]
                        st.session_state.res_adv = {"lim": lim, "fator": fator, "prod_b": prod_b, "eq": eq_f}

        with c_right:
            if "res_adv" in st.session_state:
                res = st.session_state.res_adv
                st.info(f"**Limitante:** {res['lim']}")
                tab_data = []
                for p, c in res["prod_b"].items():
                    m_p = res["fator"] * c * Substance.from_formula(p).mass
                    tab_data.append({"Produto": p, "Massa (g)": f"{m_p:.4f}"})
                st.table(pd.DataFrame(tab_data))
                st.divider()
                with st.spinner("Analisando..."):
                    st.markdown(motor.consultoria_ia(res["eq"], res["lim"], tab_data[0]["Massa (g)"]))

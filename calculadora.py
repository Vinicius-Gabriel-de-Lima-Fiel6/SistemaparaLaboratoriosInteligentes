import streamlit as st
import math
import pandas as pd
import numpy as np
from chempy.chemistry import Substance
from motores_quimicos import MotorCalculoAvancado

def show_calculadora():
    st.title("🧪 Central de Inteligência Química")
    
    tab_bancada, tab_avancada = st.tabs(["📊 Power Bancada", "🚀 Estequiometria IA"])

    with tab_bancada:
        # --- PARTE 1: QUÍMICA ANALÍTICA E SOLUÇÕES ---
        with st.expander("🧪 1. Química Analítica e Soluções", expanded=True):
            calc_q = st.selectbox("Escolha o cálculo analítico:", [
                "Molaridade (m/MM*V)", "Diluição (C1V1=C2V2)", "pH de Ácido Forte", "pH de Base Forte",
                "pOH", "Massa para Normalidade", "Fração Molar", "PPM para Molaridade", 
                "Porcentagem em Massa (%m/m)", "Conversão g/L para mol/L", "Molalidade",
                "Rendimento Percentual", "Fator de Diluição", "Volume Molar (CNTP)", "Densidade da Solução"
            ])
            
            c1, c2 = st.columns(2)
            res_q = 0.0

            if calc_q == "Molaridade (m/MM*V)":
                formula = c1.text_input("Fórmula do Soluto", "NaCl", key="q1")
                massa = c2.number_input("Massa (g)", min_value=0.0, key="q2")
                vol = c1.number_input("Volume (mL)", min_value=0.1, key="q3")
                if formula and massa > 0:
                    mm = Substance.from_formula(formula).mass
                    res_q = massa / (mm * (vol/1000))
                    st.caption(f"Massa Molar: {mm:.2f} g/mol")

            elif calc_q == "Diluição (C1V1=C2V2)":
                v1 = c1.number_input("V1 Inicial (mL)", key="q4")
                c1_v = c2.number_input("C1 Inicial (mol/L)", key="q5")
                v2 = c1.number_input("V2 Final (mL)", key="q6")
                c2_v = c2.number_input("C2 Final (mol/L)", key="q7")
                if v2 == 0 and all([v1, c1_v, c2_v]): res_q = (c1_v * v1) / c2_v
                elif c2_v == 0 and all([v1, c1_v, v2]): res_q = (c1_v * v1) / v2

            elif calc_q == "pH de Ácido Forte":
                conc = st.number_input("Concentração [H+] (mol/L)", format="%.10f", key="q8")
                if conc > 0: res_q = -math.log10(conc)

            elif calc_q == "Rendimento Percentual":
                teo = c1.number_input("Massa Teórica (g)", key="q9")
                exp = c2.number_input("Massa Experimental (g)", key="q10")
                if teo > 0: res_q = (exp / teo) * 100

            st.metric(f"Resultado: {calc_q}", f"{res_q:.4f}")

        # --- PARTE 2: CONVERSOR UNIVERSAL DE UNIDADES ---
        with st.expander("🔁 2. Conversor Universal de Unidades (SI)", expanded=False):
            calc_c = st.selectbox("Escolha a grandeza para converter:", [
                "Kg para g", "g para Kg", "mg para g", "g para mg", "L para mL", "mL para L",
                "m³ para L", "Celsius para Kelvin", "Kelvin para Celsius", "atm para mmHg",
                "mmHg para atm", "bar para atm", "psi para bar", "Joules para Calorias", "Calorias para Joules"
            ])
            v_in = st.number_input("Valor de entrada:", value=1.0, key="c_in")
            
            fatores = {
                "Kg para g": v_in * 1000, "g para Kg": v_in / 1000, "mg para g": v_in / 1000,
                "g para mg": v_in * 1000, "L para mL": v_in * 1000, "mL para L": v_in / 1000,
                "m³ para L": v_in * 1000, "Celsius para Kelvin": v_in + 273.15,
                "Kelvin para Celsius": v_in - 273.15, "atm para mmHg": v_in * 760,
                "mmHg para atm": v_in / 760, "bar para atm": v_in * 0.9869,
                "psi para bar": v_in * 0.0689, "Joules para Calorias": v_in / 4.184,
                "Calorias para Joules": v_in * 4.184
            }
            st.success(f"Convertido: **{fatores[calc_c]:.4f}**")

        # --- PARTE 3: TERMODINÂMICA, GASES E FÍSICO-QUÍMICA ---
        with st.expander("🔥 3. Termodinâmica e Físico-Química", expanded=False):
            calc_t = st.selectbox("Escolha o cálculo termodinâmico:", [
                "Gases Ideais (PV=nRT)", "Gases Reais (Van der Waals)", "Energia Livre de Gibbs (ΔG)",
                "Equação de Arrhenius (k)", "Tempo de Meia-Vida (1ª Ordem)", "Entalpia (ΔH = m.c.ΔT)",
                "Equação de Henderson-Hasselbalch", "Pressão Osmótica", "Ponto de Ebulição (Ebulioscopia)",
                "Constante de Equilíbrio (Kc)", "Velocidade Média de Difusão (Graham)",
                "Energia de Ativação", "Trabalho de Expansão (W)", "Eficiência de Carnot", "Calor Latente"
            ])
            
            t1, t2 = st.columns(2)
            res_t = 0.0

            if calc_t == "Gases Ideais (PV=nRT)":
                n = t1.number_input("n (mols)", value=1.0, key="t1")
                temp = t2.number_input("T (Kelvin)", value=298.0, key="t2")
                vol = t1.number_input("V (Litros)", value=22.4, key="t3")
                res_t = (n * 0.08206 * temp) / vol
                st.metric("Pressão (atm)", f"{res_t:.4f}")

            elif calc_t == "Gases Reais (Van der Waals)":
                n = t1.number_input("n (mol)", 1.0, key="t4")
                v = t2.number_input("V (L)", 1.0, key="t5")
                te = t1.number_input("T (K)", 298.0, key="t6")
                a = t2.number_input("Constante a", 0.0, key="t7")
                b = t1.number_input("Constante b", 0.0, key="t8")
                res_t = ((n * 0.08206 * te) / (v - n*b)) - (a * (n/v)**2)

            elif calc_t == "Equação de Henderson-Hasselbalch":
                pka = t1.number_input("pKa", 4.76, key="t9")
                base = t2.number_input("[Base]", 0.1, key="t10")
                acido = t1.number_input("[Ácido]", 0.1, key="t11")
                if acido > 0: res_t = pka + math.log10(base/acido)

            elif calc_t == "Tempo de Meia-Vida (1ª Ordem)":
                k = st.number_input("Constante k", 0.001, format="%.4f", key="t12")
                res_t = 0.693 / k

            st.metric(f"Resultado: {calc_t}", f"{res_t:.4f}")

    # --- SUB-ABA 2: ESTEQUIOMETRIA IA (PODER EXTREMO) ---
    with tab_avancada:
        st.subheader("🚀 Estequiometria Automática e Consultoria IA")
        motor = MotorCalculoAvancado()
        
        col_l, col_r = st.columns([1.2, 1])
        with col_l:
            reac = st.text_input("Reagentes:", placeholder="Ex: H2 + O2", key="adv_r")
            prod = st.text_input("Produtos:", placeholder="Ex: H2O", key="adv_p")
            
            if reac and prod:
                rb, pb, err = motor.balancear_e_resolver(reac, prod)
                if err:
                    st.warning("⚠️ Digite apenas as fórmulas. Ex: NaOH + HCl")
                else:
                    eq = " + ".join([f"{v if v>1 else ''}{k}" for k, v in rb.items()]) + " ➞ " + \
                         " + ".join([f"{v if v>1 else ''}{k}" for k, v in pb.items()])
                    st.success(f"Equação: {eq}")
                    
                    m_dict = {}
                    for r in rb.keys():
                        m_val = st.number_input(f"Massa de {r} (g)", min_value=0.0, key=f"m_{r}")
                        if m_val > 0: m_dict[r] = m_val
                    
                    if st.button("CALCULAR IMPACTO IA", type="primary"):
                        m_mols = {s: m_dict[s] / Substance.from_formula(s).mass for s in m_dict}
                        lim = min(m_mols, key=lambda x: m_mols[x] / rb[x])
                        fat = m_mols[lim] / rb[lim]
                        st.session_state.calc_ia = {"lim": lim, "fat": fat, "pb": pb, "eq": eq}

        with col_r:
            if "calc_ia" in st.session_state:
                res = st.session_state.calc_ia
                st.info(f"**Limitante:** {res['lim']}")
                lista = []
                for p, c in res["pb"].items():
                    m_f = res["fat"] * c * Substance.from_formula(p).mass
                    lista.append({"Produto": p, "Massa (g)": f"{m_f:.4f}"})
                st.table(pd.DataFrame(lista))
                with st.spinner("IA Analisando..."):
                    st.markdown(motor.consultoria_ia(res["eq"], res["lim"], lista[0]["Massa (g)"]))

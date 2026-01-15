import streamlit as st
import math
import pandas as pd
import numpy as np
from chempy.chemistry import Substance
from motores_quimicos import MotorCalculoAvancado

def show_calculadora():
    st.title("🧪 Central de Inteligência e Cálculos")
    
    tab_bancada, tab_avancada = st.tabs(["📊 Power Bancada", "🚀 Estequiometria IA"])

    with tab_bancada:
        # Menu Lateral para Navegação de Módulos
        modulo = st.sidebar.selectbox("Módulo de Cálculo", [
            "🧪 Soluções e Concentrações",
            "🔁 Conversor Universal SI",
            "🔥 Termodinâmica & Gases",
            "⚡ Cinética & Equilíbrio",
            "🧬 Bioquímica & Clínicos",
            "🛡️ Segurança & Blindagem",
            "📈 Estatística de Controle"
        ])

        st.subheader(f"🛠️ {modulo}")
        c1, c2 = st.columns(2)
        res = 0.0

        # --- MÓDULO: CONVERSOR UNIVERSAL (Kg, G, Unidades SI) ---
        if modulo == "🔁 Conversor Universal SI":
            cat = st.selectbox("Grandeza:", ["Massa", "Volume", "Pressão", "Temperatura", "Energia/Potência"])
            v_in = st.number_input("Valor de Entrada:", value=1.0, key="conv_val")
            
            if cat == "Massa":
                op = st.selectbox("Conversão:", ["Kg para g", "g para Kg", "mg para g", "µg para mg", "Ton para Kg", "Libra para g"])
                f = {"Kg para g": v_in*1000, "g para Kg": v_in/1000, "mg para g": v_in/1000, "µg para mg": v_in/1000, "Ton para Kg": v_in*1000, "Libra para g": v_in*453.592}
            elif cat == "Volume":
                op = st.selectbox("Conversão:", ["L para mL", "mL para L", "m³ para L", "µL para mL", "Galão (US) para L"])
                f = {"L para mL": v_in*1000, "mL para L": v_in/1000, "m³ para L": v_in*1000, "µL para mL": v_in/1000, "Galão (US) para L": v_in*3.78541}
            elif cat == "Pressão":
                op = st.selectbox("Conversão:", ["atm para mmHg", "mmHg para atm", "bar para atm", "Pa para bar", "psi para bar"])
                f = {"atm para mmHg": v_in*760, "mmHg para atm": v_in/760, "bar para atm": v_in*0.9869, "Pa para bar": v_in/100000, "psi para bar": v_in*0.06894}
            elif cat == "Temperatura":
                op = st.selectbox("Conversão:", ["°C para K", "K para °C", "°F para °C", "°C para °F"])
                f = {"°C para K": v_in+273.15, "K para °C": v_in-273.15, "°F para °C": (v_in-32)*5/9, "°C para °F": (v_in*9/5)+32}
            
            st.success(f"Resultado Convertido: **{f[op]:.6f}**")

        # --- MÓDULO: SOLUÇÕES & CONCENTRAÇÕES ---
        elif modulo == "🧪 Soluções e Concentrações":
            op = st.selectbox("Tipo:", ["Molaridade (Auto-MM)", "Diluição Serial", "Normalidade", "Fração Molar", "PPM/PPB"])
            if op == "Molaridade (Auto-MM)":
                formula = c1.text_input("Fórmula do Soluto:", "NaOH")
                massa = c2.number_input("Massa (g):", 0.0)
                vol = c1.number_input("Vol. Final (mL):", 0.1)
                pureza = c2.slider("Pureza %:", 0, 100, 100)
                if formula and massa > 0:
                    mm = Substance.from_formula(formula).mass
                    res = (massa * (pureza/100)) / (mm * (vol/1000))
                    st.metric("Concentração (mol/L)", f"{res:.4f}")
                    st.caption(f"MM de {formula}: {mm:.2f} g/mol")

        # --- MÓDULO: TERMODINÂMICA ---
        elif modulo == "🔥 Termodinâmica & Gases":
            op = st.selectbox("Equação:", ["Gases Reais (Van der Waals)", "Energia de Gibbs", "Entalpia de Reação"])
            if op == "Gases Reais (Van der Waals)":
                n = c1.number_input("n (mol)", 1.0)
                v = c2.number_input("V (L)", 1.0)
                t = c1.number_input("T (K)", 298.0)
                a = c2.number_input("Constante a (atm.L²/mol²)", 0.0)
                b = c1.number_input("Constante b (L/mol)", 0.0)
                res = ((n * 0.08206 * t) / (v - n*b)) - (a * (n/v)**2)
                st.metric("Pressão Real (atm)", f"{res:.4f}")

        # --- MÓDULO: BIOQUÍMICA & CLÍNICOS ---
        elif modulo == "🧬 Bioquímica & Clínicos":
            op = st.selectbox("Análise:", ["Equação de Henderson-Hasselbalch (Tampão)", "Cinética Michaelis-Menten", "Clearance de Creatinina"])
            if op == "Equação de Henderson-Hasselbalch (Tampão)":
                pka = c1.number_input("pKa do par ácido/base", 4.76)
                base = c2.number_input("[Base Conjugada]", 0.1)
                acido = c1.number_input("[Ácido]", 0.1)
                if acido > 0:
                    res = pka + math.log10(base/acido)
                    st.metric("pH Resultante", f"{res:.4f}")

        # --- MÓDULO: ESTATÍSTICA DE CONTROLE ---
        elif modulo == "📈 Estatística de Controle":
            st.write("Insira as leituras para análise de erro e precisão (separadas por vírgula):")
            data_str = st.text_area("Dados Brutos:", "0.102, 0.105, 0.101, 0.103")
            if data_str:
                vals = [float(x.strip()) for x in data_str.split(",")]
                media = np.mean(vals)
                desvio = np.std(vals)
                cv = (desvio/media)*100
                st.metric("Média Amostral", f"{media:.4f}")
                c1.metric("Desvio Padrão", f"{desvio:.4f}")
                c2.metric("Coef. Variação (CV%)", f"{cv:.2f}%")
                st.progress(min(cv/10, 1.0), text="Índice de Imprecisão")

    # --- SUB-ABA 2: ESTEQUIOMETRIA IA (PODER EXTREMO) ---
    with tab_avancada:
        motor = MotorCalculoAvancado()
        cl1, cl2 = st.columns([1.2, 1])
        with cl1:
            st.write("### 🚀 Balanceamento Matricial & IA")
            ri = st.text_input("Reagentes (Ex: KMnO4 + HCl)", key="ri_ext")
            pi = st.text_input("Produtos (Ex: MnCl2 + KCl + Cl2 + H2O)", key="pi_ext")
            if ri and pi:
                rb, pb, err = motor.balancear_e_resolver(ri, pi)
                if err: st.warning("Verifique a sintaxe (Apenas fórmulas e '+')")
                else:
                    eq = " + ".join([f"{v if v>1 else ''}{k}" for k, v in rb.items()]) + " ➞ " + " + ".join([f"{v if v>1 else ''}{k}" for k, v in pb.items()])
                    st.success(eq)
                    massas = {}
                    for r in rb.keys():
                        mi = st.number_input(f"Massa {r} (g)", min_value=0.0, key=f"mi_{r}")
                        if mi > 0: massas[r] = mi
                    
                    if st.button("ANALISAR VIA GROQ", type="primary"):
                        mols = {s: massas[s] / Substance.from_formula(s).mass for s in massas}
                        lim = min(mols, key=lambda x: mols[x] / rb[x])
                        fat = mols[lim] / rb[lim]
                        
                        st.session_state.res_ia = {"lim": lim, "fat": fat, "pb": pb, "eq": eq}

        with cl2:
            if "res_ia" in st.session_state:
                res = st.session_state.res_ia
                st.info(f"**Limitante:** {res['lim']}")
                out = []
                for p, c in res["pb"].items():
                    m_p = res["fat"] * c * Substance.from_formula(p).mass
                    out.append({"Produto": p, "Massa (g)": f"{m_p:.4f}"})
                st.table(pd.DataFrame(out))
                with st.spinner("IA consultando bases científicas..."):
                    st.markdown(motor.consultoria_ia(res["eq"], res["lim"], out[0]["Massa (g)"]))

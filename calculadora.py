import streamlit as st
import math
import webbrowser

def show_calculadora():
    st.title("🧪 Calculadora Química e Conversor SI")
    st.write("Realize cálculos complexos de molaridade, diluição, conversões e termodinâmica.")

    # --- BLOCO 1: CÁLCULOS QUÍMICOS ---
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
                mol = col1.number_input("Moles do soluto (mol)", format="%.4f")
                vol = col2.number_input("Volume da solução (L)", min_value=0.0001)
                if vol > 0: res_q = mol / vol

            elif escolha_q == "Diluição (C1V1 = C2V2)":
                st.info("Deixe em 0 o valor que deseja descobrir")
                c1 = col1.number_input("C1 (Conc. Inicial)", format="%.4f")
                v1 = col2.number_input("V1 (Vol. Inicial)", format="%.4f")
                c2 = col1.number_input("C2 (Conc. Final)", format="%.4f")
                v2 = col2.number_input("V2 (Vol. Final)", format="%.4f")
                
                if c2 == 0 and v2 != 0: res_q = (c1 * v1) / v2
                elif v2 == 0 and c2 != 0: res_q = (c1 * v1) / c2

            elif escolha_q == "pH":
                h = st.number_input("Concentração de H⁺ (mol/L)", format="%.10f", min_value=0.0)
                if h > 0: res_q = -math.log10(h)

            elif escolha_q == "PPM":
                m_soluto = col1.number_input("Massa soluto (mg)")
                m_solucao = col2.number_input("Massa solução (kg)", min_value=0.0001)
                res_q = m_soluto / m_solucao

            st.metric("Resultado", f"{res_q:.4f}")
        except Exception as e:
            st.error(f"Erro no cálculo: {e}")

    # --- BLOCO 2: CONVERSÕES SI ---
    with st.expander("🔁 Conversões de Unidades"):
        col_c1, col_c2 = st.columns([2, 1])
        valor_conv = col_c1.number_input("Valor para converter:", value=1.0)
        tipo_conv = col_c2.selectbox("Conversão:", [
            "g para kg", "kg para g", "L para mL", "mL para L", 
            "°C para K", "atm para mmHg", "cal para J"
        ])

        f_conv = {
            "g para kg": valor_conv / 1000,
            "kg para g": valor_conv * 1000,
            "L para mL": valor_conv * 1000,
            "mL para L": valor_conv / 1000,
            "°C para K": valor_conv + 273.15,
            "atm para mmHg": valor_conv * 760,
            "cal para J": valor_conv * 4.184
        }
        st.success(f"Resultado convertido: **{f_conv[tipo_conv]:.4f}**")

    # --- BLOCO 3: AVANÇADO E LINKS ---
    with st.expander("📘 Termodinâmica e Gases"):
        op_avancada = st.selectbox("Cálculo Avançado:", ["Gases Ideais (PV=nRT)", "Energia de Gibbs"])
        if op_avancada == "Gases Ideais (PV=nRT)":
            st.write("Descobrir Pressão (P = nRT/V)")
            n = st.number_input("n (mol)", value=1.0)
            t = st.number_input("T (K)", value=298.15)
            v = st.number_input("V (L)", value=22.4)
            r = 0.0821
            res_p = (n * r * t) / v
            st.metric("Pressão Estimada (atm)", f"{res_p:.4f}")

    st.divider()
    if st.button("🌐 Abrir Calculadora Científica Online"):
        # No Streamlit, usamos links diretos ou st.link_button
        st.link_button("Ir para Calculadora Online", "https://www.calculadoraonline.com.br/cientifica")
import streamlit as st
import google.generativeai as genai
import cv2
from ultralytics import YOLO

# --- FUNÇÃO DE CONEXÃO ROBUSTA ---
def configurar_ia():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        genai.configure(api_key=api_key)
        
        # Lista de modelos para testar (do mais novo para o mais compatível)
        modelos_para_testar = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
        
        for nome_modelo in modelos_para_testar:
            try:
                model = genai.GenerativeModel(nome_modelo)
                # Teste de fumaça: tenta gerar algo vazio só para ver se o modelo existe
                model.generate_content("teste", generation_config={"max_output_tokens": 1})
                return model
            except:
                continue # Tenta o próximo da lista se der 404
        return None
    except Exception as e:
        st.error(f"Erro crítico de configuração: {e}")
        return None

# Inicializa o modelo
model_gemini = configurar_ia()

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None

    def get_ai_answer(self, user_text: str):
        if model_gemini is None:
            return "Erro: Não foi possível encontrar um modelo Gemini disponível. Verifique sua chave de API e o projeto no Google Cloud."
        
        try:
            # Responde em português como assistente de laboratório
            response = model_gemini.generate_content(
                f"Aja como assistente de laboratório técnico. Responda de forma curta e em português: {user_text}"
            )
            return response.text
        except Exception as e:
            return f"Erro na comunicação com o Google: {e}"

    def run_object_detection(self):
        """Detector YOLO"""
        if self.yolo_model is None:
            self.yolo_model = YOLO("yolov8n.pt")
        cap = cv2.VideoCapture(0)
        st.toast("Câmera ativada! Pressione 'Q' para fechar.")
        while True:
            success, img = cap.read()
            if not success: break
            results = self.yolo_model.track(img, persist=True)
            for result in results:
                img = result.plot()
            cv2.imshow("LabSmartAI - Detector de Objetos", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

# --- FUNÇÃO PRINCIPAL DA INTERFACE ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")
    
    # Verifica se a IA carregou
    if model_gemini is None:
        st.error("⚠️ O Google não reconheceu o modelo solicitado (Erro 404). Verifique se o seu arquivo 'requirements.txt' tem a linha: google-generativeai>=0.8.3")

    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()
    
    bot = st.session_state.ia_class

    # Links científicos
    st.subheader("🌐 Bases de Dados & IA Especializada")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.link_button("🧪 PubMed", "https://pubmed.ncbi.nlm.nih.gov/", use_container_width=True)
    with c2: st.link_button("🔬 Scielo", "https://scielo.org/", use_container_width=True)
    with c3: st.link_button("🎓 Scholar", "https://scholar.google.com/", use_container_width=True)
    with c4: st.link_button("🧠 Perplexity", "https://www.perplexity.ai/", use_container_width=True)

    st.divider()

    # Histórico do Chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada do Usuário
    if prompt := st.chat_input("Digite 'Oi' para testar..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = bot.get_ai_answer(prompt)
                st.markdown(resposta)
                st.session_state.chat_history.append({"role": "assistant", "content": resposta})

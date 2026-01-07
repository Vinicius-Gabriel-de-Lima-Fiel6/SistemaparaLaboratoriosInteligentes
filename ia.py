import streamlit as st
import google.generativeai as genai
import cv2
from ultralytics import YOLO

# --- CONFIGURAÇÃO DA IA ---
try:
    # Busca a chave nos Secrets (Imagem 1)
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    # Usamos 'gemini-1.5-flash' para evitar o erro 404 (Imagens 2 e 3)
    model_gemini = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Erro na configuração da IA: {e}")

class LabSmartAI:
    def __init__(self):
        self.yolo_model = None

    def get_ai_answer(self, user_text: str):
        try:
            # Responde em português como assistente de laboratório
            response = model_gemini.generate_content(f"Aja como assistente de laboratório. Responda em português: {user_text}")
            return response.text
        except Exception as e:
            return f"Erro ao processar: {e}"

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

# --- FUNÇÃO CHAMADA PELO APP.PY (Resolve o AttributeError da Imagem 8) ---
def show_chatbot():
    st.header("🤖 Assistente Científico com IA")

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

    # Chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Pergunte qualquer coisa ao Gemini..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            resposta = bot.get_ai_answer(prompt)
            st.markdown(resposta)
            st.session_state.chat_history.append({"role": "assistant", "content": resposta})

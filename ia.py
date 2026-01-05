import streamlit as st
import pandas as pd
import requests
from io import StringIO
from unidecode import unidecode
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import cv2
import numpy as np
from collections import defaultdict
from ultralytics import YOLO

class LabSmartAI:
    def __init__(self):
        # Configurações iniciais
        self.csv_url = "https://raw.githubusercontent.com/Vinicius-Gabriel-de-Lima-Fiel6/Projeto-QAT-LAB/refs/heads/main/LIVROS/REPONSES.csv"
        self._PT_STOPWORDS = {'a', 'o', 'de', 'do', 'da', 'e', 'é', 'em', 'para', 'com', 'que'}
        self._token_re = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+")
        
        # Carregamento automático ao instanciar
        self.df, self.vectorizer, self.tfidf_matrix = self._load_dataset_and_model()

    def _preprocess(self, text: str) -> str:
        if not isinstance(text, str):
            return ""
        text = unidecode(text.lower())
        tokens = self._token_re.findall(text)
        tokens = [t for t in tokens if t not in self._PT_STOPWORDS and len(t) > 1]
        return " ".join(tokens)

    def _load_dataset_and_model(self):
        try:
            response = requests.get(self.csv_url)
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                df["Pergunta_Preprocessado"] = df["Pergunta"].map(self._preprocess)
                
                vectorizer = TfidfVectorizer()
                tfidf_matrix = vectorizer.fit_transform(df["Pergunta_Preprocessado"])
                return df, vectorizer, tfidf_matrix
            return None, None, None
        except Exception:
            return None, None, None

    def get_answer(self, user_text: str) -> str:
        if self.df is None or self.vectorizer is None:
            return "Erro ao carregar a base de dados do laboratório."
        
        q = self._preprocess(user_text)
        if not q:
            return "Pode reformular sua pergunta? 🙂"
            
        q_vec = self.vectorizer.transform([q])
        sims = cosine_similarity(q_vec, self.tfidf_matrix)[0]
        idx = int(sims.argmax())
        return str(self.df["Resposta"].iloc[idx])

    def run_object_detection(self):
        """Método para rodar o YOLO (abre janela local)"""
        cap = cv2.VideoCapture(0)
        model = YOLO("yolov8n.pt")
        st.toast("Câmera ativada! Pressione 'Q' na janela da imagem para fechar.")
        
        while True:
            success, img = cap.read()
            if not success: break
            results = model.track(img, persist=True)
            for result in results:
                img = result.plot()
            
            cv2.imshow("LabSmartAI - Detector de Objetos", img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

# --- FUNÇÃO DE INTERFACE (A que o app.py chama) ---
def show_chatbot():
    st.header("🤖 Assistente de Inteligência Artificial")

    # Inicializa a classe no estado da sessão para não recarregar toda hora
    if "ia_class" not in st.session_state:
        st.session_state.ia_class = LabSmartAI()

    bot = st.session_state.ia_class

    # Sidebar com ferramentas
    with st.sidebar:
        st.subheader("Visão Computacional")
        if st.button("🚀 Abrir Detector (YOLO)", use_container_width=True):
            bot.run_object_detection()

    # Histórico de Chat
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Renderiza balões de conversa
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Entrada do Usuário
    if prompt := st.chat_input("Perqunte sobre reagentes ou procedimentos..."):
        # Adiciona pergunta do usuário
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Resposta da Classe
        resposta = bot.get_answer(prompt)
        
        # Adiciona resposta do bot
        with st.chat_message("assistant"):
            st.markdown(resposta)
            st.session_state.chat_history.append({"role": "assistant", "content": resposta})
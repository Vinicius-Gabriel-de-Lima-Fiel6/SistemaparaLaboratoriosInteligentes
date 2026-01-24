FROM python:3.10-slim

# Define o diretório onde o código vai morar no servidor
WORKDIR /app

# Instala dependências do sistema necessárias para algumas libs Python
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copia o requirements.txt primeiro (otimiza o cache do Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia TODOS os seus 15+ módulos, pastas de CSS e HTML
COPY . .

# Expõe a porta que o Koyeb vai usar para o mundo externo
EXPOSE 8080

# Comando para rodar o Streamlit
# IMPORTANTE: Mude 'seu_arquivo_principal.py' para o nome do seu arquivo
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

FROM python:3.10-slim

# 1. Instala dependências de sistema (Essencial para OpenCV, Scipy e WebRTC)
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    pkg-config \
    cmake \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Copia o requirements e instala (com upgrade do pip para evitar erros de versão)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copia o restante dos 15 módulos e arquivos
COPY . .

# 4. Porta do Koyeb
EXPOSE 8080

# 5. Comando de execução
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

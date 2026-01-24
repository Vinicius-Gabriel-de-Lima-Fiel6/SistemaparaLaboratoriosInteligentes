FROM python:3.10-slim

# 1. Instala apenas o essencial do sistema para não ocupar RAM
RUN apt-get update && apt-get install -y \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Configura o Python para não gerar arquivos inúteis (.pyc) e economizar RAM
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

COPY requirements.txt .

# 3. Instala um por um para não sobrecarregar a memória
# O --no-build-isolation ajuda se algumas libs tentarem baixar dependências extras
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8080

# 4. Comando para rodar o app limitando o uso de memória do Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0", "--logger.level=error"]

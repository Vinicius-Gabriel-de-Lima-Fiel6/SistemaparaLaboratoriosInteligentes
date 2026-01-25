# Estágio 1: Builder
FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y build-essential
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Estágio 2: Runtime (Imagem final)
FROM python:3.11-slim
WORKDIR /app
# Copia apenas o que foi instalado no estágio anterior
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]

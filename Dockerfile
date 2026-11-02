FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

# Utilizador sem privilégios; os diretórios dos volumes já pertencem a ele
# (volumes nomeados herdam o dono do diretório da imagem na primeira montagem).
RUN useradd --create-home --uid 1000 flowcred \
    && mkdir -p /app/data /app/uploads \
    && sed -i 's/\r$//' entrypoint.sh \
    && chmod +x entrypoint.sh \
    && chown -R flowcred:flowcred /app

USER flowcred

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

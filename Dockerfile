FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    wget \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY image_processor.py .

# Criar diretórios
RUN mkdir -p /app/fonts /app/assets /app/output /app/temp

# Baixar fontes automaticamente
RUN cd /app/fonts && \
    wget -q https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf && \
    wget -q https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf && \
    wget -q https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.ttf && \
    wget -q https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Medium.ttf

# Expor porta
EXPOSE 5000

# Variáveis de ambiente
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Comando
CMD ["python", "-u", "image_processor.py"]
```

#### **2. `requirements.txt`**
```
Flask==3.0.0
Pillow==10.1.0
requests==2.31.0
gunicorn==21.2.0

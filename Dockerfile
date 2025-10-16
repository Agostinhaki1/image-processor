FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    wget \
    curl \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7-dev \
    libtiff5-dev \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY image_processor.py .

RUN mkdir -p /app/fonts /app/assets /app/output /app/temp

RUN cd /app/fonts && \
    wget -O Montserrat-Bold.ttf "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Bold.ttf" && \
    wget -O Montserrat-Black.ttf "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat-Black.ttf" && \
    wget -O Inter-Regular.ttf "https://github.com/rsms/inter/raw/v4.1/docs/font-files/Inter-Regular.ttf" && \
    wget -O Inter-Medium.ttf "https://github.com/rsms/inter/raw/v4.1/docs/font-files/Inter-Medium.ttf" || \
    (echo "Fontes não baixadas, usando fallback" && touch fallback.txt)

EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "image_processor:app"]

FROM python:3.11-slim

WORKDIR /app

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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY image_processor.py .

RUN mkdir -p /app/fonts /app/assets /app/output /app/temp

RUN cd /app/fonts && \
    wget -q https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Bold.ttf && \
    wget -q https://github.com/JulietaUla/Montserrat/raw/master/fonts/ttf/Montserrat-Black.ttf && \
    wget -q https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Regular.ttf && \
    wget -q https://github.com/rsms/inter/raw/master/docs/font-files/Inter-Medium.ttf

EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["python", "-u", "image_processor.py"]

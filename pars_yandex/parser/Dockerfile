# FROM python:3.12
FROM --platform=linux/amd64 python:3.12

ENV TZ=Europe/Moscow
RUN apt-get update && apt-get install -y nano htop vim default-libmysqlclient-dev build-essential python3-mysqldb 
RUN apt-get install -y iproute2 openresolv wget dpkg




# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы 
COPY . /app
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libvulkan1 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

#chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb
RUN apt-get install -f

# chromedriver
RUN wget https://chromedriver.storage.googleapis.com/92.0.4515.107/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver



# Устанавливаем зависимости из requirements.txt
RUN pip3 install poetry
# RUN pip3 install --upgrade setuptools
RUN poetry install



# Копируем файл .env внутрь контейнера
# COPY .env authorized_key.json /app/
# CMD ["python3", "workTelegram.py"]
CMD ["poetry", "run", "python3", "workTelegram.py"]
# CMD ["gunicorn", "wsgi:app", "-c", "wsgi_config.py"]
# gunicorn wsgi:app -c wsgi_config.py

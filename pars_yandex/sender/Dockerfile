FROM python:3.12

ENV TZ=Europe/Moscow
RUN apt-get update && apt-get install -y nano htop vim default-libmysqlclient-dev build-essential python3-mysqldb 
RUN apt-get install -y iproute2 openresolv




# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файлы 
COPY . /app



# Устанавливаем зависимости из requirements.txt
RUN pip3 install poetry
RUN pip3 install --upgrade setuptools
RUN poetry install



# Копируем файл .env внутрь контейнера
# COPY .env authorized_key.json /app/
# CMD ["python3", "workTelegram.py"]
CMD ["poetry", "run", "python3", "workTelegram.py"]
# CMD ["gunicorn", "wsgi:app", "-c", "wsgi_config.py"]
# gunicorn wsgi:app -c wsgi_config.py

FROM python:3.13

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000/tcp
LABEL org.opencontainers.image.source=https://github.com/Tifeko/jellyfinavatars

CMD [ "gunicorn", "-b", "0.0.0.0:8000", "main:app" ]
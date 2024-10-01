FROM arm64v8/python:3.11-slim-buster

   WORKDIR /app

   COPY . /app

   RUN pip install --upgrade pip && \
       pip install --no-cache-dir -r requirements.txt

   EXPOSE 80

   CMD ["python", "PUM_main.py"]
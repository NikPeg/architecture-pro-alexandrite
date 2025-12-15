FROM python:3.11-slim

WORKDIR /app

# Копирование requirements и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода приложения
COPY app.py .

# Открытие порта
EXPOSE 8080

# Запуск приложения
CMD ["python", "app.py"]


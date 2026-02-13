FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean
WORKDIR /app
COPY requirements.txt .
# Yahan hum yt-dlp ko force update kar rahe hain
RUN pip install --no-cache-dir -r requirements.txt && pip install -U yt-dlp
COPY . .
CMD ["python3", "app.py"]

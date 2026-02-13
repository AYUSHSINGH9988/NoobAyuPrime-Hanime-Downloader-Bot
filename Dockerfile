# Python ka official image use kar rahe hain
FROM python:3.10-slim

# System updates aur ffmpeg install karna zaroori hai video processing ke liye
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Ek working directory banate hain
WORKDIR /app

# Sabse pehle requirements copy karte hain taaki cache build fast ho
COPY requirements.txt .

# Libraries install karte hain
RUN pip install --no-cache-dir -r requirements.txt

# Baaki saara code copy karte hain
COPY . .

# Bot ko run karne ki command
CMD ["python3", "app.py"]


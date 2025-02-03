# Use a lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install required system dependencies (including ping)
RUN apt-get update && apt-get install -y iputils-ping && rm -rf /var/lib/apt/lists/*

# Install required Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY ntp_monitor.py .

# Expose environment variables
ENV NTP_SERVER="pool.ntp.org"
ENV OFFSET_THRESHOLD="0.5"
ENV TELEGRAM_BOT_TOKEN=""
ENV TELEGRAM_CHAT_ID=""
ENV CHECK_INTERVAL="60"

# Run the script
CMD ["python", "ntp_monitor.py"]

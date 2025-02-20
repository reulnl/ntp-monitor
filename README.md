# NTP Monitor

This repository contains a Dockerfile for monitoring an NTP server and sending Telegram alerts when the server is offline or the time offset is out of range.

## How to Build and Run

### Build the Docker Image
```bash
docker build -t ntp-monitor .
```

### Run the Docker Image

```bash
docker run -d \
  --restart unless-stopped \
  -e NTP_SERVER="your_ntp_server" \
  -e OFFSET_THRESHOLD="0.5" \
  -e TELEGRAM_BOT_TOKEN="your_telegram_bot_token" \
  -e TELEGRAM_CHAT_ID="your_chat_id" \
  -e CHECK_INTERVAL="60" \
  -e NTP_RETRY_COUNT="1" \
  ghcr.io/reulnl/ntp-monitor:latest
```

Optionally the variable `NTP_MONITOR_LOCATION` can be set to differentiate locations where the NTP Monitor container is running.

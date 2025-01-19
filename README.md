# NTP Monitor

This repository contains a Dockerfile for monitoring an NTP server and sending Telegram alerts when the server is offline or the time offset is out of range.

## How to Build and Run

### Build the Docker Image
```bash
docker build -t ntp-monitor .

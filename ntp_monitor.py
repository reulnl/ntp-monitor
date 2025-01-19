import ntplib
import time
import requests
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
NTP_SERVER = os.getenv("NTP_SERVER", "pool.ntp.org")
OFFSET_THRESHOLD = float(os.getenv("OFFSET_THRESHOLD", "0.5"))  # in seconds
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # in seconds

def send_telegram_alert(message):
    """Send alert to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "disable_notification": False,
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Telegram alert: {e}")

def check_ntp_server():
    """Check the NTP server and report status."""
    try:
        client = ntplib.NTPClient()
        response = client.request(NTP_SERVER, version=3)
        offset = response.offset
        logging.info(f"NTP Server: {NTP_SERVER}, Offset: {offset:.6f} seconds")

        if abs(offset) > OFFSET_THRESHOLD:
            message = (
                f"⚠️ Alert: NTP server {NTP_SERVER} offset is out of range!\n"
                f"Offset: {offset:.6f} seconds\nThreshold: {OFFSET_THRESHOLD} seconds"
            )
            send_telegram_alert(message)

    except Exception as e:
        logging.error(f"Error connecting to NTP server {NTP_SERVER}: {e}")
        send_telegram_alert(
            f"🚨 Alert: Unable to reach NTP server {NTP_SERVER}.\nError: {e}"
        )

def main():
    """Main loop."""
    while True:
        check_ntp_server()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
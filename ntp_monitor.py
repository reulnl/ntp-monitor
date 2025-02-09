import ntplib
import time
import requests
import os
import logging
import socket
import subprocess

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
NTP_SERVER = os.getenv("NTP_SERVER", "pool.ntp.org")
OFFSET_THRESHOLD = float(os.getenv("OFFSET_THRESHOLD", "0.5"))  # in seconds
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "60"))  # in seconds
NTP_RETRY_COUNT = int(os.getenv("NTP_RETRY_COUNT", "1"))  # Number of retries

server_unreachable = False
last_offset_out_of_range = False

def send_telegram_alert(message):
    """Send alert to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "disable_notification": False}
    try:
        response = requests.post(url, json=payload)
        if response.status_code != 200:
            logging.error(f"Failed to send Telegram alert: {response.text}")
    except Exception as e:
        logging.error(f"Error sending Telegram alert: {e}")

def check_dns_resolution(server):
    try:
        ip_address = socket.gethostbyname(server)
        return True, ip_address
    except socket.error:
        return False, None

def check_ping(server):
    try:
        result = subprocess.run(["ping", "-c", "1", server],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "time=" in line:
                    response_time = line.split("time=")[1].split(" ")[0]
                    return True, response_time
        return False, None
    except Exception as e:
        logging.error(f"Ping check failed: {e}")
        return False, None

def check_ntp_server():
    global server_unreachable, last_offset_out_of_range
    for attempt in range(NTP_RETRY_COUNT):
        try:
            client = ntplib.NTPClient()
            response = client.request(NTP_SERVER, version=3)
            offset = response.offset
            logging.info(f"NTP Server: {NTP_SERVER}, Offset: {offset:.6f} seconds")

            if abs(offset) > OFFSET_THRESHOLD:
                # Alert if offset is out-of-range and it was not already flagged
                if not last_offset_out_of_range:
                    location = os.getenv("NTP_MONITOR_LOCATION", "").strip()
                    message = (f"[{location}] ⚠️ Alert: NTP offset for {NTP_SERVER} out-of-range: {offset:.6f} seconds "
                               f"(Threshold: {OFFSET_THRESHOLD} seconds)")
                    send_telegram_alert(message)
                    last_offset_out_of_range = True
            else:
                # Recovery alert if previously out-of-range
                if last_offset_out_of_range:
                    location = os.getenv("NTP_MONITOR_LOCATION", "").strip()
                    message = (f"[{location}] ✅ Recovery: NTP offset for {NTP_SERVER} back within threshold: {offset:.6f} seconds.")
                    send_telegram_alert(message)
                    last_offset_out_of_range = False

            # If the server was previously unreachable, announce recovery
            if server_unreachable:
                location = os.getenv("NTP_MONITOR_LOCATION", "").strip()
                message = (f"[{location}] ✅ Recovery: NTP server {NTP_SERVER} is back online.")
                send_telegram_alert(message)
                server_unreachable = False

            return  # Exit function if successful
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}/{NTP_RETRY_COUNT}: Error connecting to NTP server {NTP_SERVER}: {e}")
            time.sleep(2)  # Wait before retrying

    # Only mark as unreachable if all attempts fail
    if not server_unreachable:
        dns_status, ip_address = check_dns_resolution(NTP_SERVER)
        ping_status, response_time = check_ping(NTP_SERVER)
        location = os.getenv("NTP_MONITOR_LOCATION", "").strip()
        message = (
            f"[{location}] 🚨 Alert: NTP server {NTP_SERVER} unreachable.\n"
            f"DNS Resolution: {'Successful, IP: ' + ip_address if dns_status else 'Failed'}\n"
            f"Ping: {'Successful, Response Time: ' + str(response_time) + ' ms' if ping_status else 'Failed'}"
        )
        send_telegram_alert(message)
        server_unreachable = True

def main():
    while True:
        check_ntp_server()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

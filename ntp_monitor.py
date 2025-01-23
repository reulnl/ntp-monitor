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

# Track server unreachable and offset out-of-range status
server_unreachable = False
last_offset_out_of_range = False

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

def check_dns_resolution(server):
    """Check if DNS resolution works for the server and return IP."""
    try:
        ip_address = socket.gethostbyname(server)
        return True, ip_address
    except socket.error:
        return False, None

def check_ping(server):
    """Check if the server can be pinged and return response time."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", server], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
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
    """Check the NTP server and report status."""
    global server_unreachable, last_offset_out_of_range

    try:
        client = ntplib.NTPClient()
        response = client.request(NTP_SERVER, version=3)
        offset = response.offset
        logging.info(f"NTP Server: {NTP_SERVER}, Offset: {offset:.6f} seconds")

        # Check if the offset is within the acceptable range
        if abs(offset) > OFFSET_THRESHOLD:
            if not last_offset_out_of_range:
                message = (
                    f"⚠️ Alert: NTP server {NTP_SERVER} offset is out of range!\n"
                    f"Offset: {offset:.6f} seconds\nThreshold: {OFFSET_THRESHOLD} seconds"
                )
                send_telegram_alert(message)
            last_offset_out_of_range = True
        else:
            if last_offset_out_of_range:
                message = (
                    f"✅ Recovery: NTP server {NTP_SERVER} offset is back within range.\n"
                    f"Offset: {offset:.6f} seconds\nThreshold: {OFFSET_THRESHOLD} seconds"
                )
                send_telegram_alert(message)
            last_offset_out_of_range = False

        # If the server was previously unreachable and is now reachable, send recovery message
        if server_unreachable:
            send_telegram_alert(f"✅ Recovery: NTP server {NTP_SERVER} is back online.")
            server_unreachable = False

    except Exception as e:
        logging.error(f"Error connecting to NTP server {NTP_SERVER}: {e}")

        # Only send alert if the server was not previously unreachable
        if not server_unreachable:
            dns_status, ip_address = check_dns_resolution(NTP_SERVER)
            ping_status, response_time = check_ping(NTP_SERVER)
            message = (
                f"🚨 Alert: Unable to reach NTP server {NTP_SERVER}.\n"
                f"Error: {e}\n"
                f"DNS Resolution: {'Successful, IP: ' + ip_address if dns_status else 'Failed'}\n"
                f"Ping: {'Successful, Response Time: ' + response_time + ' ms' if ping_status else 'Failed'}"
            )
            send_telegram_alert(message)
            server_unreachable = True

def main():
    """Main loop."""
    while True:
        check_ntp_server()
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()

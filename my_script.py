import time
import random
import string
import requests
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED

# --- Helper functions for email/OTP ---
def get_email():
    try:
        url = "http://api.guerrillamail.com/ajax.php"
        params = {'f': 'get_email_address', 'ip': '127.0.0.1', 'lang': 'en'}
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            email = data.get('email_addr', '')
            sid = r.cookies['PHPSESSID'] if 'PHPSESSID' in r.cookies else None
            return email, sid
    except:
        pass
    # Fallback
    email = f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@guerrillamailblock.com"
    return email, None

def check_mail(sid):
    try:
        url = "http://api.guerrillamail.com/ajax.php"
        params = {'f': 'check_email', 'seq': 0, 'ip': '127.0.0.1'}
        cookies = {'PHPSESSID': sid} if sid else {}
        r = requests.get(url, params=params, cookies=cookies, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def get_mail(sid, id):
    try:
        url = "http://api.guerrillamail.com/ajax.php"
        params = {'f': 'fetch_email', 'email_id': id, 'ip': '127.0.0.1'}
        cookies = {'PHPSESSID': sid} if sid else {}
        r = requests.get(url, params=params, cookies=cookies, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def find_otp(text):
    patterns = [r'\b(\d{6})\b', r'\b(\d{4})\b', r'code[:\s]*(\d{4,8})', r'otp[:\s]*(\d{4,8})']
    for p in patterns:
        matches = re.findall(p, text, re.IGNORECASE)
        if matches:
            for m in matches:
                if 4 <= len(m) <= 8:
                    return m
    return None

def wait_for_otp(sid):
    max_attempts = 30
    for attempt in range(max_attempts):
        r = check_mail(sid)
        if r and 'list' in r and r['list']:
            for msg in r['list']:
                mail = get_mail(sid, msg.get('mail_id'))
                if mail:
                    body = mail.get('mail_body', '')
                    subject = mail.get('mail_subject', '')
                    clean_body = re.sub('<[^<]+?>', '', body)
                    otp = find_otp(clean_body + " " + subject)
                    if otp:
                        return otp
        time.sleep(3)
    return None

def setup_browser_options():
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--aggressive-cache-discard')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-notifications')
    # options.add_argument('--headless=new')
    return options

def create_driver():
    chrome_bin = "/usr/bin/chromium-browser"
    chromedriver_bin = "/usr/bin/chromedriver"
    options = setup_browser_options()
    if os.path.exists(chrome_bin) and os.path.exists(chromedriver_bin):
        options.binary_location = chrome_bin
        service = Service(executable_path=chromedriver_bin)
        driver = webdriver.Chrome(service=service, options=options)
    else:
        driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(30)
    return driver

# --- Main automation loop ---
REGISTRATION_LINK = "https://hyper3d.ai/r/E9B2STV3"  # Change as needed
PARALLEL_BROWSERS = 5  # Safe for GitHub Actions runner

def run_automation(run_id):
    print(f"\n--- Automation Run {run_id} ---")
    email, sid = get_email()
    print(f"Email: {email}")
    user = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    pwd = ''.join(random.choices(string.ascii_letters + string.digits + '!@#$%', k=12))
    driver = None
    try:
        driver = create_driver()
        driver.get(REGISTRATION_LINK)
        wait = WebDriverWait(driver, 10)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"userInfoCheck\"]/div[1]/div/div'))).click()
            time.sleep(0.5)
        except:
            print("First click element not found, continuing...")
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"root\"]/div[3]/div[1]/div[2]/div[10]/span'))).click()
            time.sleep(0.5)
        except:
            print("Second click element not found, continuing...")
        email_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"root\"]/div[3]/div[1]/div[2]/input')))
        email_input.clear()
        email_input.send_keys(email)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"root\"]/div[3]/div[1]/div[2]/div[3]'))).click()
        time.sleep(1)
        username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"root\"]/div[3]/div[1]/div[2]/input[1]')))
        username_input.clear()
        username_input.send_keys(user)
        password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"root\"]/div[3]/div[1]/div[2]/input[2]')))
        password_input.clear()
        password_input.send_keys(pwd)
        print("Waiting for OTP...")
        otp = wait_for_otp(sid)
        if otp:
            print(f"OTP Found: {otp}")
            otp_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id=\"root\"]/div[3]/div[1]/div[2]/input[3]')))
            otp_input.clear()
            otp_input.send_keys(otp)
            time.sleep(1)
            signup_script = """
            const el = [...document.querySelectorAll('div, button, span, a')].find(e => e.textContent.trim() === 'Sign Up');
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                setTimeout(() => {
                    ['pointerdown', 'mousedown', 'pointerup', 'mouseup', 'click'].forEach(type => {
                        const event = new PointerEvent(type, {
                            bubbles: true,
                            cancelable: true,
                            pointerType: 'mouse'
                        });
                        el.dispatchEvent(event);
                    });
                }, 300);
                return 'clicked';
            } else {
                return 'not found';
            }
            """
            result = driver.execute_script(signup_script)
            time.sleep(2)
            if result != 'clicked':
                try:
                    signup_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(),'Sign Up')]")))
                    signup_btn.click()
                except:
                    print("Sign Up button not found!")
            print(f"Registration completed! Email: {email}, Username: {user}, Password: {pwd}, OTP: {otp}")
            time.sleep(5)  # Wait 5 seconds after clicking Sign Up
        else:
            print("OTP not received in time")
    except Exception as e:
        print(f"Automation failed: {e}")
    finally:
        if driver:
            driver.quit()

# --- Dynamic pool: always 5 running ---
# def dynamic_pool():
#     run_id = 1
#     with ThreadPoolExecutor(max_workers=PARALLEL_BROWSERS) as executor:
#         futures = {executor.submit(run_automation, run_id + i): run_id + i for i in range(PARALLEL_BROWSERS)}
#         run_id += PARALLEL_BROWSERS
#         while True:
#             done, _ = wait(futures, return_when=FIRST_COMPLETED)
#             for fut in done:
#                 # Remove completed future
#                 futures.pop(fut)
#                 # Start a new one
#                 futures[executor.submit(run_automation, run_id)] = run_id
#                 run_id += 1

if __name__ == "__main__":
    run_automation(1)

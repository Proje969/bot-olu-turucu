import time
import random
import string
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from database import TwitterDatabase
import undetected_chromedriver as uc
from bs4 import BeautifulSoup

class AccountCreator:
    def __init__(self, use_proxy=True):
        self.db = TwitterDatabase()
        self.use_proxy = use_proxy
        self.driver = None
        self.temp_mail_session = requests.Session()

    def setup_driver(self):
        options = uc.ChromeOptions()
        
        if self.use_proxy:
            proxy = self.db.get_available_proxy()
            if proxy and self.check_proxy_health(proxy):
                proxy_str = f"{proxy[1]}:{proxy[2]}"
                if proxy[3] and proxy[4]:
                    proxy_str = f"{proxy[3]}:{proxy[4]}@{proxy_str}"
                options.add_argument(f'--proxy-server={proxy_str}')

        options.add_argument('--start-maximized')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        self.driver = uc.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def check_proxy_health(self, proxy):
        try:
            proxy_str = f"{proxy[1]}:{proxy[2]}"
            if proxy[3] and proxy[4]:
                proxy_str = f"{proxy[3]}:{proxy[4]}@{proxy_str}"
            
            proxies = {
                'http': f'http://{proxy_str}',
                'https': f'https://{proxy_str}'
            }
            
            response = requests.get('https://api.ipify.org', proxies=proxies, timeout=10)
            return response.status_code == 200
        except:
            return False

    def get_temp_email(self):
        try:
            # temp-mail.io API'sini kullan
            response = self.temp_mail_session.get("https://temp-mail.io/api/v3/email/new")
            if response.status_code == 200:
                email_data = response.json()
                return email_data["email"]
            
            # Yedek olarak mail.tm servisini dene
            response = requests.post("https://api.mail.tm/accounts", json={
                "address": f"test_{random.randint(1000,9999)}@mail.tm",
                "password": "Test12345!"
            })
            if response.status_code == 201:
                return response.json()["address"]
                
        except Exception as e:
            print(f"Temp mail error: {str(e)}")
        
        # Son çare olarak rastgele email oluştur
        random_email = f"test_{random.randint(1000, 9999)}@example.com"
        return random_email

    def wait_for_email_verification(self, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = self.temp_mail_session.get("https://temp-mail.io/api/v3/email/messages")
                if response.status_code == 200:
                    messages = response.json()
                    for message in messages:
                        if "Twitter" in message["subject"]:
                            # Email içeriğinden doğrulama kodunu çıkar
                            soup = BeautifulSoup(message["body"], "html.parser")
                            code = soup.find("strong").text.strip()
                            return code
            except:
                pass
            time.sleep(5)
        return None

    def generate_random_info(self):
        # Rastgele kullanıcı adı oluştur
        username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        
        # Rastgele şifre oluştur
        password = ''.join(random.choices(string.ascii_letters + string.digits + string.punctuation, k=12))
        
        # Rastgele isim oluştur
        name = ''.join(random.choices(string.ascii_lowercase, k=8)).capitalize()
        
        return username, password, name

    def create_account(self):
        try:
            self.setup_driver()
            self.driver.get("https://twitter.com/signup")
            
            # Rastgele bilgileri oluştur
            username, password, name = self.generate_random_info()
            email = self.get_temp_email()
            
            # Kayıt formunu doldur
            wait = WebDriverWait(self.driver, 10)
            
            # İsim giriş alanı
            name_input = wait.until(EC.presence_of_element_located((By.NAME, "name")))
            name_input.send_keys(name)
            
            # Email giriş alanı
            email_input = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            email_input.send_keys(email)
            
            # Doğum tarihi seçimi
            # Not: Twitter'ın güncel kayıt formuna göre güncellenmeli
            birth_day = random.randint(1, 28)
            birth_month = random.randint(1, 12)
            birth_year = random.randint(1980, 2000)
            
            # Kullanıcı adı giriş alanı
            username_input = wait.until(EC.presence_of_element_located((By.NAME, "username")))
            username_input.send_keys(username)
            
            # Şifre giriş alanı
            password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(password)
            
            # Kayıt ol butonuna tıkla
            submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Sign up']")))
            submit_button.click()
            
            # Email doğrulama kodunu bekle
            time.sleep(30)  # Email API'sine göre bu kısım güncellenecek
            
            # Hesabı veritabanına kaydet
            self.db.add_account(
                username=username,
                password=password,
                email=email
            )
            
            return {
                "status": "success",
                "username": username,
                "password": password,
                "email": email
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
            
        finally:
            if self.driver:
                self.driver.quit()

    def verify_email(self, verification_code):
        try:
            # Doğrulama kodu giriş alanı
            code_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "verification_code"))
            )
            code_input.send_keys(verification_code)
            
            # Doğrula butonuna tıkla
            verify_button = self.driver.find_element(By.XPATH, "//span[text()='Verify']")
            verify_button.click()
            
            return True
        except:
            return False

def main():
    creator = AccountCreator(use_proxy=True)
    result = creator.create_account()
    print(result)

if __name__ == "__main__":
    main() 
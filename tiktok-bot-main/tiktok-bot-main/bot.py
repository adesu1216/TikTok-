import re
import shutil
from os import system
from time import sleep
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    UnexpectedAlertPresentException,
)
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options


def find_firefox_binary() -> str:
    """
    Windows向け Firefox 実行ファイルの場所を推定して返す。
    見つからなければ空文字を返す。
    """
    p = shutil.which("firefox")
    if p:
        return p

    candidates = [
        r"C:\Program Files\Mozilla Firefox\firefox.exe",
        r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
        r"C:\Program Files\WindowsApps\Mozilla.Firefox_*\VFS\ProgramFiles\Mozilla Firefox\firefox.exe",
    ]
    for c in candidates:
        if "*" in c:
            base = Path(r"C:\Program Files\WindowsApps")
            if base.exists():
                for path in base.glob("Mozilla.Firefox_*"):
                    exe = path / "VFS" / "ProgramFiles" / "Mozilla Firefox" / "firefox.exe"
                    if exe.exists():
                        return str(exe)
        else:
            if Path(c).exists():
                return c
    return ""


class Bot:
    def __init__(self):
        system("cls || clear")
        self._print_banner()
        self.driver = self._init_driver()
        self.services = self._init_services()

    def start(self):
        self.driver.get("https://zefoy.com")
        self._solve_captcha()

        # Page refresh sequence
        sleep(2); self.driver.refresh()
        sleep(2); self.driver.refresh()

        self._check_services_status()
        self.driver.minimize_window()
        self._print_services_list()
        service = self._choose_service()
        video_url = self._choose_video_url()
        self._start_service(service, video_url)

    def _print_banner(self):
        print("+--------------------------------------------------------+")
        print("|                                                        |")
        print("|   Made by : adesu                                      |")
        print("|   supportserver  : https://discord.gg/9FE9qP693t       |")
        print("|                                                        |")
        print("+--------------------------------------------------------+\n")

    # ===== Driver =====
    def _init_driver(self):
        """
        Windows向け:
          - geckodriver.exe は同フォルダを使用
          - Firefox は自動検出（見つからなければエラー）
          - 通知/Push をブロックして UnexpectedAlert を防止
        """
        try:
            print("[~] Loading driver, please wait...")

            here = Path(__file__).resolve().parent
            gecko_path = str((here / "geckodriver.exe").resolve())
            if not Path(gecko_path).exists():
                raise FileNotFoundError(f"geckodriver.exe not found at: {gecko_path}")

            options = Options()
            options.add_argument("--width=800")
            options.add_argument("--height=700")

            # ★ 通知とPushをブロック
            options.set_preference("dom.webnotifications.enabled", False)
            options.set_preference("dom.push.enabled", False)
            options.set_preference("permissions.default.desktop-notification", 2)  # 2=Block

            # Firefox 実行ファイルの自動検出
            firefox_bin = find_firefox_binary()
            if firefox_bin:
                options.binary_location = firefox_bin
            else:
                raise FileNotFoundError(
                    "Firefox browser binary was not found automatically.\n"
                    "Install Firefox or set the path manually, e.g.:\n"
                    r'  options.binary_location = r"C:\Program Files\Mozilla Firefox\firefox.exe"'
                )

            service = Service(executable_path=gecko_path, log_output=str(here / "geckodriver.log"))
            driver = webdriver.Firefox(service=service, options=options)

            print("[+] Driver loaded successfully\n")
            return driver

        except Exception as e:
            print(f"[x] Error loading driver: {e}")
            raise

    # ===== Service list =====
    def _init_services(self):
        return {
            "followers": {"title": "Followers", "selector": "t-followers-button", "status": None},
            "hearts": {"title": "Hearts", "selector": "t-hearts-button", "status": None},
            "comments_hearts": {"title": "Comments Hearts", "selector": "t-chearts-button", "status": None},
            "views": {"title": "Views", "selector": "t-views-button", "status": None},
            "shares": {"title": "Shares", "selector": "t-shares-button", "status": None},
            "favorites": {"title": "Favorites", "selector": "t-favorites-button", "status": None},
            "live_stream": {"title": "Live Stream [VS+LIKES]", "selector": "t-livesteam-button", "status": None},
        }

    # ===== Flow =====
    def _solve_captcha(self):
        self._wait_for_element(By.TAG_NAME, "input")
        print("[~] Please complete the captcha")
        self._wait_for_element(By.LINK_TEXT, "Youtube")
        print("[+] Captcha completed successfully\n")

    def _check_services_status(self):
        for service in self.services:
            selector = self.services[service]["selector"]
            try:
                element = self.driver.find_element(By.CLASS_NAME, selector)
                self.services[service]["status"] = "[WORKING]" if element.is_enabled() else "[OFFLINE]"
            except NoSuchElementException:
                self.services[service]["status"] = "[OFFLINE]"

    def _print_services_list(self):
        for index, service in enumerate(self.services):
            title = self.services[service]["title"]
            status = self.services[service]["status"]
            print("[{}] {}".format(str(index + 1), title).ljust(30), status)
        print()

    def _choose_service(self):
        while True:
            try:
                choice = int(input("[~] Choose an option : "))
            except ValueError:
                print("[!] Invalid input format. Please try again...\n")
                continue

            if 1 <= choice <= 7:
                key = list(self.services.keys())[choice - 1]
                if self.services[key]["status"] == "[OFFLINE]":
                    print("[!] Service is offline. Please choose another...\n")
                    continue
                print(f"[+] You have chosen {self.services[key]['title']}\n")
                return key
            else:
                print("[!] No service found with this number\n")

    def _choose_video_url(self):
        video_url = input("[~] Video URL : ")
        print()
        return video_url

    def _start_service(self, service, video_url):
        # Click service button
        self._wait_for_element(By.CLASS_NAME, self.services[service]["selector"]).click()

        # Get container
        container = self._wait_for_element(
            By.CSS_SELECTOR, "div.col-sm-5.col-xs-12.p-1.container:not(.nonec)"
        )

        # Fill video URL
        input_element = container.find_element(By.TAG_NAME, "input")
        input_element.clear()
        input_element.send_keys(video_url)

        while True:
            # Search
            container.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()
            sleep(3)

            # Submit if present
            try:
                container.find_element(By.CSS_SELECTOR, "button.btn.btn-dark").click()
                print(f"[~] {self.services[service]['title']} sent successfully")
            except NoSuchElementException:
                pass

            sleep(3)
            remaining_time = self._compute_remaining_time(container)
            if remaining_time is not None:
                minutes = remaining_time // 60
                seconds = remaining_time - minutes * 60
                print(f"[~] Sleeping for {minutes} minutes {seconds} seconds")
                sleep(remaining_time)
            print()

    # ===== Helpers =====
    def _compute_remaining_time(self, container):
        try:
            text = container.find_element(By.CSS_SELECTOR, "span.br").text
            if "Please wait" in text:
                minutes, seconds = re.findall(r"\d+", text)
                return int(minutes) * 60 + int(seconds) + 5  # safety margin
            else:
                print("NO TIME")
                return None
        except NoSuchElementException:
            print("NO ELEMENT")
            return None

    def _dismiss_alerts(self):
        """通知許可などのブラウザアラートが出たら閉じる"""
        try:
            alert = self.driver.switch_to.alert
            txt = alert.text
            alert.dismiss()  # 必要なら accept() に変更可
            print(f"[i] Dismissed alert: {txt}")
        except Exception:
            pass

    def _wait_for_element(self, by, value):
        while True:
            try:
                return self.driver.find_element(by, value)
            except NoSuchElementException:
                sleep(1)
            except UnexpectedAlertPresentException:
                self._dismiss_alerts()
                sleep(0.5)


if __name__ == "__main__":
    bot = Bot()
    bot.start()



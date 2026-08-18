import os
import sys
import pathlib
import time
import re

# Ensure Playwright finds installed browsers on Windows even when running from a packaged .exe
if sys.platform == "win32" and "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        default_pw_path = os.path.join(local_app_data, "ms-playwright")
        if os.path.exists(default_pw_path):
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = default_pw_path

from scripts.config import *
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

class Spider:

    def __init__(self, username=None, password=None, browser_login=False, browser_name="Firefox / Floorp"):
        self.submissions = []
        self.start, self.end = 0, 0

        self.playwright = sync_playwright().start()

        if browser_login:
            # ── Browser login (Google / SSO / Chosen Browser) ────────────
            session_dir = str(pathlib.Path.home() / ".apparate" / "session")

            engine_type, selected_name, channel = self._resolve_browser_engine(browser_name)
            print(f"Opening {selected_name} for HackerRank login…")
            logger.info(f"Browser login: engine={engine_type}, name={selected_name}, channel={channel}, session={session_dir}")

            engine = self.playwright.firefox if engine_type == "firefox" else self.playwright.chromium
            launch_kwargs = {
                "user_data_dir": session_dir,
                "headless": False,
            }
            if channel:
                launch_kwargs["channel"] = channel

            try:
                self._persistent_ctx = engine.launch_persistent_context(**launch_kwargs)
            except Exception as e:
                logger.warning(f"Failed to launch with {engine_type} (channel={channel}): {e}. Attempting fallback…")
                try:
                    self._persistent_ctx = self.playwright.firefox.launch_persistent_context(
                        user_data_dir=session_dir,
                        headless=False
                    )
                except Exception:
                    self._persistent_ctx = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=session_dir,
                        headless=False
                    )

            self.page = self._persistent_ctx.pages[0] if self._persistent_ctx.pages else self._persistent_ctx.new_page()

            # Navigate to login page
            self.page.goto(login_page_url)
            time.sleep(2)

            # Check if user is already logged in
            cookies_dict = {c['name']: c['value'] for c in self._persistent_ctx.cookies()}
            is_already_logged_in = "_hrank_session" in cookies_dict or "remember_hacker_token" in cookies_dict
            curr_url = self.page.url

            if not is_already_logged_in and ("/login" in curr_url or "/auth" in curr_url):
                print("Please log in to HackerRank in the opened browser window (Google / SSO / Email)…")
                start_wait = time.time()
                login_success = False

                while time.time() - start_wait < 300:  # 5 minutes wait
                    try:
                        if self.page.is_closed():
                            print("Browser window was closed before login was completed.")
                            self.quit_driver()
                            raise SystemExit(1)

                        curr_url = self.page.url
                        current_cookies = {c['name']: c['value'] for c in self._persistent_ctx.cookies()}

                        # Login completed when redirected away from login or session cookie acquired
                        if ("/login" not in curr_url and "/auth" not in curr_url) or "_hrank_session" in current_cookies:
                            print("HackerRank Login Successful!")
                            logger.info("HackerRank Login Successful (browser)")
                            login_success = True
                            time.sleep(2)  # Allow page state to settle
                            break

                        time.sleep(1)
                    except SystemExit:
                        raise
                    except Exception as err:
                        if "closed" in str(err).lower():
                            print("Browser window was closed.")
                            self.quit_driver()
                            raise SystemExit(1)
                        time.sleep(1)

                if not login_success:
                    print("Login timed out (5 minutes). Please try again.")
                    self.quit_driver()
                    raise SystemExit(1)
            else:
                print("HackerRank session active — already signed in.")
                logger.info("Reused existing session")

        else:
            # ── Automated credential login ────────────────────────────────
            self.browser = self.playwright.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
            )
            self.page = context.new_page()

            logger.info("Headless Playwright Initialized")
            print("Headless Playwright Initialized")

            self.page.goto("https://www.hackerrank.com/auth/login")

            # Wait for username input (supports modern and legacy form fields)
            user_input = self.page.locator("input[name='username'], input[name='login'], input[placeholder*='username' i], input[type='text']").first
            user_input.wait_for(timeout=10000)
            user_input.fill(username)

            pass_input = self.page.locator("input[name='password'], input[type='password']").first
            pass_input.fill(password)

            btn = self.page.locator("button[type='submit'], button:has-text('Log In'), button[name='commit']").first
            btn.click()

            time.sleep(3)

            # verify login
            try:
                error_locator = self.page.locator(".error:has-text('Invalid'), .error-msg, [data-analytics*='error' i], text='Invalid login or password', text='Invalid credentials'")
                if error_locator.count() > 0 and error_locator.first.is_visible():
                    logger.info("Unable to login to HackerRank, please verify username or password")
                    print("Unable to login to HackerRank, please verify username/password or use 'Login via browser'")
                    self.quit_driver()
                    raise SystemExit(1)
                else:
                    logger.info("HackerRank Login Successful")
                    print("HackerRank Login Successful")
            except SystemExit:
                raise
            except Exception as e:
                logger.info(f"Login check note: {e}")

    def _resolve_browser_engine(self, choice_str):
        """
        Resolves user's browser choice or default selection.
        Returns: (engine_type, display_name, channel)
        """
        c = (choice_str or "").lower()
        if "firefox" in c or "floorp" in c or "zen" in c:
            return "firefox", "Firefox / Floorp", None
        elif "chrome" in c:
            return "chromium", "Google Chrome", "chrome"
        elif "edge" in c:
            return "chromium", "Microsoft Edge", "msedge"
        return "firefox", "Firefox / Floorp", None

    def fetch_pagination_params(self):
        try:
            self.page.goto(all_submissions_page_url)
            self.page.wait_for_selector(".pagination, .submissions_item", timeout=MAX_WAIT * 1000)

            if self.page.locator(".pagination").count() > 0:
                start_href = self.page.locator(".pagination li:nth-child(3) a").get_attribute("href")
                end_href = self.page.locator(".pagination li:last-child a").get_attribute("href")

                if start_href:
                    self.start = int(re.search(p, start_href).group(0))
                if end_href:
                    self.end = int(re.search(p, end_href).group(0))
            else:
                self.start, self.end = 1, 1
        except Exception as e:
            logger.debug(f"Pagination note: {e}")
            self.start, self.end = 1, 1

        logger.info("pagination params, {} - {}".format(self.start, self.end))
        print("pagination params, {} - {}".format(self.start, self.end))

    def fetch_new_submissions(self, last_saved):
        self.fetch_pagination_params()
        self.submissions = []

        if self.start == 0 or self.end == 0:
            return

        for i in range(self.start, self.end + 1):
            try:
                self.page.goto(submissions_page_i_url + str(i))
                self.page.wait_for_selector(".submissions_item", timeout=MAX_WAIT * 1000)
            except Exception:
                break

            time.sleep(2)
            rows = self.page.locator(".submissions_item").all()

            for row in rows:
                try:
                    title_elem = row.locator(".submissions-title a")
                    title = title_elem.inner_text().strip()
                    problem = title_elem.get_attribute("href")

                    language = row.locator(".submissions-language p").inner_text().strip()
                    result = row.locator(".span3 p").inner_text().strip()
                    link = row.locator(".view-results").get_attribute("href")

                    if link == last_saved:
                        return

                    if result != "Accepted":
                        continue

                    self.submissions.append((title, language, problem, result, link))
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue

    def fetch_code_for_submissions(self, submissions):
        codes = {}
        i = 1
        for submission in submissions:
            logger.info(" - fetching code for submission {}".format(i))
            print(" - fetching code for submission {}. {}".format(i, submission[0]))

            link = submission[4]
            if link.startswith("/"):
                link = "https://www.hackerrank.com" + link

            try:
                self.page.goto(link)
                self.page.wait_for_selector("span[role=presentation]", timeout=MAX_WAIT * 1000)
                lines = self.page.locator("span[role=presentation]").all()
                code = "\n".join([line.inner_text() for line in lines])
            except Exception:
                code = "// Could not fetch code snippet"

            codes[submission] = self.prettify_code(submission[1], code)
            i += 1

        return codes

    def prettify_code(self, language, code):
        return code

    def quit_driver(self):
        try:
            if hasattr(self, '_persistent_ctx'):
                self._persistent_ctx.close()
            if hasattr(self, 'browser'):
                self.browser.close()
            self.playwright.stop()
        except Exception:
            pass

if __name__ == "__main__":
    pass

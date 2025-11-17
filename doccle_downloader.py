"""
Doccle Document Downloader
Automates login and document downloads from Doccle.be
"""

import os
import time
import json
import logging
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class DoccleDownloader:
    """Automates document downloads from Doccle.be"""

    def __init__(self, config_path="config.json"):
        """Initialize the downloader with configuration"""
        self.config = self.load_config(config_path)
        self.setup_logging()
        self.driver = None
        self.wait = None
        self.downloaded_files = set()  # Track downloaded files

    def load_config(self, config_path):
        """Load configuration from JSON file"""
        if not os.path.exists(config_path):
            # Create default config if doesn't exist
            default_config = {
                "username": "",
                "password": "",
                "download_folder": str(Path.home() / "Downloads" / "Doccle"),
                "wait_timeout": 20,
                "headless": False,
                "only_unread": False,
                "max_documents": None
            }
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file: {config_path}")
            print("Please edit config.json with your credentials")
            return default_config

        with open(config_path, 'r') as f:
            return json.load(f)

    def setup_logging(self):
        """Setup logging to file and console"""
        log_folder = Path("logs")
        log_folder.mkdir(exist_ok=True)

        log_file = log_folder / f"doccle_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        """Setup Chrome driver with download preferences"""
        chrome_options = Options()

        # Create download folder if it doesn't exist
        download_folder = Path(self.config['download_folder'])
        download_folder.mkdir(parents=True, exist_ok=True)

        # Set download preferences
        prefs = {
            "download.default_directory": str(download_folder.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True  # Download PDFs instead of opening
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if self.config.get('headless', False):
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--disable-gpu')

        # Additional options for stability
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        self.logger.info("Setting up Chrome driver...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.wait = WebDriverWait(self.driver, self.config['wait_timeout'])

        self.logger.info(f"Download folder: {download_folder}")

    def login(self):
        """Login to Doccle"""
        try:
            self.logger.info("Navigating to Doccle login page...")
            self.driver.get("https://secure.doccle.be/doccle-euui/dashboard")

            # Wait for login page to load
            time.sleep(2)

            # Check if we need to login or already logged in
            current_url = self.driver.current_url
            self.logger.info(f"Current URL: {current_url}")

            # Look for username field (adjust selectors based on actual page)
            # These are common selectors - may need adjustment
            username_selectors = [
                (By.ID, "username"),
                (By.NAME, "username"),
                (By.ID, "j_username"),
                (By.NAME, "j_username"),
                (By.CSS_SELECTOR, "input[type='text']"),
                (By.CSS_SELECTOR, "input[type='email']")
            ]

            username_field = None
            for selector_type, selector_value in username_selectors:
                try:
                    username_field = self.wait.until(
                        EC.presence_of_element_located((selector_type, selector_value))
                    )
                    self.logger.info(f"Found username field with: {selector_type}={selector_value}")
                    break
                except TimeoutException:
                    continue

            if not username_field:
                raise Exception("Could not find username field")

            # Find password field
            password_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.ID, "j_password"),
                (By.NAME, "j_password"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]

            password_field = None
            for selector_type, selector_value in password_selectors:
                try:
                    password_field = self.driver.find_element(selector_type, selector_value)
                    self.logger.info(f"Found password field with: {selector_type}={selector_value}")
                    break
                except NoSuchElementException:
                    continue

            if not password_field:
                raise Exception("Could not find password field")

            # Enter credentials
            self.logger.info("Entering credentials...")
            username_field.clear()
            username_field.send_keys(self.config['username'])

            password_field.clear()
            password_field.send_keys(self.config['password'])

            # Find and click login button
            login_button_selectors = [
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.ID, "login-button"),
                (By.NAME, "submit"),
                (By.XPATH, "//button[contains(text(), 'Log in')]"),
                (By.XPATH, "//button[contains(text(), 'Aanmelden')]"),
                (By.XPATH, "//input[@type='submit']")
            ]

            login_button = None
            for selector_type, selector_value in login_button_selectors:
                try:
                    login_button = self.driver.find_element(selector_type, selector_value)
                    self.logger.info(f"Found login button with: {selector_type}={selector_value}")
                    break
                except NoSuchElementException:
                    continue

            if not login_button:
                raise Exception("Could not find login button")

            login_button.click()
            self.logger.info("Clicked login button")

            # Wait for dashboard to load
            time.sleep(2)

            # Check if login was successful
            if "dashboard" in self.driver.current_url.lower():
                self.logger.info("Login successful!")
                return True
            else:
                self.logger.error(f"Login may have failed. Current URL: {self.driver.current_url}")
                return False

        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise

    def get_documents(self):
        """Find and download all available documents"""
        try:
            self.logger.info("Looking for documents...")

            # Store the dashboard URL
            dashboard_url = self.driver.current_url

            # Wait for page to fully load
            time.sleep(1)

            # Apply filters if needed
            max_docs = self.config.get('max_documents')
            only_unread = self.config.get('only_unread', False)

            if only_unread:
                self.logger.info("Filtering for unread documents only...")
                # Try to click unread filter if available
                try:
                    unread_filter = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Unread') or contains(text(), 'Ongelezen')]")
                    unread_filter.click()
                    time.sleep(2)
                except:
                    self.logger.warning("Could not find unread filter button")

            download_count = 0
            processed_count = 0

            # Keep processing until we reach max_documents or run out of documents
            while True:
                # Make sure we're on the dashboard
                if not self.driver.current_url.startswith(dashboard_url.split('?')[0]):
                    self.logger.debug("Returning to dashboard...")
                    self.driver.get(dashboard_url)
                    time.sleep(3)

                # Re-query documents each iteration to avoid stale elements
                documents = self.find_document_elements()

                if not documents:
                    self.logger.warning("No documents found")
                    break

                self.logger.info(f"Found {len(documents)} total documents on page")

                # Process documents one by one
                for i in range(len(documents)):
                    # Make sure we're on the dashboard before re-querying
                    if not self.driver.current_url.startswith(dashboard_url.split('?')[0]):
                        self.logger.debug("Returning to dashboard before re-query...")
                        self.driver.get(dashboard_url)
                        time.sleep(2)

                    # Re-query to avoid stale elements
                    documents = self.find_document_elements()
                    if i >= len(documents):
                        break

                    doc = documents[i]

                    try:
                        processed_count += 1
                        self.logger.info(f"Processing document {processed_count}...")

                        # Log element details for debugging
                        try:
                            self.logger.debug(f"Document class: {doc.get_attribute('class')}")
                            self.logger.debug(f"Document HTML: {doc.get_attribute('outerHTML')[:200]}")
                        except:
                            pass

                        # Check if document is already read/opened (if filtering)
                        if only_unread and self.is_document_read(doc):
                            self.logger.info(f"Skipping document {processed_count} - already read")
                            continue

                        # Try to download
                        if self.download_document(doc, processed_count):
                            download_count += 1
                            self.logger.info(f"[OK] Downloaded document {processed_count} (total: {download_count})")

                            # Check if we've hit the limit
                            if max_docs and download_count >= max_docs:
                                self.logger.info(f"Reached maximum document limit: {max_docs}")
                                return download_count
                        else:
                            self.logger.warning(f"[FAIL] Could not download document {processed_count}")

                    except Exception as e:
                        self.logger.warning(f"Error processing document {processed_count}: {str(e)}")
                        continue

                # If we've processed all documents on this page, we're done
                break

            return download_count

        except Exception as e:
            self.logger.error(f"Error getting documents: {str(e)}")
            raise

    def find_document_elements(self):
        """Find all document elements on the current page"""
        # Try different selectors to find documents
        document_selectors = [
            (By.CSS_SELECTOR, "div.document"),
            (By.CSS_SELECTOR, "[class*='document-item']"),
            (By.CSS_SELECTOR, "[class*='documentItem']"),
            (By.CSS_SELECTOR, ".document-list-item"),
            (By.XPATH, "//div[contains(@class, 'document')]"),
        ]

        for selector_type, selector_value in document_selectors:
            try:
                documents = self.driver.find_elements(selector_type, selector_value)
                if documents:
                    self.logger.debug(f"Found {len(documents)} documents with: {selector_type}={selector_value}")
                    return documents
            except Exception as e:
                continue

        return []

    def is_document_read(self, doc_element):
        """Check if a document has already been read/opened"""
        try:
            # Look for indicators that document is unread
            # Common patterns: 'unread' class, 'new' badge, bold text, etc.
            classes = doc_element.get_attribute('class') or ''

            # If it has 'unread' or 'new' class, it's unread
            if 'unopened' in classes.lower() or 'new' in classes.lower():
                return False

            # If it has 'read' or 'opened' class, it's read
            if 'read' in classes.lower() or 'opened' in classes.lower():
                return True

            # Default: assume unread if we can't determine
            return False

        except Exception as e:
            self.logger.debug(f"Could not determine read status: {str(e)}")
            return False

    def download_document(self, doc_element, doc_number):
        """Attempt to download a single document"""
        try:
            # Scroll element into view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", doc_element)
            time.sleep(0.5)

            # Get initial file count
            initial_files = self.get_download_files()

            # Try to get the detail URL from the document element
            detail_url = doc_element.get_attribute('data-url-detail')

            if detail_url:
                # Navigate to the document detail page
                base_url = "https://secure.doccle.be"
                full_url = base_url + detail_url if not detail_url.startswith('http') else detail_url

                self.logger.info(f"Doc {doc_number}: Opening document at {full_url[:80]}...")
                self.driver.get(full_url)

                # Wait for page to load
                time.sleep(3)

                # Track files downloaded
                files_downloaded = 0

                # Look for the "Open/print document in new window" button
                self.logger.debug(f"Doc {doc_number}: Looking for open/print button...")
                try:
                    # Look for the "Open/print document in new window" button
                    button_selectors = [
                        (By.XPATH, "//a[contains(text(), 'Open/print document in new window')]"),
                        (By.XPATH, "//button[contains(text(), 'Open/print document in new window')]"),
                        (By.XPATH, "//a[contains(text(), 'open') and contains(text(), 'print')]"),
                        (By.XPATH, "//a[contains(text(), 'Open') or contains(text(), 'print')]"),
                        (By.XPATH, "//button[contains(text(), 'Open') or contains(text(), 'print')]"),
                        (By.CSS_SELECTOR, "a[target='_blank']"),
                    ]

                    open_print_btn = None
                    for selector_type, selector_value in button_selectors:
                        try:
                            buttons = self.driver.find_elements(selector_type, selector_value)
                            for btn in buttons:
                                btn_text = btn.text.strip()
                                if btn_text and ('open' in btn_text.lower() or 'print' in btn_text.lower() or 'download' in btn_text.lower()):
                                    open_print_btn = btn
                                    self.logger.info(f"Doc {doc_number}: Found button: '{btn_text}'")
                                    break
                            if open_print_btn:
                                break
                        except:
                            continue

                    if open_print_btn:
                        # Click the button
                        self.logger.debug(f"Doc {doc_number}: Files before open/print click: {initial_files}")
                        open_print_btn.click()
                        self.logger.info(f"Doc {doc_number}: Clicked open/print button, waiting for download...")

                        # Wait for download to complete (PDFs download instantly)
                        for attempt in range(10):  # Wait up to 10 seconds
                            time.sleep(1)
                            current_files = self.get_download_files()

                            self.logger.debug(f"Doc {doc_number}: Attempt {attempt+1} - initial: {len(initial_files)}, current: {len(current_files)}")

                            # Check if new file appeared
                            if len(current_files) > len(initial_files):
                                new_files = current_files - initial_files
                                self.logger.info(f"Doc {doc_number}: Downloaded PDF: {list(new_files)}")
                                self.downloaded_files.update(new_files)
                                files_downloaded += len(new_files)
                                # Update initial_files for the XML check
                                initial_files = current_files
                                break

                except Exception as e:
                    self.logger.debug(f"Doc {doc_number}: Error clicking open/print button: {e}")

                # Now look for "Download XML" button
                self.logger.debug(f"Doc {doc_number}: Looking for Download XML button...")
                try:
                    xml_button_selectors = [
                        (By.XPATH, "//a[contains(text(), 'Download XML')]"),
                        (By.XPATH, "//button[contains(text(), 'Download XML')]"),
                        (By.XPATH, "//a[contains(text(), 'XML')]"),
                        (By.XPATH, "//button[contains(text(), 'XML')]"),
                    ]

                    xml_btn = None
                    for selector_type, selector_value in xml_button_selectors:
                        try:
                            buttons = self.driver.find_elements(selector_type, selector_value)
                            for btn in buttons:
                                btn_text = btn.text.strip()
                                if btn_text and 'xml' in btn_text.lower():
                                    xml_btn = btn
                                    self.logger.info(f"Doc {doc_number}: Found XML button: '{btn_text}'")
                                    break
                            if xml_btn:
                                break
                        except:
                            continue

                    if xml_btn:
                        # Click the XML button
                        self.logger.debug(f"Doc {doc_number}: Files before XML click: {initial_files}")
                        xml_btn.click()
                        self.logger.info(f"Doc {doc_number}: Clicked Download XML button, waiting for download...")

                        # Wait for XML download
                        for attempt in range(10):  # Wait up to 10 seconds
                            time.sleep(1)
                            current_files = self.get_download_files()

                            self.logger.debug(f"Doc {doc_number}: XML attempt {attempt+1} - initial: {len(initial_files)}, current: {len(current_files)}")

                            # Check if new file appeared
                            if len(current_files) > len(initial_files):
                                new_files = current_files - initial_files
                                self.logger.info(f"Doc {doc_number}: Downloaded XML: {list(new_files)}")
                                self.downloaded_files.update(new_files)
                                files_downloaded += len(new_files)
                                break
                    else:
                        self.logger.debug(f"Doc {doc_number}: No Download XML button found")

                except Exception as e:
                    self.logger.debug(f"Doc {doc_number}: Error clicking Download XML button: {e}")

                # Go back to dashboard
                self.driver.back()
                time.sleep(1)

                # Success if at least one file was downloaded
                if files_downloaded > 0:
                    self.logger.info(f"Doc {doc_number}: Successfully downloaded {files_downloaded} file(s)")
                    return True
                else:
                    self.logger.warning(f"Doc {doc_number}: No files were downloaded")
                    return False
            else:
                self.logger.warning(f"Doc {doc_number}: No detail URL found")
                return False

        except Exception as e:
            self.logger.warning(f"Doc {doc_number}: Download attempt failed: {str(e)}")
            try:
                # Try to get back to dashboard
                if "dashboard" not in self.driver.current_url.lower():
                    self.driver.back()
                    time.sleep(2)
            except:
                pass
            return False

    def get_download_files(self):
        """Get set of current files in download folder"""
        try:
            download_folder = Path(self.config['download_folder'])
            if not download_folder.exists():
                return set()

            files = set()
            for f in download_folder.iterdir():
                if f.is_file() and not f.name.endswith('.crdownload') and not f.name.startswith('.'):
                    files.add(f.name)
            self.logger.debug(f"Current files in download folder: {files}")
            return files
        except Exception as e:
            self.logger.debug(f"Error getting download files: {e}")
            return set()

    def wait_for_downloads(self, timeout=60):
        """Wait for all downloads to complete"""
        self.logger.info("Waiting for downloads to complete...")
        download_folder = Path(self.config['download_folder'])

        end_time = time.time() + timeout
        while time.time() < end_time:
            # Check for .crdownload files (Chrome's temporary download files)
            downloading = list(download_folder.glob("*.crdownload"))
            if not downloading:
                self.logger.info("All downloads completed")
                return True
            time.sleep(1)

        self.logger.warning("Timeout waiting for downloads to complete")
        return False

    def run(self):
        """Main execution method"""
        try:
            self.logger.info("=" * 60)
            self.logger.info("Starting Doccle Downloader")
            self.logger.info("=" * 60)

            # Validate config
            if not self.config.get('username') or not self.config.get('password'):
                raise Exception("Username or password not set in config.json")

            self.setup_driver()

            if self.login():
                download_count = self.get_documents()

                if download_count > 0:
                    self.wait_for_downloads()
                    self.logger.info(f"Successfully processed {download_count} documents")
                else:
                    self.logger.warning("No documents were downloaded")

                self.logger.info(f"Downloads saved to: {self.config['download_folder']}")
            else:
                self.logger.error("Login failed")

        except Exception as e:
            self.logger.error(f"Error during execution: {str(e)}", exc_info=True)
            raise

        finally:
            if self.driver:
                time.sleep(2)  # Brief pause before closing
                self.logger.info("Closing browser...")
                self.driver.quit()

            self.logger.info("=" * 60)
            self.logger.info("Doccle Downloader finished")
            self.logger.info("=" * 60)


def main():
    """Entry point"""
    try:
        downloader = DoccleDownloader()
        downloader.run()
        print("\n✓ Process completed successfully!")
        print(f"Check the logs folder for details")
        input("\nPress Enter to exit...")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("Check the logs folder for more details")
        input("\nPress Enter to exit...")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())

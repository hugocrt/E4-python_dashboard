"""
    Module which provides methods for scraping data using Firefox webdriver.
"""
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


class FirefoxScraperHolder:
    """
        Class for scraping data using Firefox webdriver.
    """

    def __init__(self, target_url):
        """
        Initialize a FirefoxScraperHolder instance.

        Args:
            target_url (str): The URL to scrape data from.
        """
        self.cwf = Path(__file__).resolve().parent

        self.options = webdriver.FirefoxOptions()
        self.driver = webdriver.Firefox(options=self.set_preferences())
        self.target_url = target_url

        self._updated_data_date = None
        self._csv_id = None

    def set_preferences(self):
        """
        Set Firefox WebDriver preferences, specifically for downloading files.

        Returns:
            selenium.webdriver.firefox.options.Options: The configured Firefox
            options.
        """
        # 2 : chosen directory as download folder
        self.options.set_preference("browser.download.folderList", 2)
        self.options.set_preference("browser.download.dir", str(self.cwf))
        return self.options

    @property
    def updated_data_date(self):
        """
        Retrieve the date of the last data update.

        Returns:
            str: The date of the last data update.
        """
        return self._updated_data_date

    @property
    def csv_id(self):
        """
        Retrieve the filename of the downloaded CSV.

        Returns:
            str: The filename of the downloaded CSV.
        """
        return self._csv_id

    def perform_scraping(self, aria_label, ng_if):
        """
        Perform the scraping process to retrieve data from a website.

        Args:
            aria_label (str): The ARIA label for the CSV element.

            ng_if (str): The NG-if attribute for the updated data date element.

        Raises:
            WebDriverException: If an error occurs during the scraping process.
        """
        try:
            with self.driver:
                self.driver.maximize_window()
                self.driver.get(self.target_url)

                # Retrieves csv information
                self._click_on(By.LINK_TEXT, "Informations")
                self._updated_data_date = self._retrieve_text_info(
                    By.CSS_SELECTOR, f"[ng-if='{ng_if}']")
                self._csv_id = self._retrieve_text_info(By.CLASS_NAME,
                                                        'ods-dataset-'
                                                        'metadata-block__meta'
                                                        'data-value') + '.csv'
                # Download csv
                self._click_on(By.LINK_TEXT, "Export")
                self._click_on(By.CSS_SELECTOR, f"[aria-label='{aria_label}']")
                self._wait_until_download_finishes()

        except WebDriverException as exception:
            print(f"An error occurred during the get operation: {exception}")

    def _click_on(self, find_by, value):
        """
        Click on a web element identified by the specified method and value.

        Args:
            find_by: The method used to find the element (e.g., By.LINK_TEXT).

            value: The value to search for.

        Returns:
            None
        """
        # The usage of 'wait' and 'EC' is employed to prevent errors caused by
        # website loading.
        wait = WebDriverWait(self.driver, 20)
        element = wait.until(EC.element_to_be_clickable((find_by, value)))
        element.click()

    def remove_cwf_existing_csvs(self):
        """
            Remove existing CSV files from the current working folder.
        """
        for file in self.cwf.glob('*.csv'):
            file.unlink(missing_ok=True)

    def _retrieve_text_info(self, find_by, value):
        """
        Retrieve text information of a web element identified by 'find_by' and
        'value'.

        Args:
            find_by: The method used to find the element (e.g., By.CSS_SELECTOR)
            .

            value: The value to search for.

        Returns:
            str: The text information of the web element.
        """
        # Here 'wait' and 'EC' avoid error due to the loading of the website
        wait = WebDriverWait(self.driver, 20)
        info = wait.until(EC.visibility_of_element_located((find_by, value)))
        return info.text

    def _wait_until_download_finishes(self):
        """
        Wait until the download of a file finishes.

        This function checks the current folder for files with a '.part' suffix
        and waits for them to disappear, indicating the download has finished.
        """
        dl_wait = True
        while dl_wait:
            time.sleep(5)
            dl_wait = False
            for file_name in self.cwf.iterdir():
                print(file_name, file_name.suffix)
                if file_name.suffix == '.part':
                    dl_wait = True

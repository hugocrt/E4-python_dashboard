""" Module which provides methods for scraping data using Firefox webdriver.
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

            :param target_url: The URL to scrape data from.
        """
        self.cwf = Path(__file__).resolve().parent

        self.options = webdriver.FirefoxOptions()
        self.driver = webdriver.Firefox(options=self.set_preferences())
        self.target_url = target_url

        self._updated_data_date = None
        self._csv_id = None

    def set_preferences(self):
        """
            Set Firefox webdriver preferences
            (Here only for downloading files)

            :return: The configured Firefox options.
        """
        # 2 means we use chosen directory as download folder
        self.options.set_preference("browser.download.folderList", 2)
        self.options.set_preference("browser.download.dir", str(self.cwf))
        return self.options

    @property
    def updated_data_date(self):
        """
        Get the last updated data date.

        :return: The last updated data date.
        :rtype: str
        """
        return self._updated_data_date

    @property
    def csv_id(self):
        """
        Get the filename of the downloaded CSV.

        :return: The filename of the downloaded CSV.
        :rtype: str
        """
        return self._csv_id

    def perform_scraping(self, aria_label, ng_if):
        """
            Perform the scraping process.

            :param aria_label: ARIA label for the CSV element.
            :param ng_if: NG-if attribute for updated data date element.
        """
        try:
            with self.driver:
                self.driver.maximize_window()
                self.driver.get(self.target_url)

                # Retrieves csv information
                self.click_on(By.LINK_TEXT, "Informations")
                self._updated_data_date = self.retrieve_text_info(
                    By.CSS_SELECTOR,
                    f"[ng-if='{ng_if}']")
                self._csv_id = self.retrieve_text_info(
                    By.CLASS_NAME,
                    'ods-dataset-metadata-block__metadata-value'
                ) + '.csv'

                # Download csv
                self.click_on(By.LINK_TEXT, "Export")
                self.click_on(By.CSS_SELECTOR, f"[aria-label='{aria_label}']")
                self.wait_for_fully_downloaded()

        except WebDriverException as exception:
            print(f"An error occurred during the get operation: {exception}")

    def click_on(self, find_by, value):
        """
            Click on a web element identified by 'find_by' and 'value'.

            :param find_by: The method used to find the element
            (e.g., By.LINK_TEXT).
            :param value: The value to search for.
        """
        # Here 'wait' and 'EC' avoid error due to the loading of the website
        wait = WebDriverWait(self.driver, 20)
        element = wait.until(EC.element_to_be_clickable((find_by, value)))
        element.click()

    def remove_cwf_existing_csvs(self):
        """
            Remove existing CSV files from the current working folder.
        """
        for file in self.cwf.glob('*.csv'):
            file.unlink(missing_ok=True)

    def retrieve_text_info(self, find_by, value):
        """
            Retrieve text information of a web element identified
            by 'find_by' and 'value'.

            :param find_by: The method used to find the element
            (e.g., By.CSS_SELECTOR).
            :param value: The value to search for.
            :return: The text information of the web element.
            :rtype: str
        """
        # Here 'wait' and 'EC' avoid error due to the loading of the website
        wait = WebDriverWait(self.driver, 20)
        info = wait.until(EC.visibility_of_element_located((find_by, value)))
        return info.text

    def wait_for_fully_downloaded(self, timeout=60, check_interval=1):
        """
            Wait for a file to be fully downloaded.

            :param timeout: Maximum time to wait in seconds.
            Default is 60 seconds.
            :param check_interval: Interval for checking file size
             in seconds. Default is 1 second.
        """
        file_path = self.cwf / self._csv_id
        start_time = time.time()

        while time.time() - start_time < timeout:
            if file_path.is_file():
                initial_size = file_path.stat().st_size
                time.sleep(check_interval)
                # Checks if the file size changes during check_interval
                if file_path.stat().st_size == initial_size:
                    return
        return

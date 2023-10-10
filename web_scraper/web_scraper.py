""" Module which provides methods for scraping data using Firefox webdriver.
"""
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class FirefoxScraperHolder:
    """
    Class for scraping data using Firefox webdriver.
    """

    def __init__(self, target_url, csv_aria_label=None,
                 updated_data_date_ngif=None):
        """
        Initialize the FirefoxScraperHolder instance.

        :parameter:
            target_url (str): The URL to scrape data from.
            csv_aria_label (str, optional): ARIA label for the CSV element.
            updated_data_date_ngif (str, optional): NG-if attribute for updated
             data date element.
        """
        self.current_working_folder = Path(__file__).resolve().parent
        self.driver = webdriver.Firefox(options=self.set_preferences())
        self.target_url = target_url
        # Heritage ?
        self.csv_aria_label = csv_aria_label
        self.updated_data_date_ngif = updated_data_date_ngif
        self._updated_data_date = None
        self.downloaded_csv_filename = None

    def remove_existing_csvs(self):
        """
        Remove any existing CSV files in the current working folder.
        """
        for file in self.current_working_folder.glob('*.csv'):
            file.unlink(missing_ok=True)

    def update_csv_filename(self):
        """
        Update the filename of the downloaded CSV file.
        """
        csv_files = list(self.current_working_folder.glob("*.csv"))
        if csv_files:
            self.downloaded_csv_filename = csv_files[0].name

    def set_preferences(self):
        """
        Set Firefox webdriver preferences for downloading files.

        Returns:
            webdriver.FirefoxOptions: The configured Firefox options.
        """
        options = webdriver.FirefoxOptions()
        options.set_preference("browser.download.folderList", 2)
        options.set_preference("browser.download.dir",
                               str(self.current_working_folder))
        return options

    def perform_scraping(self):
        """
        Perform the scraping process.

        This method performs the following steps:
        1. Opens the target URL.
        2. Clicks on the "Export" link to download the CSV.
        3. Retrieves and clicks on the CSV download link.
        4. Goes to the information page to retrieve the last updated data date.
        """
        with self.driver:
            self.driver.get(self.target_url)

            # Download the csv
            export_page_link = self.driver.find_element(By.LINK_TEXT, "Export")
            export_page_link.click()

            # Waiting for the csv download link to appears, otherwise an
            # error occurs
            csv_download_link = (WebDriverWait(self.driver, 20)
            .until(EC.visibility_of_element_located(
                (By.CSS_SELECTOR, f"[aria-label='{self.csv_aria_label}']"))))
            csv_download_link.click()

            # Retrieves the last updated data date
            info_page_link = self.driver.find_element(By.LINK_TEXT,
                                                      "Informations")
            info_page_link.click()

            # Waiting for the updated data date to appears, otherwise an
            # error occurs
            self._updated_data_date = WebDriverWait(self.driver, 20).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR,
                     f"[ng-if='{self.updated_data_date_ngif}']"))).text

    @property
    def updated_data_date(self):
        """
        :return str: The last updated data date.
        """
        return self._updated_data_date

    @property
    def csv_id(self):
        """
        :return: The filename of the downloaded CSV.
        """
        return self.downloaded_csv_filename

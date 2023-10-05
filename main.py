from processor.data_processor import DataFrameHolder

# Donwload and put the .csv file in the folder "fetcher"
browser = webdriver.Firefox()
browser.get('https://data.economie.gouv.fr/explore/dataset/prix-des-carburants-en-france-flux-instantane-v2/'
            'export/')
browser.implicitly_wait(5)
url_data_gouv = browser.find_element(By.XPATH, '/html/body/div[1]/main/div/div[4]/div[3]/div[2]/div[7]/div/'
                                                'div/div/div[1]/ul[1]/li[1]/div/a').get_attribute('href')
browser.quit()

fetcher = DataFetcher(url_data_gouv)
result_tuple = fetcher.import_data()
# Check the value (df, last modification date)
print(result_tuple)

# On traite nos données de prix des carburants des voitures en france
df_holder = DataFrameHolder('prix-des-carburants-en-france-flux-instantane-v2.csv')
df_holder.process_data()
df_holder.save_processed_dataframe()

# Import the required library



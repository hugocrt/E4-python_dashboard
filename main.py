from data_processor.data_processor import DataFrameHolder
from data_visualizer.data_visualizer import DashboardHolder
from web_scraper.web_scraper import FirefoxScraperHolder


target_url = ('https://data.economie.gouv.fr/explore/dataset/prix-des-'
              'carburants-en-france-flux-instantane-v2/')
csv_aria_label = 'Dataset export (CSV)'
updated_data_date_ng_if = 'ctx.dataset.metas.data_processed'

# Retrieves datas
firefox_scraper = FirefoxScraperHolder(target_url)
firefox_scraper.remove_cwf_existing_csvs()
firefox_scraper.perform_scraping(csv_aria_label, updated_data_date_ng_if)

# Data processing
df_holder = DataFrameHolder(firefox_scraper.csv_id)
df_holder.process_data()
df_holder.save_dataframe()

# Dashboard
dashboard = DashboardHolder(df_holder.data_frame, df_holder.price_columns)
dashboard.app.run_server(debug=True)




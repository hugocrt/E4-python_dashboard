from processor.data_processor import DataFrameHolder
from fetcher.data_fetcher import DataFetcher

# Créez une instance de la classe DataFetcher avec l'URL de base appropriée
data_fetcher = DataFetcher(base_url="https://data.economie.gouv.fr/explore/dataset/"
                                    "prix-des-carburants-en-france-flux-instantane-v2/")

data_fetcher.fetch_data()

# On traite nos données de prix des carburants des voitures en france
# df_holder = DataFrameHolder('prix-des-carburants-en-france-flux-instantane-v2.csv')
# df_holder.process_data()
# df_holder.save_processed_dataframe()



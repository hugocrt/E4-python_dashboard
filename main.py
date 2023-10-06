from processor.data_processor import DataFrameHolder
from fetcher.data_fetcher import DataFetcher

# Créez une instance de la classe DataFetcher avec l'URL de base appropriée
data_fetcher = DataFetcher(base_url="https://data.economie.gouv.fr/explore/dataset/"
                                    "prix-des-carburants-en-france-flux-instantane-v2/")

try:
    # Obtenez l'URL du fichier CSV
    csv_url = data_fetcher.get_csv_url()

    # Téléchargez et sauvegardez le fichier CSV localement
    data_fetcher.save_file_as_csv()

    # Obtenez la date de la page web
    data_fetcher.get_date()

    # Affichez les données et la date obtenues
    print("Données CSV téléchargées :", csv_url)
    print("Date de dernière modification :", data_fetcher.date)
except Exception as e:
    print(f"Une erreur s'est produite : {e}")

# On traite nos données de prix des carburants des voitures en france
df_holder = DataFrameHolder('prix-des-carburants-en-france-flux-instantane-v2.csv')
df_holder.process_data()
df_holder.save_processed_dataframe()



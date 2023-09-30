from fetcher.data_fetcher import DataFetcher
from processor.data_processor import DataProcessor
from visualizer.data_visualizer import DataVisualizer

# Étape 1: Récupération des données depuis data.gouv.fr
fetcher = DataFetcher('lien_vers_le_fichier.csv')
data = fetcher.fetch_data()

# Étape 2: Traitement des données
processor = DataProcessor(data)
processed_data = processor.process_data()

# Étape 3: Création des visualisations
visualizer = DataVisualizer(processed_data)
visualizer.create_maps()
visualizer.create_dashboard()

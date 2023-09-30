import requests
from urllib.parse import urlparse

url = "https://www.data.gouv.fr/fr/datasets/r/64e02cff-9e53-4cb2-adfd-5fcc88b2dc09"

response = requests.get(url)

if response.status_code == 200:
    file_name = urlparse(url).path.split("/")[-1] + ".csv"  # Ajout de l'extension .csv
    with open(file_name, 'wb') as file:
        file.write(response.content)
        print(f"Le fichier {file_name} a été téléchargé avec succès.")
else:
    print("Erreur lors du téléchargement du fichier.")
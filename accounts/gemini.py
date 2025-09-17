import requests
import json

# Remplace par ta vraie clé API
API_KEY = "AIzaSyB_xs42vFrvhcd8vtUGR8Lqgltu605vXUo"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# Corps de la requête
data = {
    "contents": [
        {
            "parts": [
                {
                    "text": "tu me connait"
                }
            ]
        }
    ]
}

# En-têtes HTTP
headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}

# Requête POST
response = requests.post(URL, headers=headers, data=json.dumps(data))

# Vérification du statut
if response.status_code == 200:
    result = response.json()
    # Affichage de la réponse générée
    print("Réponse :", result["candidates"][0]["content"]["parts"][0]["text"])
else:
    print(f"Erreur {response.status_code} :", response.text)

# services/gemini_service.py
import requests
import json
from django.conf import settings
from typing import Dict, Any, Optional

class GeminiService:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        
        if not self.api_key:
            raise ValueError("Clé API Gemini non configurée. Ajoutez GEMINI_API_KEY dans vos settings.")
            
    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash", **kwargs) -> Dict[str, Any]:
        """
        Génère du contenu avec l'API Gemini
        
        Args:
            prompt: Le texte à envoyer à l'API
            model: Le modèle à utiliser (par défaut: gemini-2.0-flash)
            **kwargs: Paramètres supplémentaires pour la requête
            
        Returns:
            La réponse JSON de l'API
        """
        url = f"{self.base_url}/{model}:generateContent"
        headers = {
            'Content-Type': 'application/json',
            'X-goog-api-key': self.api_key
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }
        
        # Ajouter les paramètres optionnels
        if kwargs:
            data.update(kwargs)
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur API Gemini: {str(e)}")
    
    def extract_text_response(self, api_response: Dict[str, Any]) -> Optional[str]:
        """
        Extrait le texte de la réponse de l'API Gemini
        
        Args:
            api_response: La réponse JSON de l'API
            
        Returns:
            Le texte généré ou None si non trouvé
        """
        if ("candidates" in api_response and 
            api_response["candidates"] and 
            "content" in api_response["candidates"][0] and
            "parts" in api_response["candidates"][0]["content"] and
            api_response["candidates"][0]["content"]["parts"] and
            "text" in api_response["candidates"][0]["content"]["parts"][0]):
            
            return api_response["candidates"][0]["content"]["parts"][0]["text"]
        return None

# Instance singleton pour une utilisation globale
gemini_service = GeminiService()
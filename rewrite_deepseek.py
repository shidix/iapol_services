import requests
import re

class CorrectorDeepSeek:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1/chat/completions"
    
    def corregir_texto(self, texto, tipo_correccion="general"):
        """Corrige texto con diferentes modos"""
        
        prompts = {
            "general": "Corrige ortografía, gramática y puntuación:",
            "formal": "Corrige y convierte a lenguaje formal:",
            "datos": "Corrige y da formato a datos personales (DNI, teléfono, email):",
            "tecnico": "Corrige terminología técnica:"
        }
        
        prompt = f"{prompts.get(tipo_correccion, prompts['general'])} {texto}"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "Solo devuelve el texto corregido."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
            
        except Exception as e:
            return f"Error: {str(e)}"


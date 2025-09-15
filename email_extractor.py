import re
import unicodedata
from typing import List, Dict, Optional

class EmailExtractor:
    def __init__(self):
        # Palabras clave que indican que viene un email
        self.palabras_clave = [
            'email es', 'correo es', 'correo electrónico es', 
            'mail es', 'e-mail es', 'contacto es',
            'email:', 'correo:', 'mail:', 'contacto:',
            'escribir a', 'escribir al', 'contactar a',
            'dirigirse a', 'comunicarse con'
        ]
        
        # Patrón para emails con espacios en username
        self.patron_email_espacios = re.compile(r'''
            (?:[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ%+_\-\s]+)  # Username con espacios
            \s*                                    # Espacios
            (?:@|arroba)                           # @ o arroba
            \s*                                    # Espacios
            (?:[a-zA-Z0-9áéíóúÁÉÍÓÚñÑüÜ\-\s]+)    # Dominio con espacios
            \s*                                    # Espacios
            \.                                     # Punto
            \s*                                    # Espacios
            (?:[a-zA-ZáéíóúÁÉÍÓÚ]{2,})            # TLD
        ''', re.VERBOSE | re.IGNORECASE)
    
    def extraer_emails(self, texto: str) -> List[Dict]:
        """Extrae emails con espacios y después de palabras clave"""
        
        emails = []
        
        # Estrategia 1: Buscar después de palabras clave
        emails.extend(self._buscar_despues_palabras_clave(texto))
        
        # Estrategia 2: Buscar patrones de email con espacios
        emails.extend(self._buscar_patrones_espacios(texto))
        
        # Eliminar duplicados
        emails_unicos = []
        emails_vistos = set()
        for email in emails:
            if email['email_limpio'] not in emails_vistos:
                emails_unicos.append(email)
                emails_vistos.add(email['email_limpio'])
        
        return emails_unicos
    
    def _buscar_despues_palabras_clave(self, texto: str) -> List[Dict]:
        """Busca emails después de palabras clave como 'email es'"""
        
        emails = []
        
        for palabra_clave in self.palabras_clave:
            # Buscar la palabra clave en el texto
            patron_clave = re.escape(palabra_clave) + r'\s*[:\.]?\s*([^\s,;]+(?:\s+[^\s,;]+)*)'
            
            for match in re.finditer(patron_clave, texto, re.IGNORECASE):
                posible_email = match.group(1).strip()
                
                # Intentar extraer email del texto después de la palabra clave
                email_extraido = self._extraer_email_de_texto(posible_email)
                email_extraido = posible_email
                if email_extraido:
                    email_limpio = self._limpiar_y_normalizar_email(email_extraido)
                    if self._es_email_valido(email_limpio):
                        emails.append({
                            'email_original': email_extraido,
                            'email_limpio': email_limpio,
                            'tipo': 'después_palabra_clave',
                            'palabra_clave': palabra_clave
                        })
        return emails
    
    def _buscar_patrones_espacios(self, texto: str) -> List[Dict]:
        """Busca patrones de email con espacios en el username"""
        
        emails = []
        
        for match in self.patron_email_espacios.finditer(texto):
            email_bruto = match.group()
            email_limpio = self._limpiar_y_normalizar_email(email_bruto)
            
            if self._es_email_valido(email_limpio):
                emails.append({
                    'email_original': email_bruto,
                    'email_limpio': email_limpio,
                    'tipo': 'patron_espacios'
                })
        
        return emails
    
    def _extraer_email_de_texto(self, texto: str) -> Optional[str]:
        """Intenta extraer un email de un texto que puede contenerlo"""
        
        # Patrones para encontrar emails en texto libre
        patrones = [
            r'([a-zA-Z0-9áéíóúñÑüÜ\s]+@[a-zA-Z0-9áéíóúñÑüÜ\s]+\.[a-zA-Záéíóú]{2,})',
            r'([a-zA-Z0-9áéíóúñÑüÜ\s]+arroba[a-zA-Z0-9áéíóúñÑüÜ\s]+punto[a-zA-Záéíóú]{2,})',
            r'(\b[\wáéíóúñÑüÜ\s.%+-]+\s*@\s*[\wáéíóúñÑüÜ\s.-]+\s*\.\s*[\wáéíóú]{2,}\b)'
        ]
        
        for patron in patrones:
            match = re.search(patron, texto, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _limpiar_y_normalizar_email(self, email_bruto: str) -> str:
        """Limpia espacios y normaliza el email"""
        # Reemplazar "arroba" y "punto"
        email = re.sub(r'\s*arroba\s*', '@', email_bruto, flags=re.IGNORECASE)
        email = re.sub(r'\s*punto\s*', '.', email, flags=re.IGNORECASE)
        
        # Eliminar espacios alrededor de @ y .
        email = re.sub(r'\s*@\s*', '@', email)
        email = re.sub(r'\s*\.\s*', '.', email)
        
        # Eliminar todos los espacios restantes
        email = re.sub(r'\s+', '', email)
        
        # Eliminar tildes (excepto ñ)
        email = self._eliminar_tildes(email)
        
        return email.lower()
    
    def _eliminar_tildes(self, texto: str) -> str:
        """Elimina tildes preservando la ñ"""
        texto_normalizado = unicodedata.normalize('NFD', texto)
        return ''.join(
            c for c in texto_normalizado 
            if not unicodedata.category(c) == 'Mn' or c in ['ñ', 'Ñ']
        )
    
    def _es_email_valido(self, email: str) -> bool:
        """Valida el formato del email"""
        patron_valido = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(patron_valido, email))


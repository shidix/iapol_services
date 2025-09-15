import re
import spacy
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class Direccion:
    calle: Optional[str] = None
    numero: Optional[str] = None
    piso: Optional[str] = None
    puerta: Optional[str] = None
    codigo_postal: Optional[str] = None
    localidad: Optional[str] = None
    provincia: Optional[str] = None
    pais: Optional[str] = None
    texto_original: Optional[str] = None
    confianza: float = 0.0

class ComponentesDireccionExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("es_core_news_md")
        except:
            self.nlp = None
        
        # Expresiones regulares para cada componente
        self.patrones = {
            'calle': r'(?:(?:calle|avenida|avda|paseo|plaza|carretera|c/|av/)\s+)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)',
            'numero': r'(?:nº?|número|num|#)?\s*(\d{1,3}(?:\s*[-°]?\s*\d{0,3})?)(?=\s|,|$)',
            'piso': r'(?:piso|planta|pt\.)\s*(\d+|[A-Z])',
            'puerta': r'(?:puerta|portal|letra|pt\.)\s*([A-Z0-9]+)',
            'codigo_postal': r'\b(\d{5})\b',
            'localidad': r'(?:\d{5}\s+)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{3,})*)',
            'provincia': r'\(([A-ZÁÉÍÓÚÑ]{2,})\)',
            'pais': r'\b(?:españa|espana|spain|francia|italia|portugal|alemania)\b'
        }
        
        # Provincias españolas para validación
        self.provincias_españa = {
            'madrid', 'barcelona', 'valencia', 'sevilla', 'zaragoza', 'málaga', 'murcia',
            'palma', 'bilbao', 'alicante', 'córdoba', 'valladolid', 'vigo', 'gijón',
            'granada', 'elche', 'oviedo', 'santa cruz', 'pamplona', 'cartagena'
        }

    def extraer_componentes(self, texto: str) -> Direccion:
        """Extrae todos los componentes de una dirección"""
        
        direccion = Direccion(texto_original=texto)
        
        # Extraer cada componente
        direccion.calle = self._extraer_calle(texto)
        direccion.numero = self._extraer_numero(texto)
        direccion.piso = self._extraer_piso(texto)
        direccion.puerta = self._extraer_puerta(texto)
        direccion.codigo_postal = self._extraer_codigo_postal(texto)
        direccion.localidad = self._extraer_localidad(texto)
        direccion.provincia = self._extraer_provincia(texto)
        direccion.pais = self._extraer_pais(texto)
        
        # Calcular confianza
        direccion.confianza = self._calcular_confianza(direccion)
        
        return direccion

    def _extraer_calle(self, texto: str) -> Optional[str]:
        """Extrae el nombre de la calle"""
        match = re.search(self.patrones['calle'], texto, re.IGNORECASE)
        if match:
            # Limpiar y normalizar
            calle = match.group(1).strip()
            calle = re.sub(r'\s+', ' ', calle)
            return calle.title()
        return None

    def _extraer_numero(self, texto: str) -> Optional[str]:
        """Extrae el número de la calle"""
        match = re.search(self.patrones['numero'], texto, re.IGNORECASE)
        if match:
            numero = match.group(1).strip()
            # Normalizar formato: eliminar espacios en el número
            numero = re.sub(r'\s', '', numero)
            return numero
        return None

    def _extraer_piso(self, texto: str) -> Optional[str]:
        """Extrae el piso"""
        match = re.search(self.patrones['piso'], texto, re.IGNORECASE)
        return match.group(1) if match else None

    def _extraer_puerta(self, texto: str) -> Optional[str]:
        """Extrae la puerta/portal"""
        match = re.search(self.patrones['puerta'], texto, re.IGNORECASE)
        return match.group(1) if match else None

    def _extraer_codigo_postal(self, texto: str) -> Optional[str]:
        """Extrae el código postal"""
        match = re.search(self.patrones['codigo_postal'], texto)
        if match:
            cp = match.group(1)
            # Validar que sea un código postal español válido
            if cp.isdigit() and 1000 <= int(cp) <= 52999:
                return cp
        return None

    def _extraer_localidad(self, texto: str) -> Optional[str]:
        """Extrae la localidad/ciudad"""
        # Primero intentar después del código postal
        cp_match = re.search(self.patrones['codigo_postal'], texto)
        if cp_match:
            # Buscar texto después del código postal
            texto_despues = texto[cp_match.end():]
            match = re.search(self.patrones['localidad'], texto_despues, re.IGNORECASE)
            if match:
                return match.group(1).strip().title()
        
        # Buscar en todo el texto
        match = re.search(self.patrones['localidad'], texto, re.IGNORECASE)
        if match:
            localidad = match.group(1).strip()
            # Filtrar palabras que no son localidades
            if len(localidad.split()) <= 3 and not any(palabra in localidad.lower() for palabra in ['calle', 'avenida']):
                return localidad.title()
        
        return None

    def _extraer_provincia(self, texto: str) -> Optional[str]:
        """Extrae la provincia"""
        # Buscar entre paréntesis
        match = re.search(self.patrones['provincia'], texto, re.IGNORECASE)
        if match:
            provincia = match.group(1).strip().title()
            if provincia.lower() in self.provincias_españa:
                return provincia
        
        # Buscar en el texto sin paréntesis
        palabras = texto.lower().split()
        for palabra in palabras:
            if palabra in self.provincias_españa:
                return palabra.title()
        
        return None

    def _extraer_pais(self, texto: str) -> Optional[str]:
        """Extrae el país"""
        match = re.search(self.patrones['pais'], texto, re.IGNORECASE)
        if match:
            pais = match.group(0).strip().title()
            # Normalizar España
            if pais.lower() in ['espana', 'españa']:
                return 'España'
            return pais
        return None

    def _calcular_confianza(self, direccion: Direccion) -> float:
        """Calcula la confianza de la extracción"""
        confianza = 0.0
        
        # Puntos por cada componente encontrado
        if direccion.calle: confianza += 0.2
        if direccion.numero: confianza += 0.2
        if direccion.codigo_postal: confianza += 0.2
        if direccion.localidad: confianza += 0.2
        if direccion.provincia: confianza += 0.1
        if direccion.pais: confianza += 0.1
        
        # Bonus por combinaciones válidas
        if direccion.calle and direccion.numero: confianza += 0.1
        if direccion.codigo_postal and direccion.localidad: confianza += 0.1
        
        return min(confianza, 1.0)

class ComponentesConSpacyExtractor:
    def __init__(self):
        try:
            self.nlp = spacy.load("es_core_news_md")
        except:
            self.nlp = None
        
        self.extractor = ComponentesDireccionExtractor()

    def extraer_con_contexto(self, texto: str) -> Dict:
        """Extrae componentes con contexto de spaCy"""
        
        if not self.nlp:
            return self.extractor.extraer_componentes(texto).__dict__
        
        doc = self.nlp(texto)
        direccion = self.extractor.extraer_componentes(texto)
        
        # Enriquecer con información de spaCy
        resultado = direccion.__dict__
        resultado['entidades'] = self._extraer_entidades(doc)
        resultado['oraciones'] = [sent.text for sent in doc.sents]
        resultado['contexto_valido'] = self._validar_contexto(doc, direccion)
        
        return resultado

    def _extraer_entidades(self, doc) -> List[Dict]:
        """Extrae entidades de spaCy relevantes"""
        entidades_relevantes = []
        for ent in doc.ents:
            if ent.label_ in ['LOC', 'MISC', 'ORG']:
                entidades_relevantes.append({
                    'texto': ent.text,
                    'tipo': ent.label_,
                    'inicio': ent.start_char,
                    'fin': ent.end_char
                })
        return entidades_relevantes

    def _validar_contexto(self, doc, direccion: Direccion) -> bool:
        """Valida el contexto lingüístico"""
        palabras_direccion = [
            'calle', 'avenida', 'paseo', 'plaza', 'dirección',
            'domicilio', 'reside', 'vive', 'ubicado'
        ]
        
        texto_lower = doc.text.lower()
        return any(palabra in texto_lower for palabra in palabras_direccion)

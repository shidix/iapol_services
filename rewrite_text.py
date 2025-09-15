import spacy
import re
from typing import List, Dict, Optional
from collections import Counter

class MejoradorRedaccionSpacy:
    def __init__(self):
        # Cargar modelo de spaCy en español
        try:
            self.nlp = spacy.load("es_core_news_sm")
            print("✅ Modelo spaCy cargado correctamente")
        except Exception as e:
            print(f"❌ Error cargando spaCy: {e}")
            self.nlp = None
        
        # Errores comunes a corregir
        self.errores_comunes = {
            r'\bde el\b': 'del',
            r'\ba el\b': 'al',
            r'\bhabían\b': 'había',
            r'\bmas\b': 'más',
            r'\bsolo\b': 'sólo',
            r'\badrede\b': 'adrede',
        }

        # Conectores para mejorar
        self.conectores_mejora = {
            'y': ['además', 'también', 'asimismo'],
            'pero': ['sin embargo', 'no obstante', 'aunque'],
            'porque': ['debido a que', 'puesto que', 'ya que'],
            'entonces': ['por lo tanto', 'en consecuencia', 'así pues']
        }

    def mejorar_redaccion(self, texto: str) -> Dict:
        """
        Mejora la redacción usando spaCy para análisis profundo
        """
        if not self.nlp:
            return {'texto_original': texto, 'texto_mejorado': texto}

        # Procesar texto con spaCy
        doc = self.nlp(texto)

        # Aplicar diferentes mejoras
        texto_mejorado = self._aplicar_mejoras_avanzadas(doc)

        # Analizar resultados
        analisis = self._analizar_calidad(doc)

        return {
            'texto_original': texto,
            'texto_mejorado': texto_mejorado,
            'analisis': analisis,
            'recomendaciones': self._generar_recomendaciones(analisis)
        }

    def _aplicar_mejoras_avanzadas(self, doc) -> str:
        """
        Aplica mejoras usando el análisis de spaCy
        """
        texto_mejorado = doc.text

        print("Errores comunes:")
        # 1. Corregir errores comunes
        texto_mejorado = self._corregir_errores_comunes(texto_mejorado)
        print(texto_mejorado)

        #print("Estructura:")
        # 2. Mejorar estructura de oraciones
        #texto_mejorado = self._mejorar_estructura_oraciones(texto_mejorado)
        #print(texto_mejorado)

        print("Conectores:")
        # 3. Optimizar conectores
        texto_mejorado = self._optimizar_conectores(texto_mejorado)
        print(texto_mejorado)

        print("Puntuación:")
        # 4. Mejorar puntuación
        texto_mejorado = self._mejorar_puntuacion(texto_mejorado)
        print(texto_mejorado)

        print("Capitalización:")
        # 5. Capitalización adecuada
        texto_mejorado = self._capitalizar_texto(texto_mejorado)
        print(texto_mejorado)

        return texto_mejorado

    def _corregir_errores_comunes(self, texto: str) -> str:
        """Corrige errores gramaticales comunes"""
        for patron, reemplazo in self.errores_comunes.items():
            texto = re.sub(patron, reemplazo, texto, flags=re.IGNORECASE)
        return texto

    def _mejorar_estructura_oraciones(self, texto: str) -> str:
        """Mejora la estructura de las oraciones"""
        if not self.nlp:
            return texto

        doc = self.nlp(texto)
        oraciones_mejoradas = []

        for sent in doc.sents:
            oracion = sent.text.strip()

            # Dividir oraciones muy largas
            if len(sent) > 25:  # Más de 25 palabras
                oraciones_divididas = self._dividir_oracion_larga(oracion)
                oraciones_mejoradas.extend(oraciones_divididas)
            else:
                oraciones_mejoradas.append(oracion)

        return '. '.join(oraciones_mejoradas) + '.'

    def _dividir_oracion_larga(self, oracion: str) -> List[str]:
        """Divide oraciones demasiado largas"""
        if not self.nlp:
            return [oracion]

        doc = self.nlp(oracion)
        partes = []
        parte_actual = []

        for token in doc:
            parte_actual.append(token.text)

            # Dividir en conjunciones y comas
            if token.text in [',', ';', 'y', 'pero', 'aunque'] and len(parte_actual) > 8:
                partes.append(' '.join(parte_actual))
                parte_actual = []

        if parte_actual:
            partes.append(' '.join(parte_actual))

        return partes

    def _optimizar_conectores(self, texto: str) -> str:
        """Optimiza el uso de conectores"""
        if not self.nlp:
            return texto

        doc = self.nlp(texto)
        tokens_mejorados = []

        for token in doc:
            if token.text.lower() in self.conectores_mejora:
                # Variar conectores para mejor flujo
                alternativas = self.conectores_mejora[token.text.lower()]
                nuevo_conector = alternativas[len(tokens_mejorados) % len(alternativas)]
                tokens_mejorados.append(nuevo_conector)
            else:
                tokens_mejorados.append(token.text)

        return ' '.join(tokens_mejorados)

    def _mejorar_puntuacion(self, texto: str) -> str:
        """Mejora la puntuación del texto"""
        # Correcciones de puntuación
        correcciones = [
            (r'\s+\.', '.'),
            (r'\.\.+', '.'),
            (r'\s+,', ','),
            (r',\s*', ', '),
            (r'\.\s*', '. '),
            (r'\s+', ' '),
            (r'\.([A-Za-z])', r'. \1'),  # Espacio después de punto
        ]
        
        for patron, reemplazo in correcciones:
            texto = re.sub(patron, reemplazo, texto)
        
        return texto

    def _capitalizar_texto(self, texto: str) -> str:
        """Capitaliza adecuadamente el texto"""
        oraciones = re.split(r'([.!?]+)', texto)
        resultado = []

        for i, parte in enumerate(oraciones):
            if i % 2 == 0:  # Parte de texto (no signos de puntuación)
                if parte.strip():
                    parte = parte[0].upper() + parte[1:] if parte else parte
            resultado.append(parte)

        return ''.join(resultado)

    def _analizar_calidad(self, doc) -> Dict:
        """Analiza la calidad del texto usando spaCy"""
        metricas = {
            'total_palabras': len(doc),
            'total_oraciones': len(list(doc.sents)),
            'oraciones_largas': self._contar_oraciones_largas(doc),
            'vocabulario_riqueza': self._calcular_riqueza_vocabulario(doc),
            'voz_pasiva': self._contar_voz_pasiva(doc),
            'adverbios': self._contar_adverbios(doc),
            'conectores': self._contar_conectores(doc)
        }

        metricas['palabras_por_oracion'] = (
            metricas['total_palabras'] / metricas['total_oraciones']
            if metricas['total_oraciones'] > 0 else 0
        )

        return metricas

    def _contar_oraciones_largas(self, doc, umbral=20) -> int:
        """Cuenta oraciones con muchas palabras"""
        return sum(1 for sent in doc.sents if len(sent) > umbral)

    def _calcular_riqueza_vocabulario(self, doc) -> float:
        """Calcula la riqueza de vocabulario"""
        palabras = [token.lemma_.lower() for token in doc if token.is_alpha]
        if not palabras:
            return 0.0
        return len(set(palabras)) / len(palabras)

    def _contar_voz_pasiva(self, doc) -> int:
        """Cuenta construcciones en voz pasiva"""
        voz_pasiva = 0
        for token in doc:
            if token.dep_ == 'auxpass' or (token.tag_ == 'VMP' and token.dep_ == 'aux'):
                voz_pasiva += 1
        return voz_pasiva

    def _contar_adverbios(self, doc) -> int:
        """Cuenta adverbios"""
        return sum(1 for token in doc if token.pos_ == 'ADV')

    def _contar_conectores(self, doc) -> int:
        """Cuenta conectores discursivos"""
        conectores = {'y', 'pero', 'porque', 'aunque', 'sin embargo', 'no obstante'}
        return sum(1 for token in doc if token.text.lower() in conectores)

    def _generar_recomendaciones(self, analisis: Dict) -> List[str]:
        """Genera recomendaciones basadas en el análisis"""
        recomendaciones = []

        if analisis['palabras_por_oracion'] > 20:
            recomendaciones.append("🔹 Reducir longitud promedio de oraciones (ideal: 15-20 palabras)")

        if analisis['oraciones_largas'] > 2:
            recomendaciones.append("🔹 Dividir oraciones muy largas")

        if analisis['voz_pasiva'] > 3:
            recomendaciones.append("🔹 Reducir el uso de voz pasiva")

        if analisis['vocabulario_riqueza'] < 0.5:
            recomendaciones.append("🔹 Ampliar variedad de vocabulario")

        if analisis['adverbios'] > 10:
            recomendaciones.append("🔹 Reducir adverbios innecesarios")

        return recomendaciones

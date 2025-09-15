# test_spacy.py
import spacy

try:
    nlp = spacy.load("es_core_news_sm")
    print("✅ spaCy instalado correctamente!")
    
    # Probar con un texto
    texto = "El señor Carlos Martínez con DNI 12345678X presenta denuncia"
    doc = nlp(texto)
    
    print("Entidades encontradas:")
    for ent in doc.ents:
        print(f"- {ent.text} ({ent.label_})")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("Ejecuta: python -m spacy download es_core_news_sm")

import spacy

# Cargar el modelo de spaCy para español
nlp = spacy.load('es_core_news_sm')

# Ejemplo de target
target = "By 2030, ensure that all men and women, in particular the poor and the vulnerable, have equal rights to economic resources, as well as access to basic services, ownership and control over land and other forms of property, inheritance, natural resources, appropriate new technology and financial services, including microfinance."

# Procesar el target
doc = nlp(target)

# Extraer grupos nominales
conceptos = set()
for chunk in doc.noun_chunks:
    conceptos.add(chunk.text.lower())

print("Conceptos extraídos:")
for concepto in conceptos:
    print("-", concepto)
import requests
import pandas as pd
import time
import urllib.parse

# Reemplaza 'TU_API_KEY' con tu clave de API de Elsevier
API_KEY = '81860af3fc1ee313c3117491ef76b80f'

# Endpoint de búsqueda de Scopus
SEARCH_URL = 'https://api.elsevier.com/content/search/scopus'

def buscar_articulos_scopus_titulo(frase_clave, max_resultados=1000, resultados_por_pagina=25):
    headers = {
        'X-ELS-APIKey': API_KEY,
        'Accept': 'application/json'
    }
    
    # Construir la consulta de búsqueda
    consulta = f'TITLE("{frase_clave}")'
    
    # Codificar la consulta para la URL
    consulta_codificada = urllib.parse.quote(consulta)
    
    # Inicializar parámetros de búsqueda
    params = {
        'query': consulta,
        'count': resultados_por_pagina,  # Máximo permitido por solicitud (Scopus: 25)
        'start': 0,                       # Índice de inicio para paginación
        'view': 'STANDARD'                # 'STANDARD' para metadatos básicos, 'COMPLETE' para más detalles
    }
    
    articulos = []
    total_obtenidos = 0
    total_disponibles = None
    
    while True:
        response = requests.get(SEARCH_URL, headers=headers, params=params)
        
        if response.status_code == 200:
            datos = response.json()
            
            # Obtener el total de resultados disponibles en la primera solicitud
            if total_disponibles is None:
                try:
                    total_disponibles = int(datos['search-results']['opensearch:totalResults'])
                    print(f"Total de artículos encontrados: {total_disponibles}")
                except (KeyError, ValueError):
                    print("No se pudo obtener el número total de resultados.")
                    break
            
            entries = datos['search-results'].get('entry', [])
            
            if not entries:
                print("No se encontraron más artículos.")
                break
            
            for entry in entries:
                articulo = {
                    'Título': entry.get('dc:title', 'N/A'),
                    'Autores': entry.get('dc:creator', 'N/A'),
                    'DOI': entry.get('prism:doi', 'N/A'),
                    'Fuente': entry.get('prism:publicationName', 'N/A'),
                    'Fecha de Publicación': entry.get('prism:coverDate', 'N/A'),
                    'Enlace': entry.get('prism:url', 'N/A')
                }
                articulos.append(articulo)
                total_obtenidos += 1
                
                # Verificar si se ha alcanzado el máximo deseado
                if total_obtenidos >= max_resultados:
                    break
            
            print(f"Artículos obtenidos hasta ahora: {total_obtenidos}")
            
            if total_obtenidos >= max_resultados:
                break
            
            # Preparar la siguiente solicitud
            params['start'] += resultados_por_pagina
            
            # Respetar los límites de tasa (ejemplo: 1 segundo de pausa entre solicitudes)
            time.sleep(1)
        else:
            print(f"Error en la solicitud: {response.status_code}")
            print(response.text)
            break
    
    return articulos

def guardar_articulos_csv(articulos, nombre_archivo='articulos_titulo_OCSTP.csv'):
    df = pd.DataFrame(articulos)
    df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
    print(f"Artículos guardados en {nombre_archivo}")

if __name__ == "__main__":
    frase_clave = "Sustainable Development Goals"            # Frase clave para buscar en el título
    max_resultados = 8000             # Número máximo de artículos a obtener (ajustable)
    resultados_por_pagina = 25       # Scopus permite hasta 25 resultados por solicitud
    
    articulos = buscar_articulos_scopus_titulo(frase_clave, max_resultados, resultados_por_pagina)
    
    if articulos:
        guardar_articulos_csv(articulos, 'articulos_SDG.csv')
    else:
        print("No se encontraron artículos con la frase clave proporcionada en el título.")

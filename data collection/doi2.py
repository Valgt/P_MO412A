import requests
import pandas as pd
import time
import urllib.parse
import os
import logging
import re

# Configuración del registro (logging)
logging.basicConfig(
    filename='descargar_articulos_SDG.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Obtener la clave de API desde una variable de entorno
API_KEY = os.getenv('ELSEVIER_API_KEY')

if not API_KEY:
    logging.error("La clave de API no está configurada. Establece la variable de entorno 'ELSEVIER_API_KEY'.")
    print("Error: La clave de API no está configurada. Establece la variable de entorno 'ELSEVIER_API_KEY'.")
    exit(1)

# Endpoint de búsqueda de Scopus
SEARCH_URL = 'https://api.elsevier.com/content/search/scopus'

def es_valido_doi(doi):
    """
    Verifica si el DOI tiene una estructura válida.
    
    :param doi: String que representa el DOI a verificar.
    :return: True si el DOI es válido, False en caso contrario.
    """
    patron = r'^10.\d{4,9}/[-._;()/:A-Z0-9]+$'
    return re.match(patron, doi, re.I) is not None

def buscar_articulos_scopus_titulo(frase_clave, anio, max_resultados=5000, resultados_por_pagina=25):
    """
    Busca artículos en Scopus por frase clave en el título y año específico.

    :param frase_clave: Frase clave para buscar en el título.
    :param anio: Año de publicación para la búsqueda.
    :param max_resultados: Número máximo de artículos a obtener por consulta (máximo 5000).
    :param resultados_por_pagina: Número de artículos por solicitud (máximo 25 para Scopus).
    :return: Lista de diccionarios con la información de los artículos encontrados.
    """
    headers = {
        'X-ELS-APIKey': API_KEY,
        'Accept': 'application/json'
    }
    
    # Construir la consulta de búsqueda con año específico
    consulta = f'TITLE("{frase_clave}") AND PUBYEAR = {anio}'
    
    params = {
        'query': consulta,
        'count': resultados_por_pagina,
        'start': 0,
        'view': 'STANDARD'
    }
    
    articulos = []
    total_obtenidos = 0
    total_disponibles = None
    
    while True:
        try:
            response = requests.get(SEARCH_URL, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                datos = response.json()
                
                # Obtener el total de resultados disponibles en la primera solicitud
                if total_disponibles is None:
                    try:
                        total_disponibles = int(datos['search-results']['opensearch:totalResults'])
                        logging.info(f"Total de artículos encontrados en {anio}: {total_disponibles}")
                        print(f"Total de artículos encontrados en {anio}: {total_disponibles}")
                        if total_disponibles == 0:
                            logging.info(f"No se encontraron artículos en el año {anio}.")
                            print(f"No se encontraron artículos en el año {anio}.")
                            break
                    except (KeyError, ValueError):
                        logging.error("No se pudo obtener el número total de resultados.")
                        print("Error: No se pudo obtener el número total de resultados.")
                        break
                
                entries = datos['search-results'].get('entry', [])
                
                if not entries:
                    logging.info(f"No se encontraron más artículos en {anio}.")
                    print(f"No se encontraron más artículos en {anio}.")
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
                    # Validar que el DOI es válido antes de agregar
                    doi = articulo['DOI']
                    if es_valido_doi(doi):
                        articulos.append(articulo)
                        total_obtenidos += 1
                    else:
                        logging.warning(f"DOI inválido encontrado y omitido: {doi}")
                
                print(f"Artículos obtenidos hasta ahora en {anio}: {total_obtenidos}")
                logging.info(f"Artículos obtenidos hasta ahora en {anio}: {total_obtenidos}")
                
                if total_obtenidos >= max_resultados:
                    logging.info(f"Se ha alcanzado el máximo de resultados ({max_resultados}) para el año {anio}.")
                    break
                
                # Preparar la siguiente solicitud
                params['start'] += resultados_por_pagina
                
                # Respetar los límites de tasa (ejemplo: 1 segundo de pausa entre solicitudes)
                time.sleep(1)
            else:
                logging.error(f"Error en la solicitud para el año {anio}: {response.status_code}")
                logging.error(f"Mensaje: {response.text}")
                print(f"Error en la solicitud para el año {anio}: {response.status_code}")
                print(f"Mensaje: {response.text}")
                break
        except requests.exceptions.RequestException as e:
            logging.error(f"Excepción durante la solicitud para el año {anio}: {e}")
            print(f"Excepción durante la solicitud para el año {anio}: {e}")
            # Implementar una pausa antes de reintentar
            time.sleep(5)
            continue
    
    return articulos

def guardar_articulos_csv(articulos, nombre_archivo='articulos_SDG.csv'):
    """
    Guarda los artículos en un archivo CSV.

    :param articulos: Lista de diccionarios con la información de los artículos.
    :param nombre_archivo: Nombre del archivo CSV.
    """
    if not articulos:
        logging.info("No hay artículos para guardar.")
        print("No hay artículos para guardar.")
        return
    
    df = pd.DataFrame(articulos)
    
    if os.path.exists(nombre_archivo):
        # Cargar el CSV existente para evitar duplicados
        df_existente = pd.read_csv(nombre_archivo)
        df_nuevos = df[~df['DOI'].isin(df_existente['DOI'])]
        if not df_nuevos.empty:
            df_nuevos.to_csv(nombre_archivo, mode='a', header=False, index=False, encoding='utf-8-sig')
            logging.info(f"Se agregaron {len(df_nuevos)} nuevos artículos al archivo {nombre_archivo}.")
            print(f"Se agregaron {len(df_nuevos)} nuevos artículos al archivo {nombre_archivo}.")
        else:
            logging.info("No se encontraron nuevos artículos para agregar.")
            print("No se encontraron nuevos artículos para agregar.")
    else:
        # Guardar todos los artículos en un nuevo CSV
        df.to_csv(nombre_archivo, index=False, encoding='utf-8-sig')
        logging.info(f"Artículos guardados en {nombre_archivo}.")
        print(f"Artículos guardados en {nombre_archivo}.")

def main():
    frase_clave = "Sustainable Development Goals"  # Frase clave para buscar en el título
    anio_inicio = 2010  # Año de inicio
    anio_fin = 2024     # Año de fin (ajusta según el año actual)
    
    todos_articulos = []
    
    for anio in range(anio_inicio, anio_fin + 1):
        print(f"\nProcesando año: {anio}")
        logging.info(f"Iniciando búsqueda para el año {anio}")
        articulos = buscar_articulos_scopus_titulo(frase_clave, anio, max_resultados=5000, resultados_por_pagina=25)
        logging.info(f"Encontrados {len(articulos)} artículos en el año {anio}")
        print(f"Encontrados {len(articulos)} artículos en el año {anio}")
        todos_articulos.extend(articulos)
        print(f"Finalizada búsqueda para el año {anio}")
        logging.info(f"Finalizada búsqueda para el año {anio}")
    
    if todos_articulos:
        guardar_articulos_csv(todos_articulos, 'articulos_SDG.csv')
    else:
        logging.info("No se encontraron artículos con la frase clave proporcionada en el título.")
        print("No se encontraron artículos con la frase clave proporcionada en el título.")

if __name__ == "__main__":
    main()

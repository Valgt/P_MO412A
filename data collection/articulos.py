import requests
import pandas as pd
import os
import time
import urllib.parse
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuración del registro (logging)
logging.basicConfig(
    filename='descargas_articulos.log',
    filemode='a',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Reemplaza 'TU_NUEVA_API_KEY' con tu nueva clave de API de Elsevier
API_KEY = '81860af3fc1ee313c3117491ef76b80f'

# Endpoint para obtener artículos por DOI
BASE_URL = 'https://api.elsevier.com/content/article/doi/'

# Directorio donde se guardarán los artículos descargados
DIRECTORIO_DESCARGAS = 'articulos'

# Crear el directorio si no existe
os.makedirs(DIRECTORIO_DESCARGAS, exist_ok=True)

# Configuración de la sesión con reintentos
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    #method_whitelist=["HEAD", "GET", "OPTIONS"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount('https://', adapter)
session.mount('http://', adapter)

def limpiar_doi_para_archivo(doi):
    """Reemplaza caracteres no permitidos en nombres de archivos."""
    return doi.replace('/', '_').replace(':', '_')

def descargar_articulo(doi, formato):
    """
    Descarga el artículo en el formato especificado.

    :param doi: DOI del artículo.
    :param formato: 'text/plain' o 'text/xml'.
    """
    headers = {
        'X-ELS-APIKey': API_KEY,
        'Accept': formato
    }

    # Codificar el DOI para la URL
    doi_codificado = urllib.parse.quote(doi)
    url = BASE_URL + doi_codificado

    # Definir la extensión del archivo basado en el formato
    extension = 'txt' if formato == 'text/plain' else 'xml' if formato == 'text/xml' else 'dat'

    # Limpiar el DOI para usarlo en el nombre del archivo
    doi_limpio = limpiar_doi_para_archivo(doi)
    nombre_archivo = f"{doi_limpio}.{extension}"
    ruta_archivo = os.path.join(DIRECTORIO_DESCARGAS, nombre_archivo)

    # Verificar si el archivo ya existe
    if os.path.exists(ruta_archivo):
        logging.info(f"El archivo '{nombre_archivo}' ya existe. Se omite la descarga.")
        return

    try:
        response = session.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            # Guardar el contenido en el archivo
            with open(ruta_archivo, 'wb') as archivo:
                archivo.write(response.content)
            logging.info(f"Descargado: {nombre_archivo}")
        elif response.status_code == 403:
            logging.error(f"Acceso prohibido al descargar DOI {doi}: {response.status_code}")
            logging.error(f"Mensaje: {response.text}")
        elif response.status_code == 404:
            logging.error(f"DOI {doi} no encontrado: {response.status_code}")
            logging.error(f"Mensaje: {response.text}")
        elif response.status_code == 410:
            logging.error(f"El recurso para DOI {doi} ya no está disponible (410 Gone).")
            logging.error(f"Mensaje: {response.text}")
        else:
            logging.error(f"Error al descargar DOI {doi}: {response.status_code}")
            logging.error(f"Mensaje: {response.text}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Excepción al descargar DOI {doi}: {e}")

def procesar_csv(nombre_csv):
    """
    Procesa el archivo CSV y descarga los artículos correspondientes.

    :param nombre_csv: Nombre del archivo CSV que contiene los DOIs.
    """
    try:
        df = pd.read_csv(nombre_csv)
    except FileNotFoundError:
        logging.error(f"El archivo '{nombre_csv}' no se encontró.")
        return
    except pd.errors.EmptyDataError:
        logging.error(f"El archivo '{nombre_csv}' está vacío.")
        return
    except pd.errors.ParserError:
        logging.error(f"El archivo '{nombre_csv}' no se pudo parsear correctamente.")
        return

    # Suponiendo que la columna que contiene los DOIs se llama 'DOI'
    if 'DOI' not in df.columns:
        logging.error("El archivo CSV no contiene una columna llamada 'DOI'.")
        return

    total_dois = len(df)
    logging.info(f"Total de DOIs a procesar: {total_dois}")

    for index, row in df.iterrows():
        doi = row['DOI']
        if pd.isna(doi):
            logging.warning(f"Fila {index + 1} tiene un DOI vacío. Se omite.")
            continue

        doi = str(doi).strip()
        logging.info(f"Procesando DOI {index + 1}/{total_dois}: {doi}")

        # Descargar en formato texto plano
        descargar_articulo(doi, 'text/plain')

        # Descargar en formato XML
        descargar_articulo(doi, 'text/xml')

        # Pausa para respetar límites de tasa (ejemplo: 1 segundo)
        time.sleep(1)

if __name__ == "__main__":
    nombre_csv = 'articulos_SDG.csv'  # Nombre del archivo CSV generado previamente
    procesar_csv(nombre_csv)

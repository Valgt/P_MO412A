import feedparser

# URL base de búsqueda en arXiv
search_query = "all:sustainable development goals"
base_url = f'http://export.arxiv.org/api/query?search_query={search_query}&start=0&max_results=10'

# Parsear el feed de resultados
response = feedparser.parse(base_url)

# Mostrar los resultados
for entry in response.entries:
    print(f"Authors: {[author.name for author in entry.authors]}")
    print(f"Published: {entry.published}")
    print(f"Summary: {entry.summary}")
    print(f"Link: {entry.link}\n")

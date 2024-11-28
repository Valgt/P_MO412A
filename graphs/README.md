No ejecutas los archivos Build.ipynb y Build_bk.ipynb
    - se usa para crear el grafico

El archivo analysis_thershold_bk.ipynb
    - Tiene un analisis usando threshold sin eliminar los targets del objetivo 17
    - No esta actualizado

1. Ejecutar analysis_complete_graph.ipynb
    - Analisis del grafo entero, sin definir un threshold

2. Ejeecutar analysis_thershold.ipynb
    - Analisis usando los threshold 0.4, 0.5 y 0.6
    - Las imagenes ya tienen los valores medios

3. Ejecutar communities.ipynb
    - Analisis de las comunidades
    - Louvain y Leiden producen el mismo resultado
    - Se compara Louvain/Leiden vs Label
    - En la celda final hay un analisis de las comunidades obtenidos por cada algoritmo
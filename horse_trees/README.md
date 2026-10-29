# Establo de Árboles – Taller de Árboles (Python)

**Caso de estudio:** gestión de un establo de caballos Paso Fino / Criollo.

1. **Genealogía (árbol binario):** cada caballo tiene un padre (hijo izquierdo) y una madre (hijo derecho).
   Operaciones: agregar/eliminar ancestros, recorridos (preorden, inorden, postorden, por niveles),
   altura (generaciones), ruta desde el caballo principal y detección de ancestros repetidos (consanguinidad).
2. **Ranking de concurso (árbol binario de búsqueda):** los caballos se ordenan por puntos.
   Operaciones: insertar, buscar, eliminar (3 casos), mejor/menor puntaje, altura y clasificación.

## Estructura
```
horse_trees/
├── app.py                  # Backend Flask (API JSON)
├── models/
│   ├── pedigree_tree.py    # Árbol binario de genealogía
│   └── ranking_bst.py      # Árbol binario de búsqueda
├── templates/index.html    # Frontend (interfaz en español)
├── static/style.css
├── static/app.js           # Dibujo de árboles en SVG + llamadas a la API
└── requirements.txt
```

## Ejecutar
```
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000

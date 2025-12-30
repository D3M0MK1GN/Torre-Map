# Sistema de Mapas de Inteligencia

## Descripción
Sistema completo para crear y editar mapas de inteligencia con ubicaciones de torres telefónicas. Incluye modo de creación rápida y modo de edición avanzada con servidor web.

## Replit Environment
- **Language**: Python 3.11
- **Framework**: Flask
- **Port**: 5000 (web server)
- **Main Entry**: `run.py` - imports KMZ file and starts the map editor server
- **Deployment**: gunicorn with autoscale

## Modos de Uso

### Modo Interactivo (Menú)
```bash
python mapa_torres.py
```
Muestra un menú con opciones:
1. **Crear Mapa de Inteligencia** - Genera un HTML estático desde Excel
2. **Trabajar Mapa de Inteligencia** - Abre editor interactivo con servidor web
   - Mapa Existente: Carga un HTML ya creado
   - Nuevo Mapa: Crea desde Excel y abre editor

### Modo Línea de Comandos
```bash
python mapa_torres.py torres.xlsx -r 500
python mapa_torres.py torres.xlsx --servidor
python mapa_torres.py --servidor --html mapa_existente.html
```

## Estructura del Proyecto
```
├── mapa_torres.py      # Script principal con menú y lógica de mapas
├── app.py              # Servidor Flask para editor interactivo
├── templates/
│   └── editor.html     # Interfaz del editor web
├── torres.xlsx         # Archivo Excel de ejemplo
└── pyproject.toml      # Dependencias
```

## Funcionalidades del Editor Web
- **Dibujar Rutas**: Click en puntos, doble click para finalizar
- **Agregar Etiquetas**: Marcadores con texto personalizado
- **Agregar Círculos**: Áreas circulares con radio configurable
- **Torres Telefónicas**: Marcadores especiales con:
  - Nombre/etiqueta personalizada
  - Radio configurable (metros)
  - Color del radio seleccionable
  - Grosor de línea ajustable
  - Edición completa después de crear (nombre, radio, color, grosor)
- **Medir Distancia**: Herramienta de medición entre múltiples puntos con:
  - Cálculo usando fórmula Haversine
  - Visualización en metros o kilómetros
  - Marcadores visuales A, B, C... y línea de conexión
  - Panel flotante con distancia total y número de puntos
- **Exportar Mapa**: Exportación a formatos geográficos:
  - KML (Google Earth/Maps compatible)
  - KMZ (KML comprimido)
  - Exporta rutas, etiquetas, círculos y torres con estilos
- **Selector de Color**: Personalización de elementos
- **Deshacer/Limpiar**: Control de cambios
- **Guardar Mapa**: Exporta como nuevo HTML con todos los cambios
- **Importar KMZ/KML**: Carga archivos de Google Earth con:
  - Marcadores con iconos personalizados (preservados en base64)
  - Líneas y rutas con estilos
  - Todos los elementos importados son completamente editables
- **Gestión de Capas**: Organizar elementos por caso/proyecto:
  - Crear capas con nombre y color identificativo
  - Asignar elementos a capas desde la lista de elementos
  - Toggle de visibilidad por capa (checkbox ojo)
  - Contador de elementos por capa
  - Persistencia en capas_mapa.json
  - Compatible con visibilidad individual de elementos

## Dependencias
- pandas
- folium
- openpyxl
- branca
- flask

## Requisitos del Excel
- Hoja llamada "FTD"
- Columnas "Latitud" y "Longitud"

## Archivos Generados
- `mapa_YYYYMMDD_HHMMSS.html` - Mapas estáticos
- `mapa_editado_YYYYMMDD_HHMMSS.html` - Mapas editados
- `mapa_trabajo_temp.html` - Archivo temporal para edición

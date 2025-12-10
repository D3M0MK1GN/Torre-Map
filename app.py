from flask import Flask, render_template, request, jsonify, send_file
import os
import json
import re
from datetime import datetime

app = Flask(__name__)

ARCHIVO_ELEMENTOS = 'elementos_mapa.json'

def obtener_archivo_mapa():
    """Obtiene el archivo de mapa actual desde variable de entorno."""
    mapa_env = os.environ.get('MAPA_HTML')
    if mapa_env and os.path.exists(mapa_env):
        return mapa_env
    return None

def cargar_contenido_mapa():
    """Carga el contenido HTML del mapa."""
    archivo = obtener_archivo_mapa()
    if archivo:
        with open(archivo, 'r', encoding='utf-8') as f:
            return f.read()
    return None

def cargar_elementos():
    """Carga los elementos desde el archivo JSON de persistencia."""
    if os.path.exists(ARCHIVO_ELEMENTOS):
        try:
            with open(ARCHIVO_ELEMENTOS, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_elementos(elementos):
    """Guarda los elementos en el archivo JSON de persistencia."""
    with open(ARCHIVO_ELEMENTOS, 'w', encoding='utf-8') as f:
        json.dump(elementos, f, ensure_ascii=False, indent=2)

def extraer_elementos_de_html(contenido_html):
    """Extrae elementos guardados previamente del HTML."""
    elementos = []
    patron = r'var elementosGuardados = (\[.*?\]);'
    match = re.search(patron, contenido_html, re.DOTALL)
    if match:
        try:
            elementos = json.loads(match.group(1))
        except:
            pass
    return elementos

def inicializar_elementos():
    """Inicializa los elementos al cargar un mapa."""
    contenido = cargar_contenido_mapa()
    if contenido:
        elementos_html = extraer_elementos_de_html(contenido)
        if elementos_html:
            guardar_elementos(elementos_html)
            return elementos_html
    elementos_existentes = cargar_elementos()
    return elementos_existentes

@app.route('/')
def editor():
    """Página principal del editor."""
    mapa_html = cargar_contenido_mapa()
    if not mapa_html:
        return "Error: No se ha cargado ningún mapa. Ejecute el script con la opción de servidor.", 404
    
    elementos = inicializar_elementos()
    return render_template('editor.html', mapa_contenido=mapa_html, elementos=json.dumps(elementos))

def obtener_siguiente_id():
    """Obtiene el siguiente ID para un elemento."""
    elementos = cargar_elementos()
    if not elementos:
        return 1
    return max(e.get('id', 0) for e in elementos) + 1

@app.route('/api/agregar-ruta', methods=['POST'])
def agregar_ruta():
    """Agrega una nueva ruta al mapa."""
    elementos = cargar_elementos()
    data = request.json
    elemento = {
        'id': obtener_siguiente_id(),
        'tipo': 'ruta',
        'puntos': data.get('puntos', []),
        'color': data.get('color', '#FF0000'),
        'grosor': data.get('grosor', 3),
        'nombre': data.get('nombre', f'Ruta {len(elementos) + 1}')
    }
    elementos.append(elemento)
    guardar_elementos(elementos)
    return jsonify({'success': True, 'elemento': elemento})

@app.route('/api/agregar-etiqueta', methods=['POST'])
def agregar_etiqueta():
    """Agrega una nueva etiqueta al mapa."""
    elementos = cargar_elementos()
    data = request.json
    elemento = {
        'id': obtener_siguiente_id(),
        'tipo': 'etiqueta',
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'texto': data.get('texto', 'Etiqueta'),
        'color': data.get('color', '#000000'),
        'icono': data.get('icono', 'info')
    }
    elementos.append(elemento)
    guardar_elementos(elementos)
    return jsonify({'success': True, 'elemento': elemento})

@app.route('/api/agregar-circulo', methods=['POST'])
def agregar_circulo():
    """Agrega un nuevo círculo al mapa."""
    elementos = cargar_elementos()
    data = request.json
    elemento = {
        'id': obtener_siguiente_id(),
        'tipo': 'circulo',
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'radio': data.get('radio', 100),
        'color': data.get('color', '#3388ff'),
        'nombre': data.get('nombre', f'Circulo {len(elementos) + 1}')
    }
    elementos.append(elemento)
    guardar_elementos(elementos)
    return jsonify({'success': True, 'elemento': elemento})

@app.route('/api/agregar-torre', methods=['POST'])
def agregar_torre():
    """Agrega una nueva torre telefónica al mapa."""
    elementos = cargar_elementos()
    data = request.json
    elemento = {
        'id': obtener_siguiente_id(),
        'tipo': 'torre',
        'lat': data.get('lat'),
        'lon': data.get('lon'),
        'radio': data.get('radio', 500),
        'color': data.get('color', '#e74c3c'),
        'grosor': data.get('grosor', 2),
        'nombre': data.get('nombre', f'Torre Telefonica {len(elementos) + 1}')
    }
    elementos.append(elemento)
    guardar_elementos(elementos)
    return jsonify({'success': True, 'elemento': elemento})

@app.route('/api/actualizar-torre/<int:elemento_id>', methods=['PATCH'])
def actualizar_torre(elemento_id):
    """Actualiza una torre telefónica existente."""
    elementos = cargar_elementos()
    data = request.json
    
    for elem in elementos:
        if elem['id'] == elemento_id:
            if 'nombre' in data:
                elem['nombre'] = data['nombre']
            if 'radio' in data:
                elem['radio'] = data['radio']
            if 'color' in data:
                elem['color'] = data['color']
            if 'grosor' in data:
                elem['grosor'] = data['grosor']
            guardar_elementos(elementos)
            return jsonify({'success': True, 'elemento': elem})
    
    return jsonify({'success': False, 'mensaje': 'Elemento no encontrado'}), 404

@app.route('/api/eliminar-elemento/<int:elemento_id>', methods=['DELETE'])
def eliminar_elemento(elemento_id):
    """Elimina un elemento del mapa."""
    elementos = cargar_elementos()
    elementos = [e for e in elementos if e['id'] != elemento_id]
    guardar_elementos(elementos)
    return jsonify({'success': True})

@app.route('/api/deshacer', methods=['POST'])
def deshacer():
    """Elimina el último elemento agregado."""
    elementos = cargar_elementos()
    if elementos:
        eliminado = elementos.pop()
        guardar_elementos(elementos)
        return jsonify({'success': True, 'eliminado': eliminado})
    return jsonify({'success': False, 'mensaje': 'No hay elementos para deshacer'})

@app.route('/api/limpiar', methods=['POST'])
def limpiar():
    """Limpia todos los elementos agregados."""
    guardar_elementos([])
    return jsonify({'success': True})

@app.route('/api/elementos', methods=['GET'])
def obtener_elementos_api():
    """Obtiene todos los elementos agregados."""
    return jsonify(cargar_elementos())

@app.route('/api/actualizar-elemento/<int:elemento_id>', methods=['PATCH'])
def actualizar_elemento(elemento_id):
    """Actualiza un elemento existente (renombrar)."""
    elementos = cargar_elementos()
    data = request.json
    
    for elem in elementos:
        if elem['id'] == elemento_id:
            if 'nombre' in data:
                elem['nombre'] = data['nombre']
            if 'texto' in data:
                elem['texto'] = data['texto']
            guardar_elementos(elementos)
            return jsonify({'success': True, 'elemento': elem})
    
    return jsonify({'success': False, 'mensaje': 'Elemento no encontrado'}), 404

@app.route('/api/guardar', methods=['POST'])
def guardar_mapa():
    """Guarda el mapa con los elementos agregados."""
    archivo_original = obtener_archivo_mapa()
    if not archivo_original:
        return jsonify({'success': False, 'mensaje': 'No hay mapa cargado'})
    
    with open(archivo_original, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    contenido = re.sub(
        r'<script>\s*\(function\(\)\s*\{\s*var elementosGuardados = \[.*?\].*?\}\)\(\);\s*</script>',
        '',
        contenido,
        flags=re.DOTALL
    )
    
    elementos = cargar_elementos()
    script_elementos = generar_script_elementos(elementos)
    
    if '</body>' in contenido:
        contenido = contenido.replace('</body>', f'{script_elementos}</body>')
    else:
        contenido += script_elementos
    
    nombre_salida = f"mapa_editado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    with open(nombre_salida, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    return jsonify({
        'success': True, 
        'archivo': nombre_salida,
        'mensaje': f'Mapa guardado como {nombre_salida}'
    })

def generar_script_elementos(elementos):
    """Genera el script JavaScript para los elementos agregados."""
    if not elementos:
        return ''
    
    elementos_limpios = []
    for elem in elementos:
        elem_limpio = {k: v for k, v in elem.items() if not k.startswith('_')}
        elementos_limpios.append(elem_limpio)
    
    elementos_json = json.dumps(elementos_limpios, ensure_ascii=False)
    return f'''
<script>
(function() {{
    var elementosGuardados = {elementos_json};
    
    function calcularPuntoFinal(lat, lon, distKm, angulo) {{
        var R = 6371, distRad = distKm / R, brngRad = angulo * Math.PI / 180;
        var lat1Rad = lat * Math.PI / 180, lon1Rad = lon * Math.PI / 180;
        var lat2Rad = Math.asin(Math.sin(lat1Rad) * Math.cos(distRad) + Math.cos(lat1Rad) * Math.sin(distRad) * Math.cos(brngRad));
        var lon2Rad = lon1Rad + Math.atan2(Math.sin(brngRad) * Math.sin(distRad) * Math.cos(lat1Rad), Math.cos(distRad) - Math.sin(lat1Rad) * Math.sin(lat2Rad));
        return [lat2Rad * 180 / Math.PI, lon2Rad * 180 / Math.PI];
    }}
    
    function esperarMapa() {{
        var mapInstance = null;
        for (var key in window) {{
            try {{
                if (window[key] instanceof L.Map) {{
                    mapInstance = window[key];
                    break;
                }}
            }} catch(e) {{}}
        }}
        
        if (!mapInstance) {{
            setTimeout(esperarMapa, 100);
            return;
        }}
        
        elementosGuardados.forEach(function(elem) {{
            if (elem.tipo === 'ruta') {{
                L.polyline(elem.puntos, {{
                    color: elem.color,
                    weight: elem.grosor
                }}).addTo(mapInstance).bindPopup(elem.nombre);
            }} else if (elem.tipo === 'etiqueta') {{
                L.marker([elem.lat, elem.lon]).addTo(mapInstance)
                    .bindPopup(elem.texto);
            }} else if (elem.tipo === 'torre') {{
                var torreColor = elem.color || '#e74c3c';
                var torreGrosor = elem.grosor || 2;
                var iconoSvg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28"><path fill="' + torreColor + '" stroke="white" stroke-width="1" d="M12 2L8 10h3v10h2V10h3L12 2z"/><circle cx="12" cy="5" r="2" fill="white"/><path fill="none" stroke="' + torreColor + '" stroke-width="2" d="M6 8c0-3 2.5-5 6-5s6 2 6 5"/><path fill="none" stroke="' + torreColor + '" stroke-width="2" d="M4 10c0-4 3.5-7 8-7s8 3 8 7"/></svg>';
                var torreIcono = L.divIcon({{
                    className: 'bts-marker',
                    html: '<div style="background:white;border-radius:50%;padding:2px;box-shadow:0 2px 5px rgba(0,0,0,0.3);">' + iconoSvg + '</div>',
                    iconSize: [32, 32],
                    iconAnchor: [16, 16]
                }});
                L.marker([elem.lat, elem.lon], {{icon: torreIcono}}).addTo(mapInstance)
                    .bindPopup('<b>' + elem.nombre + '</b><br>Radio: ' + elem.radio + 'm');
                L.circle([elem.lat, elem.lon], {{
                    radius: elem.radio,
                    color: torreColor,
                    fill: true,
                    fillOpacity: 0.15,
                    weight: torreGrosor
                }}).addTo(mapInstance);
                var angulos = [180, 300, 60];
                var colores = ['blue', 'green', 'red'];
                angulos.forEach(function(angulo, i) {{
                    var pf = calcularPuntoFinal(elem.lat, elem.lon, elem.radio / 1000, angulo);
                    L.polyline([[elem.lat, elem.lon], pf], {{
                        color: colores[i],
                        weight: 2,
                        opacity: 0.8,
                        dashArray: '5, 5'
                    }}).addTo(mapInstance);
                }});
                var cardinales = {{'N': 0, 'E': 90, 'S': 180, 'O': 270}};
                for (var p in cardinales) {{
                    var pc = calcularPuntoFinal(elem.lat, elem.lon, (elem.radio * 0.9) / 1000, cardinales[p]);
                    L.marker(pc, {{
                        icon: L.divIcon({{
                            className: 'cardinal-label',
                            html: '<div style="font-size:10pt;font-weight:bold;color:black;background:white;padding:2px;border-radius:3px;">' + p + '</div>',
                            iconSize: [20, 20],
                            iconAnchor: [10, 10]
                        }})
                    }}).addTo(mapInstance);
                }}
            }} else if (elem.tipo === 'circulo') {{
                L.circle([elem.lat, elem.lon], {{
                    radius: elem.radio,
                    color: elem.color,
                    fillOpacity: 0.2
                }}).addTo(mapInstance).bindPopup(elem.nombre);
            }}
        }});
    }}
    
    document.addEventListener('DOMContentLoaded', function() {{
        setTimeout(esperarMapa, 500);
    }});
}})();
</script>
'''

@app.route('/api/descargar/<nombre_archivo>')
def descargar_archivo(nombre_archivo):
    """Descarga un archivo guardado."""
    if os.path.exists(nombre_archivo):
        return send_file(nombre_archivo, as_attachment=True)
    return jsonify({'success': False, 'mensaje': 'Archivo no encontrado'}), 404

def set_mapa_archivo(archivo):
    """Configura el archivo de mapa a usar."""
    os.environ['MAPA_HTML'] = archivo
    if os.path.exists(ARCHIVO_ELEMENTOS):
        os.remove(ARCHIVO_ELEMENTOS)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium.features import CustomIcon
from branca.element import Element
import argparse
import sys
import json
import os
import zipfile
import base64
from fastkml import kml

NOMBRE_HOJA = "FTD"
ICONO_TORRE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="40" height="40">
  <rect x="28" y="10" width="8" height="50" fill="#8B0000"/>
  <polygon points="32,0 20,15 44,15" fill="#8B0000"/>
  <rect x="18" y="20" width="28" height="4" fill="#555"/>
  <rect x="22" y="30" width="20" height="3" fill="#555"/>
  <rect x="26" y="40" width="12" height="3" fill="#555"/>
  <circle cx="32" cy="6" r="4" fill="#FF4444"/>
</svg>"""

def limpiar_coordenada(coord_str):
    if pd.isna(coord_str) or coord_str is None:
        return None
    s = str(coord_str).strip().replace(' ', '')
    if '.' not in s:
        return s
    negativo = s.startswith('-')
    s = s.lstrip('-')
    partes = s.rsplit('.', 1)
    resultado = partes[0].replace('.', '') + '.' + partes[1] if len(partes) == 2 else s
    return f"-{resultado}" if negativo else resultado

def encontrar_columnas_coordenadas(df):
    col_map = {col.lower(): col for col in df.columns}
    lat_col = next((v for k, v in col_map.items() if 'latitud' in k), None)
    lon_col = next((v for k, v in col_map.items() if 'longitud' in k), None)
    return (lat_col, lon_col) if lat_col and lon_col else (None, None)

def crear_icono_torre():
    return f"data:image/svg+xml;base64,{base64.b64encode(ICONO_TORRE_SVG.encode()).decode()}"

def crear_mapa_base(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=14, max_zoom=22, tiles=None)
    folium.TileLayer('OpenStreetMap', name='Mapa Estandar', max_zoom=19).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satelital', overlay=False, max_zoom=22
    ).add_to(m)
    return m

def guardar_mapa(m, guardar_como, prefijo):
    archivo = guardar_como or f"{prefijo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    m.save(archivo)
    print("-" * 50)
    print(f"Mapa generado: {archivo}")
    print("-" * 50)
    return archivo

def crear_html_control_y_scripts(radio_inicial, torres_data):
    return f'''<div id="control-radio" style="position:fixed;top:10px;left:50%;transform:translateX(-50%);z-index:1000;background:#2c3e50;color:white;padding:10px 20px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.3);display:flex;align-items:center;gap:15px;font-family:Arial,sans-serif;">
    <h3 style="margin:0;font-size:1.1em;">Mapa de Torres Telefonicas</h3>
    <label style="font-size:0.9em;">Radio (metros):</label>
    <input type="number" id="radio-input" value="{radio_inicial}" min="100" max="5000" style="padding:5px 10px;border:none;border-radius:4px;width:80px;">
    <button onclick="actualizarRadio()" style="background:#3498db;color:white;border:none;padding:8px 15px;border-radius:4px;cursor:pointer;">Actualizar</button>
</div>
<script>
var torresData = {json.dumps(torres_data)};
var sectoresLayer = null, mapInstance = null;
document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        for (var key in window) if (window[key] instanceof L.Map) {{ mapInstance = window[key]; break; }}
        if (mapInstance) {{ sectoresLayer = L.layerGroup().addTo(mapInstance); dibujarSectores({radio_inicial}); }}
    }}, 500);
}});
function calcularPuntoFinal(lat, lon, distKm, angulo) {{
    var R = 6371, distRad = distKm / R, brngRad = angulo * Math.PI / 180;
    var lat1Rad = lat * Math.PI / 180, lon1Rad = lon * Math.PI / 180;
    var lat2Rad = Math.asin(Math.sin(lat1Rad) * Math.cos(distRad) + Math.cos(lat1Rad) * Math.sin(distRad) * Math.cos(brngRad));
    var lon2Rad = lon1Rad + Math.atan2(Math.sin(brngRad) * Math.sin(distRad) * Math.cos(lat1Rad), Math.cos(distRad) - Math.sin(lat1Rad) * Math.sin(lat2Rad));
    return [lat2Rad * 180 / Math.PI, lon2Rad * 180 / Math.PI];
}}
function dibujarSectores(radioMetros) {{
    if (!sectoresLayer) return;
    sectoresLayer.clearLayers();
    var angulos = [180, 300, 60], colores = ['blue', 'green', 'red'], cardinales = {{'N': 0, 'E': 90, 'S': 180, 'O': 270}};
    torresData.forEach(function(torre) {{
        L.circle([torre.lat, torre.lon], {{radius: radioMetros, color: '#FFFF00', fill: true, fillOpacity: 0.15, weight: 1}}).addTo(sectoresLayer);
        angulos.forEach(function(angulo, i) {{
            var pf = calcularPuntoFinal(torre.lat, torre.lon, radioMetros / 1000, angulo);
            L.polyline([[torre.lat, torre.lon], pf], {{color: colores[i], weight: 2, opacity: 0.8, dashArray: '5, 5'}}).addTo(sectoresLayer);
        }});
        for (var p in cardinales) {{
            var pc = calcularPuntoFinal(torre.lat, torre.lon, (radioMetros * 0.9) / 1000, cardinales[p]);
            L.marker(pc, {{icon: L.divIcon({{className: 'cardinal-label', html: '<div style="font-size:10pt;font-weight:bold;color:black;background:white;padding:2px;border-radius:3px;">' + p + '</div>', iconSize: [20, 20], iconAnchor: [0, 0]}}))}}).addTo(sectoresLayer);
        }}
    }});
}}
function actualizarRadio() {{
    var r = parseInt(document.getElementById('radio-input').value);
    if (r >= 100 && r <= 5000) dibujarSectores(r); else alert('El radio debe estar entre 100 y 5000 metros');
}}
</script>'''

def crear_mapa_de_torres(archivo_excel, radio_metros, guardar_como=None):
    print(f"Buscando hoja '{NOMBRE_HOJA}' en '{archivo_excel}'...")
    print(f"Radio configurado: {radio_metros} metros")
    try:
        df = pd.read_excel(archivo_excel, sheet_name=NOMBRE_HOJA)
    except FileNotFoundError:
        print(f"Error: Archivo '{archivo_excel}' no encontrado.")
        return None
    except ValueError:
        print(f"Error: Hoja '{NOMBRE_HOJA}' no encontrada en el archivo.")
        return None
    except Exception as e:
        print(f"Error al leer Excel: {e}")
        return None
    
    lat_col, lon_col = encontrar_columnas_coordenadas(df)
    if not lat_col or not lon_col:
        print("Error: No se encontraron columnas 'Latitud' y 'Longitud'.")
        return None
    
    print(f"Columnas encontradas: Latitud ('{lat_col}'), Longitud ('{lon_col}')")
    df['Lat_F'] = pd.to_numeric(df[lat_col].apply(limpiar_coordenada), errors='coerce')
    df['Lon_F'] = pd.to_numeric(df[lon_col].apply(limpiar_coordenada), errors='coerce')
    df_valido = df.dropna(subset=['Lat_F', 'Lon_F'])
    
    if df_valido.empty:
        print("Error: No se encontraron coordenadas validas.")
        return None
    
    print(f"{len(df_valido)} coordenadas validas procesadas.")
    torres_data = [{'lat': row['Lat_F'], 'lon': row['Lon_F']} for _, row in df_valido.iterrows()]
    
    m = crear_mapa_base(df_valido['Lat_F'].mean(), df_valido['Lon_F'].mean())
    cluster = MarkerCluster(name='Torres Telefonicas').add_to(m)
    icono_url = crear_icono_torre()
    
    for _, row in df_valido.iterrows():
        folium.Marker(
            location=[row['Lat_F'], row['Lon_F']],
            icon=CustomIcon(icono_url, icon_size=(40, 40), icon_anchor=(20, 40)),
            tooltip=f"Lat: {row['Lat_F']:.4f}, Lon: {row['Lon_F']:.4f}"
        ).add_to(cluster)
    
    folium.LayerControl(position='topleft', collapsed=False).add_to(m)
    m.get_root().html.add_child(Element(crear_html_control_y_scripts(radio_metros, torres_data)))
    return guardar_mapa(m, guardar_como, 'mapa')

def leer_contenido_kml(archivo):
    extension = archivo.lower().split('.')[-1]
    try:
        if extension == 'kmz':
            with zipfile.ZipFile(archivo, 'r') as z:
                for nombre in z.namelist():
                    if nombre.endswith('.kml'):
                        return z.read(nombre)
            print("Error: No se encontro archivo KML dentro del KMZ.")
            return None
        elif extension == 'kml':
            with open(archivo, 'rb') as f:
                return f.read()
        else:
            print("Error: Extension no soportada. Use .kml o .kmz")
            return None
    except Exception as e:
        print(f"Error al leer archivo: {e}")
        return None

def extraer_iconos_kmz(archivo):
    iconos_base64 = {}
    extension = archivo.lower().split('.')[-1]
    if extension != 'kmz':
        return iconos_base64
    try:
        with zipfile.ZipFile(archivo, 'r') as z:
            for nombre in z.namelist():
                if nombre.startswith('images/') and nombre.endswith('.png'):
                    datos = z.read(nombre)
                    icono_base64 = f"data:image/png;base64,{base64.b64encode(datos).decode()}"
                    iconos_base64[nombre] = icono_base64
                    print(f"  Icono extraido: {nombre}")
    except Exception as e:
        print(f"Error al extraer iconos: {e}")
    return iconos_base64

def parsear_estilos_kml(contenido_kml):
    import re
    estilos = {}
    style_maps = {}
    contenido_str = contenido_kml.decode('utf-8') if isinstance(contenido_kml, bytes) else contenido_kml
    style_pattern = r'<Style id="([^"]+)"[^>]*>.*?<Icon>.*?<href>([^<]+)</href>.*?</Icon>.*?</Style>'
    for match in re.finditer(style_pattern, contenido_str, re.DOTALL):
        style_id = match.group(1)
        href = match.group(2)
        estilos[style_id] = href
    stylemap_pattern = r'<StyleMap id="([^"]+)"[^>]*>.*?<Pair>.*?<key>normal</key>.*?<styleUrl>#([^<]+)</styleUrl>.*?</Pair>.*?</StyleMap>'
    for match in re.finditer(stylemap_pattern, contenido_str, re.DOTALL):
        map_id = match.group(1)
        normal_style = match.group(2)
        if normal_style in estilos:
            style_maps[map_id] = estilos[normal_style]
    return estilos, style_maps

def obtener_style_url_placemark(contenido_kml, nombre_placemark):
    import re
    contenido_str = contenido_kml.decode('utf-8') if isinstance(contenido_kml, bytes) else contenido_kml
    pattern = rf'<Placemark[^>]*>.*?<name>{re.escape(nombre_placemark)}</name>.*?<styleUrl>#([^<]+)</styleUrl>.*?</Placemark>'
    match = re.search(pattern, contenido_str, re.DOTALL)
    if match:
        return match.group(1)
    return None

def extraer_placemarks_con_estilos(contenido_kml):
    import re
    contenido_str = contenido_kml.decode('utf-8') if isinstance(contenido_kml, bytes) else contenido_kml
    placemarks = []
    placemark_pattern = r'<Placemark[^>]*>(.*?)</Placemark>'
    for match in re.finditer(placemark_pattern, contenido_str, re.DOTALL):
        placemark_content = match.group(1)
        name_match = re.search(r'<name>([^<]*)</name>', placemark_content)
        nombre = name_match.group(1) if name_match else ''
        desc_match = re.search(r'<description>([^<]*)</description>', placemark_content)
        desc = desc_match.group(1) if desc_match else ''
        style_match = re.search(r'<styleUrl>#([^<]+)</styleUrl>', placemark_content)
        style_url = style_match.group(1) if style_match else None
        coord_match = re.search(r'<coordinates>([^<]+)</coordinates>', placemark_content)
        if coord_match:
            coords_str = coord_match.group(1).strip()
            coords_list = coords_str.split()
            if len(coords_list) == 1:
                parts = coords_str.split(',')
                if len(parts) >= 2:
                    try:
                        lon = float(parts[0])
                        lat = float(parts[1])
                        placemarks.append({
                            'tipo': 'punto',
                            'lat': lat,
                            'lon': lon,
                            'nombre': nombre,
                            'desc': desc,
                            'style_url': style_url
                        })
                    except:
                        pass
            else:
                coords = []
                for coord in coords_list:
                    parts = coord.split(',')
                    if len(parts) >= 2:
                        try:
                            lon = float(parts[0])
                            lat = float(parts[1])
                            coords.append((lat, lon))
                        except:
                            pass
                if coords:
                    if coords[0] == coords[-1] and len(coords) > 3:
                        placemarks.append({
                            'tipo': 'poligono',
                            'coords': coords,
                            'nombre': nombre,
                            'desc': desc,
                            'style_url': style_url
                        })
                    else:
                        placemarks.append({
                            'tipo': 'linea',
                            'coords': coords,
                            'nombre': nombre,
                            'desc': desc,
                            'style_url': style_url
                        })
    return placemarks

def importar_kml_kmz(archivo, guardar_como=None):
    print(f"Importando archivo: {archivo}")
    contenido = leer_contenido_kml(archivo)
    if not contenido:
        return None
    
    print("Extrayendo iconos del archivo...")
    iconos_base64 = extraer_iconos_kmz(archivo)
    
    print("Parseando estilos...")
    estilos, style_maps = parsear_estilos_kml(contenido)
    
    print("Extrayendo elementos con estilos...")
    placemarks = extraer_placemarks_con_estilos(contenido)
    
    puntos = [p for p in placemarks if p['tipo'] == 'punto']
    lineas = [p for p in placemarks if p['tipo'] == 'linea']
    poligonos = [p for p in placemarks if p['tipo'] == 'poligono']
    
    if not placemarks:
        print("Error: No se encontraron elementos geograficos.")
        return None
    
    print(f"Elementos: {len(puntos)} puntos, {len(lineas)} lineas, {len(poligonos)} poligonos")
    
    todas = [(p['lat'], p['lon']) for p in puntos]
    for l in lineas: todas.extend(l['coords'])
    for p in poligonos: todas.extend(p['coords'])
    
    m = crear_mapa_base(sum(c[0] for c in todas)/len(todas), sum(c[1] for c in todas)/len(todas))
    
    for p in puntos:
        popup = f"<b>{p['nombre']}</b><br>{p['desc']}" if p['nombre'] or p['desc'] else f"Lat: {p['lat']:.4f}, Lon: {p['lon']:.4f}"
        icono_url = None
        if p.get('style_url'):
            style_id = p['style_url']
            href = None
            if style_id in style_maps:
                href = style_maps[style_id]
            elif style_id in estilos:
                href = estilos[style_id]
            elif style_id + '-normal' in estilos:
                href = estilos[style_id + '-normal']
            if href and href in iconos_base64:
                icono_url = iconos_base64[href]
        
        if icono_url:
            icono = CustomIcon(icono_url, icon_size=(32, 32), icon_anchor=(16, 32))
            folium.Marker([p['lat'], p['lon']], popup=popup, tooltip=p['nombre'] or None, icon=icono).add_to(m)
        else:
            folium.Marker([p['lat'], p['lon']], popup=popup, tooltip=p['nombre'] or None).add_to(m)
    
    for l in lineas:
        popup = f"<b>{l['nombre']}</b><br>{l['desc']}" if l['nombre'] or l['desc'] else None
        folium.PolyLine(l['coords'], color='blue', weight=3, popup=popup).add_to(m)
    
    for p in poligonos:
        popup = f"<b>{p['nombre']}</b><br>{p['desc']}" if p['nombre'] or p['desc'] else None
        folium.Polygon(p['coords'], color='green', fill=True, fillOpacity=0.3, popup=popup).add_to(m)
    
    folium.LayerControl(position='topleft', collapsed=False).add_to(m)
    return guardar_mapa(m, guardar_como, 'mapa_kml')

def mostrar_menu_principal():
    print("\n" + "=" * 60)
    print("       SISTEMA DE MAPAS DE INTELIGENCIA")
    print("=" * 60)
    print("\n  1. Crear Mapa de Inteligencia")
    print("  2. Trabajar Mapa de Inteligencia")
    print("  0. Salir")
    print("\n" + "-" * 60)
    return input("Seleccione una opcion: ").strip()

def mostrar_menu_trabajar():
    print("\n" + "-" * 60)
    print("       TRABAJAR MAPA DE INTELIGENCIA")
    print("-" * 60)
    print("\n  A. Mapa Existente (cargar archivo HTML, KML/KMZ)")
    print("  B. Nuevo Mapa (crear desde Excel)")
    print("  0. Volver al menu principal")
    print("\n" + "-" * 60)
    return input("Seleccione una opcion: ").strip().upper()

def opcion_crear_mapa():
    print("\n--- CREAR MAPA DE INTELIGENCIA ---\n")
    archivo = input("Ruta del archivo Excel [torres.xlsx]: ").strip() or "torres.xlsx"
    radio = input("Radio en metros [500]: ").strip()
    if crear_mapa_de_torres(archivo, int(radio) if radio else 500):
        print("\nAbra el archivo en su navegador para ver las torres.")
    input("\nPresione Enter para continuar...")

def iniciar_servidor_editor(archivo_html):
    print(f"\nIniciando servidor de edicion para: {archivo_html}")
    print("El servidor se ejecutara en http://0.0.0.0:5000")
    print("Presione Ctrl+C para detener el servidor.\n")
    from app import app, set_mapa_archivo
    set_mapa_archivo(archivo_html)
    app.run(host='0.0.0.0', port=5000, debug=False)

def opcion_trabajar_mapa():
    opcion = mostrar_menu_trabajar()
    
    if opcion == 'A':
        archivo = input("\nRuta del archivo (HTML, KML o KMZ): ").strip()
        if not archivo or not os.path.exists(archivo):
            print("Error: Archivo no encontrado.")
            input("Presione Enter para continuar...")
            return
        
        ext = archivo.lower().split('.')[-1]
        if ext in ['kml', 'kmz']:
            resultado = importar_kml_kmz(archivo, guardar_como="mapa_kml_temp.html")
            if resultado:
                iniciar_servidor_editor("mapa_kml_temp.html")
            else:
                input("Presione Enter para continuar...")
        elif ext == 'html':
            iniciar_servidor_editor(archivo)
        else:
            print("Error: Extension no soportada. Use .html, .kml o .kmz")
            input("Presione Enter para continuar...")
            
    elif opcion == 'B':
        print("\n--- NUEVO MAPA PARA EDICION ---\n")
        archivo = input("Ruta del archivo Excel [torres.xlsx]: ").strip() or "torres.xlsx"
        radio = input("Radio en metros [500]: ").strip()
        resultado = crear_mapa_de_torres(archivo, int(radio) if radio else 500, guardar_como="mapa_trabajo_temp.html")
        if resultado:
            iniciar_servidor_editor("mapa_trabajo_temp.html")
        else:
            input("Presione Enter para continuar...")
    elif opcion != '0':
        print("Opcion no valida.")
        input("Presione Enter para continuar...")

def modo_interactivo():
    while True:
        opcion = mostrar_menu_principal()
        if opcion == '1': opcion_crear_mapa()
        elif opcion == '2': opcion_trabajar_mapa()
        elif opcion == '0': print("\nHasta luego!\n"); break
        else: print("Opcion no valida."); input("Presione Enter para continuar...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Sistema de Mapas de Inteligencia")
        parser.add_argument("archivo_excel", nargs='?', help="Ruta al archivo Excel")
        parser.add_argument("-r", "--radio", type=int, default=500, help="Radio en metros (default: 500)")
        parser.add_argument("--servidor", action="store_true", help="Modo servidor para edicion")
        parser.add_argument("--html", type=str, help="Archivo HTML para editar")
        args = parser.parse_args()
        
        if args.servidor:
            if args.html and os.path.exists(args.html):
                iniciar_servidor_editor(args.html)
            elif args.archivo_excel:
                resultado = crear_mapa_de_torres(args.archivo_excel, args.radio, guardar_como="mapa_trabajo_temp.html")
                if resultado: iniciar_servidor_editor("mapa_trabajo_temp.html")
            else:
                print("Error: Debe proporcionar --html o un archivo Excel para modo servidor.")
        elif args.archivo_excel:
            crear_mapa_de_torres(args.archivo_excel, args.radio)
        else:
            modo_interactivo()
    else:
        modo_interactivo()

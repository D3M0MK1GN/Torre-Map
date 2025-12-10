import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium.features import DivIcon, CustomIcon
from branca.element import Element
import argparse
import sys
import json
import os
from math import radians, cos, sin, atan2, degrees, asin

NOMBRE_HOJA = "FTD"

ICONO_TORRE_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="40" height="40">
  <rect x="28" y="10" width="8" height="50" fill="#8B0000"/>
  <polygon points="32,0 20,15 44,15" fill="#8B0000"/>
  <rect x="18" y="20" width="28" height="4" fill="#555"/>
  <rect x="22" y="30" width="20" height="3" fill="#555"/>
  <rect x="26" y="40" width="12" height="3" fill="#555"/>
  <circle cx="32" cy="6" r="4" fill="#FF4444"/>
</svg>
"""

def limpiar_coordenada(coord_str):
    if pd.isna(coord_str) or coord_str is None:
        return None
    s = str(coord_str).strip()
    if '.' not in s:
        return s
    negativo = '-' in s
    s = s.replace('-', '').replace(' ', '')
    partes = s.rsplit('.', 1)
    resultado = partes[0].replace('.', '') + '.' + partes[1] if len(partes) == 2 else s
    return f"-{resultado}" if negativo else resultado

def encontrar_columnas_coordenadas(df):
    col_map = {col.lower(): col for col in df.columns}
    lat_col = next((v for k, v in col_map.items() if 'latitud' in k), None)
    lon_col = next((v for k, v in col_map.items() if 'longitud' in k), None)
    return (lat_col, lon_col) if lat_col and lon_col else (None, None)

def crear_icono_torre():
    import base64
    svg_bytes = ICONO_TORRE_SVG.encode('utf-8')
    svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"

def crear_html_control_y_scripts(radio_inicial, torres_data):
    torres_json = json.dumps(torres_data)
    return f'''
<div id="control-radio" style="
    position: fixed;
    top: 10px;
    left: 50%;
    transform: translateX(-50%);
    z-index: 1000;
    background: #2c3e50;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    display: flex;
    align-items: center;
    gap: 15px;
    font-family: Arial, sans-serif;
">
    <h3 style="margin: 0; font-size: 1.1em;">Mapa de Torres Telefonicas</h3>
    <label style="font-size: 0.9em;">Radio (metros):</label>
    <input type="number" id="radio-input" value="{radio_inicial}" min="100" max="5000" style="
        padding: 5px 10px;
        border: none;
        border-radius: 4px;
        width: 80px;
    ">
    <button onclick="actualizarRadio()" style="
        background: #3498db;
        color: white;
        border: none;
        padding: 8px 15px;
        border-radius: 4px;
        cursor: pointer;
    ">Actualizar</button>
</div>

<script>
var torresData = {torres_json};
var sectoresLayer = null;
var mapInstance = null;

document.addEventListener('DOMContentLoaded', function() {{
    setTimeout(function() {{
        for (var key in window) {{
            if (window[key] instanceof L.Map) {{
                mapInstance = window[key];
                break;
            }}
        }}
        if (mapInstance) {{
            sectoresLayer = L.layerGroup().addTo(mapInstance);
            dibujarSectores({radio_inicial});
        }}
    }}, 500);
}});

function calcularPuntoFinal(lat, lon, distKm, angulo) {{
    var R = 6371;
    var distRad = distKm / R;
    var brngRad = angulo * Math.PI / 180;
    var lat1Rad = lat * Math.PI / 180;
    var lon1Rad = lon * Math.PI / 180;
    
    var lat2Rad = Math.asin(Math.sin(lat1Rad) * Math.cos(distRad) + 
                            Math.cos(lat1Rad) * Math.sin(distRad) * Math.cos(brngRad));
    var lon2Rad = lon1Rad + Math.atan2(Math.sin(brngRad) * Math.sin(distRad) * Math.cos(lat1Rad),
                                        Math.cos(distRad) - Math.sin(lat1Rad) * Math.sin(lat2Rad));
    
    return [lat2Rad * 180 / Math.PI, lon2Rad * 180 / Math.PI];
}}

function dibujarSectores(radioMetros) {{
    if (!sectoresLayer) return;
    sectoresLayer.clearLayers();
    
    var angulos = [180, 300, 60];
    var colores = ['blue', 'green', 'red'];
    var cardinales = {{'N': 0, 'E': 90, 'S': 180, 'O': 270}};
    
    torresData.forEach(function(torre) {{
        var lat = torre.lat;
        var lon = torre.lon;
        
        L.circle([lat, lon], {{
            radius: radioMetros,
            color: '#FFFF00',
            fill: true,
            fillOpacity: 0.15,
            weight: 1
        }}).addTo(sectoresLayer);
        
        angulos.forEach(function(angulo, i) {{
            var puntoFinal = calcularPuntoFinal(lat, lon, radioMetros / 1000, angulo);
            L.polyline([[lat, lon], puntoFinal], {{
                color: colores[i],
                weight: 2,
                opacity: 0.8,
                dashArray: '5, 5'
            }}).addTo(sectoresLayer);
        }});
        
        for (var punto in cardinales) {{
            var angulo = cardinales[punto];
            var puntoCardinal = calcularPuntoFinal(lat, lon, (radioMetros * 0.9) / 1000, angulo);
            L.marker(puntoCardinal, {{
                icon: L.divIcon({{
                    className: 'cardinal-label',
                    html: '<div style="font-size:10pt;font-weight:bold;color:black;background:white;padding:2px;border-radius:3px;">' + punto + '</div>',
                    iconSize: [20, 20],
                    iconAnchor: [0, 0]
                }})
            }}).addTo(sectoresLayer);
        }}
    }});
}}

function actualizarRadio() {{
    var nuevoRadio = parseInt(document.getElementById('radio-input').value);
    if (nuevoRadio >= 100 && nuevoRadio <= 5000) {{
        dibujarSectores(nuevoRadio);
    }} else {{
        alert('El radio debe estar entre 100 y 5000 metros');
    }}
}}
</script>
'''

def crear_mapa_de_torres(archivo_excel, radio_metros, guardar_como=None):
    """Crea un mapa de torres desde un archivo Excel."""
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
    print("Limpiando formato de coordenadas...")
    
    df['Lat_F'] = pd.to_numeric(df[lat_col].apply(limpiar_coordenada), errors='coerce')
    df['Lon_F'] = pd.to_numeric(df[lon_col].apply(limpiar_coordenada), errors='coerce')
    df_valido = df.dropna(subset=['Lat_F', 'Lon_F'])
    
    if df_valido.empty:
        print("Error: No se encontraron coordenadas validas.")
        return None
    
    print(f"{len(df_valido)} coordenadas validas procesadas.")
    
    torres_data = [{'lat': row['Lat_F'], 'lon': row['Lon_F']} for _, row in df_valido.iterrows()]
    
    m = folium.Map(location=[df_valido['Lat_F'].mean(), df_valido['Lon_F'].mean()], zoom_start=14, max_zoom=22, tiles=None)
    
    folium.TileLayer('OpenStreetMap', name='Mapa Estandar', max_zoom=19).add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri', name='Satelital', overlay=False, max_zoom=22
    ).add_to(m)
    
    cluster = MarkerCluster(name='Torres Telefonicas').add_to(m)
    icono_url = crear_icono_torre()
    
    for _, row in df_valido.iterrows():
        lat, lon = row['Lat_F'], row['Lon_F']
        icono_torre = CustomIcon(icono_url, icon_size=(40, 40), icon_anchor=(20, 40))
        folium.Marker(location=[lat, lon], icon=icono_torre,
            tooltip=f"Lat: {lat:.4f}, Lon: {lon:.4f}").add_to(cluster)
    
    folium.LayerControl(position='topleft', collapsed=False).add_to(m)
    
    html_extra = crear_html_control_y_scripts(radio_metros, torres_data)
    m.get_root().html.add_child(Element(html_extra))
    
    if guardar_como:
        archivo_salida = guardar_como
    else:
        archivo_salida = f"mapa_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    m.save(archivo_salida)
    print("-" * 50)
    print(f"Mapa generado: {archivo_salida}")
    print("-" * 50)
    return archivo_salida

def mostrar_menu_principal():
    """Muestra el menú principal."""
    print("\n" + "=" * 60)
    print("       SISTEMA DE MAPAS DE INTELIGENCIA")
    print("=" * 60)
    print("\n  1. Crear Mapa de Inteligencia")
    print("  2. Trabajar Mapa de Inteligencia")
    print("  0. Salir")
    print("\n" + "-" * 60)
    return input("Seleccione una opcion: ").strip()

def mostrar_menu_trabajar():
    """Muestra el submenú de trabajar mapa."""
    print("\n" + "-" * 60)
    print("       TRABAJAR MAPA DE INTELIGENCIA")
    print("-" * 60)
    print("\n  A. Mapa Existente (cargar archivo HTML)")
    print("  B. Nuevo Mapa (crear desde Excel)")
    print("  0. Volver al menu principal")
    print("\n" + "-" * 60)
    return input("Seleccione una opcion: ").strip().upper()

def opcion_crear_mapa():
    """Opción 1: Crear mapa estático."""
    print("\n--- CREAR MAPA DE INTELIGENCIA ---\n")
    archivo = input("Ruta del archivo Excel [torres.xlsx]: ").strip() or "torres.xlsx"
    radio = input("Radio en metros [500]: ").strip()
    radio = int(radio) if radio else 500
    
    resultado = crear_mapa_de_torres(archivo, radio)
    if resultado:
        print("\nAbra el archivo en su navegador para ver las torres.")
    input("\nPresione Enter para continuar...")

def opcion_trabajar_mapa():
    """Opción 2: Trabajar mapa con servidor interactivo."""
    opcion = mostrar_menu_trabajar()
    
    if opcion == 'A':
        archivo_html = input("\nRuta del archivo HTML existente: ").strip()
        if not archivo_html or not os.path.exists(archivo_html):
            print("Error: Archivo no encontrado.")
            input("Presione Enter para continuar...")
            return
        iniciar_servidor_editor(archivo_html)
        
    elif opcion == 'B':
        print("\n--- NUEVO MAPA PARA EDICION ---\n")
        archivo = input("Ruta del archivo Excel [torres.xlsx]: ").strip() or "torres.xlsx"
        radio = input("Radio en metros [500]: ").strip()
        radio = int(radio) if radio else 500
        
        archivo_temp = "mapa_trabajo_temp.html"
        resultado = crear_mapa_de_torres(archivo, radio, guardar_como=archivo_temp)
        if resultado:
            iniciar_servidor_editor(archivo_temp)
        else:
            input("Presione Enter para continuar...")
    
    elif opcion == '0':
        return
    else:
        print("Opcion no valida.")
        input("Presione Enter para continuar...")

def iniciar_servidor_editor(archivo_html):
    """Inicia el servidor Flask para edición interactiva."""
    print(f"\nIniciando servidor de edicion para: {archivo_html}")
    print("El servidor se ejecutara en http://0.0.0.0:5000")
    print("Presione Ctrl+C para detener el servidor.\n")
    
    from app import app, set_mapa_archivo
    set_mapa_archivo(archivo_html)
    app.run(host='0.0.0.0', port=5000, debug=False)

def modo_interactivo():
    """Ejecuta el menú interactivo."""
    while True:
        opcion = mostrar_menu_principal()
        
        if opcion == '1':
            opcion_crear_mapa()
        elif opcion == '2':
            opcion_trabajar_mapa()
        elif opcion == '0':
            print("\nHasta luego!\n")
            break
        else:
            print("Opcion no valida.")
            input("Presione Enter para continuar...")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser(description="Sistema de Mapas de Inteligencia")
        parser.add_argument("archivo_excel", nargs='?', help="Ruta al archivo Excel")
        parser.add_argument("-r", "--radio", type=int, default=500, help="Radio del circulo en metros (default: 500)")
        parser.add_argument("--servidor", action="store_true", help="Iniciar en modo servidor para edicion")
        parser.add_argument("--html", type=str, help="Archivo HTML para editar en modo servidor")
        args = parser.parse_args()
        
        if args.servidor:
            if args.html and os.path.exists(args.html):
                iniciar_servidor_editor(args.html)
            elif args.archivo_excel:
                archivo_temp = "mapa_trabajo_temp.html"
                resultado = crear_mapa_de_torres(args.archivo_excel, args.radio, guardar_como=archivo_temp)
                if resultado:
                    iniciar_servidor_editor(archivo_temp)
            else:
                print("Error: Debe proporcionar --html o un archivo Excel para modo servidor.")
        elif args.archivo_excel:
            crear_mapa_de_torres(args.archivo_excel, args.radio)
        else:
            modo_interactivo()
    else:
        modo_interactivo()

import pandas as pd
import folium
from folium.plugins import MarkerCluster
from folium.features import DivIcon, CustomIcon
from branca.element import Template, MacroElement
import argparse
import sys
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

BRUJULA_HTML = """
{% macro html(this, kwargs) %}
<div id="brujula" style="
    position: fixed;
    top: 10px;
    right: 10px;
    z-index: 1000;
    background: rgba(255,255,255,0.95);
    border-radius: 50%;
    width: 80px;
    height: 80px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #333;
">
    <div style="position: relative; width: 70px; height: 70px;">
        <div style="position: absolute; top: 2px; left: 50%; transform: translateX(-50%); font-weight: bold; color: #c00; font-size: 14px;">N</div>
        <div style="position: absolute; bottom: 2px; left: 50%; transform: translateX(-50%); font-weight: bold; color: #333; font-size: 12px;">S</div>
        <div style="position: absolute; left: 2px; top: 50%; transform: translateY(-50%); font-weight: bold; color: #333; font-size: 12px;">O</div>
        <div style="position: absolute; right: 2px; top: 50%; transform: translateY(-50%); font-weight: bold; color: #333; font-size: 12px;">E</div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">
            <svg width="30" height="30" viewBox="0 0 30 30">
                <polygon points="15,2 12,15 15,12 18,15" fill="#c00"/>
                <polygon points="15,28 12,15 15,18 18,15" fill="#333"/>
            </svg>
        </div>
        <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 6px; height: 6px; background: #333; border-radius: 50%;"></div>
    </div>
</div>
{% endmacro %}
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

def calcular_punto_final(lat, lon, dist_km, angulo):
    R = 6371
    dist_rad, brng_rad = dist_km / R, radians(angulo)
    lat1_rad, lon1_rad = radians(lat), radians(lon)
    lat2_rad = asin(sin(lat1_rad) * cos(dist_rad) + cos(lat1_rad) * sin(dist_rad) * cos(brng_rad))
    lon2_rad = lon1_rad + atan2(sin(brng_rad) * sin(dist_rad) * cos(lat1_rad), cos(dist_rad) - sin(lat1_rad) * sin(lat2_rad))
    return degrees(lat2_rad), degrees(lon2_rad)

def dibujar_sectores_y_cardinales(m, lat, lon, radio_metros):
    folium.Circle(location=[lat, lon], radius=radio_metros, color='#FFFF00', fill=True, fill_opacity=0.15, weight=1).add_to(m)
    
    for angulo, color in zip([180, 300, 60], ['blue', 'green', 'red']):
        lat_f, lon_f = calcular_punto_final(lat, lon, radio_metros / 1000, angulo)
        folium.PolyLine([[lat, lon], [lat_f, lon_f]], color=color, weight=2, opacity=0.8, dash_array='5, 5').add_to(m)
    
    for punto, angulo in {'N': 0, 'E': 90, 'S': 180, 'O': 270}.items():
        lat_e, lon_e = calcular_punto_final(lat, lon, (radio_metros * 0.9) / 1000, angulo)
        folium.Marker(location=[lat_e, lon_e], icon=DivIcon(icon_size=(20, 20), icon_anchor=(0, 0),
            html=f'<div style="font-size:10pt;font-weight:bold;color:black;background:white;padding:2px;border-radius:3px;">{punto}</div>')).add_to(m)

def crear_icono_torre():
    import base64
    svg_bytes = ICONO_TORRE_SVG.encode('utf-8')
    svg_base64 = base64.b64encode(svg_bytes).decode('utf-8')
    return f"data:image/svg+xml;base64,{svg_base64}"

def agregar_brujula(m):
    brujula = MacroElement()
    brujula._template = Template(BRUJULA_HTML)
    m.get_root().html.add_child(brujula)

def crear_mapa_de_torres(archivo_excel, radio_metros):
    print(f"Buscando hoja '{NOMBRE_HOJA}' en '{archivo_excel}'...")
    print(f"Radio configurado: {radio_metros} metros")
    try:
        df = pd.read_excel(archivo_excel, sheet_name=NOMBRE_HOJA)
    except FileNotFoundError:
        sys.exit(f"Error: Archivo '{archivo_excel}' no encontrado.")
    except ValueError:
        sys.exit(f"Error: Hoja '{NOMBRE_HOJA}' no encontrada en el archivo.")
    except Exception as e:
        sys.exit(f"Error al leer Excel: {e}")
    
    lat_col, lon_col = encontrar_columnas_coordenadas(df)
    if not lat_col or not lon_col:
        sys.exit("Error: No se encontraron columnas 'Latitud' y 'Longitud'.")
    
    print(f"Columnas encontradas: Latitud ('{lat_col}'), Longitud ('{lon_col}')")
    print("Limpiando formato de coordenadas...")
    
    df['Lat_F'] = pd.to_numeric(df[lat_col].apply(limpiar_coordenada), errors='coerce')
    df['Lon_F'] = pd.to_numeric(df[lon_col].apply(limpiar_coordenada), errors='coerce')
    df_valido = df.dropna(subset=['Lat_F', 'Lon_F'])
    
    if df_valido.empty:
        sys.exit("Error: No se encontraron coordenadas validas.")
    
    print(f"{len(df_valido)} coordenadas validas procesadas.")
    
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
        dibujar_sectores_y_cardinales(m, lat, lon, radio_metros)
    
    folium.LayerControl(position='topleft', collapsed=False).add_to(m)
    agregar_brujula(m)
    
    archivo_salida = f"mapa_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.html"
    m.save(archivo_salida)
    print("-" * 50)
    print(f"Mapa generado: {archivo_salida}")
    print("Abra el archivo en su navegador para ver las torres.")
    print("-" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grafica torres telefonicas desde Excel con sectores de 120 grados.")
    parser.add_argument("archivo_excel", help="Ruta al archivo Excel")
    parser.add_argument("-r", "--radio", type=int, default=500, help="Radio del circulo en metros (default: 500)")
    args = parser.parse_args()
    crear_mapa_de_torres(args.archivo_excel, args.radio)

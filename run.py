from mapa_torres import importar_kml_kmz, iniciar_servidor_editor

resultado = importar_kml_kmz("ROBO-SANARE.kmz", guardar_como="mapa_kml_temp.html")
if resultado:
    iniciar_servidor_editor("mapa_kml_temp.html")

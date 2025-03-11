import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

# Ruta del archivo .shp en la carpeta Maps
shapefile_path = "D:/Desktop/TZIKIN-WINDOWS/Maps/ne_110m_admin_0_countries.shp"

# Cargar el mapa mundial
world = gpd.read_file(shapefile_path)

# Coordenadas proporcionadas
coordinates = [
    (14.638694833333334, -90.57108516666666)
]

# Crear un GeoDataFrame para los puntos
gdf_points = gpd.GeoDataFrame(geometry=[Point(lon, lat) for lat, lon in coordinates])

# Aplicar colores personalizados
background_color = "#1a2631"  # Fondo oscuro
land_color = "#cce6c6"        # Color de los continentes
border_color_default = "#cce6c6"  # Color de los bordes de los continentes (por defecto)
border_color_zoom = "#e4ffde"     # Color de los bordes para los zooms

# Función para generar el mapa con diferentes niveles de zoom manteniendo la proporción
def generate_map(fig, ax, zoom_level=0, border_color=border_color_default):
    fig.patch.set_facecolor(background_color)  # Fondo de la figura
    ax.set_facecolor(background_color)         # Fondo del eje

    # Dibujar el mapa mundial con los colores personalizados
    world.plot(ax=ax, color=land_color, edgecolor=border_color)

    # Agregar los puntos al mapa con triángulos sin relleno y borde rojo
    for lat, lon in coordinates:
        ax.scatter(lon, lat, color='none', edgecolor='red', marker='^', s=100, linewidth=2)  # Triángulo sin relleno

    # Ajustar los límites del mapa si se requiere zoom, manteniendo la proporción original
    if zoom_level > 0:
        center_lat = sum(lat for lat, lon in coordinates) / len(coordinates)
        center_lon = sum(lon for lat, lon in coordinates) / len(coordinates)
        
        zoom_factor = 30 / zoom_level  # Ajustar el factor de zoom dinámicamente

        # Mantener la relación de aspecto del mapa original (mismo ancho y alto proporcional)
        lat_range = zoom_factor
        lon_range = lat_range * 2  # Ajuste de la proporción de aspecto

        ax.set_xlim(center_lon - lon_range, center_lon + lon_range)
        ax.set_ylim(center_lat - lat_range, center_lat + lat_range)

    # Eliminar los ejes, etiquetas y marcos
    ax.set_xticks([])
    ax.set_yticks([])
    ax.axis("off")  # Elimina completamente los ejes y el borde

# Crear y guardar la imagen del mapa mundial completo
fig1, ax1 = plt.subplots(figsize=(10, 5))  # Mantener la proporción rectangular
generate_map(fig1, ax1, zoom_level=0)
plt.savefig("mapa_mundial.png", bbox_inches="tight", pad_inches=0, dpi=300, facecolor=background_color)

# Crear y guardar la imagen con zoom moderado (menos zoom que antes)
fig2, ax2 = plt.subplots(figsize=(10, 5))  # Mantener la misma proporción que el primer mapa
generate_map(fig2, ax2, zoom_level=1.5, border_color=border_color_zoom)  # Reducido el zoom
plt.savefig("mapa_zoom.png", bbox_inches="tight", pad_inches=0, dpi=300, facecolor=background_color)

# Crear y guardar la imagen con un zoom más cercano
fig3, ax3 = plt.subplots(figsize=(10, 5))  # Mantener la misma proporción que las otras imágenes
generate_map(fig3, ax3, zoom_level=4, border_color=border_color_zoom)  # Mayor nivel de zoom
plt.savefig("mapa_zoom_cercano.png", bbox_inches="tight", pad_inches=0, dpi=300, facecolor=background_color)

plt.close(fig1)
plt.close(fig2)
plt.close(fig3)

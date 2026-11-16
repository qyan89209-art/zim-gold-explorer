import streamlit as st
import folium
from streamlit_folium import st_folium
import simplekml
import math

st.set_page_config(page_title="DigHere 穆塔雷沙金勘探", layout="centered")
st.title("⛏️ DigHere 沙金勘探系统")

col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("纬度 (Latitude)", value=-18.8850, format="%.5f", step=0.001)
with col2:
    lon = st.number_input("经度 (Longitude)", value=32.6650, format="%.5f", step=0.001)

radius_m = st.slider("勘探网格半径 (米)", 100, 1000, 300, 50)

m = folium.Map(location=[lat, lon], zoom_start=15, tiles=None)
folium.TileLayer(
    tiles="https://arcgisonline.com{z}/{y}/{x}",
    attr="Esri", name="高清卫星影像", overlay=False, control=True
).add_to(m)
folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr="OpenTopoMap", name="等高线微地形", overlay=False, control=True
).add_to(m)

folium.Circle([lat, lon], radius=radius_m, color="#FFD700", fill=True, fill_opacity=0.15).add_to(m)
folium.Marker([lat, lon], popup="中心点", icon=folium.Icon(color="red")).add_to(m)

line_spacing = st.number_input("勘探线距 (米)", min_value=10, max_value=200, value=50, step=10)
point_spacing = st.number_input("探井点距 (米)", min_value=10, max_value=200, value=25, step=5)

deg_lat = 1 / 111320.0
deg_lon = 1 / (111320.0 * math.cos(math.radians(lat)))
kml = simplekml.Kml()
pit_count = 0

for i in range(-int(radius_m / line_spacing), int(radius_m / line_spacing) + 1):
    for j in range(-int(radius_m / point_spacing), int(radius_m / point_spacing) + 1):
        dx, dy = i * line_spacing, j * point_spacing
        if math.sqrt(dx**2 + dy**2) <= radius_m:
            p_lat, p_lon = lat + (dy * deg_lat), lon + (dx * deg_lon)
            pit_count += 1
            folium.CircleMarker([p_lat, p_lon], radius=3, color="#00FF00", fill=True, popup=f"PIT-{pit_count:03d}").add_to(m)
            kml.newpoint(name=f"PIT-{pit_count:03d}", coords=[(p_lon, p_lat)])

folium.LayerControl().add_to(m)
st_folium(m, width=360, height=400)
st.info(f"已生成 **{pit_count}** 个探井点位（绿点）。")

st.download_button(
    label="📥 导出 KML 导航文件 (直接用 Gaia GPS 打开)",
    data=kml.kml().encode("utf-8"),
    file_name=f"Mutare_Gold_Pits_{lat:.4f}_{lon:.4f}.kml",
    mime="application/vnd.google-earth.kml+xml",
    use_container_width=True
)

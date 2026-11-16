import streamlit as st
import folium
from streamlit_folium import st_folium
import simplekml
import math
import requests

st.set_page_config(page_title="DigHere 沙金智能靶区系统", layout="centered")
st.title("⛏️ DigHere 沙金智能靶区系统")
st.caption("自动剔除高处山坡废点 · 精准锁定低洼河谷与古河道阶地")

col1, col2 = st.columns(2)
with col1:
    lat = st.number_input("纬度 (Latitude)", value=-18.8850, format="%.5f", step=0.001)
with col2:
    lon = st.number_input("经度 (Longitude)", value=32.6650, format="%.5f", step=0.001)

radius_m = st.slider("勘探网格半径 (米)", 100, 800, 300, 50)

c1, c2 = st.columns(2)
with c1:
    line_spacing = st.number_input("勘探线距 (米)", 20, 200, 50, 10)
with c2:
    point_spacing = st.number_input("探井点距 (米)", 10, 100, 25, 5)

max_elev_diff = st.slider("高程过滤阈值：仅保留高出最低河谷 (米) 以内的区域", 2, 30, 10, 1)

deg_lat = 1 / 111320.0
deg_lon = 1 / (111320.0 * math.cos(math.radians(lat)))
candidates = []

for i in range(-int(radius_m / line_spacing), int(radius_m / line_spacing) + 1):
    for j in range(-int(radius_m / point_spacing), int(radius_m / point_spacing) + 1):
        dx, dy = i * line_spacing, j * point_spacing
        if math.sqrt(dx**2 + dy**2) <= radius_m:
            candidates.append((lat + dy * deg_lat, lon + dx * deg_lon))

valid_pits = []
filtered_out = 0
min_elev = None

if candidates:
    try:
        elevations = []
        for idx in range(0, len(candidates), 100):
            batch = candidates[idx:idx+100]
            loc_str = "|".join([f"{pt[0]:.5f},{pt[1]:.5f}" for pt in batch])
            resp = requests.get(f"https://opentopodata.org{loc_str}", timeout=8).json()
            elevations.extend([r["elevation"] for r in resp["results"]])
        
        min_elev = min([e for e in elevations if e is not None])
        for (p_lat, p_lon), elev in zip(candidates, elevations):
            if elev is not None and (elev - min_elev) <= max_elev_diff:
                valid_pits.append((p_lat, p_lon, elev))
            else:
                filtered_out += 1
    except Exception:
        valid_pits = [(pt[0], pt[1], 0) for pt in candidates]

m = folium.Map(location=[lat, lon], zoom_start=15, tiles=None)
folium.TileLayer(
    tiles="https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png",
    attr="OpenTopoMap", name="等高线微地形", overlay=False, control=True
).add_to(m)
folium.TileLayer(
    tiles="https://arcgisonline.com{z}/{y}/{x}",
    attr="Esri", name="高清卫星影像", overlay=False, control=True
).add_to(m)

folium.Circle([lat, lon], radius=radius_m, color="#FFD700", fill=False, weight=2).add_to(m)

kml = simplekml.Kml()
for idx, (p_lat, p_lon, elev) in enumerate(valid_pits, 1):
    pit_name = f"GOLD-PIT-{idx:03d}"
    diff = (elev - min_elev) if min_elev else 0
    pin_color = "#FF2B2B" if diff <= 3 else "#FFA500"
    folium.CircleMarker(
        [p_lat, p_lon], radius=4, color=pin_color, fill=True, fill_opacity=0.9,
        popup=f"{pit_name} | 海拔:{elev:.1f}m (高出河床+{diff:.1f}m)"
    ).add_to(m)
    kml.newpoint(name=pit_name, description=f"海拔:{elev:.1f}m", coords=[(p_lon, p_lat)])

folium.LayerControl().add_to(m)
st_folium(m, width=360, height=400)

if min_elev:
    st.success(f"🎯 智能过滤完成：已自动剔除 **{filtered_out}** 个高处山坡废点！保留 **{len(valid_pits)}** 个低洼河谷/阶地高潜力探井（🔴红点=主河床及河弯内侧；🟠橙点=高出河床3-{max_elev_diff}米的古河道阶地）。")

st.download_button(
    label="📥 导出精选高潜力探井 KML (导入 Gaia GPS)",
    data=kml.kml().encode("utf-8"),
    file_name=f"Smart_Gold_Targets_{lat:.4f}_{lon:.4f}.kml",
    mime="application/vnd.google-earth.kml+xml",
    use_container_width=True
)

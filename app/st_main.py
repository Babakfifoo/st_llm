# %%
import folium
import streamlit as st
import geopandas as gpd
from streamlit_folium import st_folium
from folium.plugins import Draw
import math
import duckdb
from shapely import wkt
from llm.prompt_generator import generate_answer
import json
# %%


def get_bbox(st_data):
    bbox = [
        st_data["bounds"]["_southWest"]["lng"],
        st_data["bounds"]["_southWest"]["lat"],
        st_data["bounds"]["_northEast"]["lng"],
        st_data["bounds"]["_northEast"]["lat"],
    ]
    return bbox


@st.cache_data
def get_buildings(bbox):
    con = duckdb.connect()
    con.sql("""
    INSTALL spatial;
    LOAD spatial;        
    """)
    url = "./data/HMA_buildings_prepared.parquet"
    query = """
        SELECT 
            CAST(num_floors AS INTEGER) AS num_floors, AREA AS Footprint, 
            subtype_clean, floor_area, est_num_floors, residential, commercial, 
            ST_AsText(geometry::GEOMETRY) AS geometry
        FROM read_parquet('{url}')
        WHERE 
            CAST(bbox.xmin AS FLOAT) > {xmin} AND
            CAST(bbox.xmax AS FLOAT) < {xmax} AND
            CAST(bbox.ymin AS FLOAT) > {ymin} AND
            CAST(bbox.ymax AS FLOAT) < {ymax}
    """
    proper_query = query.format(
        xmin=bbox[0], ymin=bbox[1], xmax=bbox[2], ymax=bbox[3], url=url
    )
    result = con.sql(proper_query).df()
    result = gpd.GeoDataFrame(
        result, geometry=result["geometry"].apply(wkt.loads), crs=4326
    )
    return result


def get_bbox_circle(lon, lat, radius=500):
    
    radius_in_degrees = (radius / 1000) / 6371.0  # earth radius
    min_lat = lat - math.degrees(radius_in_degrees)
    max_lat = lat + math.degrees(radius_in_degrees)
    min_lng = lon - math.degrees(radius_in_degrees / math.cos(math.radians(lat)))
    max_lng = lon + math.degrees(radius_in_degrees / math.cos(math.radians(lat)))

    bbox = [min_lng, min_lat, max_lng, max_lat]
    return bbox


# %%
st.set_page_config(page_title="Floor Area Agent", layout='wide', initial_sidebar_state="expanded")
col1, col2 = st.columns(spec=[0.3,0.7])


m = folium.Map(location=[60.164097, 24.941238], zoom_start=14)
m.add_child(child=folium.LayerControl())

draw = Draw(
    draw_options={
        "polyline": False,
        "rectangle": False,
        "polygon": False,
        "circle": False,
        "marker": True,
        "circlemarker": False,
    },
    edit_options={"edit": False},
)
m.add_child(draw)
fg = folium.FeatureGroup(name="Buildings")


def style_func(feature):
    default = {
        "fillColor": "grey",
        "color": "black",
        "weight": 1,
        }
    if feature["properties"]["residential"] == 1:
        default["fillColor"] = "yellow"
        
    if feature["properties"]["commercial"] == 1:
        default["fillColor"] = "red"
        
    return default

if "Buildings" in st.session_state.keys():
    fg.add_child(
        child=folium.GeoJson(
            data=st.session_state["Buildings"],
            tooltip=folium.GeoJsonTooltip(
                fields=["subtype_clean", "floor_area", "num_floors", "Footprint"],
                aliases=["Usage", "Floor area (m2):", "Floor count:", "Area (m2):"],
                labels=True,
            ),
        style_function=style_func
        )
    )

if "last_clicked" in st.session_state.keys():
    fg.add_child(child=st.session_state["last_clicked"]["marker"])

with col2:
    values = st.slider(label="Select the radius (m)", min_value=100, max_value=1000, value=500, step=50)
    st.write("Radius (m)", values)
    st_data = st_folium(fig=m, width=1200, height=800, feature_group_to_add=fg)
    if "Buildings" not in st.session_state:
        if st_data["last_clicked"]:
            lat = st_data["last_clicked"]["lat"]
            lon = st_data["last_clicked"]["lng"]
            st.session_state["last_clicked"] = {
                "lat": lat,
                "lon": lon,
                "marker": folium.Marker(location=[lat, lon]),
            }


    if "Buildings" in st.session_state.keys():
        if st.button(label="Clear Map"):
            st.session_state.pop("Buildings")
            
    if st.button(label="Get the data"):
        if 'last_clicked' in st.session_state:
            bbox = get_bbox_circle(
                lon=st.session_state["last_clicked"]["lon"],
                lat=st.session_state["last_clicked"]["lat"],
                radius=values
            )
            st.write(f"getting:{bbox}")
            buildings = get_buildings(bbox=bbox).assign(floor_area = lambda x: x["floor_area"].round())
            st.session_state["prompt_stats"] = {
                "Mean building Footprint area (m2)" : buildings["Footprint"].mean(),
                "Mean floor count" :  buildings["num_floors"].mean(), 
                "Mean Floor area (m2)" :  buildings["floor_area"].mean(),
                "share of residential building (%)" : buildings.query("subtype_clean == 'residential'").shape[0] * 100 / buildings.shape[0]
            }

            st.session_state["Buildings"] = buildings

            st.session_state["ongoing_prompt"] = 1
            st.success("Buildings acquired")
        else:
            st.warning("Please click on the location of interest")


with col1:
    st.title("Your AI Assistant:")
    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": " Hi! I am your assistant. What would you like to know?"}]
    for message in st.session_state["messages"]:
        if message["content"][:4] == "skip":
            continue
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if prompt := st.chat_input("Enter prompt here.."):
        # add latest message to history in format {role, content}
        st.session_state["messages"].append({"role": "user", "content": prompt})

        with st.chat_message(name="user"):
            st.markdown(body=prompt)

        with st.chat_message(name="assistant"):
            message = st.write_stream(stream=generate_answer(
                messages=st.session_state["messages"],
                user_question=prompt,
                information=json.dumps(
                    obj=st.session_state.get("prompt_stats", default=""), 
                    indent=4)
                ))
            st.session_state["messages"].append({"role": "assistant", "content": message})
import streamlit as st

from api_analyse.analysis.heatmap_road_works import generate_heatmap_road_work
from api_analyse.utils.config import config
from streamlit_folium import st_folium


@st.cache_data(ttl=3600)
def get_map():
    return generate_heatmap_road_work()

def show_graphics():
    st.set_page_config(layout="wide")
    st.title("Switzerland Traffic Analysis")

    col1, col2 = st.columns(2)

    graphics_path = config.paths.data_processed

    with col1:
        st.subheader("Interactive Heatmap")
        st_folium(get_map())

    with col2:
        st.subheader("Static Overview Chart")
        st.image(
            str(graphics_path / "switzerland_road_works_chart.webp"),
            width="stretch"
        )

if __name__ == "__main__":
    show_graphics()
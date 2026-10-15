from api_analyse import streamlit as st

from api_analyse.analysis.chart_road_works import generate_chart_road_work
from api_analyse.analysis.heatmap_road_works import generate_heatmap_road_work
from api_analyse.utils.config import config
from streamlit_folium import st_folium


@st.cache_resource(ttl=3600)
def get_map():
    return generate_heatmap_road_work()


def show_graphics():
    st.set_page_config(layout="wide")
    st.title("Switzerland Traffic Analysis")

    col1, col2 = st.columns(2)

    graphics_path = config.paths.data_processed
    chart_path = graphics_path / "switzerland_road_works_chart.webp"

    with col1:
        st.subheader("Interactive Heatmap")
        st_folium(get_map(), use_container_width=True, height=600, returned_objects=[])

    with col2:
        st.subheader("Static Overview Chart")
        if not chart_path.is_file():
            generate_chart_road_work(chart_path)
        if chart_path.is_file():
            st.image(str(chart_path), width="stretch")
        else:
            st.warning("Chart image was not generated.")


if __name__ == "__main__":
    show_graphics()

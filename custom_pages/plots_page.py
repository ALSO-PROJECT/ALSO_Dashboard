import streamlit as st
from utils.plots_utils import PlotsLayout

def app(dataframe_dict):
    st.subheader("Plots and Metrics Page")
    PlotsLayout(dataframe_dict=dataframe_dict)
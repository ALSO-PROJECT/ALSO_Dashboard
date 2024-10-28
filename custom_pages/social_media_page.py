import streamlit as st
import os 

# Custom modules
from utils.layout import SocialMediaLayout

def app(dataframe_dict):
    st.subheader("Social Media Analysis")

    SocialMediaLayout(dataframe_dict=dataframe_dict)
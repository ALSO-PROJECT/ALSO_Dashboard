import streamlit as st

def app():
    st.subheader('Overview')

    with open('README.md', 'r', encoding='utf-8') as file:
        readme_content = file.read()

    st.markdown(readme_content)
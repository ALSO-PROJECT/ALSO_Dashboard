import streamlit as st
from streamlit_option_menu import option_menu

import os 

# custom modules
from custom_pages import overview_page,social_media_page,plots_page,keyword_in_context_page,topic_modelling_page

st.set_page_config(layout="wide",page_title="ALSO DASHBOARD")
st.title("__ALSO PROJECT DASHBOARD__")

class ALSO_DASHBOARD:

    def __init__(self):
        self.apps = []
    
    def add_app(self,title,function):
        self.apps.append({"title":title,
                          "function":function
                          })
        
    def run():
        ############### KORPUS DATABASE ##################
        DATABASE_DIR = 'database'

        korpus_dict= {'Altersarmut_korpus':DATABASE_DIR+'/Altersarmut_korpus.csv',
                    'Altersvorsorge_korpus':DATABASE_DIR+'/Altersvorsorge_korpus.csv',
                    'Rentensystem_korpus':DATABASE_DIR+'/Rentensystem_korpus.csv',

                    'Betriebliche_Altersvorsoge_korpus':DATABASE_DIR+'/Betriebliche_Altersvorsoge_korpus.csv',
                    'öR-Pflichtsysteme_korpus':DATABASE_DIR+'/öR_Pflichtsysteme_korpus.csv',
                    'Private_Vorsorge_korpus':DATABASE_DIR+'/Private_Vorsorge_korpus.csv',
                    'Säulenübergreifend_korpus':DATABASE_DIR+'/Säulenübergreifend_korpus.csv',
                    
                    'influencer_korpus':DATABASE_DIR+'/influencer_korpus.csv',

                    'Top_50_Posts_Report':DATABASE_DIR+'/Top_50_Posts_Report.csv'
                    }

        with st.sidebar:
            app = option_menu(
                menu_title = "Features",
                options = ["Overview", "Social Media", "Plots&Metrics","Keyword in Context","Topic Modelling"],
                icons = ['house-fill','person-circle','trophy-fill','chat-text-fill','chat-fill'],
                default_index = 0,  
            )        

        if app == 'Overview':
            overview_page.app()
        elif app == 'Social Media':
            social_media_page.app(dataframe_dict=korpus_dict)
        elif app == 'Plots&Metrics':
            plots_page.app(dataframe_dict=korpus_dict)
        elif app == 'Keyword in Context':
            keyword_in_context_page.app()
        elif     app == 'Topic Modelling':
            topic_modelling_page.app()
            
    run()

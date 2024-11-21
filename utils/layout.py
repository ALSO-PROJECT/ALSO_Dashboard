# import modules
import time
import datetime
from millify import millify
import pandas as pd
import numpy as np
import json

from sklearn.feature_extraction.text import CountVectorizer
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from io import BytesIO

import plotly.express as px
import plotly.graph_objects as go

import streamlit as st
import ast

import locale

# Custom imports
from utils.social_media_utils import SocialMedia

class SocialMediaLayout():
    
    def __init__(self,dataframe_dict) -> None:
        
        self.filters = {
            'corpus_select': None,
            'hashtags_select': [],
            'channels_select': [],
            'start_date': None,
            'end_date': None,
            'platform': [],
            'shorts_filter': False,
            'videos_filter': False,
            'posts_filter': False,
            'reels_filter': False,
            'carousel_filter': False,
            'keywords': [],
            'caption_filter': False,
            'title_filter': False,
            'transcripts_filter': False,
            'views_slider': (0, 0),
            'subscribers_slider': (0, 0),
            'likes_slider': (0, 0),
            'comments_slider': (0, 0),
            'positive_filter': False,
            'neutral_filter': False,
            'negative_filter': False,
            'video_id_input': ''
        }
        

        self.dataframe_dict = dataframe_dict
        
        filtered_df,corpus_select = self.create_filters()

        # st.markdown(
        #             """
        #             <style>
        #             .layout-page-container {
        #                 height: 600px;
        #             }
        #             </style>
        #             """,
        #             unsafe_allow_html=True
        #         )
        # Hide this until you get the data.   
        with st.container(height=600):
            # st.markdown('<div class="layout-page-container">', unsafe_allow_html=True)
            cl_1,cl_2,cl_3 = st.columns(3)
            cl_1.success('Displaying data for the selected filters')
            cl_3.download_button(
                    label="Download as csv",
                    data=filtered_df.to_csv(),
                    file_name=f"Social_media_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="csv",
                )
            display_dataframe = self.display_dataframe(filtered_df)
            display_dataframe.reset_index(drop=True, inplace=True)
            received_data = st.dataframe(display_dataframe,
                                        use_container_width=True,
                                        on_select='rerun',
                                        selection_mode=['single-row'],
                                        height=500,
                                        )
            print("\nReceived Data : ",received_data)
            # st.markdown('</div>', unsafe_allow_html=True)

        if received_data["selection"]["rows"]:
            row_idx = received_data['selection']['rows'][0]
            row_video_id = display_dataframe['video_id'][row_idx]
            SocialMedia().display_reconstructed_page(corpus_select,row_video_id,dataframe=filtered_df)

    def create_filters(self):
        save_button, load_button = st.columns(2)
        with save_button:
            if st.download_button(
                    label="Save Presets",
                    data=self.save_presets(),
                    file_name=f"preset_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                ):
                st.success("saved presets sucessfully")
        
        with load_button:
            uploaded_file = st.file_uploader("Upload a JSON file to load presets",
                                             type="json",accept_multiple_files=False,
                                             help="Upload the presets file",label_visibility="collapsed")
            #st.link_button("Load_presets",'uploaded_file')
            if uploaded_file is not None:
                st.success("loaded presets sucessfully")
    
        
        
        # Grid for the korpus filters 
        first_col,second_col,third_col = st.columns(3)
        
        corpus_select = first_col.selectbox('Select a Korpus', 
                                options=self.dataframe_dict.keys(),
                                )
        
        self.filters['corpus_select'] = corpus_select
        # self.apply_loaded_presets() # TODO : NEED TO change the approach

        # Set the data types for the pandas dataframe
        dataframe = pd.read_csv(self.dataframe_dict[self.filters['corpus_select']],low_memory=False)
        dataframe = self.set_dataframe_format(dataframe,corpus_select)

        # Filters for hashtag and profile names
        if not corpus_select == 'influencer_korpus':
            hashtags_list = dataframe['hashtag'].unique()
            hashtag_text = "Select the hashtags"
        else:
            hashtags_list = dataframe['profile_name'].unique()
            hashtag_text = "Select the profile"

        hashtags_select = first_col.multiselect(hashtag_text,
                                          options=hashtags_list,
                                          default=None
                                          )
        self.filters['hashtags_select'] = hashtags_select  
        
        # Fist stage of data filtering for hashtags and channel names
        if hashtags_select:
            if corpus_select != 'influencer_korpus':
                filtered_df = dataframe[dataframe['hashtag'].isin(hashtags_select)]
            else:
                filtered_df = dataframe[dataframe['profile_name'].isin(hashtags_select)]
        else:
            filtered_df = dataframe # If no hashtags selected, use the entire dataframe

        platform = first_col.multiselect('Select a platform', 
                                options=["Instagram","TikTok","YouTube"],
                                default= None
                                )
        
        # Filter based on selected platforms
        if platform:
            filtered_df = filtered_df[filtered_df['platform'].isin(platform)]

        with first_col:
            if 'YouTube' in platform:
                st.caption("Youtube Filters")
                shorts_col,videos_col = st.columns(2,vertical_alignment='top')
                shorts_filter,videos_filter = shorts_col.checkbox('Shorts'),videos_col.checkbox('Videos')
                if shorts_filter and videos_filter:
                    filtered_df = filtered_df[
                        filtered_df['media_type'].isin(['shorts', 'video'])
                    ]
                elif shorts_filter:
                    filtered_df = filtered_df[filtered_df['media_type'] == 'shorts']
                elif videos_filter:
                    filtered_df = filtered_df[filtered_df['media_type'] == 'video']
            if 'Instagram' in platform:
                st.caption("Instagram Filters")
                posts_col,reels_col,carousel_col = st.columns(3,vertical_alignment='top')
                posts_filter,reels_filter,carousel_filter = posts_col.checkbox('Posts',disabled=False),reels_col.checkbox('Reels',disabled=False),carousel_col.checkbox('Carousel',disabled=False)
                selected_filters = []
                if posts_filter:
                    selected_filters.append('Posts')
                if reels_filter:
                    selected_filters.append('Reels')
                if carousel_filter:
                    selected_filters.append('Carousel')

                if selected_filters:
                    filtered_df = filtered_df[filtered_df['media_type'].isin(selected_filters)]

        
        # Second stage filters
        with second_col:
            start_date_filter, end_date_filter = st.columns(2)
            start_date = start_date_filter.date_input(
                "Start date",
                min_value=min(filtered_df['upload_date'].dt.date),
                max_value=max(filtered_df['upload_date'].dt.date),
                value=min(filtered_df['upload_date'].dt.date),
            )
            end_date = end_date_filter.date_input(
                "End date",
                min_value=min(filtered_df['upload_date'].dt.date),
                max_value=max(filtered_df['upload_date'].dt.date),
                value=max(filtered_df['upload_date'].dt.date),
            )
        filtered_df = self.filter_by_date(
            filtered_df, start_date, end_date)

        # Get channel names based on the filtered dataframe
        channels_list = filtered_df['channel_name'].unique().tolist()

        channels_select = second_col.multiselect("Select channel names",
                                               options=channels_list,
                                               default=None,
                                               )
        if channels_select:
                filtered_df = filtered_df[filtered_df['channel_name'].isin(channels_select)]
        
        # filter data based on the keywords:
        keywords = second_col.text_input('Enter the keywords').split(',')
        with second_col: # keyword filters
            caption_col,title_col,transcripts_col = st.columns(3)
            caption_filter = caption_col.checkbox('Caption')
            title_filter = title_col.checkbox("Title")
            if 'YouTube' in platform:
                transcripts_filter = transcripts_col.checkbox("Transcripts")
            else:
                transcripts_filter= transcripts_col.checkbox("Transcripts",disabled=True)

            if keywords !=['']:
                mask = self.get_filter_keywords(filtered_df,caption_filter,title_filter,transcripts_filter,keywords=keywords)
                if mask is not None:
                    filtered_df= filtered_df[mask]
                else:
                    st.warning("Please select the filter for the keywords")

        # third stage filter        
        filtered_df['comments_count'] = pd.to_numeric(filtered_df['comments_count'], errors='coerce').fillna(0).astype(int)
        filtered_df['subscribers_count'] = pd.to_numeric(filtered_df['subscribers_count'], errors='coerce').fillna(0).astype(int)
        with third_col:
            views_slider = st.slider("Views",
                                min_value=int(filtered_df['views_count'].min()), 
                                max_value=int(filtered_df['views_count'].max()), 
                                value=(int(filtered_df['views_count'].min()), int(filtered_df['views_count'].max())))

            if 'YouTube' in platform:
                subscribers_slider = st.slider("Subscribers",
                                        min_value=int(filtered_df['subscribers_count'].min()), 
                                        max_value=int(filtered_df['subscribers_count'].max()), 
                                        value=(int(filtered_df['subscribers_count'].min()), int(filtered_df['subscribers_count'].max())))
                filtered_df = filtered_df[(filtered_df['subscribers_count'] >= subscribers_slider[0]) & (filtered_df['subscribers_count'] <= subscribers_slider[1])]
            
            likes_slider = st.slider("Likes",
                                    min_value=int(filtered_df['like_count'].min()), 
                                    max_value=int(filtered_df['like_count'].max()), 
                                    value=(int(filtered_df['like_count'].min()), int(filtered_df['like_count'].max())))
            
            comments_slider = st.slider("Comments",
                                        min_value=int(filtered_df['comments_count'].min()), 
                                        max_value=int(filtered_df['comments_count'].max()), 
                                        value=(int(filtered_df['comments_count'].min()), int(filtered_df['comments_count'].max())))

            
        filtered_df = filtered_df[
                        (filtered_df['views_count'] >= views_slider[0]) & (filtered_df['views_count'] <= views_slider[1]) &
                        (filtered_df['like_count'] >= likes_slider[0]) & (filtered_df['like_count'] <= likes_slider[1]) &
                        (filtered_df['comments_count'] >= comments_slider[0]) & (filtered_df['comments_count'] <= comments_slider[1])
                    ]

        with third_col:
            # Extract primary sentiment into a new column
            filtered_df['primary_sentiment'] = filtered_df['german_sentiment_transcript'].apply(self.extract_primary_sentiment)

            third_col.write("Select Sentiment")
            positive_senti_col,neutral_senti_col,negative_senti_col = st.columns(3)
            positive_filter = positive_senti_col.checkbox('Positive Sentiment')
            neutral_filter = neutral_senti_col.checkbox('Neutral Sentiment')
            negative_filter = negative_senti_col.checkbox('Negative Sentiment')
            
            # Now, proceed with the sentiment filtering
            sentiment_filters = []
            if positive_filter:
                sentiment_filters.append('positive')
            if neutral_filter:
                sentiment_filters.append('neutral')
            if negative_filter:
                sentiment_filters.append('negative')

            # Apply the sentiment filter based on the 'primary_sentiment' column
            if sentiment_filters:
                posts_with_selected_sentiments = filtered_df[filtered_df['primary_sentiment'].isin(sentiment_filters)]
                selected_video_ids = posts_with_selected_sentiments['video_id'].unique()
                filtered_df = filtered_df[filtered_df['video_id'].isin(selected_video_ids)]
                
                # filtered_df = filtered_df[filtered_df['primary_sentiment'].isin(sentiment_filters)]



        # Display DataFrame based on Video ID
        with first_col:
            # Input for video_id
            video_id_input = st.text_input("Enter Video ID")
            if video_id_input !='':
                filtered_df = filtered_df[filtered_df['video_id'] == video_id_input]
                st.write(f"Showing data for Video ID: {video_id_input}")
        
        filtered_df = filtered_df.reset_index(drop=True)

        return filtered_df,corpus_select

    def extract_primary_sentiment(self,sentiment_data):
        try:
            parsed_data = ast.literal_eval(sentiment_data)
            if isinstance(parsed_data, tuple):
                primary_sentiment = parsed_data[0][0]
                return primary_sentiment.lower()
        except (ValueError, SyntaxError, IndexError, TypeError):
            return None

    def display_dataframe(self,dataframe):
        columns_to_display = ['video_id','hashtag','platform','channel_name','title',
                              'views_count','comments_count','like_count',
                              'subscribers_count','upload_date','extracted_date',
                              'video_category','media_type','time_stamp',
                              'is_private','transcript_source'
                              ]
        return dataframe[pd.notna(dataframe['title'])][columns_to_display]


    def set_dataframe_format(self,dataframe,corpus_select):

        dataframe['views_count'] = dataframe['views_count'].fillna(0)
        dataframe['subscribers_count'] = dataframe['subscribers_count'].fillna(0)
        dataframe['like_count'] = dataframe['like_count'].fillna(0)
        dataframe['comments_count'] = dataframe['comments_count'].fillna(0)

        if corpus_select == 'influencer_korpus':
            col_key = 'profile_name'
        else:
            col_key = 'hashtag'

        mapping_types_conversion = {
                                "video_id":"string",
                                "title":"string",
                                "video_description":"string",
                                "thumbnail_url":"string",
                                "channel_id":"category",
                                "channel_url":"string",
                                "video_duration":"string",
                                "views_count":"Int64",
                                "original_url":"string",
                                "comments_count":"Int64",
                                "like_count":"Int64",
                                "time_stamp":"string",
                                "transcript_german":"string",
                                # "extracted_date":"datetime64[ns]",
                                f"{col_key}":"category", # For influencer corpus there is no hashtag only profilename
                                "platform":"category",
                                "media_type":"category",
                                "comment_text":"string",
                                # "comment_likes":"Int64",
                                "author_name":"string",
                                "author_id":"category",
                                "comment_id":"category",
                                "replied_to_comment_id":"category",
                                "comment_date":"datetime64[ns]",
                                # "upload_date":"datetime64[ns]",
                            }
        try:
            dataframe.astype(mapping_types_conversion)
        except Exception as e:
            st.error(f"The error is {e}")
        # Replace 'No subscribers count' with 0 for TikTok
        dataframe.loc[(dataframe['platform'] == 'TikTok') & (dataframe['subscribers_count'] == 'No subscribers count'), 'subscribers_count'] = 0
        dataframe['subscribers_count'] = self.safe_convert_to_int(dataframe['subscribers_count'])
        dataframe["upload_date"] = pd.to_datetime(dataframe["upload_date"], errors='coerce')
        dataframe["comment_date"] = pd.to_datetime(dataframe["comment_date"], errors='coerce')
        # dataframe["extracted_date"] = pd.to_datetime(dataframe["extracted_date"], errors='coerce')
        dataframe['comment_likes'] = dataframe['comment_likes'].fillna(0.0)

        return dataframe

    def safe_convert_to_int(self,column):
        column_numeric = pd.to_numeric(column, errors='coerce')
        column_int = column_numeric.dropna().astype(int)
        column_int = column_numeric.astype('Int64')
        return column_int
        
    
    def apply_loaded_presets(self):
        
        if self.filters['corpus_select']:
            st.selectbox('Select a Korpus',
                         options= self.dataframe_dict.keys(), index=list(self.dataframe_dict.keys()).index(self.filters['corpus_select']))

        if self.filters['hashtags_select']:
            st.multiselect('Select hashtags', 
                           options= self.dataframe_dict[self.filters['corpus_select']]['hashtag'].unique(), 
                           default=self.filters['hashtags_select'])

    
    
    def save_presets(self):
        return json.dumps(self.filters, indent=4)
        
    def load_presets(self):
        uploaded_file = st.file_uploader("Choose a preset file", type="json")
        if uploaded_file is not None:
            self.filters = json.load(uploaded_file)
            st.success("Presets loaded successfully")
    
    
    def filter_by_date(self, df, start_date, end_date):
        try:
            
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            video_ids_in_range = df[
                (df['upload_date'] >= start_date) & 
                (df['upload_date'] <= end_date)
            ]['video_id'].unique()

            filtered_data = df[df['video_id'].isin(video_ids_in_range)]

            return filtered_data

        except Exception as e:
            st.error(f"An error occurred while filtering by date: {e}")
            return pd.DataFrame()
    
    
    def first_stage_filter_df(self, df, hashtags_select, channels_select, corpus_select):
        try:
            # Apply hashtag/profile filter if selections are made
            if hashtags_select:
                if corpus_select != 'influencer_korpus':
                    df = df[df['hashtag'].isin(hashtags_select)]
                else:
                    df = df[df['profile_name'].isin(hashtags_select)]

            # Apply channel filter if selections are made
            if channels_select:
                df = df[df['channel_name'].isin(channels_select)]

            return df

        except Exception as e:
            st.error(f"An error occurred while filtering the data: {e}")
            return pd.DataFrame()


    def color_platform_cell(self,platform):

        colors = {"YouTube" : "Red",
                  "Instagram" : "Orange",
                  "TikTok" : "Gray"
                  }
        return f"background-color: {colors[platform]}"

    def get_filter_keywords(self,dataframe,caption_filter,title_filter,transcripts_filter,keywords):
        """
        Returns the mask based on the applied filters.
            mask: list(True|False)
        """
        if caption_filter and title_filter and transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(text =x[col],keywords=keywords) for col in ['title','video_description','transcript_german']), axis=1)
        elif not caption_filter and not title_filter and not transcripts_filter:
            mask = None
        elif caption_filter and title_filter and not transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(x[col],keywords=keywords) for col in ['title','video_description']), axis=1)
        elif caption_filter and not title_filter and transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(x[col],keywords=keywords) for col in ['video_description','transcript_german']), axis=1)
        elif not caption_filter and title_filter and transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(x[col],keywords=keywords) for col in ['title','transcript_german']), axis=1)
        elif caption_filter and not title_filter and not transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(x[col],keywords=keywords) for col in ['video_description']), axis=1)
        elif not caption_filter and title_filter and not transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(x[col],keywords=keywords) for col in ['title']), axis=1)
            print("Title mask : ", mask)
        elif not caption_filter and not title_filter and transcripts_filter:
            mask = dataframe.apply(lambda x: any(self.check_keywords(x[col],keywords=keywords) for col in ['transcript_german']), axis=1)
        
        return mask
    
    def check_keywords(self,text,keywords):
        """
        Returns True if the keyword is present in the text
        """
        return any(keyword.lower() in str(text).lower() for keyword in keywords)
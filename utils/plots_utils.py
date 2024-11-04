# import modules
import time
import datetime
import locale
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

# # Custom imports
# from utils.social_media_utils import SocialMedia
# from utils.plots_utils import PlotsMetrics



class PlotsLayout():
    
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
        
        filtered_df = self.create_filters()

        plots_col1,plots_col2 = st.columns(2)
        
        plots_container_height = 650
        

        if self.filters['corpus_select'] == 'influencer_korpus':
            col_name = 'profile_name'
            header_name = 'Profile'
        else:
            col_name = 'hashtag'
            header_name = 'Hashtag'


        # Metrics Visualization
        with plots_col1:
            with st.container(height=plots_container_height):
                st.subheader(f"Social Media Post Metrics by {header_name}",divider='blue')
                self.display_metrics(filtered_df,col_name)

        # Number of posts visualization for hashtag/platform.
        with plots_col2:
            with st.container(height=plots_container_height):
                    st.subheader(f"Number of Posts/{header_name} ",divider='blue')
                    self.display_pie_chart(dataframe=filtered_df,column_name=col_name.lower())
        
        # Number of posts over time
        with plots_col1.container(height=plots_container_height):
            st.subheader("Number of posts over time",divider='blue')
            day_col,year_col = st.columns(2)
            day_checked = day_col.checkbox('Day', value=False)
            year_checked = year_col.checkbox('Year', value=False)

            if day_checked:
                time_granularity = 'D'
            elif year_checked:
                time_granularity = 'Y'
            else:
                time_granularity = 'M'

            self.num_posts_over_time(dataframe=filtered_df,col_name=col_name,date_filter=time_granularity)

        with plots_col2.container(height=plots_container_height):
            st.subheader("Number of subscribers over time",divider='blue')
            day_col,year_col = st.columns(2)
            day_check = day_col.checkbox('day', value=False)
            year_check = year_col.checkbox('year', value=False)

            if day_check:
                time_granularity = 'D'
            elif year_check:
                time_granularity = 'Y'
            else:
                time_granularity = 'M'
            
            self.num_subscribers_over_time(dataframe=filtered_df,col_name=col_name,date_filter=time_granularity)

        # Views,likes,comments over time
        with plots_col1.container(height=plots_container_height):
            self.views_likes_comments_over_time(dataframe = filtered_df,col_name=col_name)
        
        with plots_col2.container(height=plots_container_height):
            st.subheader("Relationship Between Views/Likes/Comments",divider='blue')
            self.views_likes_comments_relationship(dataframe=filtered_df,col_name=col_name)

        with plots_col1:
            # Word cloud transcripts
            with st.container(height=plots_container_height):
                col1,col2 = st.columns(2)
                col1.subheader("Word Cloud Transcripts",divider='blue')
                buffer = self.display_word_cloud(filtered_df,column_name='transcript_german')
                col2.download_button(
                    label="Download Transcripts Image",
                    data=buffer,
                    file_name="wordcloud.png",
                    mime="image/png"
                )
        with plots_col2:
            # Word cloud comments
            with st.container(height=plots_container_height):
                col1,col2 = st.columns(2)
                col1.subheader("Word Cloud Comments",divider='blue')
                buffer = self.display_word_cloud(filtered_df,column_name='comment_text')
                col2.download_button(
                    label="Download Comments Image",
                    data=buffer,
                    file_name="wordcloud.png",
                    mime="image/png"
                )
    
    def views_likes_comments_relationship(self, dataframe, col_name):
        # Allow the user to select one or two metrics for comparison
        filter_options = st.multiselect(
            "Select up to two metrics to plot:",
            ["Views", "Likes", "Comments"],
            default=["Views"]
        )

        if len(filter_options) == 0:
            st.warning("Please select at least one metric.")
            return

        # Map the selected metrics to the corresponding column names
        metric_map = {
            "Views": 'views_count',
            "Likes": 'like_count',
            "Comments": 'comments_count'
        }

        filter_columns = [metric_map[option] for option in filter_options]
        dataframe = dataframe[dataframe['title'].notna()]
        dataframe = dataframe[[col_name, 'upload_date', 'video_id'] + filter_columns].dropna()

        if dataframe.empty:
            st.warning("No data available to plot.")
            return

        dataframe = dataframe.sort_values(by='upload_date').reset_index(drop=True)
        dataframe['post_index'] = range(1, len(dataframe) + 1)

        display_name = 'Profile' if col_name == 'profile_name' else 'Hashtag'

        # Create the plot
        fig = go.Figure()

        hashtags = dataframe[col_name].unique()
        
        metric_colors = {
                        'Views': 'rgba(31, 119, 180, 1)',  # blue
                        'Likes': 'rgba(255, 127, 14, 1)',  # orange
                        'Comments': 'rgba(44, 160, 44, 1)'  # green
                    }



        for i, hashtag in enumerate(hashtags):
            hashtag_df = dataframe[dataframe[col_name] == hashtag]
            for i, filter_option in enumerate(filter_options):
                fig.add_trace(go.Bar(
                    x=hashtag_df['post_index'],
                    y=hashtag_df[filter_columns[i]],
                    name=f'{hashtag} - {filter_option}',
                    marker_color=metric_colors[filter_option],
                    hovertemplate='<b>Post Index:</b> <b>%{x}</b><br>' +
                                f'<b>{filter_option}:</b> <b>%{{y}}</b><br>' +
                                '<b>Video ID:</b> <b>%{customdata}</b><br>' +
                                '<extra></extra>', 
                    customdata=hashtag_df['video_id']
                ))


        if len(dataframe) <50:
            interval = 5
        elif len(dataframe) >50 and len(dataframe) <100:
            interval = 10
        else:
            interval = 25

        tick_vals = list(range(1, len(dataframe) + 1, interval))
        tick_text = [str(i) for i in tick_vals]

        fig.update_layout(
            title=f'{" and ".join(filter_options)} by {display_name}',
            xaxis_title='Number of Posts',
            yaxis_title='Count',
            xaxis=dict(
                title='Number of Posts',
                titlefont=dict(size=18, color='black'),
                tickformat='%Y.%m.%d',
                type='category',
                tickangle=-90,
                tickvals=tick_vals,
                ticktext=tick_text,
                tickfont=dict(size=12, color='black'),
            ),
            yaxis=dict(
                title='Count',
                titlefont=dict(size=18, color='black'),
                autorange=True,
                tickfont=dict(size=14, color='black'),
            ),
            legend=dict(
                font=dict(size=18, color='black'),
                orientation='v',
                xanchor='left',
                x=1.05,
                yanchor='top',
                y=1
            ),
            width=1200,
            height=500
        )

        st.plotly_chart(fig, use_container_width=True)

    def views_likes_comments_over_time(self, dataframe, col_name):
        filter_option = st.selectbox(
            "Select the metric to plot:",
            ["Views", "Likes", "Comments"]
        )
        
        # Map filter_option to the corresponding column
        filter_column_name = {
            'Views': 'views_count',
            'Likes': 'like_count',
            'Comments': 'comments_count'
        }[filter_option]

        display_name = 'Profile' if col_name == 'profile_name' else 'Hashtag'

        st.subheader(f"Number of {filter_option} by {display_name}",divider='blue')
        
        dataframe = dataframe[dataframe['title'].notna()]
        dataframe = dataframe[[col_name, filter_column_name, 'upload_date', 'video_id']].dropna()
        
        if dataframe.empty:
            st.warning("No data available to plot.")
            return
        
        dataframe = dataframe.sort_values(by='upload_date').reset_index(drop=True)
        dataframe['post_index'] = dataframe.groupby(col_name).cumcount() + 1
        
        
        
        # Create a bar plot
        fig = go.Figure()

        hashtags = dataframe[col_name].unique()
        color_map = {hashtag: f'rgb({i*50}, {100+(i*30)%150}, {200-(i*50)%150})' for i, hashtag in enumerate(hashtags)}

        # Prepare a combined DataFrame for all hashtags
        combined_df = pd.DataFrame({'post_index': range(1, dataframe['post_index'].max() + 1)})

        for hashtag in hashtags:
            hashtag_df = dataframe[dataframe[col_name] == hashtag]
            hashtag_df = hashtag_df.set_index('post_index').reindex(combined_df['post_index']).reset_index()
            
            fig.add_trace(go.Bar(
                x=hashtag_df['post_index'],
                y=hashtag_df[filter_column_name],
                name=hashtag,
                marker_color=color_map[hashtag],
                hovertemplate='<b>Post Index:</b> <b>%{x}</b><br>' +
                            '<b>Num:</b> <b>%{y}</b><br>' +
                            '<b>Video ID:</b> <b>%{customdata}</b><br>' +
                            '<extra></extra>', 
                customdata=hashtag_df['video_id']
            ))

        if len(dataframe) <50:
            interval = 5
        elif len(dataframe) >50 and len(dataframe) <100:
            interval = 10
        else:
            interval = 25
        tick_vals = list(range(1, dataframe['post_index'].max() + 1, interval))
        tick_text = [str(i) for i in tick_vals]

        fig.update_layout(
            title=f'Number of {filter_option} by {display_name}',
            xaxis_title='Number of Posts',
            yaxis_title=f'Number of {filter_option}',
            xaxis=dict(
                title='Number of Posts',
                titlefont=dict(size=18, color='black'),
                type='category',
                tickangle=-90,
                tickvals=tick_vals,
                ticktext=tick_text,
                tickfont=dict(size=12, color='black'),
            ),
            yaxis=dict(
                title=f'Number of {filter_option}',
                titlefont=dict(size=18, color='black'),
                autorange=True,
                tickfont=dict(size=14, color='black')
            ),
            legend=dict(
                font=dict(size=18, color='black'),
                orientation='v',
                xanchor='left',
                x=1.05,
                yanchor='top',
                y=1
            ),
            width=1200,
            height=500,
            barmode='group'  # This ensures bars for different hashtags are placed side by side
        )

        st.plotly_chart(fig, use_container_width=True)


    # def views_likes_comments_over_time(self,dataframe,col_name):
    #     filter_option = st.selectbox(
    #             "Select the metric to plot:",
    #             ["Views", "Likes", "Comments"]
    #         )
        
    #     if filter_option == 'Views':
    #         filter_column_name = 'views_count'
    #     elif filter_option == 'Likes':
    #         filter_column_name = 'like_count'
    #     elif filter_option == 'Comments':
    #         filter_column_name = 'comments_count' 
        
    #     dataframe = dataframe[[col_name, filter_column_name, 'upload_date','video_id']].dropna()
        
    #     if dataframe.empty:
    #         st.warning("No data available to plot.")
    #         return
        
    #     dataframe = dataframe.sort_values(by='upload_date').reset_index(drop=True)
    #     dataframe['post_index'] = range(1, len(dataframe) + 1)

    #     if col_name == 'profile_name':
    #         display_name = 'Profile'
    #     else:
    #         display_name = 'Hashtag'
        
    #     # Create a bar plot
    #     fig = go.Figure()

    #     hashtags = dataframe[col_name].unique()
    #     color_map = {hashtag: f'rgb({i*50}, {100+(i*30)%150}, {200-(i*50)%150})' for i, hashtag in enumerate(hashtags)}

    #     for hashtag in hashtags:
    #         hashtag_df = dataframe[dataframe[col_name] == hashtag]
    #         fig.add_trace(go.Bar(
    #             x=hashtag_df['post_index'],
    #             y=hashtag_df[filter_column_name],
    #             name=hashtag,
    #             marker_color=color_map[hashtag],
    #             hovertemplate='<b>Post Index:</b> <b>%{x}</b><br>' +
    #                         '<b>Num</b>: <b>%{y}</b><br>' +
    #                         '<b>Video ID:</b> <b>%{customdata}</b><br>' +
    #                         '<extra></extra>', 
    #             customdata=hashtag_df['video_id']
    #             ))
    #         # fig.add_trace(go.Scatter(
    #         # x=hashtag_df['post_index'],
    #         # y=hashtag_df[filter_column_name],
    #         # mode='lines+markers',
    #         # name=hashtag,
    #         # line=dict(color=color_map[hashtag]),
    #         # marker=dict(size=8),
    #         # hovertemplate='<b>Post Index:</b> <b>%{x}</b><br>' +
    #         #             '<b>Num:</b> <b>%{y}</b><br>' +
    #         #             '<b>Video ID:</b> <b>%{customdata}</b><br>' +
    #         #             '<extra></extra>', 
    #         # customdata=hashtag_df['video_id']
    #         # ))


    #     interval = 10
    #     tick_vals = list(range(1, len(dataframe) + 1, interval))
    #     tick_text = [str(i) for i in tick_vals]

    #     fig.update_layout(
    #         title=f'Number of {filter_option} by {display_name}',
    #         xaxis_title='Date',
    #         yaxis_title=f'Number of {filter_option}',
    #         xaxis=dict(
    #             title = 'Number of Posts',
    #             titlefont=dict(
    #                 size=18, 
    #                 color='black'
    #             ),
    #             tickformat='%Y.%m.%d',
    #             # tickvals=dataframe['post_index'],
    #             # ticktext=[value for value in dataframe['post_index']],
    #             type='category',
    #             tickangle=-90,
    #             tickvals = tick_vals,
    #             ticktext = tick_text,
    #             tickfont=dict(
    #                 size=12,
    #                 color='black',
    #             )
    #         ),
    #         yaxis=dict(
    #             title=f'Number of {filter_option}',
    #             titlefont=dict(
    #                 size=18, 
    #                 color='black'
    #             ),
    #             autorange=True, 
    #             tickfont=dict(
    #                 size=14,
    #                 color='black'
    #             )
    #         ),
    #         legend=dict(
    #             font=dict(size=18, color='black'),
    #             orientation='v',
    #             xanchor='left',
    #             x=1.05,
    #             yanchor='top',
    #             y=1
    #         ),
    #         width=1200,
    #         height=500,
    #         barmode='group'
    #     )

    #     st.plotly_chart(fig, use_container_width=True)

    def num_subscribers_over_time(self,dataframe,col_name,date_filter):
        
        dataframe = dataframe[dataframe['title'].notna()]
        if not col_name == 'profile_name':
            col_name = 'channel_name'

        # TODO: change youtube to self.platform
        dataframe = dataframe[dataframe['platform']=='YouTube']
        
        subscribers_over_time = dataframe.groupby(
            [dataframe['upload_date'].dt.to_period(date_filter), col_name]
        )['subscribers_count'].sum().reset_index()

        subscribers_over_time['upload_date'] = subscribers_over_time['upload_date'].astype(str)

        dates = sorted(subscribers_over_time['upload_date'].unique())
        hashtags = sorted(subscribers_over_time[col_name].unique())

        fig = go.Figure()
        color_map = {hashtag: f'rgb({i*50}, {100+(i*30)%150}, {200-(i*50)%150})' for i, hashtag in enumerate(hashtags)}

        for hashtag in hashtags:
            hashtag_data = subscribers_over_time[subscribers_over_time[col_name] == hashtag]

            # fig.add_trace(go.Bar(
            #     x=hashtag_data['upload_date'],
            #     y=hashtag_data['subscribers_count'],
            #     name=hashtag,
            #     marker_color=color_map[hashtag]
            # ))

            fig.add_trace(go.Scatter(
                x=hashtag_data['upload_date'],
                y=hashtag_data['subscribers_count'],
                mode='lines+markers',
                name=hashtag,
                line=dict(color=color_map[hashtag]),
                marker=dict(size=8),
                ))

        if col_name == 'profile_name':
            display_name = 'Profile'
        else:
            display_name = 'Hashtag'

        fig.update_layout(
            title=f'Number of Subscribers Over Time for Each {display_name.capitalize()}',
            xaxis_title='Date',
            yaxis_title='Number of Subscribers',
            xaxis=dict(
                title = 'Date',
                titlefont=dict(
                    size=18, 
                    color='black'
                ),
                tickformat='%Y.%m.%d',
                tickvals=dates,
                ticktext=[date for date in dates],
                type='category',
                tickangle=-45,
                tickfont=dict(
                    size=14,
                    color='black'
                )
            ),
            yaxis=dict(
                title='Number of Subscribers',
                titlefont=dict(
                    size=18, 
                    color='black'
                ),
                autorange=True, 
                tickfont=dict(
                    size=14,
                    color='black'
                )
            ),
            legend=dict(
                font=dict(
                    size=18,
                    color='black'
                ),
                orientation='v',
                xanchor='left',
                x=1.05,
                yanchor='top',
                y=1
            ),
            barmode='group',
            # margin=dict(t=50, b=50, l=50, r=150),
            width=900,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)


    def num_posts_over_time(self,dataframe,col_name,date_filter):

        dataframe = dataframe[dataframe['title'].notna()]

        posts_over_time = dataframe.groupby(
            [col_name, dataframe['upload_date'].dt.to_period(date_filter)]
        ).size().reset_index(name='post_count')

        posts_over_time = posts_over_time[posts_over_time['post_count'] > 0]
        posts_over_time['upload_date'] = posts_over_time['upload_date'].astype(str)

        dates = sorted(posts_over_time['upload_date'].unique())
        hashtags = sorted(posts_over_time[col_name].unique())

        fig = go.Figure()
        color_map = {hashtag: f'rgb({i*50}, {100+(i*30)%150}, {200-(i*50)%150})' for i, hashtag in enumerate(hashtags)}

        for hashtag in hashtags:
            hashtag_df = posts_over_time[posts_over_time[col_name] == hashtag]
            fig.add_trace(go.Bar(
                x=hashtag_df['upload_date'],
                y=hashtag_df['post_count'],
                name=hashtag,
                marker_color=color_map[hashtag]
            ))
        
        if col_name == 'profile_name':
            display_name = 'Profile'
        else:
            display_name = 'Hashtag'

        fig.update_layout(
            title=f'Number of Posts Over Time for Each {display_name.capitalize()}',
            xaxis_title='Date',
            yaxis_title='Number of Posts',
            xaxis=dict(
                title = 'Date',
                titlefont=dict(
                    size=18, 
                    color='black'
                ),
                tickformat='%Y.%m.%d',
                tickvals=dates,
                ticktext=[date for date in dates],
                type='category',
                tickangle=-45,
                tickfont=dict(
                    size=14,
                    color='black'
                )
            ),
            yaxis=dict(
                title='Number of Posts',
                titlefont=dict(
                    size=18, 
                    color='black'
                ),
                autorange=True, 
                tickfont=dict(
                    size=14,
                    color='black'
                )
            ),
            legend=dict(
                font=dict(
                    size=18,
                    color='black'
                ),
                orientation='v',
                xanchor='left',
                x=1.05,
                yanchor='top',
                y=1
            ),
            barmode='group',
            # margin=dict(t=50, b=50, l=50, r=150),
            width=900,
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)


    def display_metrics(self,df,col_name):
        # Group by hashtag_name
        grouped = df.groupby(col_name)

        # Iterate through each hashtag group
        for hashtag, group in grouped:
            st.subheader(f"Metrics for {col_name.upper()} : {hashtag}",divider='green')
            
            platforms = ['YouTube', 'TikTok', 'Instagram']
            col1, col2, col3 = st.columns(3)
            for i, platform in enumerate(platforms):
                platform_group = group[group['platform'] == platform]
                platform_data = platform_group[platform_group['title'].notna()]
                if not platform_group.empty:
                    max_views = platform_group['views_count'].max()
                    max_views_post = platform_group.loc[platform_group['views_count'].idxmax(), 'video_id']

                    max_likes = platform_group['like_count'].max()
                    max_likes_post = platform_group.loc[platform_group['like_count'].idxmax(), 'video_id']

                    max_comments = platform_group['comments_count'].max()
                    max_comments_post = platform_group.loc[platform_group['comments_count'].idxmax(), 'video_id']

                    if i == 0:
                        with col1:
                            st.markdown(f"### {platform}")

                            st.markdown(f"##### :violet-background[Total Posts:] ___{int(len(platform_data))}___")

                            st.markdown(f"##### :red-background[Max Views:] ___{int(max_views)}___")
                            st.markdown(f'##### :red-background[Post ID:] ___{max_views_post}___')

                            st.markdown(f"##### :blue-background[Max Likes:] ___{int(max_likes)}___")
                            st.markdown(f'##### :blue-background[Post ID:] ___{max_likes_post}___')
                            
                            st.markdown(f"##### :green-background[Max Comments:] ___{int(max_comments)}___")
                            st.markdown(f'##### :green-background[Post ID:] ___{max_comments_post}___')
                            
                    elif i == 1:
                        with col2:
                            st.markdown(f"### {platform}")
                            
                            st.markdown(f"##### :violet-background[Total Posts:] ___{int(len(platform_data))}___")

                            st.markdown(f"##### :red-background[Max Views:] ___{int(max_views)}___")
                            st.markdown(f'##### :red-background[Post ID:] ___{max_views_post}___')

                            st.markdown(f"##### :blue-background[Max Likes:] ___{int(max_likes)}___")
                            st.markdown(f'##### :blue-background[Post ID:] ___{max_likes_post}___')
                            
                            st.markdown(f"##### :green-background[Max Comments:] ___{int(max_comments)}___")
                            st.markdown(f'##### :green-background[Post ID:] ___{max_comments_post}___')
                    elif i == 2:
                        with col3:
                            st.markdown(f"### {platform}")
                            
                            st.markdown(f"##### :violet-background[Total Posts:] ___{int(len(platform_data))}___")

                            st.markdown(f"##### :red-background[Max Views:] ___{int(max_views)}___")
                            st.markdown(f'##### :red-background[Post ID:] ___{max_views_post}___')

                            st.markdown(f"##### :blue-background[Max Likes:] ___{int(max_likes)}___")
                            st.markdown(f'##### :blue-background[Post ID:] ___{max_likes_post}___')
                            
                            st.markdown(f"##### :green-background[Max Comments:] ___{int(max_comments)}___")
                            st.markdown(f'##### :green-background[Post ID:] ___{max_comments_post}___')

            st.markdown("---")  # Add a separator between different hashtags

    def display_pie_chart(self,dataframe,column_name):
        
        if column_name == 'profile_name':
            display_name = 'Profile'
        else:
            display_name = 'Hashtag'
        
        filtered_df = dataframe[dataframe['title'].notna()]
        hashtag_counts = filtered_df[column_name].value_counts().reset_index()
        hashtag_counts.columns = [column_name, 'post_count']

        hashtag_counts['percentage'] = (hashtag_counts['post_count'] / hashtag_counts['post_count'].sum() * 100).round(1)
        
        # rotation_offset = 5 # Number of positions to shift
        # hashtag_counts = hashtag_counts.shift(rotation_offset).reset_index(drop=True)


        # Step 3: Create an interactive pie chart with Plotly
        fig = go.Figure(data=[go.Pie(
            labels=hashtag_counts[column_name],
            values=hashtag_counts['post_count'],
            textinfo='label+percent+value',  # Show label, percent, and value
            customdata=hashtag_counts[['percentage', 'post_count']],  # Custom data for hover text
            hovertemplate='%{label} %{customdata[0]}% - %{value}',  # Custom hover text
            textposition='inside',  # Position text inside slices
            # insidetextorientation='radial',  # Rotate text to be radial
            hole=0.3,
            textfont=dict(size=18,color='black')
        )])

        # Step 4: Update layout for better aesthetics
        fig.update_layout(
            title=f'Number of Posts for Each {display_name}',
            annotations=[dict(text='Posts', x=0.5, y=0.5, font_size=20, bgcolor='white',showarrow=False)],
            # margin=dict(t=100, b=0, l=0, r=0), 
            autosize=True,
            showlegend=True,
            legend=dict(
                        font=dict(size=16),
                        itemclick='toggle', 
                        itemsizing='constant'
                    ),
            width=1000,
            height=500 
        )

    
        st.plotly_chart(fig)

    def display_word_cloud(self,dataframe,column_name):

        text_df = dataframe[column_name].dropna()
        # Combine all text into a single string
        text = " ".join(review for review in text_df.tolist())
        stop_words = np.loadtxt("/home/sathwik/college/student_job/ALSO_WebScraping/dashboard/utils/word_cloud_stopwords.txt",dtype=str)
        filtered_text = " ".join([word for word in text.split() if word.lower() not in stop_words])
        # Generate Word Cloud
        wordcloud = WordCloud(width=450, height=250, background_color='white').generate(filtered_text)
        plt.figure(figsize=(8, 4.5))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")

        # Save the plot to a BytesIO object
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)

        st.pyplot(plt)

        return buffer

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
            st.link_button("Load_presets",'uploaded_file')
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
        self.set_dataframe_format(dataframe,corpus_select)

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
                        
            if filtered_df['comments_count'].min() !=filtered_df['comments_count'].max():
                comments_slider = st.slider("Comments",
                                        min_value=int(filtered_df['comments_count'].min()), 
                                        max_value=int(filtered_df['comments_count'].max()), 
                                        value=(int(filtered_df['comments_count'].min()), int(filtered_df['comments_count'].max())))
                filtered_df = filtered_df[(filtered_df['comments_count'] >= comments_slider[0]) & (filtered_df['comments_count'] <= comments_slider[1])]
            
        filtered_df = filtered_df[
                        (filtered_df['views_count'] >= views_slider[0]) & (filtered_df['views_count'] <= views_slider[1]) &
                        (filtered_df['like_count'] >= likes_slider[0]) & (filtered_df['like_count'] <= likes_slider[1])]

        with third_col:
            third_col.write("Select Sentiment")
            positive_senti_col,neutral_senti_col,negative_senti_col = st.columns(3)
            positive_filter = positive_senti_col.checkbox('Positive Sentiment')
            neutral_filter = neutral_senti_col.checkbox('Neutral Sentiment')
            negative_filter = negative_senti_col.checkbox('Negative Sentiment')
        
        # Display DataFrame based on Video ID
        with first_col:
            # Input for video_id
            video_id_input = st.text_input("Enter Video ID")
            if video_id_input !='':
                filtered_df = filtered_df[filtered_df['video_id'] == video_id_input]
                st.write(f"Showing data for Video ID: {video_id_input}")
        
        filtered_df.loc[filtered_df['platform'] == 'TikTok', 'replied_to_comment_id'] = 'root'
        filtered_df = filtered_df.reset_index(drop=True)
        first_col.divider()
        first_col.download_button(
                    label="Download as csv",
                    data=filtered_df.to_csv(),
                    file_name=f"Social_media_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="csv",
                )

        return filtered_df


    def display_dataframe(self,dataframe):
        columns_to_display = ['video_id','platform','channel_name','title','video_description','video_duration','views_count','comments_count','like_count','subscribers_count','upload_date','extracted_date','transcript_german','video_category']
        return dataframe[columns_to_display]


    def set_dataframe_format(self,dataframe,corpus_select):

        dataframe['views_count'] = dataframe['views_count'].fillna(0)
        dataframe['subscribers_count'] = dataframe['subscribers_count'].fillna(0)
        dataframe['like_count'] = dataframe['like_count'].fillna(0)
        dataframe['comments_count'] = dataframe['comments_count'].fillna(0)
        dataframe['comment_likes'] = dataframe['comment_likes'].fillna(0)

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
                                "extracted_date":"datetime64[ns]",
                                f"{col_key}":"category", # spanch for influencer corpus there is no hashtag only profilename
                                "platform":"category",
                                "media_type":"category",
                                "comment_text":"string",
                                "comment_likes":"Int64",
                                "author_name":"string",
                                "author_id":"category",
                                "comment_id":"category",
                                "replied_to_comment_id":"category",
                                "comment_date":"datetime64[ns]",
                                "upload_date":"datetime64[ns]",
                            }
        try:
            dataframe.astype(mapping_types_conversion)
            # Replace 'No subscribers count' with 0 for TikTok
            dataframe.loc[(dataframe['platform'] == 'TikTok') & (dataframe['subscribers_count'] == 'No subscribers count'), 'subscribers_count'] = 0
            dataframe['subscribers_count'] = self.safe_convert_to_int(dataframe['subscribers_count'])
            dataframe["upload_date"] = pd.to_datetime(dataframe["upload_date"], errors='coerce')
            dataframe["comment_date"] = pd.to_datetime(dataframe["comment_date"], errors='coerce')
            dataframe["extracted_date"] = pd.to_datetime(dataframe["extracted_date"], errors='coerce')
        except Exception as e:
            st.error(e)

    def safe_convert_to_int(self,column):
        column_numeric = pd.to_numeric(column, errors='coerce')
        column_int = column_numeric.dropna().astype(int)
        column_int = column_numeric.astype('Int64')
        return column_int
        
    
    def apply_loaded_presets(self):
        # Apply the loaded presets to the UI elements
        if self.filters['corpus_select']:
            st.selectbox('Select a Korpus',
                         options= self.dataframe_dict.keys(), index=list(self.dataframe_dict.keys()).index(self.filters['corpus_select']))

        # For example, if 'hashtags_select' was loaded, you can set it in the multiselect:
        if self.filters['hashtags_select']:
            st.multiselect('Select hashtags', 
                           options= self.dataframe_dict[self.filters['corpus_select']]['hashtag'].unique(), 
                           default=self.filters['hashtags_select'])

    
    
    def save_presets(self):
        # Convert the filters to JSON format
        return json.dumps(self.filters, indent=4)
        
    def load_presets(self):
        # Load a JSON file with presets
        uploaded_file = st.file_uploader("Choose a preset file", type="json")
        if uploaded_file is not None:
            self.filters = json.load(uploaded_file)
            st.success("Presets loaded successfully")
    
    
    def filter_by_date(self, df, start_date, end_date):
        try:
            # # Filter based on the date range
            # mask = (df['upload_date'].dt.date >= start_date) & (df['upload_date'].dt.date <= end_date)
            # return df[mask]

            # Step 1: Identify the video_ids within the selected date range
            start_date = pd.to_datetime(start_date)
            end_date = pd.to_datetime(end_date)
            video_ids_in_range = df[
                (df['upload_date'] >= start_date) & 
                (df['upload_date'] <= end_date)
            ]['video_id'].unique()

            # Step 2: Filter the DataFrame to include all rows for these video_ids
            filtered_data = df[df['video_id'].isin(video_ids_in_range)]

            return filtered_data

        except Exception as e:
            st.error(f"An error occurred while filtering by date: {e}")
            return pd.DataFrame()  # Return an empty DataFrame in case of error
    
    
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
    
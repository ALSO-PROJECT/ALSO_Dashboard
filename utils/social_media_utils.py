# import modules
import time
import datetime
import locale
from millify import millify
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go


import streamlit as st
import io
import ast
import os
import yt_dlp
from pathlib import Path
import re
import imageio_ffmpeg as ffmpeg

class SocialMedia():

    def __init__(self) -> None:
        pass

    def stream_data(self,text):
        for word in text.split(" "):
            yield word + " "
            time.sleep(0.02)

    def display_reconstructed_page(self,corpus_select,row_video_id,dataframe):
        
        # Hide this until user clicks on the data

        # dataframe['video_id'] = dataframe['video_id'].astype(str)
        dataframe = dataframe[dataframe['video_id']==str(row_video_id)]
        dataframe.reset_index(drop=True, inplace=True)

        platform = str(dataframe.loc[0, 'platform'] )
        title = str(dataframe['title'][0])
        description = str(dataframe['video_description'][0])
        video_id = str(dataframe['video_id'][0])

        if platform.lower() == "youtube":
            video_url = str(dataframe['original_url'][0])
            # comments_count = int(dataframe['comments_count'][0])
            comments_count = max(len(dataframe) - 1, 0)
        elif platform.lower() == "tiktok":
            # Manually construct the TikTok URL using the video_id
            video_url = f"https://www.tiktok.com/@username/video/{video_id}"
            # comments_count = int(dataframe['comments_count'][0])
            comments_count = max(len(dataframe) - 1, 0)
        elif platform.lower()=='instagram':
            video_url = f"https://instagram.com/p/{video_id}"
            comments_count = max(len(dataframe) - 1, 0)

        views_count = str(dataframe['views_count'][0])
        likes_count = dataframe['like_count'][0]
        
        
        subscribers_count = str(dataframe['subscribers_count'][0])
        transcripts = dataframe['transcript_german'][0]

        # Date upload/extracted
        date_uploaded = dataframe['upload_date'][0].date()

        if platform.lower() == 'tiktok':
            date_extracted = dataframe['extracted_date'][0]
        elif platform.lower() == 'youtube':
            if corpus_select == 'influencer_korpus':
                date_extracted = dataframe['extracted_date'][0]
            else:
                try:
                    timestamp = float(dataframe['extracted_date'][0])
                    dt_object = datetime.datetime.utcfromtimestamp(timestamp)
                    date_extracted = dt_object.strftime('%d.%m.%Y')
                except Exception as e:
                    st.error (f"Error: {e}") 
        elif platform.lower() == 'instagram':
            date_extracted = dataframe['extracted_date'][0].split(" ")[0]
        
        
        # st.markdown(
        #             """
        #             <style>
        #             .reconstructed-page-container {
        #                 height: 1000px;
        #             }
        #             </style>
        #             """,
        #             unsafe_allow_html=True
        #         )

        main_container = st.container(height=1000)
        with main_container:
            # st.markdown('<div class="reconstructed-page-container">', unsafe_allow_html=True)
            media_col,desc_col = st.columns(2,gap='medium')
            with media_col:
                if video_url:
                    st.video(video_url,
                    loop=False,
                    autoplay=False,
                    muted=False,
                    format="video/mp4",
                    )
                
                    st.markdown(f"**Post Url :** {video_url}")

                else:
                    st.write("Video URL not available")
                
                with st.container(height=600):
                    st.subheader("Most Positive/Negative Comment Based on SentiWS",divider='blue')
                    self.most_sentiment_comments(dataframe,video_id)
                
                
            with desc_col:
                st.markdown(f"### {title}")
                # st.markdown(
                #     """
                #     <style>
                #     .video-description-container {
                #         height: 300px;
                #     }
                #     </style>
                #     """,
                #     unsafe_allow_html=True
                # )
                with st.container(height=300):
                    # st.markdown('<div class="video-description-container">', unsafe_allow_html=True)
                    st.write(f"#### Video Description \n {description}")
                    # st.markdown('</div>', unsafe_allow_html=True)
                col1,col2 = st.columns(2)
                col1.markdown(f"\n **Date Uploaded:** {date_uploaded}")
                col2.markdown(f"\n **Date Extracted:** {date_extracted}")
                col1.markdown(f"\n **Views:** {millify(views_count)}")
                col2.markdown(f"\n **Subscribers:** {millify(subscribers_count)}")
                col1.markdown(f"\n **Total comments:** {millify(comments_count)}")
                col2.markdown(f"\n **Likes:** {millify(likes_count)}")
                anonymous = col1.checkbox("Anonymous")
                if platform =='TikTok':
                    video_duration = col2.markdown(f"\n**Video Duration:** {dataframe['video_duration'][0]} sec")
                elif platform =='YouTube':
                    video_duration = col2.markdown(f"\n**Video Duration:** {dataframe['video_duration'][0]}")
                elif platform == 'Instagram':
                    video_duration = col2.markdown(f"\n**Video Duration:** {dataframe['video_duration'][0]} sec")
                col2.write("   ")

                # Analyze the post
                with col1:
                    button_disabled = platform == 'Instagram'
                    if st.button(label="Download Video", disabled=button_disabled):

                        save_path = str(Path.cwd())
                        video_path = self.download_video(video_id, platform, save_path)
                        
                        if video_path:
                            with open(video_path, "rb") as file:
                                video_bytes = file.read()
                                st.download_button(
                                    label="Click to download video",
                                    data=video_bytes,
                                    file_name=f"{platform}_{video_id}.mp4",
                                    mime="video/mp4"
                                )
                            # st.success(f"Downloaded the video with post_id: {video_id}")
                # Download the post metadata
                with col2:
                    if st.download_button(label="Download Post Data",
                                          data=self.save_post_data(df=dataframe,video_id=video_id),
                                          file_name=f'{platform}_{video_id}_post.csv',
                                          mime='text/csv'
                                                   ):
                        st.success(f"Saved the data for the post_id: {video_id}")

                # 2 Tabs for comments and transcripts
                comments_tab,transcripts_tab = st.tabs(["Comments", "Transcripts"],)
                with comments_tab:
                    # st.markdown(
                    #             """
                    #             <style>
                    #             .comments-container {
                    #                 height: 700px;
                    #             }
                    #             </style>
                    #             """,
                    #             unsafe_allow_html=True
                    #         )
                    with st.container(height=700):
                        # st.markdown('<div class="comments-container">', unsafe_allow_html=True)
                        if comments_count ==0:
                            st.write("No Comments")
                        else:
                            if anonymous== True:
                                anonymous_dict = self.create_anonymous_mapping(df=dataframe,
                                                                               video_id=video_id)
                                self.display_comments(video_id,dataframe,anonymous_dict,platform)
                            else:
                                anonymous_dict = {}
                                self.display_comments(video_id,dataframe,anonymous_dict,platform)
                            # self.display_comments(video_id,comments_df)
                        # st.markdown('</div>', unsafe_allow_html=True)
                
                with transcripts_tab:
                    # st.markdown(
                    #             """
                    #             <style>
                    #             .transcripts-container {
                    #                 height: 700px;
                    #             }
                    #             </style>
                    #             """,
                    #             unsafe_allow_html=True ast.literal_eval(sentiment_data)
                    #         )
                    with st.container(height=700):
                        indent = '&ensp;&thinsp;&ensp;&thinsp;'
                        st.markdown(f'{dataframe["transcript_source"][0]}')
                        st.markdown(f'{":speech_balloon:"} :green-background[**German_Sentiment_Score:**] {ast.literal_eval(dataframe["german_sentiment_transcript"][0])[0][0]} {indent} {":speech_balloon:"} :green-background[**Sentiws_Sentiment_Score:**] {dataframe["sentiws_sentiment_transcript"][0]}')
                        # st.markdown('<div class="transcripts-container">', unsafe_allow_html=True)
                        if transcripts is 'No Transcript':
                            st.write_stream(self.stream_data(transcripts + "Need to Implement/Transcribe automatically"))
                        else:
                            st.write(transcripts)
                        # st.markdown('</div>', unsafe_allow_html=True)

            # st.markdown('</div>', unsafe_allow_html=True)

        # st.markdown(
        #             """
        #             <style>
        #             .second-container {
        #                 height: 700px;
        #             }
        #             </style>
        #             """,
        #             unsafe_allow_html=True
        #         )

        second_container = st.container(height=700)
        with second_container:
            # st.markdown('<div class="second-container">', unsafe_allow_html=True)
            col_1,col_2 = st.columns(2)
            
            with col_1:
                st.subheader("Unique Users in Comments",divider='blue')
                with col_1.container(height=600):
                    unique_users = self.count_comments_per_author(comments_df=dataframe,
                                                   video_id=video_id,
                                                   )
            with col_2:
                st.subheader("Unique users in comments",divider='blue')
                self.unique_users_comments_pie_chart(unique_users=unique_users)

                

            # st.markdown('</div>', unsafe_allow_html=True)
        
        return None
    
    
    def download_video(self, video_id, platform, save_path):
        st.warning(f"Downloading the video from {platform}")
        
        if platform.lower() == 'youtube':
            url = f'https://www.youtube.com/watch?v={video_id}'
        elif platform.lower() == 'tiktok':
            url = f'https://www.tiktok.com/@user/video/{video_id}'
        else:
            raise ValueError("Unsupported platform. Use 'youtube' or 'tiktok'.")
        
        os.makedirs(save_path, exist_ok=True)
        video_path = os.path.join(save_path, f'{video_id}.mp4')
        
        # Path to ffmpeg from imageio-ffmpeg
        ffmpeg_path = ffmpeg.get_ffmpeg_exe()
        
        # yt-dlp options for downloading video with audio
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(save_path, f'{video_id}.mp4'),
            'merge_output_format': 'mp4',
            'quiet': True,
            'no_color': True,
            'ffmpeg_location': ffmpeg_path
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            st.success(f"Downloaded the video with post_id: {video_id}")
            return video_path
        except yt_dlp.utils.DownloadError as e:
            st.error(f"Failed to download video ID {video_id} from {platform}: {e}")
            return None
    
    def most_sentiment_comments(self, dataframe, video_id):
        indent = '&ensp;&thinsp;&ensp;&thinsp;'
        comments = dataframe[(dataframe['video_id'] == video_id) & dataframe['author_name'].notna()]
        if comments.empty:
            st.write("No comments available for this video.")
            return
        
        if 'german_sentiment_comments' not in comments.columns or 'sentiws_sentiment_comments' not in comments.columns:
            st.error("Required columns 'german_sentiment_comments' or 'sentiws_sentiment_comments' do not exist in the DataFrame.")
            return
        
        try:
            comments['sentiment_score'] = pd.to_numeric(comments['sentiws_sentiment_comments'], errors='coerce')
            # Drop rows where sentiment_score is NaN due to conversion issues
            comments = comments.dropna(subset=['sentiment_score'])
        except ValueError:
            st.error("Column 'sentiws_sentiment_comments' contains values that cannot be converted to float.")
            return

        if comments.empty:
            st.write("No valid sentiment scores available for this video.")
            return
        
        positive_comments = []
        negative_comments = []
        neutral_comments = []

        for index, row in comments.iterrows():
            
            sentiment_data = ast.literal_eval(row['german_sentiment_comments'])
            sentiment_label = sentiment_data[0][0]
            sentiment_score = row['sentiws_sentiment_comments']

            if sentiment_label == 'positive':
                positive_comments.append((index, sentiment_score, row))
            elif sentiment_label == 'negative':
                negative_comments.append((index, sentiment_score, row))
            elif sentiment_label == 'neutral':
                neutral_comments.append((index, sentiment_score, row))

        if positive_comments:
            # Sort the positive comments based on sentiment_score
            most_positive_comment = max(positive_comments, key=lambda x: x[1])[2]
            st.markdown(
                f":green-background[**Most Positive Comment:**] {indent} :speech_balloon: "
                f"**German Sentiment:** {ast.literal_eval(most_positive_comment['german_sentiment_comments'])[0][0]} {indent} "
                f"**Sentiws_Sentiment:** {most_positive_comment['sentiws_sentiment_comments']} \n\n{most_positive_comment['comment_text']}"
            )
        else:
            st.write("No positive comments available for sentiment analysis.")

        if negative_comments:
            # Sort the negative comments based on sentiment_score (lower score is more negative)
            most_negative_comment = min(negative_comments, key=lambda x: x[1])[2]
            st.markdown(
                f":red-background[**Most Negative Comment:**] {indent} :speech_balloon: "
                f"**German Sentiment:** {ast.literal_eval(most_negative_comment['german_sentiment_comments'])[0][0]} {indent} "
                f"**Sentiws_Sentiment:** {most_negative_comment['sentiws_sentiment_comments']} \n\n{most_negative_comment['comment_text']}"
            )
        else:
            st.write("No negative comments available for sentiment analysis.")



        # Display results using Streamlit
        # st.markdown(
        #     f":green-background[**Most Positive Comment:**] {indent} :speech_balloon:  " 
        #     f"**German Sentiment:** {ast.literal_eval(most_positive_comment['german_sentiment_comments'])[0][0]} {indent} {':speech_balloon:'} **Sentiws_Sentiment:** {most_positive_comment['sentiws_sentiment_comments']} \n\n{most_positive_comment['comment_text']}" 
        # )
        # st.markdown(
        #     f":red-background[**Most Negative Comment:**] {indent} :speech_balloon: "
        #     f"**German Sentiment:** {ast.literal_eval(most_negative_comment['german_sentiment_comments'])[0][0]} {indent} {':speech_balloon:'} **Sentiws_Sentiment:** {most_negative_comment['sentiws_sentiment_comments']} \n\n{most_negative_comment['comment_text']}"
        # )


    def unique_users_comments_pie_chart(self,unique_users):
        # st.markdown(
        #             """
        #             <style>
        #             .unique-container {
        #                 height: 600px;
        #             }
        #             </style>
        #             """,
        #             unsafe_allow_html=True
        #         )
        with st.container(height=600):
                    # st.markdown('<div class="unique-container">', unsafe_allow_html=True)
                    unique_df = unique_users.reset_index()
                    unique_df.columns = ['Author', 'Comment Count']
                    unique_df['percentage'] = (unique_df['Comment Count'] / unique_df['Comment Count'].sum() * 100).round(1)
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=unique_df['Author'],
                        values=unique_df['Comment Count'],
                        textinfo='label+percent+value', 
                        customdata=unique_df[['percentage', 'Comment Count']],
                        hovertemplate='%{label} %{customdata[0]}% - %{value}',  
                        textposition='inside', 
                        hole=0.4,
                        textfont=dict(size=18,color='black')
                    )])

                    fig.update_layout(
                        title=f'Distribution of Unique Users in Comments',
                        annotations=[dict(text='Comments', x=0.5, y=0.5, font_size=20, bgcolor='white',showarrow=False)],
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
                    # st.markdown('</div>', unsafe_allow_html=True)


    def plot_single_post(self,video_id,dataframe,container):
        with container:
            st.success("Plot the results for the dataframe")
    
    def count_comments_per_author(self,comments_df,video_id):
        comments = comments_df[comments_df['video_id'] == video_id]
        # filter out the none values 
        comments = comments[comments['author_name'].notna()]
        # Count comments and replies for each author
        counts = comments['author_name'].value_counts()

        st.write(f":blue-background[**Total users in comments:**] {len(comments['author_name'].unique())}")

        for author, count in counts.items():
            st.write(f"{author}:  💬 {count} ")
        return counts

    def save_post_data(self,df,video_id):
        df = df[df['video_id'] == video_id]
        output = io.StringIO()
        df.to_csv(output, index=False)
        return output.getvalue()
    
    # def eval_safe(self,val):
    #     try:
    #         return eval(val)
    #     except (SyntaxError, NameError):
    #         return None
        
    def eval_safe(self,val):
        try:
            # Check if the value is a string
            if isinstance(val, str):
                return eval(val)
            else:
                # If not a string, return the value as is or handle accordingly
                return val
        except Exception as e:
            # Handle evaluation errors gracefully
            print(f"Error in eval_safe with value {val}: {e}")
            return None 
    
    def create_anonymous_mapping(self,df,video_id):
        comments = df[df['video_id'] == video_id]
        unique_authors = comments['author_name'].unique()
        return {author: f'user{i}' for i, author in enumerate(unique_authors)}
    
    def display_comments(self,video_id,df,anonymous_dict,platform):
        
        if platform == "TikTok" or "Instagram":
            column_name = 'replied_to_comment_id'
            first_nan_index = df[df[column_name].isna()].index[0]
            # Replace all NaNs with 'root', except for the first NaN
            df.loc[df.index != first_nan_index, column_name] = df.loc[df.index != first_nan_index, column_name].fillna('root') 
        
        comments = df[df['video_id'] == video_id]
        
        root_comments = comments[comments['replied_to_comment_id'] == 'root']

        
        for _, comment in root_comments.iterrows():
            self.display_comment(comment,
                                 anonymous_dict
                                 )
            if platform == 'YouTube' or 'TikTok' or 'Instagram':
                self.display_replies(comment['comment_id'],
                                 comments,
                                 anonymous_dict
                                 )

    def display_comment(self,comment,anonymous_dict):
        indent = '&ensp;&thinsp;&ensp;&thinsp;'
        
        # anonymize the comments
        if anonymous_dict == {}:
            author_name = comment['author_name']
        else:
            author_name = comment['author_name']
            author_name = anonymous_dict[author_name]

        sentiment_score = self.eval_safe(comment['german_sentiment_comments'])

        
        if pd.isna(sentiment_score) or type(sentiment_score)==float:
            sentiment_score = 'neutral'
            sentiment_text = ':grey_question:'
        elif sentiment_score[0][0] == 'positive':
            sentiment_text = ':smiley:'
        elif sentiment_score[0][0] == 'negative':
            sentiment_text = ':rage:'
        elif sentiment_score[0][0] == 'neutral':
            sentiment_text = ':neutral_face:'

        st.markdown(f"""
        👤 **{author_name}** {indent}❤️ {int(comment['comment_likes'])} {indent} {':speech_balloon:'} **sentiment_german:** {sentiment_text} {indent} {':speech_balloon:'} **sentiment_sentiws:** {float(comment['sentiws_sentiment_comments'])}
        """)
        st.markdown(f"{indent}{comment['comment_text']}")

    def display_replies(self,comment_id, comments,anonymous_dict):
        replies = comments[comments['replied_to_comment_id'] == comment_id]
        indent = '&ensp;&thinsp;&ensp;&thinsp;'
        

        for _, reply in replies.iterrows():

            sentiment_score = self.eval_safe(reply['german_sentiment_comments'])
           
            if pd.isna(sentiment_score) or type(sentiment_score)==float:
                sentiment_score = 'neutral'
                sentiment_text = ':grey_question:'
            if sentiment_score[0][0] == 'positive':
                sentiment_text = ':smiley:'
            elif sentiment_score[0][0] == 'negative':
                sentiment_text = ':rage:'
            elif sentiment_score[0][0] == 'neutral':
                sentiment_text = ':neutral_face:'

            # anonymize the comments
            if anonymous_dict == {}:
                author_name = reply['author_name']
            else:
                author_name = reply['author_name']
                author_name = anonymous_dict[author_name]

            st.markdown(f"{indent}***Reply***")
            st.markdown(f"""
                {indent} 👤 **{author_name}** {indent}❤️ {int(reply['comment_likes'])} {indent} {':speech_balloon:'} **sentiment_german:** {sentiment_text} {indent} {':speech_balloon:'} **sentiment_sentiws:** {float(reply['sentiws_sentiment_comments'])}
                """)
            st.markdown(f"{indent}{indent}{reply['comment_text']}")
            # self.display_comment(reply, level)
            # self.display_replies(reply['comment_id'], comments,anonymous_dict)
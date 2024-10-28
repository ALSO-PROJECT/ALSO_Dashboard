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

class SocialMedia():

    def __init__(self) -> None:
        pass

    def stream_data(self,text):
        for word in text.split(" "):
            yield word + " "
            time.sleep(0.02)

    def display_reconstructed_page(self,row_idx,dataframe):

        # Hide this until user clicks on the data
        platform = str(dataframe['platform'][row_idx])
        title = str(dataframe['title'][row_idx])
        description = str(dataframe['video_description'][row_idx])
        video_url = str(dataframe['original_url'][row_idx])
        views_count = str(dataframe['views_count'][row_idx])
        likes_count = str(dataframe['like_count'][row_idx])
        
        comments_count = int(dataframe['comments_count'][row_idx]) 
        subscribers_count = str(dataframe['subscribers_count'][row_idx])
        transcripts = dataframe['transcript_german'][row_idx]

        # Date upload/extracted
        date_uploaded = dataframe['upload_date'][row_idx].date()
        date_extracted = dataframe['extracted_date'][row_idx].date()
        video_id = dataframe['video_id'][row_idx]

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

        main_container = st.container(1000)
        with main_container:
            # st.markdown('<div class="reconstructed-page-container">', unsafe_allow_html=True)
            media_col,desc_col = st.columns(2,gap='medium')
            with media_col:
                st.video(video_url,
                    loop=False,
                    autoplay=False,
                    muted=False,
                    format="video/mp4",
                    )
                
                st.markdown(f"**Post Url :** {dataframe['original_url'][row_idx]}")
                colu1,colu2 = st.columns(2)
                with colu1.container(height=600):
                    st.subheader("Most Positive/Negative Comments",divider='blue')
                    self.most_sentiment_comments(dataframe,video_id)
                with colu2.container(height=600):
                    st.subheader("Unique Users in Comments",divider='blue')
                    unique_users = self.count_comments_per_author(comments_df=dataframe,
                                                   video_id=video_id,
                                                   )
                
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
                with st.container(300):
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
                    video_duration = col2.markdown(f"\n**Video Duration:** {dataframe['video_duration'][row_idx]} sec")
                elif platform =='YouTube':
                    video_duration = col2.markdown(f"\n**Video Duration:** {dataframe['video_duration'][row_idx]}")
                elif platform == 'Instagram':
                    video_duration = col2.markdown(f"\n**Video Duration:** {dataframe['video_duration'][row_idx]} sec")
                col2.write("   ")
                
                # Analyze the post
                with col1:
                    if st.button(label="Analyze Post"):
                        self.plot_single_post(video_id,dataframe,main_container)
                        st.success(f"Results Ploted for the post_id: {video_id}")
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
                    with st.container(700):
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
                    #             unsafe_allow_html=True
                    #         )
                    with st.container(700):
                        # st.markdown('<div class="transcripts-container">', unsafe_allow_html=True)
                        if transcripts is 'No Transcript':
                            st.write_stream(self.stream_data(transcripts + "Need to Implement/Transcribe automatically"))
                        else:
                            st.write(transcripts)
                        st.markdown('</div>', unsafe_allow_html=True)

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

        second_container = st.container(700)
        with second_container:
            # st.markdown('<div class="second-container">', unsafe_allow_html=True)
            col_1,col_2 = st.columns(2)
            with col_1:
                st.subheader("Unique users in comments",divider='blue')
                self.unique_users_comments_pie_chart(unique_users=unique_users)


            with col_2:
                st.container()

            # st.markdown('</div>', unsafe_allow_html=True)
        
        return None

    def most_sentiment_comments(self,dataframe,video_id):
        
        indent = '&ensp;&thinsp;&ensp;&thinsp;'

        comments = dataframe[dataframe['video_id'] == video_id]
        comments = comments[comments['author_name'].notna()]

        if comments.empty:
            st.write("No comments available for this video.")
            return
        
        if 'sentiws_sentiment_comments' not in comments.columns:
            st.error("Column 'sentiws_sentiment_comments' does not exist in the DataFrame.")
            return
        
        if comments['sentiws_sentiment_comments'].dtype == 'object':
            try:
                comments['sentiment_score'] = comments['sentiws_sentiment_comments'].astype(float)
            except ValueError:
                st.error("Column 'sentiws_sentiment_comments' contains non-numeric values that cannot be converted to float.")
                return
        else:
            comments['sentiment_score'] = comments['sentiws_sentiment_comments']

        most_positive_comment = comments.loc[comments['sentiment_score'].idxmax()]
        most_negative_comment = comments.loc[comments['sentiment_score'].idxmin()]
        
        comments['sentiment_score'] = comments['sentiws_sentiment_comments']

        most_positive_comment = comments.loc[comments['sentiment_score'].idxmax()]
        most_negative_comment = comments.loc[comments['sentiment_score'].idxmin()]

        st.markdown(f" :green-background[**Most Positive Comment:**]{indent} {':speech_balloon:'} **sentiment_score:** {most_positive_comment['sentiment_score']} \n\n{most_positive_comment['comment_text']}")
        st.markdown(f" :red-background[**Most Negative Comment:**]{indent} {':speech_balloon:'} **sentiment_score:** {most_negative_comment['sentiment_score']} \n\n{most_negative_comment['comment_text']}")


    def unique_users_comments_pie_chart(self,unique_users):
        st.markdown(
                    """
                    <style>
                    .unique-container {
                        height: 600px;
                    }
                    </style>
                    """,
                    unsafe_allow_html=True
                )
        with st.container():
                    st.markdown('<div class="unique-container">', unsafe_allow_html=True)
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
                    st.markdown('</div>', unsafe_allow_html=True)


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
    
    def eval_safe(self,val):
        try:
            return eval(val)
        except (SyntaxError, NameError):
            return None 
    
    def create_anonymous_mapping(self,df,video_id):
        comments = df[df['video_id'] == video_id]
        unique_authors = comments['author_name'].unique()
        return {author: f'user{i}' for i, author in enumerate(unique_authors)}
    
    def display_comments(self,video_id,df,anonymous_dict,platform):
        comments = df[df['video_id'] == video_id]
        root_comments = comments[comments['replied_to_comment_id'] == 'root']

        for _, comment in root_comments.iterrows():
            self.display_comment(comment,
                                 anonymous_dict
                                 )
            if platform == 'YouTube':
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
        if sentiment_score[0][0] == 'positive':
            sentiment_text = ':smiley:'
        elif sentiment_score[0][0] == 'negative':
            sentiment_text = ':rage:'
        elif sentiment_score[0][0] == 'neutral':
            sentiment_text = ':neutral_face:'
        
        st.markdown(f"""
        👤 **{author_name}** {indent}❤️ {int(comment['comment_likes'])} {indent} {':speech_balloon:'} **sentiment_german:** {sentiment_text} **sentiment_sentiws:** {float(comment['sentiws_sentiment_comments'])}
        """)
        st.markdown(f"{indent}{comment['comment_text']}")

    def display_replies(self,comment_id, comments,anonymous_dict):
        replies = comments[comments['replied_to_comment_id'] == comment_id]
        indent = '&ensp;&thinsp;&ensp;&thinsp;'
        

        for _, reply in replies.iterrows():

            sentiment_score = self.eval_safe(reply['german_sentiment_comments'])
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
                {indent} 👤 **{author_name}** {indent}❤️ {int(reply['comment_likes'])} {indent} {':speech_balloon:'} **sentiment_german:** {sentiment_text} **sentiment_sentiws:** {float(reply['sentiws_sentiment_comments'])}
                """)
            st.markdown(f"{indent}{indent}{reply['comment_text']}")
            # self.display_comment(reply, level)
            self.display_replies(reply['comment_id'], comments,anonymous_dict)
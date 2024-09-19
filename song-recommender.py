import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import sqlite3
from datetime import datetime
import cachetools
from spotipy.exceptions import SpotifyException
import time
import plotly.graph_objects as go

# Spotify renk teması için özel CSS
st.markdown("""
<style>
    /* Ana renk (yeşil) */
    .stButton>button {
        color: #FFFFFF;
        background-color: #1DB954;
        border-color: #1DB954;
    }
    .stButton>button:hover {
        background-color: #1ED760;
        border-color: #1ED760;
    }
    
    /* Başlıklar için siyah renk */
    h1, h2, h3, h4, h5, h6 {
        color: #191414;
    }
    
    /* Linkler için yeşil renk */
    a {
        color: #1DB954;
    }
    a:hover {
        color: #1ED760;
    }
    
    /* Sidebar için koyu arka plan */
    .css-1d391kg {
        background-color: #191414;
    }
    
    /* Sidebar yazıları için beyaz renk */
    .css-1d391kg .stSelectbox label, .css-1d391kg .stTextInput label {
        color: #FFFFFF;
    }
    
    /* Ana içerik için beyaz arka plan */
    .main .block-container {
        background-color: #FFFFFF;
    }
    
    /* Expander başlıkları için yeşil renk */
    .streamlit-expanderHeader {
        background-color: #1DB954;
        color: #FFFFFF;
    }
    
    /* Tablo başlıkları için siyah arka plan, beyaz yazı */
    thead tr th {
        background-color: #191414;
        color: #FFFFFF !important;
    }
    
    /* Tablo hücrelerindeki yazıları siyah yap */
    tbody tr td {
        color: #191414;
    }
    
    /* Tablo satırları için alternatif renklendirme */
    tbody tr:nth-child(even) {
        background-color: #F0F0F0;
    }
</style>
""", unsafe_allow_html=True)

# Spotify API credentials
SPOTIPY_CLIENT_ID = 'e1904f20bafe49cfb2d6da08edc42c14'
SPOTIPY_CLIENT_SECRET = '2d3288183a6e43699eab642da0b5d08e'
SPOTIPY_REDIRECT_URI = 'http://localhost:8501/'

# Spotify OAuth
scope = "user-library-read user-top-read playlist-modify-public"

# Streamlit app
st.title('Spotify Playlist Analyzer')
st.write("Welcome to Spotify Playlist Analyzer! Explore your music taste and discover new tracks.")

# Session state to keep track of the authentication status
if 'auth_manager' not in st.session_state:
    st.session_state.auth_manager = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope,
        cache_path=None,
        show_dialog=True
    )

if 'token_info' not in st.session_state:
    st.session_state.token_info = None

# Authentication
if st.session_state.token_info is None:
    # Check if code is in url parameters
    if "code" in st.query_params:
        code = st.query_params["code"]
        try:
            st.session_state.token_info = st.session_state.auth_manager.get_access_token(code)
        except Exception as e:
            st.error(f"Error during authentication: {e}")
    else:
        auth_url = st.session_state.auth_manager.get_authorize_url()
        st.write(f'Please click [here]({auth_url}) to authorize this application.')
        st.write("After authorizing, you'll be redirected back to this app automatically.")

if st.session_state.token_info:
    if st.session_state.auth_manager.is_token_expired(st.session_state.token_info):
        try:
            st.session_state.token_info = st.session_state.auth_manager.refresh_access_token(st.session_state.token_info['refresh_token'])
        except Exception as e:
            st.error(f"Error refreshing token: {e}")
            st.session_state.token_info = None

    if st.session_state.token_info:
        sp = spotipy.Spotify(auth=st.session_state.token_info['access_token'])
        
        try:
            user = sp.current_user()
            st.write(f"Welcome, {user['display_name']}!")
            
            # Veritabanı bağlantısını oluştur
            conn = sqlite3.connect('spotify_users.db')
            c = conn.cursor()

            # Kullanıcılar tablosunu oluştur (eğer yoksa)
            c.execute('''CREATE TABLE IF NOT EXISTS users
                         (id TEXT PRIMARY KEY, display_name TEXT, email TEXT, last_login DATETIME)''')
            conn.commit()

            # Kullanıcıyı veritabanına kaydet veya güncelle
            c.execute('''INSERT OR REPLACE INTO users (id, display_name, email, last_login) 
                         VALUES (?, ?, ?, ?)''', 
                      (user['id'], user['display_name'], user.get('email', ''), datetime.now()))
            conn.commit()
            
            # Kullanıcının playlist'lerini çek
            playlists = sp.current_user_playlists()
            playlist_names = [''] + [playlist['name'] for playlist in playlists['items']]
            
            # Top Artists section
            st.header("Your Top Artists")
            top_artists = sp.current_user_top_artists(limit=10, time_range='short_term')

            col1, col2 = st.columns(2)

            with col1:
                # Create table for top artists
                artist_data = [{"Rank": i+1, "Artist": artist['name'], "Followers": artist['followers']['total']} 
                               for i, artist in enumerate(top_artists['items'])]
                df_top_artists = pd.DataFrame(artist_data)
                st.table(df_top_artists.set_index('Rank'))

            with col2:
                # Create bar chart for top artists based on popularity
                fig_artists = go.Figure(go.Bar(
                    x=[artist['name'] for artist in top_artists['items']],
                    y=[artist['popularity'] for artist in top_artists['items']],
                    marker_color='rgba(50, 171, 96, 0.7)',
                ))
                fig_artists.update_layout(
                    title='Your Top Artists (Based on Popularity)',
                    xaxis_title='Artist',
                    yaxis_title='Popularity',
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_artists, use_container_width=True)

            # Top Tracks section
            st.header("Your Top Tracks")
            top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')

            col1, col2 = st.columns(2)

            with col1:
                # Create table for top tracks
                track_data = [{"Rank": i+1, "Track": track['name'], "Artist": track['artists'][0]['name']} 
                              for i, track in enumerate(top_tracks['items'])]
                df_top_tracks = pd.DataFrame(track_data)
                st.table(df_top_tracks.set_index('Rank'))

            with col2:
                # Create bar chart for top tracks based on popularity
                fig_tracks = go.Figure(go.Bar(
                    x=[track['name'] for track in top_tracks['items']],
                    y=[track['popularity'] for track in top_tracks['items']],
                    marker_color='rgba(171, 50, 96, 0.7)',
                ))
                fig_tracks.update_layout(
                    title='Your Top Tracks (Based on Popularity)',
                    xaxis_title='Track',
                    yaxis_title='Popularity',
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig_tracks, use_container_width=True)

            # Genre distribution for top tracks
            st.header("Genre Distribution of Your Top Tracks")
            genres = []
            for track in top_tracks['items']:
                artist_id = track['artists'][0]['id']
                artist_info = sp.artist(artist_id)
                genres.extend(artist_info['genres'])

            genre_counts = pd.Series(genres).value_counts()

            fig_genres = px.pie(
                values=genre_counts.values,
                names=genre_counts.index,
                title='Genre Distribution of Top Tracks'
            )
            fig_genres.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_genres, use_container_width=True)

            # Sidebar'da sekmeler oluşturma
            st.sidebar.title("More Options")
            tab = st.sidebar.radio("Select an option:", 
                ["Analyze Playlist", "Add Track to Playlist", "Recommended Tracks", 
                 "Recommended Playlists", "Create New Playlist"])

            # Seçilen sekmeye göre içerik gösterme
            if tab == "Analyze Playlist":
                st.header("Analyze a Playlist")
                selected_playlist = st.selectbox('Select a Playlist', playlist_names)
                if selected_playlist:
                    if st.button('Analyze Playlist'):
                        try:
                            playlist_id = next((playlist['id'] for playlist in playlists['items'] if playlist['name'] == selected_playlist), None)
                            if playlist_id is None:
                                st.error(f"Playlist '{selected_playlist}' not found.")
                            else:
                                playlist_tracks = sp.playlist_tracks(playlist_id)
                                if not playlist_tracks or 'items' not in playlist_tracks:
                                    st.warning("No tracks found in the playlist.")
                                else:
                                    genres = []
                                    track_names = []
                                    artist_names = []
                                    popularities = []
                                    energies = []

                                    for track in playlist_tracks['items']:
                                        if track['track'] and 'artists' in track['track'] and track['track']['artists']:
                                            artist_id = track['track']['artists'][0]['id']
                                            artist_info = sp.artist(artist_id)
                                            if artist_info and 'genres' in artist_info:
                                                genres.extend(artist_info['genres'])
                                            
                                            track_names.append(track['track']['name'])
                                            artist_names.append(track['track']['artists'][0]['name'])
                                            popularities.append(track['track']['popularity'])
                                            
                                            # Get audio features for energy
                                            audio_features = sp.audio_features(track['track']['id'])[0]
                                            if audio_features and 'energy' in audio_features:
                                                energies.append(audio_features['energy'])

                                    # Genre Distribution
                                    if genres:
                                        genre_counts = pd.Series(genres).value_counts()
                                        fig_genres = px.pie(
                                            values=genre_counts.values,
                                            names=genre_counts.index,
                                            title='Genre Distribution of Playlist'
                                        )
                                        fig_genres.update_traces(textposition='inside', textinfo='percent+label')
                                        st.plotly_chart(fig_genres, use_container_width=True)
                                    else:
                                        st.warning("No genre information available for this playlist.")

                                    # Optional additional analyses
                                    if st.checkbox("Show More Analyses"):
                                        # Popularity vs Energy Scatter Plot
                                        if popularities and energies:
                                            fig_scatter = px.scatter(
                                                x=popularities,
                                                y=energies,
                                                hover_name=track_names,
                                                labels={'x': 'Popularity', 'y': 'Energy'},
                                                title='Popularity vs Energy'
                                            )
                                            st.plotly_chart(fig_scatter, use_container_width=True)
                                        
                                        # Artist Distribution
                                        artist_counts = pd.Series(artist_names).value_counts()
                                        fig_artists = px.bar(
                                            x=artist_counts.index,
                                            y=artist_counts.values,
                                            labels={'x': 'Artist', 'y': 'Number of Tracks'},
                                            title='Artist Distribution in Playlist'
                                        )
                                        fig_artists.update_layout(xaxis_tickangle=-45)
                                        st.plotly_chart(fig_artists, use_container_width=True)
                                        
                                        # Popularity Distribution
                                        fig_popularity = px.histogram(
                                            x=popularities,
                                            nbins=20,
                                            labels={'x': 'Popularity', 'y': 'Number of Tracks'},
                                            title='Popularity Distribution of Tracks'
                                        )
                                        st.plotly_chart(fig_popularity, use_container_width=True)

                        except Exception as e:
                            st.error(f"Error analyzing playlist: {str(e)}")
                else:
                    st.info("Please select a playlist to analyze.")

            elif tab == "Add Track to Playlist":
                st.header("Add a Track to a Playlist")
                selected_playlist_to_add = st.selectbox('Select a Playlist to Add Track', playlist_names)
                if selected_playlist_to_add:
                    track_name_to_add = st.text_input('Track Name to Add')
                    if track_name_to_add and st.button('Add Track'):
                        try:
                            # Search for the track
                            results = sp.search(q=track_name_to_add, limit=1, type='track')
                            if results['tracks']['items']:
                                track_id = results['tracks']['items'][0]['id']
                                playlist_id_to_add = next(playlist['id'] for playlist in playlists['items'] if playlist['name'] == selected_playlist_to_add)
                                sp.user_playlist_add_tracks(user=sp.current_user()['id'], playlist_id=playlist_id_to_add, tracks=[track_id])
                                st.success(f'Track "{track_name_to_add}" added to playlist "{selected_playlist_to_add}" successfully!')
                            else:
                                st.error(f'Track "{track_name_to_add}" not found.')
                        except Exception as e:
                            st.error(f"Error adding track to playlist: {e}")
                else:
                    st.info("Please select a playlist to add a track.")

            elif tab == "Recommended Tracks":
                st.header("Recommended Tracks")
                try:
                    top_track_ids = [track['id'] for track in top_tracks['items']]
                    track_recommendations = sp.recommendations(seed_tracks=top_track_ids[:5], limit=15)
                    track_recommended_tracks = [{
                        'Track Name': track['name'],
                        'Artist': track['artists'][0]['name']
                    } for track in track_recommendations['tracks']]

                    st.subheader('Playlist Based on Your Top Tracks')
                    df_track_recommended_tracks = pd.DataFrame(track_recommended_tracks)
                    st.table(df_track_recommended_tracks)
                except Exception as e:
                    st.error(f"Error fetching recommendations based on top tracks: {e}")

            elif tab == "Recommended Playlists":
                st.header("Recommended Playlists")
                try:
                    top_artist_ids = [artist['id'] for artist in top_artists['items']]
                    artist_recommendations = sp.recommendations(seed_artists=top_artist_ids[:5], limit=15)
                    artist_recommended_tracks = [{
                        'Track Name': track['name'],
                        'Artist': track['artists'][0]['name']
                    } for track in artist_recommendations['tracks']]

                    st.subheader('Playlist Based on Your Top Artists')
                    df_artist_recommended_tracks = pd.DataFrame(artist_recommended_tracks)
                    st.table(df_artist_recommended_tracks)
                except Exception as e:
                    st.error(f"Error fetching recommendations based on top artists: {e}")

            elif tab == "Create New Playlist":
                st.header("Create a New Playlist")
                playlist_name = st.text_input('Playlist Name')
                if playlist_name and st.button('Create Playlist'):
                    try:
                        user_id = sp.current_user()['id']
                        
                        # Mevcut playlist'leri kontrol et
                        existing_playlists = sp.user_playlists(user_id)
                        playlist_exists = any(playlist['name'].lower() == playlist_name.lower() for playlist in existing_playlists['items'])
                        
                        if playlist_exists:
                            st.warning(f"A playlist named '{playlist_name}' already exists. Are you sure you want to create another one?")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button('Yes, create anyway'):
                                    new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name)
                                    st.success(f'Playlist "{playlist_name}" created successfully!')
                                    st.session_state.new_playlist_id = new_playlist['id']
                                    st.session_state.new_playlist_name = playlist_name
                            with col2:
                                if st.button('No, cancel'):
                                    st.info('Playlist creation cancelled.')
                        else:
                            new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name)
                            st.success(f'Playlist "{playlist_name}" created successfully!')
                            st.session_state.new_playlist_id = new_playlist['id']
                            st.session_state.new_playlist_name = playlist_name
                    except Exception as e:
                        st.error(f"Error creating playlist: {e}")
                
                # Yeni oluşturulan playlist'e şarkı ekleme özelliği
                if 'new_playlist_id' in st.session_state:
                    st.subheader(f'Add Tracks to "{st.session_state.new_playlist_name}"')
                    track_to_add = st.text_input('Enter Track Name')
                    if track_to_add and st.button('Add Track to New Playlist'):
                        try:
                            # Search for the track
                            results = sp.search(q=track_to_add, limit=1, type='track')
                            if results['tracks']['items']:
                                track_id = results['tracks']['items'][0]['id']
                                sp.user_playlist_add_tracks(user=user_id, playlist_id=st.session_state.new_playlist_id, tracks=[track_id])
                                st.success(f'Track "{track_to_add}" added to playlist "{st.session_state.new_playlist_name}" successfully!')
                            else:
                                st.error(f'Track "{track_to_add}" not found.')
                        except Exception as e:
                            st.error(f"Error adding track to new playlist: {e}")

            # Admin paneli
            if st.sidebar.checkbox("Show Admin Panel"):
                admin_password = st.sidebar.text_input("Admin Password", type="password")
                if admin_password == "1234":  # Güvenli bir şifre belirleyin
                    st.sidebar.subheader("User Database")
                    c.execute("SELECT * FROM users")
                    users = c.fetchall()
                    if users:
                        df_users = pd.DataFrame(users, columns=['ID', 'Display Name', 'Email', 'Last Login'])
                        st.sidebar.dataframe(df_users)
                    else:
                        st.sidebar.write("No users in the database.")
                else:
                    st.sidebar.error("Incorrect password")

        except Exception as e:
            st.error(f"Error fetching user data: {e}")

        # Uygulama sonunda veritabanı bağlantısını kapat
        conn.close()

else:
    st.warning("Please authenticate to use this application.")
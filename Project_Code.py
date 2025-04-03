import streamlit as st
import sqlite3
import pandas as pd
import bcrypt
import hashlib
from datetime import datetime
import os
import matplotlib.pyplot as plt
import seaborn as sns
import re

def main():
    # extend main page to wide layout
    st.set_page_config(page_title="Track Finder", layout="wide")
    
    # style templates for the whole page
    st.markdown("""
    <style>
    /* General background */
    body {
        background-color: #E8F5E9;
    }

    /* App-background */
    .stApp {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
    }

    /* Header-Box */
    .header-box {
        background-color: #4CAF50;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Frame for Expander */
    .st-expander {
        border: 2px solid #4CAF50;
        border-radius: 10px;
        margin-bottom: 20px;
    }

    /* Buttons */
    div.stButton > button {
        background-color: #4CAF50;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #D1FFD1;
    }

    /* Table-Styling */
    .dataframe {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        margin-top: 20px;
        background-color: #FAF3E0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # All important variables are checked if they exist in session_state. If not they are initialised
    # Initialisation of Session-States, all important variables are checked if they exist in session_state. If not they are initialised
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = ""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = ""
    if 'show_legend' not in st.session_state:
        st.session_state.show_legend = False
    if 'expander_opened' not in st.session_state:
        st.session_state.expander_opened = False  # initialisation of expander_opened
    # Initialize session state
    if 'sidebar_open' not in st.session_state:
        st.session_state.sidebar_open = False

#***************************************************************
# 1. Preparation and formatting
#***************************************************************  

    # pages for the navigator
    pages = ["Your Songs", "Search", "Filter by Audio Features", "Find New Songs"]


    # Creation of 3 columns, both at the end are for the frame, to centralize the picture
    col1, col2, col3 = st.columns([2, 8, 2])
     
    # Import spotify logo
    # Centralize picture with HTML und CSS
    st.markdown("""
    <div style="text-align: center;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/7/71/Spotify.png" alt="Spotify Logo" width="220">
    </div>
    """, unsafe_allow_html=True)
    
    # To create a distance between the Logo and the boxes
    st.write("")
    
    with col2:
    
        # Header-box frontpage with html
        st.markdown("""
            <div class="header-box">
                <h1>🎵 Welcome to Track Finder!</h1>
                <p>Discover, analyze, and create playlists tailored to your taste.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Text boxes frontpage      
    with col1:
        st.markdown("""
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 15px; margin-bottom: 20px;">
            <h2 style="color: #333; font-size: 24px; margin-bottom: 8px;">🔍 Discover</h2>
            <p style="font-size: 16px; color: #555;">
            Find music that matches your style.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div style="background-color: #f0f0f0; padding: 15px; border-radius: 15px; margin-bottom: 25px;">
            <h2 style="color: #333; font-size: 24px; margin-bottom: 8px;">Analyze 📈</h2>
            <p style="font-size: 16px; color: #555;">
            Understand your audio preferences.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Text on starting page is only shown as long as the user is not logged in. After Log in the textbox disappears.
    if not st.session_state.logged_in:    
        st.markdown("""
        <div style="background-color: #D1FFD1; padding: 15px; border-radius: 10px; text-align: center; font-size: 22px;">
            Discover your perfect playlist! <br>
            Select the songs you love and let us create a personalized playlist just for you.<br>
            Dive into a new world of music tailored to your taste.<br>
            <b style="font-size: 24px;">Try it out today!</b>
        </div>
        """, unsafe_allow_html=True)
    
    # To create a distance between the boxes
    st.write("")

    # Message "Sign in" disappears after the user has logged in and the sidebar has been opened     
    # Redirects user to Login sidebar
    if not st.session_state.sidebar_open:
        st.info("**Please log in to continue**")
        if st.button("Sign in"):
            st.session_state.sidebar_open = True
            
#*******************************************************************************************************          
# 2. Dataframe and database preparation/creation
#*******************************************************************************************************

    # Definition of the path of the actual script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    songs_dir = os.path.join(script_dir, "songs")

    # Ensure that "songs" directory exists
    if not os.path.exists(songs_dir):
        os.makedirs(songs_dir)
        
    # Reads the csv-file and loads the data
    file_name_spotify_songs = os.path.join(script_dir, "spotify_songs.csv") #spotify_songs is the spotify dataframe
    df = pd.read_csv(file_name_spotify_songs)

    # Creation of the main database 'users.db' of the user 
    file_name_users = os.path.join(script_dir, "users.db")
    conn_users = sqlite3.connect(file_name_users)
    c_users = conn_users.cursor()
    c_users.execute('''CREATE TABLE IF NOT EXISTS users (user_id TEXT PRIMARY KEY, username TEXT, password TEXT)''') #new registration
    conn_users.commit()
    
    # Function to create the Users database 'user.db and to import and apply songs
    def create_user_database(user_id):
        user_db_path = os.path.join(songs_dir, f"{user_id}.db")
        conn_user_db = sqlite3.connect(user_db_path)
        df.to_sql('user_songs', conn_user_db, if_exists='replace', index=False)
        cursor = conn_user_db.cursor()
        cursor.execute("DELETE FROM user_songs;")
        conn_user_db.commit()
        conn_user_db.close()

    # creation of the database and saving a pandas dataframe into an SQL database
    def save_csv_to_database(df):
        songs_db_path = os.path.join(script_dir, "spotify_songs.db") #creates the file path SQL Database
        conn_songs_db = sqlite3.connect(songs_db_path)
        df.to_sql('spotify_songs', conn_songs_db, if_exists='replace', index=False)
        conn_songs_db.commit()
        conn_songs_db.close()
    
#**********************************************************
# 3. Login process and defining functions
#**********************************************************

    # Hash-function, creation and storing of the password 
    def hash_password(password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def check_password(password, hashed):
        return bcrypt.checkpw(password.encode('utf-8'), hashed)

    # Function that creates an User-ID to new registrated Users
    def generate_user_id(username):
        timestamp = datetime.now().strftime("%H%M%S")  # User ID based on second, minute and hour of first registration
        data = f"{username}{timestamp}"
        user_hash = hashlib.md5(data.encode()).hexdigest()[:5]  # Shortens the hash to 5 characters
        return user_hash

    # Function to check password safety
    def check_password_strength(password):
    # Conditions for a strong password:
    # 1. At least 8 characters
    # 2. At least one uppercase letter
    # 3. At least one lowercase letter
    # 4. At least one number
        #re librarie checks if the password meets the conditions
        if len(password) < 8:
            return "Weak", "The password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return "Weak", "The password must contain at least one uppercase letter."
        if not re.search(r"[a-z]", password):
            return "Weak", "The password must contain at least one lowercase letter."
        if not re.search(r"[0-9]", password):
            return "Weak", "The password must contain at least one number."
        
        return "Strong", "The password is strong!"

    # Function for registration of first-time users
    def register_user(username, password):
        if user_exists(username):
            st.warning("Username already exists!")
        else:
            user_id = generate_user_id(username)
            hashed_password = hash_password(password)
            c_users.execute("INSERT INTO users (user_id, username, password) VALUES (?, ?, ?)", 
                            (user_id, username, hashed_password))
            conn_users.commit()

            # Create a customised user database, next time the User logs in, his username and password are saved
            create_user_database(user_id)

            st.success(f"Registration successful! Your user-ID is: {user_id}. Login now!")

    # Function checks whether user exists
    def user_exists(username):
        c_users.execute("SELECT * FROM users WHERE username = ?", (username,))
        return c_users.fetchone()

    # Check if username and password are already registrated
    def login_user(username, password):
        c_users.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c_users.fetchone()
        if user and check_password(password, user[2]):
            st.session_state.user_id = user[0]  # user_id is saved in st.session_state
            return user[0]  # Returns the user_id
        return None
    
    # Access to the user's database (Personal Songs)
    def load_user_db():
        user_db_path = os.path.join(songs_dir, f"{st.session_state.user_id}.db")
        conn_user_db = sqlite3.connect(user_db_path)

        query_playlist_overview = """
        SELECT DISTINCT 
            playlist_name,
            track_name,
            track_artist,
            track_album_name,
            playlist_genre, 
            playlist_subgenre
        FROM user_songs
        """

        user_songs_df_overview = pd.read_sql_query(query_playlist_overview, conn_user_db)
        conn_user_db.close()
        return user_songs_df_overview

    # Opens sidebar if Sign in Button has been clicked
    if st.session_state.sidebar_open:
        st.sidebar.title("Login & Registration")

        # User chooses to log in or to registrate
        with st.sidebar:
            if not st.session_state.logged_in:
                option = st.selectbox("Choose an action:", ["Login", "Registration"])
    
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")

                if option == "Registration":
                    strength, message = None, None  # Initialisierung der Variablen
                    if username and password:
                        # Checks if the password is strong 
                        strength, message = check_password_strength(password) #conditions from above
                    if strength == "Weak":
                        st.error(f"Weak password: {message}")
                    else:
                        if st.button("Registration"): 
                            register_user(username, password)
                        else:
                            st.warning("Bitte Benutzername und Passwort eingeben.")
                elif option == "Login":
                    if st.button("Login"):
                        user_id = login_user(username, password)
                        if user_id:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.session_state.user_id = user_id
                            st.success(f"Welcome, {username}!")
                        else:
                            st.error("Incorrect user name or password.")
            else:
                st.sidebar.success(f"Logged in as: {st.session_state.username}")
                st.sidebar.write(f"Your user-ID: {st.session_state.user_id}")
                st.sidebar.button("Logout", on_click=lambda: st.session_state.update({"logged_in": False, "username": "", "user_id": "", "show_legend": False}))

 #*****************************************************************        
 # 4. Individual Database
 #*****************************************************************  

    # Show user database after successful login (only a small part)
    # This list is empty in the beggining
    if st.session_state.logged_in:
        # Sidebar-Navigation und initialisation
        st.sidebar.title("Navigation")
        selected_page = st.sidebar.radio("Go to", pages)
        if selected_page == "Your Songs":
            # Hauptseiten basierend auf der Auswahl
            st.subheader("Songs picked for you:")
            

            # Access to the user's database / connection
            user_db_path = os.path.join(songs_dir, f"{st.session_state.user_id}.db")
            conn_user_db = sqlite3.connect(user_db_path)        

            # Check if user_id is set in session state
            if 'user_id' not in st.session_state:
                st.session_state.user_id = 'default_user'  # Replace with your default user logic

            # Initial load and sort of displayed dataframe
            user_songs_df_overview = load_user_db()
            # Sort the data (e.g., by playlist_id or timestamp column)
            if "playlist_subgenre" in user_songs_df_overview.columns:
                user_songs_df_overview = user_songs_df_overview.sort_values(by="playlist_subgenre", ascending=False)

            # Display the data and add a refresh button, the new songs appear in the list.
            if st.button("Refresh"):
                user_songs_df_overview = load_user_db()
                if "playlist_subgenre" in user_songs_df_overview.columns:
                    user_songs_df_overview = user_songs_df_overview.sort_values(by="playlist_subgenre", ascending=False)
                st.success("Database refreshed!")

            # Displays user data
            st.dataframe(user_songs_df_overview, use_container_width=True, height=400)
            st.info("Discover more songs that you could like!")

            # Saves songs to the users database
            save_csv_to_database(df)
            songs_db_path = os.path.join(script_dir, "spotify_songs.db")
            conn_songs_db = sqlite3.connect(songs_db_path)
        
#************************************************************************        
#5. Dynamik search feature (search by track_name, playlist_name & artist_name)
#************************************************************************  
    
        
        elif selected_page == "Search":
            # initialize connection
            songs_db_path = os.path.join(script_dir, "spotify_songs.db")
            conn_songs_db = sqlite3.connect(songs_db_path)

            # Expander which stays open and doesn't need to be openend
            st.header("Search songs")
            with st.expander("Open to see more", expanded= True):
                st.write("Get inspired by searching songs by artist, name or genre!")
        

                # Add dynamik search-option
                search_column_1 = st.selectbox("Search for:", ["track_artist", "track_name", "playlist_genre"], key="search_column_1")
                search_query_1 = st.text_input(f"Please insert {search_column_1}:", key="search_query_1")
                        
                
                # Show results of the search
                if search_query_1:
                    query_playlist_search_1 = f"""SELECT DISTINCT playlist_name, track_artist, track_name, danceability, energy, loudness, speechiness, 
                    instrumentalness, liveness, valence, tempo, duration_ms FROM spotify_songs WHERE {search_column_1} LIKE ?"""
                    spotify_songs_df_search_1 = pd.read_sql_query(query_playlist_search_1, conn_songs_db, params=(f"%{search_query_1}%",))
                    if not spotify_songs_df_search_1.empty:
                        # Show results if songs were found
                        st.dataframe(spotify_songs_df_search_1, use_container_width=True, height=400)             
                    else:
                    # Display message if no hits are available
                        st.warning("No match found. Try another entry.")
                        
                    # Show legend button after successful search
                    if st.button("Explanation of the Audio Features", key="audio_features"):
                        st.session_state.show_legend = not st.session_state.show_legend

                    # Show description if legend is activated
                    if st.session_state.show_legend:
                        st.markdown("""
                        ### Danceability
                        Indicates how suitable a track is for dancing. It is based on a combination of elements such as tempo, rhythm stability, beat strength and overall rhythm.   
                        **Scale:** 0.0 to 1.0 (higher value = more danceable).

                        ### Energy
                        Indicates the level of intensity and activity of a track. Tracks with high energy have a fast tempo, a strong beat and loud instruments.    
                        **Scale:** 0.0 to 1.0 (higher value = more energetic).

                        ### Valence
                        Indicates the musical positivity of a track. Tracks with a high valence sound cheerful, happy and euphoric.   
                        **Scale:** 0.0 to 1.0 (higher value = more positive).

                        ### Tempo
                        The estimated tempo of the track in beats per minute (BPM).    
                        **Unit:** Beats per minute (BPM).

                        ### Speechiness
                        Indicates the proportion of spoken words in a track. High values indicate more spoken content (e.g. podcasts, audiobooks, rap).  
                        **Scale:** 
                        - Values above 0.66: Probably pure spoken content.
                        - 0.33-0.66: Mixture of music and spoken content.
                        - Below 0.33: Mainly music.

                        ### Liveness
                        Indicates the probability that the track was performed in front of a live audience. 
                        **Scale:** 0.0 to 1.0 (higher value = more live character). Values above 0.8 indicate live recordings.

                        ### Instrumentalness
                        Estimates how instrumental a track is. Higher values indicate that the track contains little or no vocals.
                        **Scale:** 0.0 to 1.0 (values close to 1.0 indicate pure instrumental music).

                        ### Loudness
                        Indicates the average volume of the track in decibels (dB). 
                        **Unit:** Decibel (dB).

                        ### Duration_ms
                        The length of the track in milliseconds.   
                        **Unit:** Milliseconds (ms).
                        """)  
                        
            conn_songs_db.close() #close connection
                    
#**********************************************************************
# 6. Filtering by audio features
#**********************************************************************

        
        elif selected_page == "Filter by Audio Features":
            # Selection of the variables shown in the database
            songs_db_path = os.path.join(script_dir, "spotify_songs.db")
            conn_songs_db = sqlite3.connect(songs_db_path)

            query_playlist_filter = """SELECT DISTINCT track_artist, track_name, tempo, valence, energy, danceability FROM spotify_songs"""
            spotify_songs_df_filter = pd.read_sql_query(query_playlist_filter, conn_songs_db)

            # Creation of the variables sliders
            st.subheader("Filter your songs by audio-features")
            with st.expander("Filter by audio-features", expanded=True):
                # Tempo-Filter
                col1, col2, col3 = st.columns([2, 8, 2])
                with col1:
                    st.write("Slow")
                with col2:
                    tempo_range = st.slider("Tempo", min_value=0.0, max_value=240.0, value=(0.0, 240.0), step=10.0, label_visibility="collapsed")
                with col3:
                    st.write("Fast")

                # Valence-Filter
                col1, col2, col3 = st.columns([2, 8, 2])
                with col1:
                    st.write("Sad")
                with col2:
                    valence_range = st.slider("Valence", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.1, label_visibility="collapsed")
                with col3:
                    st.write("Happy")

                # Energy-Filter
                col1, col2, col3 = st.columns([2, 8, 2])
                with col1:
                    st.write("Low energy")
                with col2:
                    energy_range = st.slider("Energy", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.1, label_visibility="collapsed")
                with col3:
                    st.write("High energie")

                # Danceability-Filter
                col1, col2, col3 = st.columns([2, 8, 2])
                with col1:
                    st.write("Chill music")
                with col2:
                    danceability_range = st.slider("Danceability", min_value=0.0, max_value=1.0, value=(0.0, 1.0), step=0.1, label_visibility="collapsed")
                with col3:
                    st.write("Dance music")

                # Select songs according to the filters
                filtered_songs = spotify_songs_df_filter[
                    (spotify_songs_df_filter['tempo'] >= tempo_range[0]) & (spotify_songs_df_filter['tempo'] <= tempo_range[1]) &
                    (spotify_songs_df_filter['valence'] >= valence_range[0]) & (spotify_songs_df_filter['valence'] <= valence_range[1]) &
                    (spotify_songs_df_filter['energy'] >= energy_range[0]) & (spotify_songs_df_filter['energy'] <= energy_range[1]) &
                    (spotify_songs_df_filter['danceability'] >= danceability_range[0]) & (spotify_songs_df_filter['danceability'] <= danceability_range[1])
                    ]

                # Show filtered songs
                st.subheader("Filtered songs")
                if not filtered_songs.empty:
                    st.dataframe(filtered_songs, use_container_width=True, height=300)

                    # Show legend 
                    if st.button("Description of audio features", key="audio_features_duplicate"):
                        st.session_state.show_legend = not st.session_state.show_legend

                    # Show descriptions when "Legend" is activated
                    if st.session_state.show_legend:
                        st.markdown("""
                        ### Tempo
                        The estimated tempo of the track in beats per minute (BPM).    
                        **Unit:** Beats per minute (BPM).
                            
                        ### Valence
                        Indicates the musical positivity of a track. Tracks with a high valence sound cheerful, happy and euphoric.  
                        **Scale:** 0.0 to 1.0 (higher value = more positive).
                            
                        ### Danceability
                        Indicates how suitable a track is for dancing. Based on a combination of elements such as tempo, rhythm stability, beat strength and overall rhythm.   
                        **Scale:** 0.0 to 1.0 (higher value = more danceable).

                        ### Energy
                        Indicates the level of intensity and activity of a track. Tracks with high energy have a fast tempo, a strong beat and loud instruments.  
                        **Scale:** 0.0 to 1.0 (higher value = more energetic).
                    """)

                else:
                    st.warning("No songs match your chosen criteria.")
                    
            conn_songs_db.close() #close connection
                
#********************************************************************************
# 7. Playlist creation with machine learning
#******************************************************************************** 

        
        elif selected_page == "Find New Songs":
            songs_db_path = os.path.join(script_dir, "spotify_songs.db")
            conn_songs_db = sqlite3.connect(songs_db_path)
            # CSS for customising the design
            st.markdown("""
                <style>
                .song-list {
                    font-size: 14px !important;
                    line-height: 1.6 !important;
                    display: flex;
                    justify-content: space-between;
                }
                .remove-button {
                    font-size: 10px !important;
                    padding: 1px 3px !important;
                    color: red !important;
                    background: none !important;
                    border: none !important;
                    cursor: pointer !important;
                }
                .song-count {
                    font-size: 16px !important;
                    font-weight: bold !important;
                    margin-bottom: 10px !important;
                }
                </style>
            """, unsafe_allow_html=True)
            st.subheader("Create your own playlist!")
            with st.expander("Find songs based on your preferences", expanded=True):
                st.write("Choose as many songs as you want. A minimum of 5 is required.")
                # Add dynamic search option
                search_column_2 = st.selectbox("Search for:", ["track_artist", "track_name"], key="search_column_2")
                search_query_2 = st.text_input(f"Please insert {search_column_2}:", key="search_query_2")

                # Save basket in the session
                if "cart" not in st.session_state:
                    st.session_state.cart = []

                # Display the number of songs in the basket
                if st.session_state.cart:
                    st.markdown(f"<div class='song-count'>Chosen songs: {len(st.session_state.cart)}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div class='song-count'>Your basket is empty.</div>", unsafe_allow_html=True)

                # Show search results
                if search_query_2:
                    # Query tracks by search term
                    query_playlist_search_2 = f"""
                    SELECT DISTINCT track_artist, track_name, danceability, energy, key, loudness, mode, speechiness, acousticness, 
                    instrumentalness, liveness, valence, tempo, duration_ms 
                    FROM spotify_songs WHERE {search_column_2} LIKE ?
                    """
                    spotify_songs_df_search_2 = pd.read_sql_query(query_playlist_search_2, conn_songs_db, params=(f"%{search_query_2}%",))

                    if not spotify_songs_df_search_2.empty:
                        st.write("Select songs to add them to the basket:")
                        
                        for i, row in spotify_songs_df_search_2.iterrows():
                            # Generate a unique key for the checkbox
                            checkbox_key = f"checkbox_{i}_{row['track_name']}_{row['track_artist']}"
                            is_checked = row.to_dict() in st.session_state.cart
                            checked = st.checkbox(
                                f"{row['track_name']} von {row['track_artist']}", 
                                value=is_checked, 
                                key=checkbox_key
                            )
                            if checked and not is_checked:
                                # Add to basket
                                st.session_state.cart.append(row.to_dict())
                            elif not checked and is_checked:
                                # Delete from basket
                                st.session_state.cart.remove(row.to_dict())
                    else:
                        # Display message if no hits are found
                        st.warning("No match found. Try another entry.")

                # Show basket (always visible)
                if st.session_state.cart:
                    st.write("Your basket:")
                    for index, track in enumerate(st.session_state.cart):
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.markdown(f"<div class='song-list'><b>{track['track_name']}</b> - <i>{track['track_artist']}</i></div>", unsafe_allow_html=True)
                        with col2:
                            if st.button(f"❌", key=f"remove_cart_{index}", help="Löschen"):
                                st.session_state.cart.pop(index)
                                st.experimental_rerun()  # Reload page to reflect changes

                # Initialize session_state
                if "similar_songs_generated" not in st.session_state:
                    st.session_state.similar_songs_generated = False

                if "save_playlist_clicked" not in st.session_state:
                    st.session_state.save_playlist_clicked = False

                # Initialize empty dataframe
                if "user_songs_df_similar" not in st.session_state:
                    st.session_state.user_songs_df_similar = pd.DataFrame()  # Fallback for later access
                
    #*********************************************************
    # 8. Supervised Machine learning, nearest neighbor 
    #*********************************************************

                # Show button only if there are at least 5 songs in the basket
                if len(st.session_state.cart) >= 5:
                    
                    # User can choose how many similar songs he want to add, since the user selects more than one song, the number selected on the slider
                    # counts per song chosen
                    defined_n_neighbors = st.slider("Number of similar songs to find:", min_value=10, max_value=300, value=150, step=10)
                        
                    if st.button("Find similar songs"):
                        # Create DataFrame 'selected_tracks_df for the users chosen songs
                        selected_tracks_df = pd.DataFrame(st.session_state.cart)
                        
                        # Use machine learning model to find similar songs
                        from sklearn.neighbors import NearestNeighbors
                        import numpy as np

                        # Prepare data for Machine Learning by defining the learning parameters                 
                        feature_columns = [
                            "danceability", "energy", "key", "loudness", "mode",
                            "speechiness", "acousticness", "instrumentalness", "liveness",
                            "valence", "tempo", "duration_ms"
                        ]

                        # Fit model on all songs
                        query_playlist_all = """
                        SELECT * FROM spotify_songs
                        """
                        spotify_songs_df_all = pd.read_sql_query(query_playlist_all, conn_songs_db)
                        knn = NearestNeighbors(n_neighbors= defined_n_neighbors, metric="euclidean") #euclidean is the distance metric, number of nearest neighbors is define with the slider
                        knn.fit(spotify_songs_df_all[feature_columns]) #training it on all songs

                        # Search for similar songs based on the selected tracks
                        selected_features = selected_tracks_df[feature_columns].values
                        distances, indices = knn.kneighbors(selected_features) #calculation of indices and distance

                        # Collect results but flatten out duplicates 
                        user_songs_df_similar = spotify_songs_df_all.iloc[np.unique(indices.flatten())] #based on the indices the correct song can be retrieved from the spotify_songs_df

                        # Save into st.session_state for further processing
                        st.session_state.user_songs_df_similar = user_songs_df_similar

                        # Add playlist metadata
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                        user_songs_df_similar["playlist_name"] = f"Mix Up {timestamp}"
                        user_songs_df_similar["playlist_subgenre"] = f"Mix Up {timestamp}"
                        user_songs_df_similar["playlist_id"] = timestamp

                        # Show results
                        st.subheader("Similar songs")
                        st.dataframe(user_songs_df_similar, use_container_width=True, height=400) # the recommended songs are displayed in the dataframe

                        # refresh state
                        st.session_state.similar_songs_generated = True
                        st.session_state.save_playlist_clicked = False

                # Save button is shown if songs have been generated 
                if st.session_state.similar_songs_generated and not st.session_state.save_playlist_clicked:
                    st.write("Do you like the songs? Save now!")
                    
                    # Playlist name input
                    playlist_name = st.text_input("Enter a name for your playlist:", "My Playlist") #name the new created playlist before adding it to the database
                    
                    if st.button("Save Playlist"):
                        # Assure that the datafram is not empty
                        if not st.session_state.user_songs_df_similar.empty:
                            try:
                                # Add the playlist name to the DataFrame
                                st.session_state.user_songs_df_similar["playlist_name"] = playlist_name 
                                user_db_path = os.path.join(songs_dir, f"{st.session_state.user_id}.db")
                                conn_user_db = sqlite3.connect(user_db_path)
                                st.session_state.user_songs_df_similar.to_sql(
                                    'user_songs', conn_user_db, if_exists='append', index=False
                                )
                                conn_user_db.commit()
                                conn_user_db.close()

                                st.success(f"The '{playlist_name}' has been saved successfully!")
                                st.session_state.similar_songs_generated = False
                            except Exception as e:
                                st.error(f"Error when saving the playlist: {e}")
                        else:
                            st.error("No songs to save available!")

    
            conn_songs_db.close() #close connection
        
#******************************************************
# 9. Visualizations
#******************************************************

           # function to get the top 10 artists
        def get_user_top_artists(user_id):
            try:
                user_db_path = os.path.join(songs_dir, f"{user_id}.db")
                conn_user_db = sqlite3.connect(user_db_path)

                # call data from database
                query = "SELECT track_artist FROM user_songs"
                user_songs_df = pd.read_sql_query(query, conn_user_db)

                if user_songs_df.empty:
                    st.warning("Keine Songs in der Datenbank gefunden.")
                    return

                # Calculate top 10 artists from a user
                top_artists = user_songs_df['track_artist'].value_counts().head(10)

                # Create plot 
                plt.figure(figsize=(10, 6))
                sns.barplot(x=top_artists.values, y=top_artists.index, palette="Blues_d")
                plt.title("Top 10 Artists")
                plt.xlabel("Number of songs")
                plt.ylabel("Artists")
                st.pyplot(plt)

                conn_user_db.close()

            except Exception as e:
                st.error(f"Fehler beim Zugriff auf die Datenbank: {e}")
            
        # function to show the distribution of the different genres
        def plot_genre_distribution(user_id):
            try:
                user_db_path = os.path.join(songs_dir, f"{user_id}.db")
                conn_user_db = sqlite3.connect(user_db_path)
                query = "SELECT playlist_genre FROM user_songs"
                genre_df = pd.read_sql_query(query, conn_user_db)

                if genre_df.empty:
                    st.warning("No genre data available.")
                    return

                genre_counts = genre_df['playlist_genre'].value_counts()

                # Plot
                plt.figure(figsize=(8, 6))
                genre_counts.plot(kind='bar', color='skyblue')
                plt.title("Distribution of Genres")
                plt.xlabel("Genre")
                plt.ylabel("Number")
                st.pyplot(plt)

                conn_user_db.close()

            except Exception as e:
                st.error(f"Error while calling the genres: {e}")
            

        # Function to calculate distribution of any variable, example valence
        def plot_audio_feature_distribution(user_id, feature):
            try:
                user_db_path = os.path.join(songs_dir, f"{user_id}.db")
                conn_user_db = sqlite3.connect(user_db_path)
                query = f"SELECT {feature} FROM user_songs"
                feature_df = pd.read_sql_query(query, conn_user_db)

                if feature_df.empty:
                    st.warning(f"No data for {feature} available.")
                    return

                # Plot
                plt.figure(figsize=(8, 6))
                sns.histplot(feature_df[feature], kde=True, bins=20, color='green')
                plt.title(f"Distribution {feature}")
                plt.xlabel(feature.capitalize())
                plt.ylabel("Anzahl")
                st.pyplot(plt)

                conn_user_db.close()

            except Exception as e:
                st.error(f"Fehler beim Abrufen von {feature}: {e}")
                
        # Sidebar: Choose the visualisation you want to open
        visualization_option = st.sidebar.selectbox(
            "Choose a visualization:",
            ["Top 10 Artists", "Genre Distribution", "Audio Feature Distribution"]
        )
        # Page, where the visualisation is shown
        st.subheader("Explore your music data")
        # Framing to show the plots
        col1, col2, col3= st.columns([1,4,1])
        # The visualisation that was chosen in the sidebar is displayed. 
        with col2:
            if visualization_option == "Top 10 Artists":
                get_user_top_artists(st.session_state.user_id)
            elif visualization_option == "Genre Distribution":
                plot_genre_distribution(st.session_state.user_id)
            elif visualization_option == "Audio Feature Distribution":
                plot_audio_feature_distribution(st.session_state.user_id, "valence")
                    
if __name__ == "__main__":
    main()
# Spotify Playlist Analyzer

Spotify Playlist Analyzer is a web application that connects to users' Spotify accounts to provide various music analyses and recommendations.

## Features

- Login with Spotify account
- View user's top artists and tracks
- Playlist analysis (genre distribution, popularity, etc.)
- Song recommendations
- Create new playlists and add tracks

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/spotify-playlist-analyzer.git
   ```

2. Navigate to the project directory:
   ```
   cd spotify-playlist-analyzer
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create an application in the Spotify Developer Dashboard and obtain the Client ID and Client Secret.

5. Update your Spotify API credentials in the `song-recommender.py` file:
   ```python
   SPOTIPY_CLIENT_ID = 'your_client_id_here'
   SPOTIPY_CLIENT_SECRET = 'your_client_secret_here'
   SPOTIPY_REDIRECT_URI = 'http://localhost:8501/'
   ```

## Usage

1. Run the application:
   ```
   streamlit run song-recommender.py
   ```

2. Go to `http://localhost:8501` in your browser.

3. Click the "Authorize" button to log in with your Spotify account.

4. Start using the application!

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## License

This project is currently not licensed. For more information, please contact the project owner.

## Contact

Project Owner: Ozgur Turkoglu(https://github.com/ozgurtrko)

Project Link: [https://github.com/yourusername/spotify-playlist-analyzer](https://github.com/yourusername/spotify-playlist-analyzer)

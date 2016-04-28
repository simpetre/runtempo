import spotipy
import os
import datetime
import requests

from bs4 import BeautifulSoup

def config_spotify_environment(username):
    """Load authorisation credentials from environment variables to prepare
    Spotify API.
    INPUT: None
    OUTPUT: sp (Spotipy object): Configured Spotipy object
    """

    CLIENT_ID = os.env(SPOTIPY_CLIENT_ID)
    CLIENT_SECRET = os.env(SPOTIPY_SECRET_ID)
    REDIRECT_URI = os.env(SPOTIPY_REDIRECT_URI)
    spotipy.util.prompt_for_user_token(username, scope=None,
                                       client_id=CLIENT_ID,
                                       client_secret=CLIENT_SECRET,
                                       redirect_uri=REDIRECT_URI)
    manager = SpotifyClientCredentials(client_id=CLIENT_ID,
                                       client_secret=CLIENT_SECRET)
    sp = spotipy.Spotify(client_credentials_manager=manager)
    return sp

def extract_filenames(path):
    """Crawl through directory, starting at path, and create
    list of filenames of all files in all subdirectories of path
    INPUT: path (string): Directory to start traversal at
    OUTPUT: filenames (list): List of all files contained within
    subdirectories of path
    """
    filenames = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            if filename[-3:] == '.h5':
                filenames.append(filename)
    return filenames

def scrape_billboard(num_tracks):
    """Store the Spotify IDs of the most recent tracks listed in the Billboard
    top 100.
    INPUT: num_tracks(int): Number of track IDs to return
    OUTPUT spotify_ids (np array): Array of relevant Spotify IDs
    """
    url_date = datetime.date(2016, 4, 23)
    spotify_ids = []
    scrape_url = "http://www.billboard.com/charts/hot-100/"
    spotify_ids.extend(scrape_billboard_once(scrape_url))

    while len(set(spotify_ids)) < num_tracks:
        date_append = "{:02d}-{:02d}-{:02d}".format(url_date.year,
                                                    url_date.month,
                                                    url_date.day)
        scrape_url = "http://www.billboard.com/charts/hot-100/" + date_append
        spotify_ids.extend(scrape_billboard_once(scrape_url))
        url_date -= datetime.timedelta(7)
    return spotify_ids

def scrape_billboard_once(scrape_url):
    """Helper function for scrape_billboard_tracks - scrape content of one
    specific URL on billboard.com.
    INPUT scrape_url (string): URL to scrape
    OUTPUT track_ids (np array): Array of relevant Spotify IDs
    """
    track_ids = []
    x = requests.get(scrape_url)
    soup = BeautifulSoup(x.content)
    results = soup.find_all("article", attrs={"data-spotifytype": "track"})
    for tag in results:
        track_ids.append(tag['data-spotifyid'])
    return track_ids

def extract_image_url(spotify_id, sp, default):
    """Return album art url of a given Spotify song ID (if it exists, else
    return default).
    INPUT: spotify_id (string): Spotify ID of a song
    sp (object): Configured Spotipy manager object
    default (string): Default image address to use if an image for the given ID
    doesn't exist
    OUTPUT: (string): Image address of relevant album art (or default)
    """
    r = sp.track('spotify_id')
    try:
        url = r['album']['images'][0]['url']
    except:
        url = default
    return url

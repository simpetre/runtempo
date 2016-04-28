import h5py
import numpy as np
import pandas as pd
import hdf5_getters
import tables
import inspect
import graphlab.aggregate as agg

from graphlab import SFrame

def get_feat_matrix(filenames):
    """Take list of MSD hdf5 file paths and aggregate them into
    numpy array of features
    INPUT: filenames (list of strings): List of hdf5 file paths
    OUTPUT: features (SFrame): Numpy array of features
    """
    column_names = []
    getter_functions = []
    # add getter functions from hdf5_getters to column names
    # getter functions start at index 6
    for element in inspect.getmembers(hdf5_getters)[6:]:
        if element[0][:4] == "get_":
            getter_functions.append(element[0])

    getter_functions.remove('get_artist_mbtags')
    getter_functions.remove('get_artist_mbtags_count')
    getter_functions.remove('get_artist_terms')
    getter_functions.remove('get_artist_terms_freq')
    getter_functions.remove('get_artist_terms_weight')
    getter_functions.remove('get_bars_confidence')
    getter_functions.remove('get_bars_start')
    getter_functions.remove('get_beats_confidence')
    getter_functions.remove('get_beats_start')
    getter_functions.remove('get_sections_start')
    getter_functions.remove('get_sections_confidence')
    getter_functions.remove('get_segments_confidence')
    getter_functions.remove('get_segments_loudness_max')
    getter_functions.remove('get_segments_loudness_max_time')
    getter_functions.remove('get_segments_loudness_start')
    getter_functions.remove('get_segments_pitches')
    getter_functions.remove('get_segments_start')
    getter_functions.remove('get_segments_timbre')
    getter_functions.remove('get_similar_artists')
    getter_functions.remove('get_tatums_confidence')
    getter_functions.remove('get_tatums_start')
    getter_functions.remove('get_track_7digitalid')
    getter_functions.remove('get_release_7digitalid')
    getter_functions.remove('get_artist_latitude')
    getter_functions.remove('get_artist_longitude')
    getter_functions.remove('get_audio_md5')
    getter_functions.remove('get_artist_7digitalid')

    for function in getter_functions:
        column_names.append(function[4:])

    temp_data = {}
    h = hdf5_getters.open_h5_file_read(filenames[0])

    for i, function in enumerate(getter_functions):
        temp_method = getattr(hdf5_getters, function)
        temp_data[column_names[i]] = [temp_method(h)]
    h.close()

    for filename in filenames[1:]:
        h = hdf5_getters.open_h5_file_read(filename)
        for i, function in enumerate(getter_functions):
            temp_method = getattr(hdf5_getters, function)
            temp_data[column_names[i]].append(temp_method(h))
        h.close()

    features = SFrame(temp_data)
    return features

def get_play_counts(path):
    """Read ratings data from triplets file in the form userid/songid/play count
    INPUT: path (string): File to read ratings from
    OUTPUT: play_counts (numpy array): Three column numpy array, containing
    userid, songid and play count in each column
    """
    plays_mat = np.genfromtxt(path, dtype=None, max_rows=1000000)
    plays_mat.dtype.names = ('user_id', 'song_title', 'play_count')

    return plays_mat

def fit_model(play_matrix):
    """Take matrix of play counts and return GraphLab recommender model
    based on these data
    INPUT: play_matrix (numpy array): Array of features to fit to
    OUTPUT: mod (GraphLab model): GraphLab matrix factorisation recommender
    model
    """
    plays_df = pd.DataFrame(play_matrix)
    plays_sf = SFrame(plays_df)
    agg_sf = plays_sf.groupby('user_id',
                  operations={'mean_plays': agg.MEAN('play_count'),
                              'sd_plays': agg.STDV('play_count'),
                              'play_quantile': agg.QUANTILE('play_count',
                                               [0.2, 0.4, 0.6, 0.8, 1])})
    plays_sf = plays_sf.join(agg_sf, on='user_id', how='inner')
    play_quantiles = np.array(plays_sf['play_quantile'])
    play_counts = np.array(plays_sf['play_count'])
    play_counts = play_counts.reshape(play_counts.shape[0], 1)
    plays_sf['rating'] = np.sum(play_counts <= play_quantiles, axis=1)
    mod = graphlab.recommender.create(plays_sf, user_id='user_id',
                                  item_id='song_title', target='rating',
                                  ranking=True)
    return mod

def get_playlist(mod, pref_songs, feature_sf,
                 desired_tempo=160, tempo_margin=15, playlist_length=10):
    """Return recommended number of songs based on run length/playlist and
    tempo
    INPUT: mod (GraphLab model): Fitted GraphLab matrix factorisation
    recommender model
    pref_songs (list): MSD(/EchoNest) Song IDs to seed new user
    feature_sf (SFrame): Song naming metadata/tempos
    desired_tempo (int): Tempo to run at
    tempo_margin (int): +/- BPM tolerance for desired tempos
    playlist_length (int): No. of songs to predict
    OUTPUT:

    """
    tempos = np.array(feature_sf['tempo'])
    artist_names = np.array(feature_sf['artist_name'])
    song_ids = np.array(feature_sf['song_id'])
    song_names = np.array(feature_sf['title'])

    # create numpy array vector that will store the tempo adjusted to be within
    # the range for that index
    tempo_adjust = np.ones(len(song_ids))

    # boolean vector of whether a particular song has an eligible tempo or not
    eligible_song = np.zeros(len(song_ids), dtype=bool)

    for i, tempo in enumerate(tempos):
        for multiplier in [1, 1.5, 2, 3]:
            if (desired_tempo - tempo_margin <=
                        multiplier * tempo <= desired_tempo + tempo_margin):
                eligible_song[i] = True
                tempo_adjust[i] = multiplier
    eligible_index = np.where(eligible_song == True)

    # set number of songs to be the number of unique songs in the play
    # count data set
    num_songs = len(np.unique(feature_sf['title']))

    # order the songs in the set in order of similarity to the elements
    # of song_titles

    newdata = SFrame({'user_id': ['PREDICT_USER',
                                'PREDICT_USER', 'PREDICT_USER'],
                          'song_title': pref_songs,
                          'rating': [5, 5, 5],
                          'play_count': [0, 0, 0],
                          'sd_plays': [0, 0, 0],
                          'play_quantile': [[0,0,0,0,0], [0,0,0,0,0],
                                            [0,0,0,0,0]],
                          'mean_plays': [0, 0, 0]})
    res = mod.recommend(users=['PREDICT_USER'],
                        new_observation_data=newdata,
                        k=num_songs)
    similar_items = res['song_title']
    count = 0
    pl_cols = ['song_name', 'artist', 'tempo_multiplier', 'original_tempo',
               'effective_tempo']
    playlist = pd.DataFrame(columns=pl_cols)
    for title in similar_items:
        if title in song_ids[eligible_index]:
            ind = title == song_ids
            row = pd.DataFrame([[song_names[ind][0],
                                 artist_names[ind][0],
                                 tempo_adjust[ind][0],
                                 tempos[ind][0],
                                 tempo_adjust[ind][0] * tempos[ind][0]
                                 ]], columns=pl_cols)
            playlist = playlist.append(row)
            count += 1
        if count == playlist_length:
            break
    playlist = playlist.sort_values('effective_tempo')
    # start with the slowest song and get progressively faster

    return playlist

def generate_pairs(mod, song_ids, k=3):
    """Generate k sets of dissimilar song pairs
    INPUT mod (graphlab model): Fitted graphlab model
    OUTPUT song_pairs (list of tuples): List of length k of liked songs
    """
    song_pairs = []
    for i in xrange(k):
        rnd = np.random.randint(1, mod.num_items)
        # generates a random song id
        song_tup = (song_ids[rnd],
                    mod.get_similar_items([song_ids[rnd]])['similar'][-1])
        # gets least similar song to the generated song
        song_pairs.append(song_tup)
    return song_pairs

def get_user_prefs(feat_mat, song_pairs):
    """Get user preferences on three different song pairs
    INPUT (list of tuples): List of pairs of songs with lowest similarity
    OUTPUT (list): List of songs (that are elements of the input tuples)
    """
    titles = feat_mat['title']
    artists = feat_mat['artist_name']
    song_ids = feat_mat['song_id']
    prefs = []

    print "Which song do you prefer? Type 1 or 2:"

    for i, pair in enumerate(song_pairs):
        artist_pair = (artists[song_ids == pair[0]],
                                    artists[song_ids == pair[1]])
        title_pair = (titles[song_ids == pair[0]],
                                    titles[song_ids == pair[1]])
        pref = int(raw_input("\n1: {0}: {1}\n2: {2}: {3} "
                    .format(artist_pair[0][0], title_pair[0][0],
                    artist_pair[1][0], title_pair[1][0]))) - 1
        pref = pair[pref]
        prefs.append(pref)
    return prefs

import pandas as pd
import numpy as np

def generate_audio_features(spotify_ids, sp):
    """Generate audio feature dataframe from list of Spotify IDs.
    INPUT spotify_ids (np array): Vector of relevant IDs
    sp (spotify manager object): Configured spotify object
    OUTPUT audio_array (dataframe): Pandas dataframe containing audio feature
    metadata
    """
    features = []
    error_indices = []
    for i, spotify_id in enumerate(spotify_ids):
        try:
            features.append(sp.audio_features([spotify_id]))
        except:
            error_indices.append(i)

    features_df = pd.DataFrame(columns=features[0][0].keys())
    for feature in features:
        features_df = features_df.append(feature[0], ignore_index=True)

    for spotify_id in spotify_ids:
        track_q = sp.track(spotify_id)
        if np.where(spotify_ids == spotify_id) not in error_indices:
            song_names.append(track_q['name'])
            album_names.append(track_q['album']['name'])
            artist_names.append(track_q['artists'][0]['name'])

    names_df = pd.DataFrame()
    names_df['spotify_id'] = spotify_ids
    names_df['song_name'] = song_names
    names_df['artist_name'] = artist_names
    names_df['album_name'] = album_names
    audio_array = pd.merge(features_df, names_df, how='inner',
                                left_on='id', right_on='spotify_id')
    return audio_array

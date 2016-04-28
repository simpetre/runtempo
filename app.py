import graphlab
import numpy as np
import pandas as pd

from flask import Flask, render_template, request
from eda import get_playlist, generate_pairs, get_user_prefs, get_play_counts
from graphlab import SFrame

app = Flask(__name__)

timeline_para = """
<li{0}>
    <div class="timeline-image">
        <img class="img-circle img-responsive" src="../static/img/about/2.jpg" alt="">
    </div>
    <div class="timeline-panel">
        <div class="timeline-heading">
            <h4>{1}</h4>
            <h4 class="subheading"><i>{2}</i></h4>
        </div>
        <div class="timeline-body">
            <p class="text-muted">You should run at <b>{3}</b> steps per beat,<br>
            at an effective cadence of <b>{4}</b> footsteps/min</p>
        </div>
    </div>
</li>
"""
# home page
@app.route('/', methods=['GET', 'POST'])
def index():
    speed_index = request.form['speed']
    tempo = 150 + speed_index * 20
    return render_template('index.html',
                t_var=timeline_obj,
                song_1a=feat_mat['title'][feat_mat['song_id'] == song_pairs[0][0]][0],
                song_1b=feat_mat['title'][feat_mat['song_id'] == song_pairs[0][1]][0],
                song_2a=feat_mat['title'][feat_mat['song_id'] == song_pairs[1][0]][0],
                song_2b=feat_mat['title'][feat_mat['song_id'] == song_pairs[1][1]][0],
                song_3a=feat_mat['title'][feat_mat['song_id'] == song_pairs[2][0]][0],
                song_3b=feat_mat['title'][feat_mat['song_id'] == song_pairs[2][1]][0],
                artist_1a=feat_mat['artist_name'][feat_mat['song_id'] == song_pairs[0][0]][0],
                artist_1b=feat_mat['artist_name'][feat_mat['song_id'] == song_pairs[0][1]][0],
                artist_2a=feat_mat['artist_name'][feat_mat['song_id'] == song_pairs[1][0]][0],
                artist_2b=feat_mat['artist_name'][feat_mat['song_id'] == song_pairs[1][1]][0],
                artist_3a=feat_mat['artist_name'][feat_mat['song_id'] == song_pairs[2][0]][0],
                artist_3b=feat_mat['artist_name'][feat_mat['song_id'] == song_pairs[2][1]][0])
    # Pass song names/titles to choose from to HTML template

if __name__ == '__main__':
    play_count_path = 'train_triplets.txt'
    feat_path = 'trimmed_tempos.csv'
    model_path = 'full_two_hour_mod_directory'

    feat_mat = SFrame.read_csv(feat_path)
    model = graphlab.load_model(model_path)
    song_pairs = generate_pairs(model, np.array(feat_mat['song_id']), k=3)
    pref_songs = get_user_prefs(feat_mat, song_pairs)
    playlist = get_playlist(model, pref_songs, feat_mat,
                            desired_tempo=160,
                            tempo_margin=10,
                            playlist_length=10)

    songs = playlist['song_name'].values
    artists = playlist['artist'].values
    tempoxs = playlist['tempo_multiplier'].values
    cadences = playlist['effective_tempo'].values
    pl_length = 10
    timeline_obj = ""

    # Generate HTML string to render playlist
    for i in xrange(pl_length):
        if i % 2 == 0:
            invert = ' class="timeline-inverted"'
        else:
            invert = ""
        timeline_obj += timeline_para.format(invert, str(songs[i]),
                   str(artists[i]),
                   int(tempoxs[i]),
                   float(cadences[i]))

    app.run(host='0.0.0.0', port=8585, debug=False)

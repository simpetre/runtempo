#Welcome to RunTempo!
#####Your personal running and music coach
Have you ever started running but got halfway through and just sort of chickened out? Started running slow, stopped and started walking, that sort of thing? If so, RunTempo is for you! If not, RunTempo is still for you! You, the user, input how fast (within a range) you'd like to run, you rate a few songs and RunTempo does the rest.

###Table of Contents

[Problem Statement](#problem)
[Data Pipeline](#pipeline)
[Model](#model)
[Future Work](#webapp)
[Webapp](#future)

<a name="problem">###Problem Statement</a>
No matter your experience level - whether you're a casual weekend jogger or an elite athlete (like the author (that's a joke)), running cadence (or footsteps/minute) is an important consideration. Generally people run at somewhere between 150 and 200 steps per minute - and no matter whether you're trying to keep track of your cadences every time you run because you love numbers, or whether you're making sure you're not slacking off, or whether you're training for a half-marathon in a few months, RunTempo is for you. Set a specific goal, to maintain a specific cadence, punch it into RunTempo and run away listening to music you love.

<a name="pipeline">###Data Pipeline</a>
I pulled data from several sources when creating RunTempo. The base recommender was built with the [Taste Profile](http://labrosa.ee.columbia.edu/millionsong/tasteprofile), which is a sister dataset to the [Million Song Dataset](http://labrosa.ee.columbia.edu/millionsong/) (MSD) and contains user/song/play count triplets for 1019318 unique users and 384546 unique songs for a total of 48373586 samples, and then filtered on tempos using data extracted from the main dataset.

<a name="model">###Model</a>
The model I settled on was a matrix factorisation recommender optimised for ranking, created using [GraphLab Create](https://dato.com). I fed in the data unaltered initially and got some pretty questionable results, so I amended the target variable to map each user's playcount to a rating out of five (I took each user's playcounts, determined the quintiles those playcounts fell into for that particular user and then used this quintile as a rating) and this is what I based my final model on.

To predict a playlist for a particular user I chose three random songs from the entire dataset, and the three respective songs that were as dissimilar to those songs as possible (i.e. were furthest away in terms of Jaccard distance) and asked the user to choose their preference out of these three pairs. I used this preference as a proxy for rating (a selected song was assumed to be rated five out of five by the user) and then I found the user that was closest to a user that had these three ratings (again in terms of Jaccard distance) to determine the ranking order of the songs in the dataset. I filtered these songs on the appropriate tempo range and return them to the user in increasing order of tempo (within a 20 footsteps or beats/minute range).

<a name="webapp">###Webapp</a>
I chose to present RunTempo in the form of a website. The user chooses from three different options for speed and selects their choice of songs, presented as three sets of two options, and the RunTempo creates and renders the playlist dynamically.

<a name="future">###Future Work</a>
The main obvious deficiency of RunTempo is that the music that it's based off is (in musical years) very old - the MSD was created in early 2011, and songs that it contains were released in 2010 or earlier. The next iteration of the project I'll be working on is to take some actual sound data for the songs in the base recommender (Spotify publish a number of derived metrics, such as "speechiness", "acousticness", "loudness", "valence" - which all have pretty self-explanatory meanings, except for valence, which is a measure of how "happy" the song sounds), and use a clustering algorithm to find popular songs (the most recent ten thousand songs that have been featured in the Billboard 100 charts) that are close to these. This will be coming in the next few weeks.

Happy running!
# runtempo

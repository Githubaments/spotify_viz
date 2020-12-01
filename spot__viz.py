import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px 
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import spotipy.util as util
import os
import tekore as tk


st.set_page_config(page_title='Spotify Viz', page_icon="https://raw.githubusercontent.com/Githubaments/Images/main/favicon.ico")

px.defaults.template = "simple_white"
client_id = (os.environ.get('client_id'))
client_secret = (os.environ.get('client_secret'))
#scope = 'playlist-modify-private,playlist-modify-public,playlist-modify-public,user-top-read,user-read-recently-played,user-library-read'
redirect_uri = 'http://localhost:5000/callback'


conf = (client_id, client_secret, redirect_uri)
scope = tk.scope.user_top_read + tk.scope.playlist_modify_private
token = tk.prompt_for_user_token(*conf, scope=scope)

spotify = tk.Spotify(token)
top_tracks = spotify.current_user_top_tracks(limit=5).items

st.write(top_tracks)


def cache_on_button_press(label, **cache_kwargs):
    """Function decorator to memoize function executions.
    Parameters
    ----------
    label : str
        The label for the button to display prior to running the cached funnction.
    cache_kwargs : Dict[Any, Any]
        Additional parameters (such as show_spinner) to pass into the underlying @st.cache decorator.
    -------

    """
    internal_cache_kwargs = dict(cache_kwargs)
    internal_cache_kwargs['allow_output_mutation'] = True
    internal_cache_kwargs['show_spinner'] = False

    def function_decorator(func):
        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            @st.cache(**internal_cache_kwargs)
            def get_cache_entry(func, args, kwargs):
                class ButtonCacheEntry:
                    def __init__(self):
                        self.evaluated = False
                        self.return_value = None

                    def evaluate(self):
                        self.evaluated = True
                        self.return_value = func(*args, **kwargs)

                return ButtonCacheEntry()

            cache_entry = get_cache_entry(func, args, kwargs)
            if not cache_entry.evaluated:
                if st.button(label):
                    cache_entry.evaluate()
                else:
                    raise st.ScriptRunner.StopException
            return cache_entry.return_value

        return wrapped_func

    return function_decorator

@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def spotify_50():

    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri=redirect,
                                                   scope=scope))
    st.write(sp)
    st.write(sp.me())
    json_response = sp.me()

    display_name = json_response['display_name']
    usernamesp = json_response['id']
    #token = get_token(usernamesp)
    pic = json_response['images'][0]['url']

    st.write(f"Hi there {display_name}")
    st.sidebar.image(pic)

    sml = ['short_term','medium_term','long_term']
    dfs = []

    for timeline in sml:
        test23 = sp.current_user_top_tracks(limit=50, offset=0, time_range=timeline)

        uri = []
        track_name = []
        track_artist = []
        artist_uri = []
        album = []
        pop = []
        explicit = []
        preview = []
        image_med = []
        image_small = []
        for index,item in enumerate(test23['items']):
            uri.append(test23['items'][index]['id'])
            track_name.append(test23['items'][index]['name'])
            track_artist.append(test23['items'][index]['artists'][0]['name'])
            artist_uri.append(test23['items'][index]['artists'][0]['id'])
            album.append(test23['items'][index]['album']['name'])
            pop.append(test23['items'][index]['popularity'])
            explicit.append(test23['items'][index]['explicit'])
            preview.append(test23['items'][index]['preview_url'])
            image_med.append(test23['items'][index]['album']['images'][1]['url'])
            image_small.append(test23['items'][index]['album']['images'][2]['url'])


        df = pd.DataFrame(sp.audio_features(tracks=uri))
        df2 = pd.DataFrame(list(zip(track_name, track_artist,artist_uri,album,pop,explicit,preview,image_med,image_small)),columns =['track_name', 'artist','artist_uri','album','popularity','explicit','preview','image_med','image_small'])
        df['timeline'] = str(timeline)
        df['key'] = [get_track_key(key, mode) for key, mode in zip(df['key'], df['mode'])]
        df['position'] = df.index
        df['duration'] = round(df.duration_ms / 1000)
        dfs.append(pd.concat([df2,df],axis=1))

    return dfs,token,usernamesp



def get_token(username):
    import spotipy.util as util


    token = util.prompt_for_user_token(username=username,
                                       scope=scope,
                                       client_id=client_id,
                                       client_secret=client_secret,
                                       redirect_uri=redirect)
    return token


def get_genres(usernamesp):
    token = get_token(usernamesp)
    endpoint_display_url = f"https://api.spotify.com/v1/recommendations/available-genre-seeds"


    response = requests.get(url=endpoint_display_url,
                             headers={"Content-Type": "application/json",
                                      "Authorization": f"Bearer {token}"})

    genres = response.json()
    genres = genres['genres']

    return genres

def get_track_key(key, mode):
    major_keys = {0: 'C Major',
                  1: 'C# Major',
                  2: 'D Major',
                  3: 'D# Major',
                  4: 'E Major',
                  5: 'F Major',
                  6: 'F# Major',
                  7: 'G Major',
                  8: 'G# Major',
                  9: 'A Major',
                  10: 'A# Major',
                  11: 'B Major'}

    minor_keys = {0: 'C Minor',
                  1: 'C# Minor',
                  2: 'D Minor',
                  3: 'D# Minor',
                  4: 'E Minor',
                  5: 'F Minor',
                  6: 'F# Minor',
                  7: 'G Minor',
                  8: 'G# Minor',
                  9: 'A Minor',
                  10: 'A# Minor',
                  11: 'B Minor'}

    if mode == 0:
        key_name = minor_keys[key]
    else:
        key_name = major_keys[key]

    return key_name

def check_response(json_response, response_check):

    api_response = {204: "No Content - The request has succeeded but returns no message body.",
                    400: "Please check input data.",
                    401: "Please check your credentials.",
                    403: "Forbidden.",
                    404: "Not found.",
                    429: "Too many requests.",
                    500: "Internal Server Error.",
                    502: "Bad Gateway.",
                    503: "Service Unavailable."
                    }

    if response_check not in (200, 201):
        try:
            st.write(api_response[response_check])
            st.write(json_response['error']['message'])
            st.stop()
        except KeyError:
            st.write(json_response['error']['message'])
            st.write("https://developer.spotify.com/documentation/web-api/")
            st.stop()

    return

@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def audio_features(df):
    df2 = pd.DataFrame(sp.audio_features(tracks=df.track_uri))
    df2['key'] = [get_track_key(key, mode) for key, mode in zip(df2['key'], df2['mode'])]
    df2['position'] = df2.index
    df2['duration'] = round(df2.duration_ms / 1000)

    df = (pd.concat([df, df2], axis=1))

    return df

def images_sidebar(dfs):

    for item in dfs[0]['image_med']:
        st.sidebar.image(item)

    return



@st.cache(suppress_st_warning=True, show_spinner=False, allow_output_mutation=True)
def data_viz(df_all):
    top_artists = df_all.sort_values(['track_name'],ascending=[True]).groupby('album')
    df_all['count'] = df_all.groupby('artist')['artist'].transform('count')
    top_songs_album = df_all.sort_values(['count'],ascending=[False]).groupby('timeline').head(20)

#    test = df_all.groupby('album')['timeline'].value_counts()
#    test.rename(column={"timeline": "count"})
#    test = test.reset_index()

    test = df_all.value_counts(['album', 'timeline']).reset_index(name='count')
    test = test.sort_values(['count'],ascending=[False])

    st.write(test)

    st.write(test.sort_values(['count'],ascending=[False]))
    df_match = dfs[0][['track_name','position']]
    df_match['matchsm'] = 0

    short = dfs[0][["position", "track_name"]]
    med = dfs[1][["position", "track_name"]]
    long = dfs[2][["position", "track_name"]]

    df = short.merge(med, how='outer', on='track_name')
    df = df.merge(long, how='outer', on='track_name')

    df = df.fillna(51)

    df['position_x'] = 50 - df['position_x']
    df['position_y'] = 50 - df['position_y']
    df['position'] = 50 - df['position']

    fig_artist_all = px.histogram(top_songs_album,
                 category_orders={'timeline':["short_term", "medium_term", "long_term"]},
                 x='artist',
                 barmode='stack',
                 color='timeline',
                 height=400,
                 color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    fig_album_all = px.histogram(test[:20],
                 category_orders={'timeline': ["short_term", "medium_term", "long_term"]},
                 x='album',
                 y='count',
                 barmode='stack',
                 color='timeline',
                 height=400,
                 color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    fig_scatter = px.scatter(df_all,
                 x=df_all.index,
                 y='popularity',
                 color='timeline',
                 category_orders={'timeline': ["short_term", "medium_term", "long_term"]},
                 hover_data=["track_name", "artist"],
                 height=400,
                 color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    st.write(top_artists)

    st.write(top_songs_album)


    fig_ex = px.histogram(df_all,
                y ='explicit',
                 color='timeline',
                barmode = 'group',
                          category_orders={'timeline': ["short_term", "medium_term", "long_term"]},
                 height=400,
                 color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    fig_violin = px.violin(df_all,
              x="energy",
                           title='Energy',
                           color='timeline',
              height=600,
              hover_name='track_name',
              hover_data=['artist'],
              orientation='h',
                           category_orders={'timeline': ["short_term", "medium_term", "long_term"]},
              box=True,
              points="all",
              color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    fig_violin2 = px.violin(df_all,
              x="popularity",
              title='Popularity',
              color='timeline',
              height=600,
              hover_name='track_name',
              hover_data=['artist'],
              orientation='h',
                            category_orders={'timeline': ["short_term", "medium_term", "long_term"]},
              box=True,
              points="all",
              color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    fig_violin3 = px.violin(df_all,
              x="valence",
              title='Tracks Valence',
              color='timeline',
              height=600,
              hover_name='track_name',
              hover_data=['artist'],
              orientation='h',
                            category_orders={'timeline': ["short_term", "medium_term", "long_term"]},
              box=True,
              points="all",
              color_discrete_sequence=px.colors.cyclical.mygbm[11:])

    figs = [fig_artist_all,fig_album_all,fig_scatter,fig_ex,fig_violin,fig_violin2,fig_violin3]

    return figs


dfs,token,usernamesp = spotify_50()
images_sidebar(dfs)
df_all = pd.concat([dfs[0],dfs[1],dfs[2]])
figs = data_viz(df_all)

st.header("Top 10")
time = ['Top 50 Short-Term','Top 50 Medium-Term','Top 50 Long-Term']



cols0 = st.beta_columns(3)
cols0[0].subheader('Short')
cols0[1].subheader('Medium')
cols0[2].subheader('Long-Term')

for index, id in enumerate(dfs[0]['track_name'][:10]):
        colsa = st.beta_columns(6)
        colsa[0].image(dfs[0]['image_small'][index])
        colsa[1].write(dfs[0]['track_name'][index])
        colsa[2].image(dfs[1]['image_small'][index])
        colsa[3].write(dfs[1]['track_name'][index])
        colsa[4].image(dfs[2]['image_small'][index])
        colsa[5].write(dfs[2]['track_name'][index])


st.header("Top 50")
for index,item in enumerate(dfs):
    example_expander = st.beta_expander(time[index])
    with example_expander:
        for index, id in enumerate(item['track_name']):
            colsb = st.beta_columns(6)
            colsb[0].image(item['image_small'][index])
            colsb[1].write(item['track_name'][index])
            colsb[2].write(item['artist'][index])
            colsb[3].write(item['album'][index])
            colsb[4].audio(item['preview'][index])


for item in figs:
    st.plotly_chart(item)

tracks = list(set(df_all.track_name))
artists = list(set(df_all.artist))
genres = (get_genres(usernamesp))
max_length = int(max(df_all.duration))
min_length = int(min(df_all.duration))

artist_dict = pd.Series(df_all.artist_uri.values,index=df_all.artist).to_dict()
track_dict = pd.Series(df_all.id.values,index=df_all.track_name).to_dict()

major_keys = {0: 'C Major',
                  1: 'C# Major',
                  2: 'D Major',
                  3: 'D# Major',
                  4: 'E Major',
                  5: 'F Major',
                  6: 'F# Major',
                  7: 'G Major',
                  8: 'G# Major',
                  9: 'A Major',
                  10: 'A# Major',
                  11: 'B Major'}

minor_keys = {0: 'C Minor',
                  1: 'C# Minor',
                  2: 'D Minor',
                  3: 'D# Minor',
                  4: 'E Minor',
                  5: 'F Minor',
                  6: 'F# Minor',
                  7: 'G Minor',
                  8: 'G# Minor',
                  9: 'A Minor',
                  10: 'A# Minor',
                  11: 'B Minor'}

st.header("Now lets find songs based on your favourites")


a = st.multiselect('Artists',artists)
t = st.multiselect('Tracks',tracks)
g = st.multiselect('Genres',list(genres))


check_seeds = len(a) + len(g) + len(t)
if check_seeds ==0:
    st.write('Please select at least one seed.')
    st.stop()

if check_seeds >5:
    st.write('You have selected too many seeds, please choose five total across the three selections.')
    st.stop()

st.write('All values have been preset based on the values from your favourite tracks, but feel free to adjust them')

song_att = ['valence',
            'danceability',
            'energy',
            'speechiness',
            'acousticness']


dict_rec = {}
for index,item in enumerate(song_att):
    dict_rec[item] = st.slider(
        item.capitalize(),
        0.0, 100.0, ((min(df_all[item]*100)), (max(df_all[item]*100)))
        )

for item in dict_rec:
    dict_rec[item] = list(dict_rec[item])
    dict_rec[item][0] = (dict_rec[item][0]) / 100
    dict_rec[item][1] = (dict_rec[item][1]) / 100



dict_rec['loudness'] = st.slider(
            'Loudness',
            0.0, 1.0, ((min(df_all['loudness'])), (max(df_all['loudness'])))
        )



dict_rec['popularity'] = st.slider(
        'Popularity',
        0, 100, ((min(df_all['popularity'])), (max(df_all['popularity'])))
        )

major_keys_sel = st.multiselect('Select Major Key?', list(major_keys.values()),default= list(major_keys.values()))
minor_keys_sel = st.multiselect('Select Minor Key?', list(minor_keys.values()),default= list(minor_keys.values()))
#st.radio('Include explicit tracks?', ('Yes','No'))

major_key_list = []
for item in major_keys_sel:
    major_key_list.append((list(major_keys.keys())[list(major_keys.values()).index(item)]))

minor_key_list = []
for item in minor_keys_sel:
    minor_key_list.append((list(minor_keys.keys())[list(minor_keys.values()).index(item)]))

key_max = max(max(major_key_list), max(minor_key_list))
key_min = min(min(major_key_list), min(minor_key_list))

min_mode = 0
max_mode = 1
if len(minor_keys) == 0:
    min_mode = 1
if len(major_keys) == 0:
    max_mode = 0


dict_rec['duration'] = st.slider(
    'Song Length in seconds',
    0, 900, (min_length, max_length)
)

dict_rec['tempo'] = st.slider(
        'Tempo (BPM)',
        0.0, 250.00, ((min(df_all['tempo'])), (max(df_all['tempo'])))
        )

a_api = []
for item in a:
    a_api.append(artist_dict[item])


t_api = []
for item in t:
    t_api.append(track_dict[item])


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                                   client_secret=client_secret,
                                                   redirect_uri=redirect,
                                                   scope=scope))


#get_playlist =  st.button('Get playlist?')
#if not get_playlist:
#    st.stop()


playlist = sp.recommendations(seed_artists=a_api, seed_genres=g, seed_tracks=t_api,
                              min_valence=dict_rec['valence'][0],
                              min_danceability=dict_rec['danceability'][0],
                              min_energy=dict_rec['energy'][0],
                              min_speechiness=dict_rec['speechiness'][0],
                              min_acousticness=dict_rec['acousticness'][0],
                              min_loudness=dict_rec['loudness'][0],
                              min_popularity=dict_rec['popularity'][0],
                              min_key=key_min,
                              min_tempo=dict_rec['tempo'][0],
                              min_duration_ms=(dict_rec['duration'][0])*100,
                              min_mode=min_mode,

                              max_valence=dict_rec['valence'][1],
                              max_danceability=dict_rec['danceability'][1],
                              max_energy=dict_rec['energy'][1],
                              max_speechiness=dict_rec['speechiness'][1],
                              max_acousticness=dict_rec['acousticness'][1],
                              max_loudness=dict_rec['loudness'][1],
                              max_popularity=dict_rec['popularity'][1],
                              max_key=key_max,
                              max_tempo=dict_rec['tempo'][1],
                              max_duration_ms=(dict_rec['duration'][1])*1000,
                              max_mode=max_mode,

                              )

playlist_length = len(playlist['tracks'])
if playlist_length == 0:
    st.write("No tracks could be found that fit those values.")
    st.stop()

playlist_uri = []
playlist_artist = []
playlist_track = []
playlist_preview = []

for index,item in enumerate(playlist['tracks']):
    playlist_uri.append(playlist['tracks'][index]['id'])
    playlist_artist.append(playlist['tracks'][index]['artists'][0]['name'])
    playlist_track.append(playlist['tracks'][index]['name'])
    playlist_preview.append(playlist['tracks'][index]['preview_url'])

df = pd.DataFrame(list(zip(playlist_track, playlist_artist,playlist_uri,playlist_preview)), columns =['Track', 'Artist','track_uri','playlist_preview'])
df_table = pd.DataFrame(columns =['Track', 'Artist','Preview'])
playlist_df = audio_features(df)

st.write("\n")
st.write("\n")
st.write("\n")
st.header("Generated Playlist:")
cols1 = st.beta_columns(3)
cols1[0].write('Track')
cols1[1].write('Artist')
cols1[2].write('Preview')

for index,item in enumerate(playlist_df.index):
    cols = st.beta_columns(3)
    cols[0].write(playlist_df.Track[index])
    cols[1].write(playlist_df.Artist[index])
    cols[2].audio(playlist_df.playlist_preview[index])

st.header('Add the playlist to your Spotify Account')
playlist_name = st.text_input('Name Playlist:', value='Generated Playlist', max_chars=30)

add_playlist =  st.button('Add playlist to your Spotify account:')
if not add_playlist:
    st.stop()
if len(playlist_name) ==0:
    playlist_name = "Generated Playlist"
    st.stop()

playlist_10 = sp.user_playlist_create(usernamesp, playlist_name, public=False, collaborative=False, description='')
playlist_10 =  sp.user_playlist_add_tracks(usernamesp, playlist_10['id'], playlist_df.uri)









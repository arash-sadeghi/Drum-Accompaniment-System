import numpy as np
import os
from time import time , ctime, sleep

def get_time():
    return ctime(time()).replace(':','_').replace(' ','_')

class CONST:
    beat_resolution = 4  # temporal resolution of a beat (in timestep)
    measure_resolution = 4 * beat_resolution
    # Data
    n_tracks = 2 # 5  # number of tracks
    n_pitches = 72  # number of pitches
    lowest_pitch = 24  # MIDI note number of the lowest pitch
    n_samples_per_song = 5  # number of samples to extract from each song in the datset
    n_measures = 4  # number of measures per sample
    programs = [0, 0, 25, 33, 48]  # program number for each track
    latent_dim = 128
    # Sampling
    n_samples = 10 #! number of samples to be generated in the output when saving results from gan to file.  not and architecture parameter. each sample includes some measure and each measure includes some beats and notes.
    tempo = 120# 100
    tempo_array = np.full((4 * 4 * measure_resolution, 1), tempo)
    genre_code = {
        'Folk' : 0 ,
        'Country' : 1 ,
        'Rap' : 2 ,
        'Blues' : 3 ,
        'RnB' : 4 ,
        'New-Age' : 5 ,
        'Vocal' : 6 ,
        'Reggae' : 7 ,
        'Pop_Rock' : 8 ,
        'Electronic' : 9 ,
        'International' : 10 ,
        'Jazz'  : 11 ,
        'Latin' : 12 ,
    }

    # s3 for weghts
    bucket_name = 'das.backend'
    s3_file_key = 'generator_weights.pth'

    # ROOT = os.path.dirname(os.path.abspath(__file__)) #!root path. this is for deployment
    # os.path.join(ROOT,
    generator_file_path = 'models/generator_weights.pth'
    result_path =  "models"

    TIME_WINDOW = 30
    MIDI_OUT_PORT = 'IAC Driver Bus 2'
    MIDI_INPUT_PORT = 'IAC Driver Bus 1'
    GENRE = 'Pop_Rock'
    _current_time = get_time()
    SAVE_PATH = os.path.join(result_path,f'generated_drum_{GENRE}_{_current_time}')

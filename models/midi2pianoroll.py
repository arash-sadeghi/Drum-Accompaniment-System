import pretty_midi
import pypianoroll

from models.CONST_VARS import CONST
# from CONST_VARS import CONST

import os
import matplotlib.pyplot as plt

def plot_multitrack(multitrack,path):
    time_trim = 20*CONST.measure_resolution #* draw only first 20 measures of song
    for c,v in enumerate(multitrack.tracks):
        multitrack.tracks[c].pianoroll = multitrack.tracks[c].pianoroll[:time_trim,:]
    axs = multitrack.plot()
    plt.gcf().set_size_inches((16, 8))
    #! this for loop only puts horizontal line in plot
    for ax in axs:
        for x in range(CONST.measure_resolution, time_trim, CONST.measure_resolution): #! data.shape[0]*data.shape[2]: samples * notes in each samples: whole notes
            if x % (CONST.measure_resolution * 4) == 0: #! marks 1 measure
                ax.axvline(x - 0.5, color='k')
            else:
                ax.axvline(x - 0.5, color='k', linestyle='-', linewidth=1) #! marks one beat of 4/4 (might include few notes)
    # plt.tight_layout()
    plt.savefig(path)

def keep_bass_only(midi):
    for instr in midi.instruments:
        if "Bass" in instr.name:
            midi.instruments = [instr]
            return midi


def midi_to_piano_roll(midi_file_path = '',midi_data=None):

    if midi_data is None: 
        midi_data = pretty_midi.PrettyMIDI(midi_file_path)
        midi_data = keep_bass_only(midi_data)
    else:
        midi_data.time_signature_changes.append(pretty_midi.TimeSignature(numerator=4,denominator=4,time=0))
    multi_track = pypianoroll.from_pretty_midi(midi_data,algorithm='strict')
    multi_track.set_resolution(CONST.beat_resolution) 
    multi_track.binarize()
    # plot_multitrack(multi_track.copy(),output+".png")
    piano_roll = multi_track.stack()
    # multi_track.write(output+"midi")
    return piano_roll.squeeze() , multi_track.tempo


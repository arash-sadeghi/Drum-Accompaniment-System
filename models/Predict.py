from models.Generator import Generator
from models.midi2pianoroll import midi_to_piano_roll, plot_multitrack
from models.CONST_VARS import CONST

# from Generator import Generator
# from midi2pianoroll import midi_to_piano_roll , plot_multitrack
# from CONST_VARS import CONST

from models.utils import generator_weight_provider

import torch
import numpy as np 
from pypianoroll import Multitrack, BinaryTrack

import pretty_midi
import mido
import mido.backends.rtmidi

import threading
import queue

import os
from time import time

# from Velocity_assigner.assign_velocity import VelocityAssigner

from mido import get_input_names, get_output_names
from models.Midi_receive_handler import Midi_Receive_Handler
from models.midi_publish_handler import Midi_Publish_Handler

def replace_drum(DB_path, D_path, output_path, vels):
    DB = pretty_midi.PrettyMIDI(DB_path)
    D = pretty_midi.PrettyMIDI(D_path)
    # D.set_resolution
    # DB.instruments[0] = D.instruments[0]
    for note_counter in range(len(DB.instruments[0].notes)):
        DB.instruments[0].notes[note_counter].velocity = vels[note_counter]
    DB.write(output_path)

class Predictor:
    WEIGHT_PATH = CONST.generator_file_path
    GENRE = CONST.GENRE
    RES_PATH = CONST.result_path
    SAVE_PATH = CONST.SAVE_PATH

    def __init__(self) -> None:
        self.generator = Generator()   
        generator_weight_provider() #! makes sure generator weghts are downloaded and ready to use
        self.generator.load_state_dict(torch.load(Predictor.WEIGHT_PATH , map_location=torch.device('cpu'))) #TODO specific to cpu machine only
        self.generator.eval() #! this solve error thrown by data length
        self.MRH = Midi_Receive_Handler()
        self.MPH = Midi_Publish_Handler()

    def generate_drum(self, bass_piano_roll = None, tempo_array = None, bass_url = None):
        print("[+] Predictor predicting offline drum")
        if not bass_url is None:
            bass_piano_roll , tempo_array = midi_to_piano_roll(bass_url)
        #TODO what is 64 here?
        #* padding to make output size divident of 64
        pad_size = 64 - bass_piano_roll.shape[0]%64
        # pad = np.zeros((pad_size , bass_piano_roll.shape[1])) #* zero padding which affects the generated music
        pad = bass_piano_roll[bass_piano_roll.shape[0]-pad_size: , :] #* padding with copying last frame
        bass_piano_roll = np.concatenate((bass_piano_roll,pad),axis=0)
        # bass_piano_roll = bass_piano_roll[:bass_piano_roll.shape[0]//64*64,:] #* no padding and cutting the excess part. Will generate better results but input and output are not of same size

        #* check to see if there were any out iof range pitch
        illegal_pitches_up = bass_piano_roll[:,:CONST.lowest_pitch]
        illegal_pitches_down = bass_piano_roll[:,CONST.lowest_pitch + CONST.n_pitches:]
        if not np.all(illegal_pitches_up == 0) :
            print("[-] Illegal up note")
        if not np.all(illegal_pitches_down == 0) :
            print("[-] Illegal down note")

        bass_piano_roll = torch.tensor(bass_piano_roll) #! in webgui blocks execution
        bass_piano_roll = bass_piano_roll[:,CONST.lowest_pitch:CONST.lowest_pitch + CONST.n_pitches] 
        bass_piano_roll = bass_piano_roll.view(-1,64,72)

        latent = torch.randn(bass_piano_roll.shape[0], CONST.latent_dim)
        latent = latent.type(torch.float32)
        bass_piano_roll = bass_piano_roll.type(torch.float32)

        genre_tensor = torch.tensor(CONST.genre_code[Predictor.GENRE]).repeat((bass_piano_roll.shape[0])) #* repeat to the size of samples
        res = self.generator(latent,bass_piano_roll,genre_tensor)

        #* reshaping data inorder to be saved as image
        temp = torch.cat((res.cpu().detach(),bass_piano_roll.unsqueeze(1)),axis = 1).numpy()
        temp = temp.transpose(1,0,2,3)

        #TODO test: filling process time by repeating last measures
        temp = np.concatenate((temp,temp[:,-1:,:,:]),axis=1)

        temp = temp.reshape(temp.shape[0] , temp.shape[1] * temp.shape[2] , temp.shape[3])

        #* removing padding
        temp = temp[:, 0:temp.shape[1]-pad_size ,:]

        # plt.imshow(temp[1])

        print(f"[+][GENERATor] after bass_piano_roll shape {temp[1].shape}")

        tracks = []
        drum_track = []
        for idx, (program, is_drum, track_name) in enumerate(zip([0,33], [True,False], ['Drum','Bass'])):
            pianoroll = np.pad(temp[idx] > 0.5,((0, 0), (CONST.lowest_pitch, 128 - CONST.lowest_pitch - CONST.n_pitches)))
            tracks.append(BinaryTrack(name=track_name,program=program,is_drum=is_drum,pianoroll=pianoroll))

            if track_name == 'Drum':
                drum_track.append(BinaryTrack(name=track_name,program=program,is_drum=is_drum,pianoroll=pianoroll))


        multi_track = Multitrack(tracks=tracks,tempo=tempo_array,resolution=CONST.beat_resolution)
        multi_track_drum = Multitrack(tracks=drum_track,tempo=tempo_array,resolution=CONST.beat_resolution)

        # plot_multitrack(multi_track.copy() , Predictor.SAVE_PATH+'.png') #! causes error from app by flask
        DB_midi = multi_track.to_pretty_midi()
        output_midi_name = Predictor.SAVE_PATH+'DB.midi'
        DB_midi.write(output_midi_name)

        output_midi_drum_name = Predictor.SAVE_PATH+'D.midi'
        multi_track_drum.to_pretty_midi().write(output_midi_drum_name)
        return DB_midi , output_midi_name , output_midi_drum_name
    

    def generate_drum_thread(self):
        while not self.stop_listening :
            lsitened_queue = self.MRH.get_result_queue()
            if lsitened_queue.qsize() == 0:
                continue

            recieved_painoroll = lsitened_queue.get()  # Get messages from the queue
            print("[Predictor] generating drum")
            drum_midi , _ , _ = self.generate_drum(recieved_painoroll["piano_roll"] , recieved_painoroll["tempo"])

            lsitened_queue.task_done()

            print("[Predictor] sent to publish in queue")
            self.MPH.get_queue().put(drum_midi)

        
    def real_time_setup(self,socket, app):
        print("[+] real_time_loop started")
        self.MRH.init()
        self.MPH.set_socket(socket, app)
        self.stop_listening = False

        self.lock = threading.Lock() #TODO should this be set to other classed MPH and MRH as well?

        self.processing_thread_drum_gen = threading.Thread(target=self.generate_drum_thread)
        self.processing_thread_drum_gen.start()


    def real_time_receive(self,message):
        self.MRH.recieve_midi(message)

    def stop_real_time(self):
        print("[Predictor] stopping realtime loop ... ")
        self.stop_listening = True
        self.processing_thread_drum_gen.join()
        self.MPH.stop_listening()
        self.MRH.stop_listening()
        print("[Predictor] realtime loop stoped")





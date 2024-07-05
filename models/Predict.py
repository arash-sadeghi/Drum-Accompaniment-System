# from models.Generator import Generator
# from models.midi2pianoroll import midi_to_piano_roll, plot_multitrack
# from models.CONST_VARS import CONST

from Generator import Generator
from midi2pianoroll import midi_to_piano_roll , plot_multitrack
from CONST_VARS import CONST

import matplotlib.pyplot as plt

import torch
import numpy as np 
from pypianoroll import Multitrack, BinaryTrack

import pretty_midi
import mido
from time import time , ctime

import threading
import queue

import os

# from Velocity_assigner.assign_velocity import VelocityAssigner

from mido import get_input_names, get_output_names


TIME_WINDOW = 30


class Predictor:
    ROOT = os.path.dirname(os.path.abspath(__file__)) #!root path. this is for deployment
    # WEIGHT_PATH = 'training_output_path_rootgenerator_20000.pth'
    # WEIGHT_PATH = 'models\generator_800.pth'
    # WEIGHT_PATH = os.path.join('models','generator_19900.pth')
    WEIGHT_PATH = os.path.join(ROOT,'generator_weights.pth')
    # WEIGHT_PATH = os.path.join('models','generator_weights.pth')
    # WEIGHT_PATH = os.path.join('models','training_output_path_rootgenerator_20000.pth')
    GENRE = 'Pop_Rock' #'Latin' #
    EXECUTION_TIME = ctime(time()).replace(':','_').replace(' ','_')
    RES_PATH = os.path.join(ROOT,'results')
    SAVE_PATH = os.path.join(RES_PATH,f'generated_drum_{GENRE}_{EXECUTION_TIME}')
    
    def __init__(self) -> None:
        print("[+] Predict ROOT",Predictor.ROOT)
        self.generator = Generator()    
        self.generator.load_state_dict(torch.load(Predictor.WEIGHT_PATH , map_location=torch.device('cpu'))) #TODO specific to cpu machine only
        self.generator.eval() #! this solve error thrown by data length
        self._MIDI_OUT_PORT = 'IAC Driver Bus 2'
        self._MIDI_INPUT_PORT = 'IAC Driver Bus 1'

    def set_midi_io(self,midiin,midiout):
        # self._MIDI_OUT_PORT = 'IAC Driver Bus 2'
        # self._MIDI_INPUT_PORT = 'A-PRO 1'
        self._MIDI_OUT_PORT = midiout
        self._MIDI_INPUT_PORT = midiin

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

        print("[+] Predictor Done")
        return DB_midi , output_midi_name , output_midi_drum_name
    
    def publish_midi(self):
        while not self.stop_listening :
            publish_duration = time()
            if self.processing_queue_2Bpublished.qsize() == 0:
                continue
            pretty_midi_messages = self.processing_queue_2Bpublished.get()  # Get messages from the queue
            self.processing_queue_2Bpublished.task_done()  # Mark the task as done

            # pretty_midi_messages = pretty_midi.PrettyMIDI('test.midi')
            drum = None
            for instrument in pretty_midi_messages.instruments:
                if instrument.is_drum: #TODO debug
                    drum = instrument
                    break
            
            assert not (drum is None)

            # start_time = time()
            #     passed_time = time() - start_time
            mido_messages = []
            for note in drum.notes:
                mido_messages.append(mido.Message('note_on', note=note.pitch, velocity=note.velocity, time = note.start))
                mido_messages.append(mido.Message('note_off', note=note.pitch, velocity=0,time=note.end))

            mido_messages_sorted = sorted(mido_messages, key=lambda x: x.time)
            midi_duration = mido_messages_sorted[-1].time
            print(f"[+][PUBLISHER] MIDI duration {midi_duration} and number of midi messages {len(mido_messages_sorted)}")
            start_time = time()
            passed_time = time() - start_time
            message_counter = 0
            print(f"[+][PUBLISHER] from listening to publishing took {time()-self.process_begin_time}")
            #TODO bypassing while time check to allow generation of drum more than time window for jamming test purpose
            # while passed_time <= TIME_WINDOW:
            while True:
                passed_time = time() - start_time
                if mido_messages_sorted[message_counter].time - passed_time <=0.001:
                    self.midi_port_out.send(mido_messages_sorted[message_counter])
                    # print(f"[+][PUBLISHER] on time {passed_time} Sent {mido_messages_sorted[message_counter]}")
                    message_counter +=1
                if message_counter >= len(mido_messages_sorted):
                    break

            print(f"[+][PUBLISHER] publishing duration ----> {time()- publish_duration}")
    
    def listen(self):
        '''
        Purpose: 
            Listens to MIDI port and gathers midi notes for the duration of TIME_WINDOW
        Parameters: None
        Raises: None
        Effect: 
            writing into self.processing_queue_listened_midi
        Return: 
            Piano roll representation of listened MIDI messages
        Note: 
            process_begin_time begins after gathering MIDI.
        '''
        while not self.stop_listening:
            # message = self.midi_port_in.receive()
            listen_start_time = time()
            pm_data = pretty_midi.PrettyMIDI()  # Create empty PrettyMIDI object
            bass = pretty_midi.Instrument(program=33) #! 33 is bass program code. got from CGAN repo
            start_time = time()
            end_time = start_time + TIME_WINDOW  # Listen for 10 seconds
            ons = {} #* this dictionary enables us to capture cords

            # while time() < end_time:
            #     for message in self.midi_port_in.iter_pending():

            for message in self.midi_port_in:
                # print(f"[+][Listener] on time {time()-start_time} message {message}")
                if time() >= end_time:
                    print(f"[debug] time over. start {start_time} end {end_time}, curr {time()} , dur {end_time-start_time}")
                    if len(bass.notes) == 0: #! if the bass notes are empty, dont return it, go back and listen from the beggining
                        start_time = time()
                        end_time = start_time + TIME_WINDOW  # Listen for 10 seconds
                        continue

                    break #! if bass notes are not empty then break it for processing

                # track.append(message)
                elif message.type == 'note_on':
                    note_beg = time() - start_time
                    ons[str(message.note)] = note_beg

                elif message.type == 'note_off':
                    if str(message.note) in ons.keys():
                        note_end = time() - start_time
                        note = pretty_midi.Note(
                            velocity=message.velocity, #! this is not accurate becuse note on and note off velocities are different
                            pitch=message.note,
                            start=ons[str(message.note)],
                            end=note_end
                            )

                        bass.notes.append(note)  # Append note to first instrument

            self.process_begin_time = time()
            pm_data.instruments.append(bass)
            print(f"[+][Listener] number of midi messages listener received {len(bass.notes)} listening duration {time()-listen_start_time} note time duration {bass.notes[0].start - bass.notes[-1].end}")
            pm_data.write(os.path.join(Predictor.RES_PATH,"listened_midi.midi")) #* no problem here
            piano_roll , tempo = midi_to_piano_roll(midi_data = pm_data) #! problem
            self.processing_queue_listened_midi.put({'piano_roll' , piano_roll , 'tempo' , tempo})

    def real_time_loop(self):
        if self._MIDI_OUT_PORT == '' or self._MIDI_INPUT_PORT == '':
            print("[-] MIDI IO ports not allocated")

        print("[+] real_time_loop started")
        self.stop_listening = False
        self.midi_port_out = mido.open_output(self._MIDI_OUT_PORT)
        self.midi_port_in = mido.open_input(self._MIDI_INPUT_PORT)

        self.lock = threading.Lock()
        self.processing_queue_2Bpublished = queue.Queue()
        self.processing_thread = threading.Thread(target=self.publish_midi)
        self.processing_thread.start()

        self.processing_queue_listened_midi = queue.Queue()
        self.processing_thread_listen = threading.Thread(target=self.listen)
        self.processing_thread_listen.start()

        # self.processing_queue_drum_gen = queue.Queue()
        # self.processing_thread_listen = threading.Thread(target=self.listen)
        # self.processing_thread_listen.start()

        while not self.stop_listening :
            # print(f"[+] listening to bass for {TIME_WINDOW} seconds from port {self._MIDI_INPUT_PORT}")
            # piano_roll , tempo = self.listen()
            if self.processing_queue_listened_midi.qsize() == 0:
                continue
            
            recieved_painoroll = self.processing_queue_listened_midi.get()  # Get messages from the queue
            self.processing_queue_listened_midi.task_done()  # Mark the task as done
            print(f"[+] Got from listenere: {recieved_painoroll}")


            print("[+] generating drum")
            drum_midi , _ , _ = self.generate_drum(recieved_painoroll["piano_roll"] , recieved_painoroll["tempo"])

            print("[+] sent to publish in queue")
            self.processing_queue_2Bpublished.put(drum_midi)


def replace_drum(DB_path, D_path, output_path, vels):
    DB = pretty_midi.PrettyMIDI(DB_path)
    D = pretty_midi.PrettyMIDI(D_path)
    # D.set_resolution
    # DB.instruments[0] = D.instruments[0]
    for note_counter in range(len(DB.instruments[0].notes)):
        DB.instruments[0].notes[note_counter].velocity = vels[note_counter]
    DB.write(output_path)
def get_available_ports():
    inports = get_input_names()
    outports = get_output_names()
    return {'inports': inports , 'outports':outports}

if __name__ == '__main__':
    """
    # offline example
    predictor = Predictor()
    res_path = predictor.generate_drum(bass_url = '/Users/arashsadeghiamjadi/Desktop/WORKDIR/JamBuddy/Server_App/models/results/user_file.midi')
    """

    predictor = Predictor()
    predictor.real_time_loop()

    # print("res_path",res_path)

#     p = Predictor()
#     va = VelocityAssigner()
#     # D_path = "/Users/arashsadeghiamjadi/Desktop/WORKDIR/JamBuddy/Results/Samples/offline_drum.midi"
#     # DB_path = "/Users/arashsadeghiamjadi/Desktop/WORKDIR/JamBuddy/Results/Samples/generated_drum_Pop_Rock_Fri_May_17_01_18_42_2024DB.midi"
#     D_path = "/Users/arashsadeghiamjadi/Desktop/WORKDIR/JamBuddy/Server_App/static/midi/for_publishing/generated drum of given LPD bass D.midi"
#     DB_path = "/Users/arashsadeghiamjadi/Desktop/WORKDIR/JamBuddy/Server_App/static/midi/for_publishing/generated drum with given bass.midi"
#     drum_with_velocity_path , vels = va.assing_velocity2midi(D_path)
#     DB_with_vel_path = 'LPD_DB_with_vel.midi'
#     replace_drum(DB_path , drum_with_velocity_path , DB_with_vel_path , vels)

#     # p.real_time_loop()

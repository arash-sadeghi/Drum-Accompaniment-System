import pretty_midi
from time import time , sleep
from models.CONST_VARS import CONST
from models.midi2pianoroll import midi_to_piano_roll
from dataclasses import dataclass
import threading
import queue
import os
@dataclass
class Message:
    type: str
    note: int
    velocity: int
    time: float


class Midi_Receive_Handler:
    def __init__(self) -> None:
        self.initilized = False
        self.stop_listening_flag = False
        self.message_queue = queue.Queue()
        self.result_queue = queue.Queue()
        processing_thread = threading.Thread(target=self.message_processor, daemon=True)
        processing_thread.start()

    def init(self):
        self.pm_data = pretty_midi.PrettyMIDI()  # Create empty PrettyMIDI object
        self.bass = pretty_midi.Instrument(program=33) #! 33 is bass program code. got from CGAN repo
        self.batch_start_time = time()
        self.ons = {} #* this dictionary enables us to capture cords
        print('[listener] batch started')
        self.initilized = True

    def get_initilized(self):
        return self.initilized

    def message_processor(self):
        while not self.stop_listening_flag:
            if self.message_queue.qsize == 0 :
                continue

            message = self.message_queue.get(block=True)
            if message.type == 'note_on':
                note_beg = message.time  - self.batch_start_time #TODO mixing fronted and backend time
                self.ons[str(message.note)] = note_beg

            elif message.type == 'note_off':
                if str(message.note) in self.ons.keys():
                    note = pretty_midi.Note(
                        velocity=message.velocity, #! this is not accurate becuse note on and note off velocities are different
                        pitch=message.note,
                        start = self.ons[str(message.note)],
                        end = message.time - self.batch_start_time   #TODO mixing fronted and backend time
                        )
                    self.bass.notes.append(note)  # Append note to first instrument

            if time() - self.batch_start_time <= CONST.TIME_WINDOW: #! keep collecting same batch
                continue
            
            if len(self.bass.notes) == 0: #! if the bass notes are empty, dont return it, go back and listen from 
                continue

            self.pm_data.instruments.append(self.bass)

            print(f"[+][Listener][{threading.current_thread()}] listener received {len(self.bass.notes)} messages. \n listening duration {round(time()-self.batch_start_time,2) } midi note duration {round(self.bass.notes[-1].end - self.bass.notes[0].start,2)}")

            piano_roll , tempo = midi_to_piano_roll(midi_data = self.pm_data) #! problem
            self.pm_data.write("xxxxlistened_midi.midi")
            self.message_queue.task_done()
            self.result_queue.put({"piano_roll": piano_roll , "tempo":tempo})
            self.init()
            
    def recieve_midi(self,message_dict):
        message = Message(message_dict['type'] , message_dict['note'] , message_dict['velocity'] , message_dict['time'])
        self.message_queue.put(message)

    def get_result_queue(self):
        return self.result_queue

    def stop_listening(self):
        self.processing_thread.join()
        self.stop_listening_flag = True


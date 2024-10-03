from time import time
import mido
import threading
import queue
import json
from numpy import int64
import mido #TODO debug
class Midi_Publish_Handler:

    def __init__(self) -> None:
        self.processing_queue_2Bpublished = queue.Queue()
        self.socket = None
        self.stop_listening_flag = False
        self.processing_thread = threading.Thread(target=self.publish, daemon=True)
        self.processing_thread.start()
        # self.midi_port_out = mido.open_output('IAC Driver Bus 3') #TODO debug

    def stop_listening(self):
        self.stop_listening_flag = True 
        self.processing_thread.join()

    def set_socket(self,socket):
        self.socket = socket

    def get_queue(self):
        return self.processing_queue_2Bpublished

    def publish(self):
        while not self.stop_listening_flag :
            publish_duration = time()
            if self.socket is None or self.processing_queue_2Bpublished.qsize() == 0:
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
            # mido_messages_mido = []#TODO debug
            for note in drum.notes:
                #! trying to avoid sending mido through websocket
                # mido_messages_mido.append(mido.Message('note_on', note=note.pitch, velocity=note.velocity, time = note.start))#TODO debug
                # mido_messages_mido.append(mido.Message('note_off', note=note.pitch, velocity=0,time=note.end))#TODO debug
                mido_messages.append({'type':'note_on', 'note' : int(note.pitch), 'velocity': int(note.velocity), "time" : float(round(note.start,2))})
                mido_messages.append({'type':'note_off', 'note' : int(note.pitch), 'velocity': 0, "time" : float(round(note.end,2))})
            
            mido_messages_sorted = sorted(mido_messages, key=lambda x: x["time"])
            # mido_messages_mido_sorted = sorted(mido_messages_mido, key=lambda x: x.time)#TODO debug

            print('emitting')
            # self.socket.emit('server_message', mido_messages_sorted, namespace='/realtime')

            # midi_duration = mido_messages_sorted[-1].time
            # print(f"[+][PUBLISHER] MIDI duration {midi_duration} and number of midi messages {len(mido_messages_sorted)}")
            start_time = time()
            passed_time = time() - start_time
            message_counter = 0
            # print(f"[+][PUBLISHER] from listening to publishing took {time()-self.process_begin_time}")
            #TODO bypassing while time check to allow generation of drum more than time window for jamming test purpose
            while True:
                passed_time = time() - start_time
                if mido_messages_sorted[message_counter]['time'] - passed_time <=0.001:
                    self.socket.emit('server_message', [mido_messages_sorted[message_counter]], namespace='/realtime')
                    # self.midi_port_out.send(mido_messages_mido_sorted[message_counter])#TODO debug
                    # print(f"[+][PUBLISHER] on time {passed_time} Sent {mido_messages_sorted[message_counter]}")
                    message_counter +=1
                if message_counter >= len(mido_messages_sorted):
                    break

            # print(f"[+][PUBLISHER] publishing duration ----> {time()- publish_duration}")
    
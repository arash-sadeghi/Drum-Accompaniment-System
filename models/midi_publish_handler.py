from time import time
import mido
import threading
import queue
import json
from numpy import int64
from flask_socketio import emit #TODO debug

class Midi_Publish_Handler:

    def __init__(self) -> None:
        self.processing_queue_2Bpublished = queue.Queue()
        self.socket = None
        self.stop_listening_flag = False
        self.processing_thread = threading.Thread(target=self.publish, daemon=True)
        self.emit = emit
        self.app = None

    def stop_listening(self):
        self.stop_listening_flag = True 
        self.processing_thread.join()

    def set_socket(self,socket, app):
        self.socket = socket
        self.test()
        self.processing_thread.start()
        self.app = app #TODO fix emit coantext probelm


    def test(self):
        self.emit('HI', {'message': 'Hello from the server from MPH!'},namespace='/realtime',broadcast=True)


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

            mido_messages = []
            for note in drum.notes:
                #! trying to avoid sending mido through websocket
                mido_messages.append({'type':'note_on', 'note' : int(note.pitch), 'velocity': int(note.velocity), "time" : float(round(note.start,2))})
                mido_messages.append({'type':'note_off', 'note' : int(note.pitch), 'velocity': 0, "time" : float(round(note.end,2))})
            
            mido_messages_sorted = sorted(mido_messages, key=lambda x: x["time"])
            # mido_messages_mido_sorted = sorted(mido_messages_mido, key=lambda x: x.time)#TODO debug

            print('emitting')
            # self.socket.emit('server_message', mido_messages_sorted, namespace='/realtime', broadcast=True)    
            self.socket.emit('server_message', mido_messages_sorted, namespace='/realtime')    
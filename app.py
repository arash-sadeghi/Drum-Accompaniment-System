from flask import Flask, render_template, request, redirect, flash, jsonify, make_response, url_for,session
from werkzeug.utils import secure_filename
from models.Predict import Predictor
import os
import json
# from models.Velocity_assigner.assign_velocity import VelocityAssigner 

from models.utils import is_running_in_docker

from flask_socketio import SocketIO, emit

from flask_session import Session

predictor = Predictor()
# va = VelocityAssigner()

#Save images to the 'static' folder as Flask serves images from this directory
UPLOAD_FOLDER = 'models/'
ROOT = os.path.dirname(os.path.abspath(__file__)) #!root path. this is for deployment

#Create an app object using the Flask class. 
app = Flask(__name__, static_folder="static")
socketio = SocketIO(app, cors_allowed_origins="*")  # Enable WebSocket support

# Configure the secret key for encryption (required by Flask-Session)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Configure Flask-Session to use filesystem (you can use other backends as per your needs)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

#Add reference fingerprint. 
#Cookies travel with a signature that they claim to be legit. 
#Legitimacy here means that the signature was issued by the owner of the cookie.
#Others cannot change this cookie as it needs the secret key. 
#It's used as the key to encrypt the session - which can be stored in a cookie.
#Cookies should be encrypted if they contain potentially sensitive information.
app.secret_key = "secret key"

#Define the upload folder to save images uploaded by the user. 
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#Define the route to be home. 
#The decorator below links the relative route of the URL to the function it is decorating.
#Here, index function is with '/', our root directory. 
#Running the app sends us to index.html.
#Note that render_template means it looks for the file in the templates folder. 
@app.route('/')
def index():
    session['tab'] = 'offline'  # Initialize or update session variable
    return render_template('index.html' ,active_tab=session.get('tab'))

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('message')
def handle_message(message):
    print('Received MIDI data:', json.loads(message))
    socketio.emit('server_message', {'message': 'Hello from the server!'})

# Handle WebSocket disconnect
@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@app.route('/realtime', methods=['POST'])
def realtime():
    print(">"*10,request.method )
    if request.method == 'POST':
        data = request.json
        action = data.get('action')

        if action == 'Start':
            midiin = data.get('midiin')
            midiout = data.get('midiout')
            # midiin = request.form.get('midiin')
            # midiout = request.form.get('midiout')
            print(f"[+][app.py] real time button pressed. Listening to {midiin} and out to {midiout}")
            predictor.set_midi_io(midiin,midiout)
            predictor.real_time_setup()
            # return redirect('/')
            print(url_for('realtime'))
            session['tab'] = 'realtime'  # Store the active tab in session
            # return jsonify({'status': 'success', 'active_tab': 'realtime'})

        elif action == 'Stop':
            predictor.stop_real_time()
            session['tab'] = 'realtime'  # Store the active tab in session
            # return jsonify({'status': 'success', 'active_tab': 'realtime'})
            print(f"[+][app.py] real time stopped")



        return jsonify(success=True)

@app.route('/offline', methods=['POST'])
def submit_file():
    global res_path
    print("request made to offlione --------------")
    if request.method == 'POST':
        # Check if the file is present in the request
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        # Check if the file name is empty
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        
        # Check the file size
        if 'file' in request.files and request.files['file'].content_length > 5 * 1024 * 1024:  # 5 MB
            flash('File size exceeds 5 MB. Please upload a smaller file.')
            return redirect(request.url)
        
        if file:
            filename = secure_filename(file.filename)  # Use this werkzeug method to secure filename.
            save_path = os.path.join(ROOT,app.config['UPLOAD_FOLDER'],'user_file.midi')
            file.save(save_path)
            _ , res_path , _ = predictor.generate_drum(bass_url = save_path)

            checkbox_value = request.form.get('assing-velocity', None)

            if checkbox_value == 'on':
                print('[+] calculating velocities')
                # va.assing_velocity2midi(res_path) #! overwrites the given drum midi file

            label = "Drum successfully generated"
            flash(label)
            full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            flash(full_filename)

            with open(res_path,'rb') as f:
                file_content = f.read()
            response = make_response(file_content)

            response.headers['Content-Type'] = 'application/octet-stream'
            response.headers['Content-Disposition'] = 'attachment; filename="'+os.path.basename(res_path)+'"'

            os.remove(res_path)

            return response

if __name__ == "__main__":
    if is_running_in_docker():
        print("[+] RUNNING in docker")
        port = int(os.environ.get('PORT', 3009)) #Define port so we can map container port to localhost
        app.run(host='0.0.0.0', port=port)  #Define 0.0.0.0 for Docker
    else:
        print("[+] RUNNING locally")
        # app.run()
        #! test
        socketio.run(app, host='0.0.0.0', port=3009)



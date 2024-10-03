from flask import Flask, render_template, request, redirect, flash, jsonify, make_response, url_for,session
from models.Predict import Predictor
import os
import json
# from models.Velocity_assigner.assign_velocity import VelocityAssigner 

from models.utils import is_running_in_docker

from flask_socketio import SocketIO, emit

from flask_session import Session

import eventlet

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

# @socketio.on('connect')
@socketio.on('connect', namespace='/realtime')
def handle_connect():
    print('Client connected xxxxxxxxxxxxxxx')

@socketio.on('message')
def handle_message(message):
    print('message rec',message)
    socketio.emit('server_message', {'message': 'Hello from the server!'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')
    predictor.stop_real_time()

@socketio.on('message', namespace='/realtime')
def realtime(data):
    data = json.loads(data)

    if data["action"] == 'Start':
        print(f"[+][app.py] starting real-time")
        predictor.real_time_setup(socketio)

    elif data["action"] == 'Stop':
        print(f"[+][app.py] real time stopped")
        predictor.stop_real_time()

    elif data["action"] == 'Process':
        if predictor.MRH.get_initilized():
            predictor.real_time_receive(data)
        else:
            print('[app.py] MRH is not initilized yet. but now it is')
            predictor.real_time_setup(socketio)


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
            # filename = secure_filename(file.filename)  # Use this werkzeug method to secure filename.
            save_path = os.path.join(ROOT,app.config['UPLOAD_FOLDER'],'user_file.midi')
            file.save(save_path)
            _ , res_path , _ = predictor.generate_drum(bass_url = save_path)

            checkbox_value = request.form.get('assing-velocity', None)

            if checkbox_value == 'on':
                print('[+] calculating velocities')
                # va.assing_velocity2midi(res_path) #! overwrites the given drum midi file

            label = "Drum successfully generated"
            flash(label)
            # full_filename = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # flash(full_filename)

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
        socketio.run(app, host='0.0.0.0', port=5000)
        
    else:
        print("[+] RUNNING locally")
        socketio.run(app, host='0.0.0.0', port=5000)
    # socketio.run(app )


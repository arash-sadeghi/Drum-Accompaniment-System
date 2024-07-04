# Deplyment probelms
## webgui
- bass_piano_roll = torch.tensor(bass_piano_roll) blocks webgui. it doesn't allow for app to continue
    - for now we relly on flask and browser without webgui
## pyinstaller
- [x] pyinstaller couldn't find files and paths but it was ok with other python modules. Solved it by using onedir and getting absolute path by relying on _interanl files

# pyinstaller commands
pyinstaller --name DAM --onefile --paths ./.env/lib/python3.11/site-packages --add-data 'static:static' --add-data 'templates:templates' --add-data 'models/generator_weights.pth:models' app.py

pyinstaller --name DAM --onedir --paths ./.env/lib/python3.11/site-packages --add-data 'static:static' --add-data 'templates:templates' --add-data 'models:models' app.py
## important: 
- velocity assigner changes drum midi pitches
## Todo
- [ ] make generator run on gpu if it finds it avaible
- [ ] decide if docker will be used
    - [ ] transport midi ports to docker
- [ ] remember relative library imports
- [ ] try using velocity assigner in real-time application
## Notes
- generator function works both with files or given bass and tempo. Genre is kept fixed during the whole session
- for logic pro drum note mapping must be checked. Some notes does not exist in a typical drumkit in logi pro
- from listening to publishing processing time takes approximately 0.5s for window of 10s and 0.7s for window of 20s
- The main time difference error was happening from function pypianoroll.from_pretty_midi because without time signiture, it didn't know where is the begginging of midi
- When we add zero padding to music to make it of size 64, the zero padding will affect the last bit of music and always music at the padding part sounds like it is about to end.
    so zero padding affects generated music. will try repeating last session. the time window will have different number of notes inside it each time becauseit depends how many note
    were played in that time frame. Still, measure length should be a function of tempo and rythm.
## How to run locally
- these instructions are for Macos operating system.
- first go ahead and istall docker from this website: https://docs.docker.com/desktop/install/mac-install/
- once docker is installed, open a terminal and copy and paste these commands:
```
docker pull arashsadeghi/drummer-companion:1.0.0
docker run -p 3000:3000 -d arashsadeghi/drummer-companion:1.0.0
```
- now go ahead to your browser and go to this address
```
http://127.0.0.1:3000
```
you should be able to see the app running.
- whenver you want the app to stop running, go to the same terminal that you started the app and pres ```Command + C```. This will stop the app from running

## info
- tempos will change to 100 even if it was different at beggining. but it can be changed by changing tempo variable in constants. 
- generated drum track for the same bass track is very similar. this could be sign of overfitting. but its different than original drum track
- docker build -t flask-app .
- docker run -p 3000:3000 flask-app 
- heroku container:push web --app drummer-companion
- docker inspect --format='{{.Size}}' flask-app-no-torch
- Azure website: drummer-companion-wa.azurewebsites.net

### Docker hub commands:
-  docker build -t drummercompanion .  
-  docker tag drummercompanion arashsadeghi/drummer-companion:latest
- docker login   
- docker push arashsadeghi/drummer-companion:latest   

### Azure commands:
-  docker build -t drummercompanion.azurecr.io/drummercompanion  .
-  docker push drummercompanion.azurecr.io/drummercompanion
- update docker image on azure: [link](https://stackoverflow.com/questions/57241655/switch-docker-image-in-azure-appservice)
### progress
- modifying CGAN to only output drum midi. The whole app will work as such. no more returning bass
- CGAN might be clipping the end of songs. must be checked
- __pycahce__ was geeting copied to docker. that was consuming space and throwing low disk space warning
    - /usr/local/lib/python3.11/site-packages/huggingface_hub/file_download.py:1006: UserWarning: Not enough free disk space to download the file. The expected file size is: 0.00 MB. The target location /root/.cache/huggingface/hub only has 0.00 MB free disk space.


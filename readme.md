# Drum Accompaniment System
## Output samples
- Please refer to this [link](https://arash-sadeghi.github.io/MusicAiPage/) for output samples and explanation of Drum Accompaniment System.

## Access over internet
- access through gui interface at www.dasmusicai.com

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
## Possible Improvements

### Notes
- generator function works both with files or given bass and tempo. Genre is kept fixed during the whole session
- for logic pro drum note mapping must be checked. Some notes does not exist in a typical drumkit in logi pro
- from listening to publishing processing time takes approximately 0.5s for window of 10s and 0.7s for window of 20s
- The main time difference error was happening from function pypianoroll.from_pretty_midi because without time signiture, it didn't know where is the begginging of midi
- When we add zero padding to music to make it of size 64, the zero padding will affect the last bit of music and always music at the padding part sounds like it is about to end.
    so zero padding affects generated music. will try repeating last session. the time window will have different number of notes inside it each time becauseit depends how many note
    were played in that time frame. Still, measure length should be a function of tempo and rythm.

### info
- tempos will change to 100 even if it was different at beggining. but it can be changed by changing tempo variable in constants. 
- generated drum track for the same bass track is very similar. this could be sign of overfitting. but its different than original drum track

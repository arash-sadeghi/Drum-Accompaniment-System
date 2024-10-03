FROM python:3.11.5
RUN apt update
RUN git clone --branch aws-deploy https://github.com/arash-sadeghi/Music-CGAN-app.git /app
RUN apt install -y libasound2 
WORKDIR /app
RUN git pull
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu

#!DEBUG to save time
# COPY models/Predict.py /app/models/
# COPY app.py /app/
# COPY models/midi_publish_handler.py /app/models/ 
# COPY models/Midi_receive_handler.py /app/models/ 
# COPY requirements.txt /app/ 
# COPY models/generator_weights.pth /app/models/ 
# COPY models/CONST_VARS.py /app/models/ 
#!DEBUG to save time

RUN pip install -r requirements.txt
# RUN wget -O models/Velocity_assigner/weights_1500.pts "$(cat BERT_download_link.txt)"


EXPOSE 5000
CMD ["python", "-u",  "app.py"]
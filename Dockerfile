FROM python:3.11.5
RUN git clone https://github.com/arash-sadeghi/Music-CGAN-app.git /app
WORKDIR /app
RUN git pull
RUN /usr/local/bin/python -m pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install torch==2.1.0 --index-url https://download.pytorch.org/whl/cpu
# RUN wget -O models/Velocity_assigner/weights_1500.pts "$(cat BERT_download_link.txt)"

#! for local test only
COPY models/generator_weights.pth /app/models/ 

EXPOSE 3009
CMD ["python", "app.py"]
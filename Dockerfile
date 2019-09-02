FROM python:3.6.7

WORKDIR /ADGLV

COPY . /ADGLV

VOLUME /var/log/ADGLV

RUN pip3 install -r requirements.txt
RUN ln -sf /dev/stdout /var/log/ADGLV/app.log

ENV ADGLV_NODES_PRIVATE_KEY_PASSPHRASE=S3cure PYTHONPATH="/ADGLV/src:/ADGLV/config" ADGLV_LOG_FILE_PATH=/var/log/ADGLV/app.log

CMD ["python3", "./src/runner.py"]

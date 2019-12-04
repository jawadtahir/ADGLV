FROM python:3.6.7

WORKDIR /ADGLV

COPY . /ADGLV

VOLUME /var/log/ADGLV

RUN pip3 install --ignore-installed -r requirements.txt
RUN ln -sf /dev/stdout /var/log/ADGLV/app.log

ENV PYTHONPATH="/ADGLV/src:/ADGLV/config" ADGLV_LOG_FILE_PATH=/var/log/ADGLV/app.log


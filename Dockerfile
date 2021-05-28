FROM python:3          

ENV IP 127.0.0.1
ENV PORT 27017
ENV TOKEN TO_REPLACE

RUN pip3 install mongoengine discord.py
RUN git clone https://github.com/zylozs/jppbot.git

WORKDIR /jppbot

CMD python3 jppbot.py --ip=$IP --port=$PORT --token=$TOKEN
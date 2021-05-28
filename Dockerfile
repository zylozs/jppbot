FROM python:3          

ENV IP 127.0.0.1
ENV PORT 27017
ENV TOKEN TO_REPLACE

COPY run.sh /
RUN chmod +x /run.sh

CMD /run.sh $IP $PORT $TOKEN
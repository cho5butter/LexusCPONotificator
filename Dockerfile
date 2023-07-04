FROM python:3
USER root

WORKDIR /app/

RUN apt-get update
RUN apt-get -y install locales && \
    localedef -f UTF-8 -i ja_JP ja_JP.UTF-8

RUN pip3 install -r requirements.ext

CMD ["python3", "run.py"]
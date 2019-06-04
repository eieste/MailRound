FROM python:3.7.3-stretch


WORKDIR /usr/src/app

COPY mailround/ /usr/src/app

RUN pip install -r requirements.txt


CMD [ "python", "./app.py", "-v" ]

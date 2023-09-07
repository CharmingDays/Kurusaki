FROM python:3.8-bullseye
COPY . .
RUN python -m pip install -r requirements.txt
ENV MONGO=ACCESS_LINK
ENV KURUSAKI=TOKEN
ENV lavalink_server=IP
ENV lavalink_password=PASSWORD
CMD ["python","kurusaki.py"]
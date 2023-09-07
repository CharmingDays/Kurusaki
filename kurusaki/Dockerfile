FROM python:3.8-bullseye
COPY . .
RUN python -m pip install -r requirements.txt
ENV MONGO=mongodb+srv://CharmingMother:QtbjhKhM3GJ6cJph@cluster0.xuwag.mongodb.net/?retryWrites=true&w=majority
ENV KURUSAKI=NDAzNDAyNjE0NDU0MzUzOTQx.GV9i7M.tch5RyfItgOjLI46P1m8IARjx5l-EAbRryG0lE
ENV lavalink_server=127.0.0.1
ENV lavalink_password=discordBotMusicPassword2231!
CMD ["python","kurusaki.py"]
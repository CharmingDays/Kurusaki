FROM openjdk:18-ea-jdk-slim

WORKDIR /opt/Lavalink

COPY Lavalink.jar Lavalink.jar
COPY application.yml application.yml

EXPOSE 2333

CMD ["java", "-jar", "-Xmx6G",,"-Xms2G","Lavalink.jar"]
FROM python:3.10.12
RUN mkdir /kurusaki
# COPY . /kurusaki
# WORKDIR /kurusaki
VOLUME /kurusaki_data
WORKDIR /kurusaki_data
RUN python -m pip install -r requirements.txt
CMD ["python3","kurusaki.py"]
FROM python:3.10.12
RUN mkdir /kurusaki
COPY . /kurusaki
WORKDIR /kurusaki
RUN python -m pip install -r requirements.txt
CMD ["python3","kurusaki.py"]
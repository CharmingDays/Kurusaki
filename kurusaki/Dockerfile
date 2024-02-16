FROM python:3.10.12-slim
COPY . .
RUN python -m pip install -r requirements.txt
EXPOSE 2333
CMD ["python3","kurusaki.py"]
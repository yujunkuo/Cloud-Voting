FROM ubuntu:20.04
RUN apt-get update -y
RUN apt-get install -y python3-pip python-dev build-essential
RUN pip3 install --upgrade pip
COPY ./src/requirements.txt .
RUN pip3 install -r ./requirements.txt
COPY ./src /src
WORKDIR /src
EXPOSE 80
ENTRYPOINT ["python3"]
CMD ["app.py"]
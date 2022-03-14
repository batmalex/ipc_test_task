FROM python:3.8-slim

RUN mkdir -p /opt/app

COPY . /opt/app
WORKDIR /opt/app

# Install app dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 85

CMD ["/bin/bash", "run.sh"]
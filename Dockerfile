FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get install git -y --no-install-recommends
    

#================================================================
# pip install required modules
#================================================================

RUN pip install --upgrade setuptools pip
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

#==================================================
# Copy the latest code
#==================================================

RUN mkdir -p /fyle-slack-app
WORKDIR /fyle-slack-app
COPY . /fyle-slack-app

# Expose server port
EXPOSE 8000

CMD /bin/bash run.sh

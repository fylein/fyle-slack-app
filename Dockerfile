FROM python:3.8-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get -y install libpq-dev gcc && apt-get install git -y --no-install-recommends

ARG CI
RUN if [ "$CI" = "ENABLED" ]; then \
        apt-get install lsb-release gnupg2 wget -y --no-install-recommends; \
        apt-cache search postgresql | grep postgresql; \
        sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'; \
        wget --no-check-certificate --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - ; \
        apt -y update; \
        apt-get install postgresql-14 -y --no-install-recommends; \
    fi
    

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

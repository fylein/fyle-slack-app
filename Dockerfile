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

#================================================================
# Set default GID if not provided during build
#================================================================
ARG SERVICE_GID=1001

#================================================================
# Setup non-root user and permissions
#================================================================
RUN groupadd -r -g ${SERVICE_GID} slack_service && \
    useradd -r -g slack_service slack_user && \
    chown -R slack_user:slack_service /fyle-slack-app

# Switch to non-root user
USER slack_user

# Expose server port
EXPOSE 8000

CMD /bin/bash run.sh

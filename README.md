# fyle-slack-app #

* Download and install Docker desktop for Mac from [here.](https://www.docker.com/products/docker-desktop)


## Local Development ##

## Prerequisites ##

* Create an .env file in the root directory with the following entries:

    ```
    SECRET_KEY=fakedjangosecretkey
    FYLE_CLIENT_ID=fakefyleclientid
    FYLE_CLIENT_SECRET=fakefyleclientsecret
    FYLE_PLATFORM_URL=fakefyleplatformurl
    FYLE_ACCOUNTS_URL=fakefyleaccounturl
    SLACK_CLIENT_ID=fakeslackclientid
    SLACK_CLIENT_SECRET=fakeslackclientsecret
    SLACK_APP_TOKEN=fakeslackapptoken
    SLACK_SIGNING_SECRET=fakeslacksigningsecret
    SLACK_APP_ID=fakeslackappid
    SLACK_SERVICE_BASE_URL=akeslackservicebaseurl
    FYLEHQ_SLACK_URL=fakefylehqurl
    FYLE_SLACK_APP_SEGMENT_KEY=fakesegmentkey
    ALLOWED_HOSTS=fakeallowedhosts
    DB_NAME=database
    DB_USER=slack_user
    DB_PASSWORD=slack12345
    DB_HOST=database
    DB_PORT=5432
    ```

### Bringing up via Docker Compose ###

* For a fresh setup run to build images for services
    ```
    docker-compose build
    ```

* Now run to start services
    ```
    docker-compose up
    ```

* No need to build again to run the services, server will automatically restart if there are changes in codebase.

* If any changes are made in `requirements.txt` you'll need to rebuild images
    ```
    docker-compose build
    
    docker-compose up
    ```

* If you want to build and start service in one shot

    ```
    docker-compose up --build
    ```


### Connecting to PostgreSQL DB container ###

* Ensure that you have services up and running. Then run the following command to connect to the PostgreSQL DB.
    ```
    PGPASSWORD=slack12345 psql -h localhost -U slack_user slack_db
    ```
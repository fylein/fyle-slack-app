# fyle-slack-app #

* Download and install Docker desktop for Mac from [here.](https://www.docker.com/products/docker-desktop)


## Local Development ##

## Prerequisites ##

* Create an .env file in the root directory with the following entries:

    ```
    SECRET_KEY=thisisafakedjangosecretkey
    FYLE_CLIENT_ID=abcd
    FYLE_CLIENT_SECRET=abcd
    FYLE_BASE_URL=abcd
    FYLE_ACCOUNTS_URL=abcd
    FYLE_SLACK_APP_SEGMENT_KEY=abcd
    SLACK_CLIENT_ID=abcd
    SLACK_CLIENT_ID=abcd
    SLACK_APP_ID=abcd
    SLACK_APP_TOKEN=abcd
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
    PGPASSWORD=slack12345 psql -h database -U slack_user slack_db
    ```
# fyle-slack-app #

* Download and install Docker desktop for Mac from [here.](https://www.docker.com/products/docker-desktop)

* Download and install ngrok for Mac from [here](https://ngrok.com/download)

* Once ngrok is installed, run the below command to start ngrok tunnel
    ```
    ngrok http 8000
    ```

* This will spin up a ngrok tunnel with a host name that will proxy slack's API calls to our local server.

* Best to always keep the ngrok tunnel open - can keep a [screen](https://www.geeksforgeeks.org/screen-command-in-linux-with-examples/) session running for this.


## Creating new slack app for local development ##

* Ask someone from Slack Team to invite you to the `demo` slack workspace, where the team test their changes.

* Create a new slack app from [here](https://api.slack.com/apps)

* Choose `Create from an app manifest` and ask someone from Slack Team to share an existing manifest file. After copy-pasting the manifest file json data, - 
    
    * You'll need to replace the existing ngrok urls with the ngrok server url (which you started in your machine) in the manifest of the new app that you created.
    
    * You'll also need to change the slack app name to "Fyle-Dev-<YOUR_NAME>", just so that you can easily identify the app (assuming multiple devs working on this service).

* After your slack app has been successfully created, you'll need to add these few creds in your `.env` file (which you will create [here](https://github.com/fylein/fyle-slack-app/blob/master/README.md#prerequisites)) -

    * Creds under `App Credentials` present on this slack app's settings page
    
    * Your fyle test org TPA creds (`FYLE_CLIENT_ID`, `FYLE_CLIENT_SECRET`)

* Now, all that is left for you, is to install your newly created slack app inside `demo` slack workspace. You can do this by opening this url in your browser.
    ```
    https://<YOUR_NGROK_URL>/slack/direct_install
    ```

* Just FYI - Each developer will be working on their own separate slack app, and not on a common one.

## Local Development ##

## Prerequisites ##

* Create an .env file in the root directory with the following entries:

    ```
    SECRET_KEY=fakedjangosecretkey
    FYLE_CLIENT_ID=fakefyleclientid
    FYLE_CLIENT_SECRET=fakefyleclientsecret
    FYLE_ACCOUNTS_URL=fakefyleaccounturl
    FYLE_BRANCHIO_BASE_URI=fakefylebranchiobaseuri
    SLACK_CLIENT_ID=fakeslackclientid
    SLACK_CLIENT_SECRET=fakeslackclientsecret
    SLACK_APP_TOKEN=fakeslackapptoken
    SLACK_SIGNING_SECRET=fakeslacksigningsecret
    SLACK_APP_ID=fakeslackappid
    SLACK_SERVICE_BASE_URL=akeslackservicebaseurl
    FYLEHQ_SLACK_URL=fakefylehqurl
    FYLE_SLACK_APP_MIXPANEL_TOKEN=fakesegmentkey
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

* Ensure that you have services up and running. Then, run the following command to go into interactive-shell of the `database` service container.
    ```
    docker-compose exec database bash
    ```

* And then run the following command to connect to the PostgreSQL DB.
    ```
    PGPASSWORD=slack12345 psql -h localhost -U slack_user slack_db
    ```
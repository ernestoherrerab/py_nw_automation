# Server and program execution

To ensure that the server is running correctly the following must be adhered to:

- A python virtual environment needs to be created where all the requirements listed in requirements.txt are installed, except of course for the python virtual environmet.

## Python Virtual Environment

1. The python virtual environment is installed like this:

    1. If pip is not installed yet, install it:

            sudo apt-get install python3-pip

    2. Then install the virtual environment application:

            pip3 install virtualenv

    3. After it is installed, create the virtual environment:
  
            python3 -m venv .venv

        **Note:** that .venv is used in the environment, but another name can be used.

    4. Navigate to the .venv directory and activate the venv:

            source bin/activate

    5. If you need to deactivate the virtual environment:

            deactivate

2. Once you have activated the virtual environment, run the applicationby specifying the type of environment (prod or dev):

        python app.py -e prod/dev &

    *The & symbol above is used to keep the application running despite the ssh session expires.

3. To kill the service if needed do the following:

        ps -ef | grep "python3 app.py -e"

4. Copy the first number which is the PID from the line containing the "python3 app.py -e" and run the following command:

        kill -9 #######

    *Where #### is the PID number

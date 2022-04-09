# Bash Script to restart service

This Bash script is used with cron to restart service in case the service goes down.

    #!/bin/bash



    if (( $(ps -ef | grep -v grep | grep app.py | wc -l) > 0 ))
    then
    echo "app.py is running!!!"
    else
    cd /home/ehb/automation/.venv
    source bin/activate
    cd /home/ehb/automation/.venv/py_nw_automation
    python app.py -e prod &
    fi

Then in the CLI enter:

    crontab -e

and write the following:

    * * * * * /home/user/automation/.venv/py_nw_automation/frontend_service.sh

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

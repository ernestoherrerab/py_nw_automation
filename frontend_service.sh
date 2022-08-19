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

if (( $(ps -ef | grep -v grep | grep py_nw_automation/file_display/node_modules/react-scripts/scripts/start.js | wc -l) > 0 ))
then
echo "React APP is running!!!"
else
cd /home/ehb/automation/.venv
source bin/activate
cd /home/ehb/automation/.venv/py_nw_automation/file_display
npm start &
fi

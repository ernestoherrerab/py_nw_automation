# Create REACT APP

REACT is JavaScript library for building user interfaces.

This is the library that is used to generate the code required to host the site documentation "windows-explorer-type" application.

1. Navigate to the py_nw_automation directory.

2. Within the directory run: "npx create-react-app file_display".
   file_display must be the name of the app to be able to synchronize the needed files within the Git Repo.

3. If the error: "Create React App requires Node 14 or higher. Please update your version of Node Error" appears, then follow the below:
  
    1. sudo npm cache clean -f
    2. sudo npm install -g n
    3. sudo n stable
    4. reboot (A reboot is required on the devbox)  
    5. Try again the "npx create-react-app file_display" command upon reboot. 
       Note: An environmental variable is used that differs between dev and prod as it references the Flask server.

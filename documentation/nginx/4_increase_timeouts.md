In order to ensure the scripts have enough time to run in the background, timeouts must be modified to avoid errors.
This are changed in the /etc/nginx/nginx.conf folder, so do a sudo nano /etc/nginx/nginx.conf

and add the following lines under the http section:

        # Timeouts
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
The following guide has been followed with some modifications to allow for the reverse proxy:
https://dev.to/thetrebelcc/how-to-run-a-flask-app-over-https-using-waitress-and-nginx-2020-235c

You can skip the steps until you reach the section that says: "Our Web Server rules will be at".
There is no need to delete the default files.

The following are the settings that are used in the /etc/nginx/sites-available/"your_domain" file
-------------------------------------------------------------------------------------------------
server {
        listen 443 ssl;
        listen [::]:443 ssl;
        include snippets/self-signed.conf;
        include snippets/ssl-params.conf;

        root /var/www/your_domain/html;
        index index.html index.htm index.nginx-debian.html;

        server_name devbox_name.your_domain;

        location / {

            proxy_pass http://devbox_ip_address:8080;
            proxy_set_header X-Real-IP $remote_addr;
                
        }
}

server {
    listen 80;
    listen [::]:80;

    server_name devbox_name.your_domain;

    return 302 https://$server_name$request_uri;
}

-------------------------------------------------------------------------------------------------
Finally restart the service with sudo systemctl status nginx.

Verify that the /etc/nginx/sites-enabled/"your_domain" looks like this too (it should since we created a simlink)
-------------------------------------------------------------------------------------------------
server {
        listen 443 ssl;
        listen [::]:443 ssl;
        include snippets/self-signed.conf;
        include snippets/ssl-params.conf;

        root /var/www/your_domain/html;
        index index.html index.htm index.nginx-debian.html;

        server_name devbox_name.your_domain;

        location / {

            proxy_pass http://devbox_ip_address:8080;
            proxy_set_header X-Real-IP $remote_addr;
                
        }
}

server {
    listen 80;
    listen [::]:80;

    server_name devbox_name.your_domain;

    return 302 https://$server_name$request_uri;
}
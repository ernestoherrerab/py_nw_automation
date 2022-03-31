NGINX is being used to overcome the limitations of Flask as a production server.

In reality, "Waitress" is being used as the production server but "Waitress" does not support HTTPS, therefore NGINX is working as a reverse proxy on port 443.

NGINX has been installed following the following guide:
https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04#step-5-%E2%80%93-setting-up-server-blocks-recommended
The steps have been followed as they are presented here, however after installation (meaning after you have tested everything in this guide), the ufw has been configured as:
- sudo ufw allow 'Nginx HTTPS'

On step 5, in the "your_domain" sections, you need to use the domain of the devbox machine.
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install nginx -y
sudo apt install git

git clone https://github.com/ClaudioLutz/Japanese_Learning_Website.git
cd Japanese_Learning_Website

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

#ERROR: Could not find a version that satisfies the requirement python-magic-bin>=0.4.14 (from versions: none)
#ERROR: No matching distribution found for python-magic-bin>=0.4.14
nano requirements.txt
#delete 
#python-magic>=0.4.24
#python-magic-bin>=0.4.14

#dann:
deactivate
sudo apt update
sudo apt install -y libmagic1 libmagic-dev
source venv/bin/activate
pip install python-magic

pip install -r requirements.txt
pip install gunicorn


# Run Gunicorn on port 5000, binding to all interfaces
gunicorn -b 0.0.0.0:5000 run:app


sudo nano /etc/nginx/sites-available/Japanese_Learning_Website
server {
    listen 80;
    server_name 34.65.213.96;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}


sudo ln -s /etc/nginx/sites-available/Japanese_Learning_Website /etc/nginx/sites-enabled
sudo systemctl restart nginx


sudo nano /etc/systemd/system/Japanese_Learning_Website.service
#paste:
[Unit]
Description=Gunicorn instance to serve Flask app
After=network.target

[Service]
User=claudio_lutz_cv
Group=www-data
WorkingDirectory=/home/claudio_lutz_cv/Japanese_Learning_Website
Environment="PATH=/home/claudio_lutz_cv/Japanese_Learning_Website/venv/bin"
ExecStart=/home/claudio_lutz_cv/Japanese_Learning_Website/venv/bin/gunicorn \
          --workers 4 \
          --bind 0.0.0.0:5000 \
          run:app

[Install]
WantedBy=multi-user.target


sudo systemctl daemon-reload
sudo systemctl start Japanese_Learning_Website
sudo systemctl enable Japanese_Learning_Website

sudo systemctl status Japanese_Learning_Website.service

########## SSL Certificate ###########
Of course. Here are the essential commands that led to the successful SSL certificate installation, broken down by what they accomplished.

-----

### 1\. Installing Certbot

After the initial `certbot: command not found` error, this was the command that correctly installed Certbot and its Nginx plugin on your Debian system.

```bash
sudo apt install -t bookworm-backports certbot python3-certbot-nginx
```

-----

### 2\. Correcting the Nginx Configuration

Certbot couldn't find your domain because your Nginx file used an IP address for the `server_name`. This command opened the file so you could fix it.

```bash
sudo nano /etc/nginx/sites-available/Japanese_Learning_Website
```

The **critical action** here was changing the line from `server_name 34.65.213.96;` to `server_name japanese-learning.ch www.japanese-learning.ch;`.

-----

### 3\. Applying the Fix and Deploying the Certificate

This sequence of three commands finalized the process.

```bash
# 1. To test your new Nginx configuration for errors
sudo nginx -t

# 2. To load the corrected configuration into Nginx
sudo systemctl reload nginx

# 3. To tell Certbot to install the certificate it had already received
sudo certbot install --cert-name japanese-learning.ch
```

This final `certbot install` command worked because the Nginx configuration now correctly listed your domain names, allowing Certbot to find it and complete the setup.
# Deployment Instructions

## Prerequisites
- AWS account with EC2 access
- GitHub personal access token. To generate your's here the tutorial: [Check the first answer](https://stackoverflow.com/questions/2505096/clone-a-private-repository-github)


## 1. EC2 Setup
1. Create an EC2 instance with required configurations
2. Note the public IP (e.g., `3.128.199.111`)

## 2. Repository Setup
1. Generate GitHub personal access token for private repository access
2. Clone the repository:
```bash
git clone https://YOUR_ACCESS_TOKEN@github.com/Ali-Haider006/LussoAIPostGeneration.git
```

## 3. Python Environment Setup
```bash
sudo apt update
sudo apt upgrade
sudo apt install python3-venv

cd LussoAIPostGeneration
python3 -m venv vvv
source vvv/bin/activate
pip install -r requirements.txt

# Environment Configuration
nano .env  # Add environment variables
cat .env   # Verify environment variables
deactivate
```

## 4. Nginx Setup
```bash
sudo apt update
sudo apt install nginx
sudo ufw app list
sudo ufw allow 'Nginx HTTP'
sudo ufw status
systemctl status nginx
```

## 5. Nginx Configuration
1. Edit default configuration:
```bash
sudo nano /etc/nginx/sites-available/default
```
2. In the server directive location block, replace contents with:
```nginx
proxy_pass http://0.0.0.0:8000;
```
3. Comment out default HTML file and root paths
4. Restart the Nginx server with:
```nginx
sudo systemctl restart nginx
```

## 6. Application Deployment
```bash
cd LussoAIPostGeneration
source vvv/bin/activate
pip install uvicorn

# Test run
uvicorn main:app --host 0.0.0.0 --port 8000

# Production deployment
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &
```

## Server Management
To stop the server:
```bash
sudo pkill 'uvicorn'
```

## Verification
Access the application through your EC2 instance's public IP address in a web browser.
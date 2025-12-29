# 🚀 Autonomous Treasurer — Full Deployment Guide (Atlantic.Net + Docker + Caddy + Monitoring)

This guide walks you through deploying the **Autonomous Treasurer** application on a **free Atlantic.Net VM**, securing it with **SSH keys + Caddy HTTPS**, assigning a **free DuckDNS domain**, and enabling **full observability** using **Netdata, Prometheus, Grafana, Node Exporter, and cAdvisor**.

This README is designed for **public consumption** and contains **no sensitive data**.

---

## 📌 Table of Contents

- [🚀 Autonomous Treasurer — Full Deployment Guide (Atlantic.Net + Docker + Caddy + Monitoring)](#-autonomous-treasurer--full-deployment-guide-atlanticnet--docker--caddy--monitoring)
  - [📌 Table of Contents](#-table-of-contents)
  - [1. Create a Free Atlantic.Net VM](#1-create-a-free-atlanticnet-vm)
  - [2. SSH Into the Server (Windows)](#2-ssh-into-the-server-windows)
  - [3. Initial Server Setup](#3-initial-server-setup)
    - [Create a non‑root user](#create-a-nonroot-user)
    - [Install essentials](#install-essentials)
    - [Install Docker](#install-docker)
  - [4. Clone \& Deploy the Autonomous Treasurer App](#4-clone--deploy-the-autonomous-treasurer-app)
    - [Example `docker-compose.yml`](#example-docker-composeyml)
  - [5. Set Up a Free DuckDNS Domain](#5-set-up-a-free-duckdns-domain)
  - [6. Configure Caddy for HTTPS + Reverse Proxy](#6-configure-caddy-for-https--reverse-proxy)
  - [7. Secure SSH (Keys Only + Custom Port)](#7-secure-ssh-keys-only--custom-port)
    - [Generate SSH key (Windows)](#generate-ssh-key-windows)
    - [Copy key to server](#copy-key-to-server)
    - [Disable password login](#disable-password-login)
  - [8. Install Netdata (Real‑Time Monitoring)](#8-install-netdata-realtime-monitoring)
  - [9. Install Prometheus + Grafana + Exporters](#9-install-prometheus--grafana--exporters)
    - [`docker-compose.yml`](#docker-composeyml)
    - [`prometheus.yml`](#prometheusyml)
  - [10. Access Grafana \& Prometheus Securely](#10-access-grafana--prometheus-securely)
    - [Grafana (SSH tunnel)](#grafana-ssh-tunnel)
    - [Prometheus (SSH tunnel)](#prometheus-ssh-tunnel)
    - [Import dashboards](#import-dashboards)
  - [11. Optional: App‑Level Metrics](#11-optional-applevel-metrics)
  - [12. Optional: Alerts \& Daily Health Reports](#12-optional-alerts--daily-health-reports)
  - [🎉 Deployment Complete](#-deployment-complete)

---

## 1. Create a Free Atlantic.Net VM

1. Sign up at **<https://www.atlantic.net>**  
2. Go to **Cloud → Servers → Create Server**  
3. Choose:
   - **OS:** Ubuntu 22.04 LTS  
   - **Plan:** Smallest free/promo tier  
   - **Hostname:** `autonomous-treasurer`  
4. Create the server and note the **public IP** (example):

```IP
203.0.113.10
```

---

## 2. SSH Into the Server (Windows)

Open **Windows Terminal** and run:

```powershell
ssh root@203.0.113.10
```

Accept the fingerprint and log in.

---

## 3. Initial Server Setup

### Create a non‑root user

```bash
adduser appuser
usermod -aG sudo appuser
```

Reconnect:

```powershell
ssh appuser@203.0.113.10
```

### Install essentials

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y ca-certificates curl git ufw fail2ban
```

### Install Docker

```bash
curl -fsSL https://get.docker.com | sudo bash
sudo usermod -aG docker appuser
```

Log out and back in.

---

## 4. Clone & Deploy the Autonomous Treasurer App

```bash
cd ~
git clone https://github.com/<your-org>/autonomous-treasurer.git
cd autonomous-treasurer
```

### Example `docker-compose.yml`

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    container_name: backend
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: frontend
    restart: unless-stopped

  caddy:
    image: caddy:latest
    container_name: caddy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - frontend
    restart: unless-stopped

volumes:
  caddy_data:
  caddy_config:
```

---

## 5. Set Up a Free DuckDNS Domain

1. Go to **<https://www.duckdns.org>**
2. Create a subdomain:

```DNS
autotreasurer.duckdns.org
```

1. Point it to your server IP.

Verify:

```powershell
ping autotreasurer.duckdns.org
```

---

## 6. Configure Caddy for HTTPS + Reverse Proxy

Create `Caddyfile`:

```caddy
autotreasurer.duckdns.org {
    encode gzip

    @frontend path / /index.html /static/* /assets/*
    handle @frontend {
        reverse_proxy frontend:3000
    }

    handle /api/* {
        reverse_proxy backend:8000
    }

    handle {
        respond "Not found" 404
    }
}
```

Open firewall:

```bash
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

Deploy:

```bash
docker compose up -d
```

Visit:

```DNS
https://autotreasurer.duckdns.org
```

---

## 7. Secure SSH (Keys Only + Custom Port)

### Generate SSH key (Windows)

```powershell
ssh-keygen -t ed25519 -C "autotreasurer"
```

### Copy key to server

```powershell
scp $env:USERPROFILE\.ssh\id_ed25519.pub appuser@203.0.113.10:/home/appuser/
```

On server:

```bash
mkdir -p ~/.ssh
cat id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
rm id_ed25519.pub
```

### Disable password login

```bash
sudo nano /etc/ssh/sshd_config
```

Set:

```config
Port 2222
PasswordAuthentication no
PermitRootLogin no
```

Restart SSH:

```bash
sudo systemctl restart ssh
sudo ufw allow 2222/tcp
```

Reconnect:

```powershell
ssh -p 2222 appuser@203.0.113.10
```

---

## 8. Install Netdata (Real‑Time Monitoring)

```bash
bash <(curl -Ss https://get.netdata.cloud/kickstart.sh)
```

Access:

```DNS
http://203.0.113.10:19999
```

---

## 9. Install Prometheus + Grafana + Exporters

```bash
mkdir -p ~/monitoring
cd ~/monitoring
```

### `docker-compose.yml`

```yaml
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    restart: unless-stopped

  node_exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    restart: unless-stopped

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

### `prometheus.yml`

```yaml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["prometheus:9090"]

  - job_name: "node_exporter"
    static_configs:
      - targets: ["node_exporter:9100"]

  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]
```

Start:

```bash
docker compose up -d
```

---

## 10. Access Grafana & Prometheus Securely

### Grafana (SSH tunnel)

```powershell
ssh -p 2222 -L 3000:localhost:3000 appuser@203.0.113.10
```

Open:

```DNS
http://localhost:3000
```

### Prometheus (SSH tunnel)

```powershell
ssh -p 2222 -L 9090:localhost:9090 appuser@203.0.113.10
```

Open:

```DNS
http://localhost:9090/targets
```

### Import dashboards

- Node Exporter Full → **1860**
- cAdvisor → **193**
- Docker Monitoring → **1229**

---

## 11. Optional: App‑Level Metrics

If backend exposes `/metrics`, add:

```yaml
  - job_name: "app_backend"
    static_configs:
      - targets: ["backend:8000"]
```

---

## 12. Optional: Alerts & Daily Health Reports

You can extend monitoring with:

- Prometheus Alertmanager  
- Email/Slack/Telegram alerts  
- Cron‑based daily health reports  
- Auto‑restart policies for containers  

---

## 🎉 Deployment Complete

You now have:

- A secure Atlantic.Net VM  
- Fully deployed Autonomous Treasurer app  
- HTTPS via Caddy  
- SSH hardened with keys  
- Real‑time monitoring (Netdata)  
- Long‑term metrics (Prometheus)  
- Dashboards (Grafana)  
- Container + system metrics (cAdvisor + Node Exporter)  
  
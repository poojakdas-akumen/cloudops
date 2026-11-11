#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "Run with sudo: sudo bash deploy/bootstrap-azure-vm.sh"; exit 1; fi

apt-get update
apt-get install -y python3 python3-venv python3-pip nginx curl rsync

id cloudops >/dev/null 2>&1 || useradd --system --create-home --home-dir /opt/cloudops-task-manager --shell /usr/sbin/nologin cloudops
mkdir -p /opt/cloudops-task-manager/app /var/lib/cloudops-task-manager
chown -R cloudops:www-data /opt/cloudops-task-manager /var/lib/cloudops-task-manager
chmod 750 /var/lib/cloudops-task-manager

if [[ ! -f /etc/cloudops-task-manager.env ]]; then
  SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')
  printf 'SECRET_KEY=%s\nDATABASE_PATH=/var/lib/cloudops-task-manager/tasks.sqlite3\n' "$SECRET" > /etc/cloudops-task-manager.env
  chmod 600 /etc/cloudops-task-manager.env
fi

cp deploy/cloudops-task-manager.service /etc/systemd/system/cloudops-task-manager.service
cp deploy/nginx-cloudops.conf /etc/nginx/sites-available/cloudops-task-manager
ln -sf /etc/nginx/sites-available/cloudops-task-manager /etc/nginx/sites-enabled/cloudops-task-manager
rm -f /etc/nginx/sites-enabled/default

systemctl daemon-reload
systemctl enable nginx cloudops-task-manager
nginx -t
systemctl restart nginx
echo "VM prepared. Run the GitHub Actions deployment workflow to publish the application."

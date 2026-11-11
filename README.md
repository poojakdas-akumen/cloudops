# CloudOps Task Manager

A small but functional Flask task-management application with automated tests and GitHub Actions deployment to an Azure Linux VM. Nginx is the public web entry point; Gunicorn runs Flask on localhost port 8000; SQLite stores tasks on persistent VM disk.

## Features

- Create and delete CloudOps tasks
- Assign owner and Low / Medium / High priority
- Update Pending / In Progress / Completed status
- Filter by status and view dashboard counts
- SQLite persistence
- JSON health endpoint at `/health`
- Eight pytest tests
- GitHub Actions CI, package and SSH-based CD

## Architecture

Browser -> Azure VM public IP:80 -> Nginx -> Gunicorn (127.0.0.1:8000) -> Flask -> SQLite (`/var/lib/cloudops-task-manager/tasks.sqlite3`).

## 1. Run locally (Windows PowerShell)

```powershell
cd cloudops-task-manager
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
pytest
python app.py
```

Open http://127.0.0.1:5000 and http://127.0.0.1:5000/health.

Linux/macOS virtual environment activation:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest
python app.py
```

## 2. Create the Azure VM

Create an Ubuntu 22.04 or 24.04 LTS VM. For a training demo, a small burstable VM is sufficient. Configure:
- SSH (TCP 22) from your current public IP only.
- HTTP (TCP 80) from the internet for the demo.
- Do not expose TCP 8000 publicly; Gunicorn binds to localhost.
- Use an SSH key and keep the private key private.

Connect:

```bash
ssh <admin-user>@<VM-PUBLIC-IP>
```

Upload/clone this project on the VM, then run the bootstrap once from the project root:

```bash
sudo bash deploy/bootstrap-azure-vm.sh
```

The bootstrap installs Python, venv, Nginx, creates the `cloudops` service user, configures Nginx/systemd and creates a random Flask secret. It does not deploy the application yet.

Copy the deployment script into its permanent location and make it executable:

```bash
sudo cp deploy/deploy.sh /opt/cloudops-task-manager/deploy.sh
sudo chmod 755 /opt/cloudops-task-manager/deploy.sh
```

The GitHub deployment user must be able to SSH to the VM and run this one deployment script with sudo without a password. Add a narrowly scoped sudoers rule using `sudo visudo -f /etc/sudoers.d/cloudops-deploy`:

```text
<admin-user> ALL=(root) NOPASSWD: /opt/cloudops-task-manager/deploy.sh
```

Replace `<admin-user>` with the actual SSH username. Validate with `sudo visudo -cf /etc/sudoers.d/cloudops-deploy`.

## 3. Configure GitHub Actions secrets

Push this project to a GitHub repository and add these repository secrets under Settings -> Secrets and variables -> Actions:

| Secret | Value |
|---|---|
| `AZURE_VM_HOST` | VM public IP or DNS name |
| `AZURE_VM_USER` | SSH admin username |
| `AZURE_VM_SSH_PRIVATE_KEY` | Full private SSH key matching the public key on the VM |

Never commit private keys, passwords or `.env` files. The workflow uses the SSH agent and deploys only from `main`.

## 4. Push to GitHub

Create an empty GitHub repository, then from this project folder:

```bash
git init
git branch -M main
git add .
git commit -m "Initial CloudOps Task Manager application"
git remote add origin https://github.com/<YOUR-ORG-OR-USER>/<REPO>.git
git push -u origin main
```

After the first push, open the repository's Actions tab. The workflow performs:
1. **Test:** installs dependencies, runs pytest and compiles Python files.
2. **Package:** creates a versioned deployment archive and uploads it as an artifact.
3. **Deploy:** downloads the archive, connects to the VM over SSH, invokes the deployment script and checks the health endpoint.

A pull request runs tests but does not deploy. A push to `main` runs all stages.

## 5. Verify the deployment

Open:

```text
http://<VM-PUBLIC-IP>/
http://<VM-PUBLIC-IP>/health
```

Expected health response:

```json
{"application":"CloudOps Task Manager","status":"healthy"}
```

On the VM:

```bash
sudo systemctl status cloudops-task-manager
sudo systemctl status nginx
sudo journalctl -u cloudops-task-manager -f
sudo nginx -t
curl http://127.0.0.1:8000/health
```

## 6. Demonstrate the CI/CD pipeline

1. Open the deployed application and create a few tasks.
2. Change a label or add a feature in `templates/index.html` or `app.py`.
3. Add a pytest test if you change business logic.
4. Commit and push to `main`.
5. Show the GitHub Actions test, package and deploy jobs.
6. Refresh the Azure VM public IP and demonstrate the updated application.
7. Show that existing tasks remain after deployment (SQLite is stored outside the release directory).

## 7. Important operational notes

- This is a learning/demo application, not a production-ready multi-user system. It has no login, role-based access control or CSRF protection.
- Restrict SSH to trusted IPs. For a public production app, add HTTPS with a domain and Let's Encrypt, authentication, CSRF protection, backups and stronger deployment controls.
- SQLite is suitable for this small single-VM demo. For concurrent production workloads, use a managed database such as Azure Database for PostgreSQL.
- Keep the database directory persistent and backed up. Do not place the database inside the release folder.
- Azure VM, disk and public IP resources can incur charges. Stop or deallocate the VM when you finish the lab.

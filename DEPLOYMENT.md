# Deployment Guide (DigitalOcean Droplet)

This runbook is based on the current droplet layout:

- App root: `/opt/mechforge/engineer-tools`
- Virtual environment: `/opt/mechforge/mechvenv`

## 1) Connect and go to app directory

```bash
ssh goenner@<droplet-ip>
cd /opt/mechforge/engineer-tools
```

## 2) Pull latest code

```bash
git status
git pull origin main
```

If there are local changes, either commit/stash first or resolve before pulling.

## 3) Install/update Python dependencies

```bash
source /opt/mechforge/mechvenv/bin/activate
pip install -r requirements.txt
```

## 4) Restart application service

Use whichever process manager is active on the droplet.

### Option A: systemd-managed Gunicorn service

```bash
sudo systemctl restart engineer-tools
sudo systemctl status engineer-tools --no-pager
```

If your unit has a different name, list candidates:

```bash
systemctl list-units --type=service | grep -Ei 'gunicorn|flask|engineer|mechforge'
```

### Option B: manual Gunicorn control script

If your deployment uses a local control script (for example `gunicorn.ctl`), run its restart command from `/opt/mechforge/engineer-tools`.

## 5) Validate deployment

```bash
curl -I http://127.0.0.1:5000/
curl -I http://127.0.0.1:5000/tools/o-ring-gland-calculator
```

If Nginx is in front of Gunicorn, also validate through your public domain.

## 6) Quick functional check for gland updates

- Open `/tools/o-ring-gland-calculator`
- Select dynamic or static service
- Choose cross-section family
- Use `Suggest Standard Sizes`
- Confirm recommended depth aligns to the midpoint of the documented L range
- Confirm warnings appear when squeeze/depth are outside standard ranges

## Notes

- Current in-repo docs for local operation are in `README.md` and `WEB_UI_README.md`.
- Standards reference for gland-depth updates is in `docs/o_ring_gland/STANDARDS_REFERENCE.md`.

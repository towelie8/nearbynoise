# Deployment Guide

Two machines: the Raspberry Pi runs the recorder, the VServer runs the archive
and the web UI. All commands assume the repo is cloned as `nearbynoise/`.

## 1. Raspberry Pi (recorder)

```bash
sudo apt update
sudo apt install -y python3-venv portaudio19-dev ffmpeg
cd /home/pi
git clone <repo-url> nearbynoise
cd nearbynoise
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Check the constants in `nearbynoise/config.py` (paths, `REMOTE_TARGET`), then
install the service:

```bash
sudo cp deploy/nearbynoise-recorder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nearbynoise-recorder
journalctl -u nearbynoise-recorder -f   # watch it start
```

## 2. SSH key (Pi -> VServer)

Generated on the Pi, installed on the VServer (one-time, manual):

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
ssh-copy-id user@vserver
ssh user@vserver true   # must succeed without a password prompt
```

`user@vserver` must match `REMOTE_TARGET` in `nearbynoise/config.py`.

## 3. VServer (archive + web UI)

Base directory, owned by the SSH user the Pi uploads as:

```bash
sudo mkdir -p /var/www/laermprotokoll
sudo chown user: /var/www/laermprotokoll
```

Web app:

```bash
sudo apt install -y python3-venv nginx
cd /opt
sudo git clone <repo-url> nearbynoise
cd nearbynoise
sudo python3 -m venv .venv
sudo .venv/bin/pip install numpy flask waitress   # webserver needs no audio deps
sudo cp deploy/nearbynoise-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now nearbynoise-web
curl -s http://127.0.0.1:8080/ | head   # sanity check
```

nginx with Basic Auth and TLS:

```bash
sudo apt install -y apache2-utils certbot python3-certbot-nginx
sudo htpasswd -c /etc/nginx/.htpasswd-nearbynoise <username>
sudo cp deploy/nginx-nearbynoise.conf /etc/nginx/sites-available/nearbynoise
# edit server_name to the real domain first
sudo ln -s /etc/nginx/sites-available/nearbynoise /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d <domain>
```

## 4. Threshold tuning (commissioning)

Levels are relative dBFS, not calibrated SPL. Tune on site:

1. Watch the journal while producing representative noise:
   `journalctl -u nearbynoise-recorder -f`
2. Compare logged `peak_dbfs` values in `events.jsonl` against noise that
   should and should not trigger.
3. Adjust `TRIGGER_DBFS` in `nearbynoise/config.py` (higher = less sensitive),
   then `sudo systemctl restart nearbynoise-recorder`.
4. Repeat until real events trigger reliably and background noise does not.

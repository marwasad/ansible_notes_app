# notes_app

Deploys a Flask-based Notes application using Nginx and systemd.

## Requirements
- RHEL / CentOS / Rocky Linux 8+
- Python 3

## Role Variables

| Variable | Default | Description |
|--------|--------|-------------|
| app_dir | /opt/notes-app | Application directory |
| web_user | nginx | Service user |
| backup_days | 7 | Backup retention |

## Variables
See defaults/main.yml

## Example
```yaml
- hosts: web
  become: yes
  roles:
    - marwasad.notes_app

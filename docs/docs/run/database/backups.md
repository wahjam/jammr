The database is backed up and copied off-site regularly so that data can be
restored in case of server failure. Backups can also be used to create
realistic test environments for development with real user accounts, recorded
jams, etc.

Backups are enabled by the `playbooks/setup-backup.yml` Ansible playbook, which
performs the following steps:

1. Create `jammrbackup` Linux user on the off-site server.
1. Create `jammrbackup` Linux user on the jammr server configured to allow ssh
   access from the off-site server only to run the backup script.
1. Create a cronjob on the off-site server to periodically run the backup
   script on the jammr server and save the backup.

There is a corresponding `playbooks/restore-backup.yml` Ansible playbook to
upload a database backup file to the jammr server and restore it.

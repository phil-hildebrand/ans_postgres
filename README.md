# PostgreSQL Self Service Deployment Tool

![]https://travis-ci.org/phil-hildebrand/ans_postgres.svg?branch=master

# Overview

This project installs and configures PostgreSQL via ansible

# Requirements

- pip
- ansible

# Installation

1. Clone https://github.com/phil-hildebrand/ans_postgres locally
2. Change directory to ans_postgres

_if ansible needed_

```
$ sudo pip install ansible
```

## Dev Environment Setup

- Assumes Virtualbox Installed
- Vagrant >= 1.7.2
- PostgreSQL Client installed
```
  $ brew install postgresql
  $ pip install psycopg2
  $ cd <repo_path>/ans_postgres
  $ vagrant box add ubuntu/trusty64
  $ vagrant up
  $ ansible -i inventory dev -m ping
```

1. Run `$ ansible-playbook -v -b -i inventory playbooks/main.yml  -l 192.168.2.11`
2. PostgreSQL should be available either directly on localhost with `psql` or at 192.168.2.12 with `psql -h 192.168.2.12` 

## Key Options

- app_user: (`default=psql_app`) - application user name 
- backup_min: backup time (minute)
- backup_hour: backup time (hour)
- backup_dir: ( `/backup` ) - Where to put postgres backups of existing data if `force=true`
- backup_notification: email address for backup mail
- data_dir: ( `default=/data`) - Where to put postgres data & log directories
- db\_port: (`default=5432`) - PostgreSQL port to listen on
- env: \[dev | prod \| travis \| (`default=dev`) - Deployment environment
- force: \[true | false\] (`default=false`) - Remove existing postgres instances
- instance_name: (`default=secondary`) - instance name for multi instance
- multi: \[true | false\] (`default=false`) - Configure secondary instance
- multi_data_dir: (`default=/data/secondary`) - Data directory for multi instance
- multi_port: (`default=5433`) - Port for secondary instance
- primary: ( `default=192.168.2.12`) - primary host/ip for replication setup
- repl: \[true | false\] (`default=false`) - Setup replication from primary to secondary
- secondary_data_dir: (`default=/data/secondary`) - Data directory for secondary instance
- version: \[9.5 | 9.6\] (`default=9.6`) - Major version of PostgreSQL to install

### Vaulted Options

- vault\_role\_dba: (`default=testing`) - Creds for dba role
- vault\_role\_dev: (`default=testing`) - Creds for dev role
- vault\_role\_app: (`default=testing`) - Creds for app role
- vault\_role\_monitor: (`default=testing`) - Creds for slave/replication role
- vault\_role\_slave: (`default=testing`) - Creds for app role
- vault\_prod\_role\_dba: (`default=****`) - Prod creds for dba role
- vault\_prod\_role\_dev: (`default=****`) - Prod creds for dev role
- vault\_prod\_role\_app: (`default=****`) - Prod creds for app role
- vault\_prod\_role\_monitor: (`default=****`) - Prod creds for app role
- vault\_prod\_role\_slave: (`default=****`) - Prod creds for slave/replication role

## Tags

- backups: Just run backup tasks
- auth: Just run auth (default users and roles) tasks
- multi: Just run multi (setup secondary instance) tasks
- repl: Just run repl (setup replication from primary to secondary instance) tasks

## Deployment

1. Update inventory file (`./inventory`) with ip/hostname of node being deployed to
2. Create a file .vault_pass that contains the secret for the encrypted vault file
   _`Note: initial vault pass is testing; this should be changed for non-development deployments`_
3. Run ansible for appropriate environment and version using the .vault_pass file
```
   $ ansible-playbook -v -b -i inventory playbooks/main.yml  -l hostname or ip --extra-vars "version=9.6 env=dev app=my_app" --vault-password-file .vault_pass.txt 
```

### Replication
1. Update inventory file (`./inventory`) with ip/hostnames of primary and secondary nodes being deployed to
```
  ...
  [primary]
  <host> pg_port=<port> xconf=<config file name> instance_name=<instance name>

  [secondary]
  <host> pg_port=<port> xconf=<config file name> instance_name=<instance name>
```
2. Remove any other hosts from the primary/secondary section
3. Update default variables (primary, etc) in playbooks/vars/default_vars.yml
4. Create a file .vault_pass that contains the secret for the encrypted vault file
5. Run ansible for appropriate environment and version using the .vault_pass file and the repl tag (-t)
```
   $ ansible-playbook -v -b -i inventory playbooks/main.yml -l primary,secondary -t repl "version=9.6 env=dev app=my_app repl=true" --vault-password-file .vault_pass.txt 
```

_Note: Any option or vaulted option can be changed at deploy time by adding it to the --extra-vars string: --extra-vars "[option=value option=value ...]"_

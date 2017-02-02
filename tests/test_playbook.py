#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import psycopg2 as p
import pytest
import random
import shlex
import string
import sys
import subprocess
import time

####################################
# Global Variables
#
# For developer tests run locally, modify ans_run to the following:
#
# ans_run = 'ansible-playbook -vv -b -i inventory playbooks/main.yml -l 192.168.* --extra-vars '
# my_host = '192.168.2.12'
#
ans_run = 'ansible-playbook -b -i inventory playbooks/main.yml -l localhost --connection=local --extra-vars '
my_host = 'localhost'
version = "{}".format(os.getenv('POSTGRES_VERSION'))
if version == 'None':
    version = '9.6'
ans_env = "version=" + version
my_user = 'travis'
my_pass = 'travis'
my_db = 'postgres'
databases = ['test_one', 'test_two', 'test_three']
tables = ['test_table_one', 'test_table_two', 'test_table_three']
#
####################################


class TestPlaybooks():

    my_port = '5432'

    def big_string(self, chars):
        return ''.join(random.choice(string.ascii_letters)
                       for _ in range(chars))

    def run_ansible(self, run):
        '''We should be able to run an ansible playbook'''
        try:
            args = shlex.split(run)
            p1 = subprocess.Popen(args, stdout=subprocess.PIPE)
            output = p1.communicate()[0]
            for line in output.splitlines(True):
                if 'ok=' in line:
                    status = line
            (host, colon, ok, changed, unreachable, failed) = status.split()
            ok_count = int(ok.split('=')[1])
            changed_count = int(changed.split('=')[1])
            unreachable_count = int(unreachable.split('=')[1])
            failed_count = int(failed.split('=')[1])

        except Exception as e:
            print ('Ansible Run Failed: (%s)' % e)
            return (False, output)

        if ok_count < 1:
            print ('Ansible Run Failed: (%s)' % output)
            return (False, output)

        return (True, output)

    @pytest.mark.order1
    def test_playbook_postgres(self):
        '''We should be able to install PostgreSQL (with and without --force)'''
        run_string = ans_run + '"env=travis force=true multi=true ' + ans_env + '"'
        print
        print " - " + run_string

        result, output = self.run_ansible(run_string)
        if result is False:
            print output
        assert (result is True)

        run_string = ans_run + '"env=travis ' + ans_env + '"'

        result, output = self.run_ansible(run_string)
        if result is False:
            print output
        assert (result is True)

    def connection(self, db):
        try:
            self.conn = p.connect(dbname=db, user=my_user,  password=my_pass, host=my_host, port=self.my_port)
            self.conn.set_isolation_level(p.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

        except Exception as e:
            print ('Get Connection Failed: [%s, %s, %s, %s, %s ] (%s)' % (db, my_user, my_pass, my_host, self.my_port, e))
            return(False)
        return(self.conn)

    @pytest.mark.order2
    def test_connection(self):
        '''We should be able to create a connection in prep for postgres tests'''

        assert (self.connection(my_db) is not False)

    def test_version(self):
        '''We should be able to get the postgres version'''
        conn = self.connection(my_db);
        sql = "select version();"
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                row = cursor.fetchone()
                while row is not None:
                    if version in row:
                        return(True)
                    row = cursor.fetchone()

        except Exception as e:
            print ('Get Version Failed: (%s)' % e)
            return(False)
        return(True)

    @pytest.mark.order3
    def test_database_creates(self):
        '''We should be able to create databases'''
        conn = self.connection(my_db);
        created = 0
        for database in databases:
            exists = 0
            check_db = "SELECT count(*) FROM pg_database WHERE datname='%s';" % database
            try:
                with conn.cursor() as cursor:
                    cursor.execute(check_db)
                    row = cursor.fetchone()
                    if row is not None:
                        exists = int(row[0])

            except Exception as e:
                print ('Database Check Failed: (%s)' % e)
            if exists < 1:
                cr_db = 'create database %s;' % database
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SET ROLE DBA;")
                        cursor.execute(cr_db)
                    created += 1
    
                except Exception as e:
                    print ('Create Database Failed: (%s)' % e)
        assert (created == 3)

    @pytest.mark.order4
    def test_create_tables(self):
        '''We should be able to create tables'''
        created = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                cr_table = 'create table if not exists %s (id serial primary key, name varchar(20), cool_json json ) ;' % new_table
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(cr_table)
                    created += 1

                except Exception as e:
                    print ('Create Table %s Failed: (%s)' % (new_table, e))
        assert (created == 9)

    @pytest.mark.order5
    def test_inserts(self):
        '''We should be able to insert data into tables'''
        inserts = 10
        inserted = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                for ins in range(1, inserts + 1):
                    my_text = self.big_string(15)
                    my_json_string_data = self.big_string(50)
                    my_json = '{"id": %d, "name": "%s", "data": "%s"}' % (ins, my_text, my_json_string_data)
                    sql = "insert into %s (name, cool_json) values ('%s', '%s');" % (new_table, my_text, my_json)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            inserted += 1

                    except Exception as e:
                        print ('Inserts Failed: (%s)' % e)
        assert (inserted == 90)

    @pytest.mark.order6
    def test_create_json_index(self):
        '''We should be able to create an index on a field in a json column'''
        created = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for each_table in tables:
                cr_index = "create index if not exists cool_json_ix on %s((cool_json ->> 'id')) ;" % each_table
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(cr_index)
                    created += 1

                except Exception as e:
                    print ('Create Json Index %s(cool_json_ix) Failed: (%s)' % (each_table, e))
        assert (created == 9)

    @pytest.mark.order7
    def test_selects(self):
        '''We should be able to select data from tables'''
        selects = 10
        selected = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                for get_id in range(1, selects + 1):
                    sql = "select name from %s where id = %d;" % (new_table, get_id)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            found = cursor.rowcount
                            assert (found == 1)
                            selected += 1

                    except Exception as e:
                        print ('Selects Failed: (%s)' % e)
        assert (selected == 90)

    @pytest.mark.order8
    def test_json_selects(self):
        '''We should be able to select and filter data from json columns'''
        selects = 10
        selected = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                for get_id in range(1, selects + 1):
                    sql = "select name from %s where cast (cool_json ->> 'id' as integer) = %d;" % (new_table, get_id)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            found = cursor.rowcount
                            assert (found == 1)
                            selected += 1

                    except Exception as e:
                        print ('Selects Failed: (%s)' % e)
        assert (selected == 90)

    @pytest.mark.order9
    def test_updates(self):
        '''We should be able to select data from tables'''
        updates = 10
        updated = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                for get_id in range(1, updates + 1):
                    my_text = self.big_string(15)
                    sql = "update %s set name = '%s' where id >= %d;" % (new_table, my_text, get_id)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            updated += 1

                    except Exception as e:
                        print ('Updates Failed: (%s)' % e)
        assert (updated == 90)

    @pytest.mark.order10
    def test_deletes(self):
        '''We should be able to delete data from tables'''
        deletes = 5 
        deleted = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                for get_id in range(1, deletes + 1):
                    sql = "delete from %s where id = %d;" % (new_table, get_id)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            deleted += 1

                    except Exception as e:
                        print ('Deletes Failed: (%s)' % e)
        assert (deleted == 45)

    @pytest.mark.order11
    def test_secondary_connection(self):
        '''We should be able to create a connection to the secondary instance'''
        self.my_port = '5433'

        assert (self.connection(my_db) is not False)

    @pytest.mark.order12
    def test_secondary_database_creates(self):
        '''We should be able to create databases in secondary instance'''
        self.my_port = '5433'
        conn = self.connection(my_db);
        created = 0
        for database in databases:
            exists = 0
            check_db = "SELECT count(*) FROM pg_database WHERE datname='%s';" % database
            try:
                with conn.cursor() as cursor:
                    cursor.execute(check_db)
                    row = cursor.fetchone()
                    if row is not None:
                        exists = int(row[0])

            except Exception as e:
                print ('Database Check Failed: (%s)' % e)
            if exists < 1:
                cr_db = 'create database %s;' % database
                try:
                    with conn.cursor() as cursor:
                        cursor.execute("SET ROLE DBA;")
                        cursor.execute(cr_db)
                    created += 1

                except Exception as e:
                    print ('Create Database Failed: (%s)' % e)
        assert (created == 3)

    @pytest.mark.order13
    def test_playbook_replicate(self):
        '''We should be able to setup replication for PostgreSQL'''
        run_string = ans_run + ' "env=travis repl=true primary=' + my_host + ' ' + ans_env + '" -t repl'
        print
        print " - " + run_string

        result, output = self.run_ansible(run_string)
        if result is False:
            print output
        assert (result is True)

    @pytest.mark.order14
    def test_replicated_connection(self):
        '''We should be able to create a connection to the replicated instance'''
        self.my_port = '5433'

        assert (self.connection(my_db) is not False)

    @pytest.mark.order15
    def test_json_replicated_selects(self):
        self.my_port = '5433'
        '''We should be able to select and filter data from json columns in the replicated instance'''
        selects = 10
        selected = 0
        for database in databases:
            conn = self.connection(database)
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SET ROLE DBA;")

            except Exception as e:
                print ('Could not connect to %s (%s)' % (database, e))
            for new_table in tables:
                for get_id in range(6, selects + 1):
                    sql = "select name from %s where cast (cool_json ->> 'id' as integer) = %d;" % (new_table, get_id)
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute(sql)
                            found = cursor.rowcount
                            assert (found == 1)
                            selected += 1

                    except Exception as e:
                        print ('Selects Failed: (%s)' % e)
        assert (selected == 45)

    @pytest.mark.order17
    def test_replicate_data(self):
        '''We should be able to create databases in the primary and see it in the secondary'''
        self.my_port = '5432'
        conn = self.connection(my_db);
        created = 0
        cr_db = 'create database verify_replication;'
        try:
            with conn.cursor() as cursor:
                cursor.execute("SET ROLE DBA;")
                cursor.execute(cr_db)
            created += 1

        except Exception as e:
                    print ('Create Database Failed: (%s)' % e)
        assert (created == 1)
        time.sleep(1)
        self.my_port = '5433'
        conn = self.connection(my_db);
        exists = 0
        check_db = "SELECT count(*) FROM pg_database WHERE datname='verify_replication';"
        try:
            with conn.cursor() as cursor:
                cursor.execute(check_db)
                row = cursor.fetchone()
                if row is not None:
                    exists = int(row[0])

        except Exception as e:
            print ('Database Check Failed: (%s)' % e)
        assert (exists == 1)

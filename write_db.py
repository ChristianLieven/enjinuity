#!/usr/bin/env python
# enjin-scraper
# Written in 2016 by David H. Wei <https://github.com/spikeh/>
#
# To the extent possible under law, the author(s) have dedicated all
# copyright and related and neighboring rights to this software to the
# public domain worldwide. This software is distributed without any
# warranty.
#
# You should have received a copy of the CC0 Public Domain Dedication
# along with this software. If not, see
# <http://creativecommons.org/publicdomain/zero/1.0/>.
import json
import pickle
import sys

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: ')
        sys.exit()

    f = open('config.json', 'r')
    config = json.load(f)['database']
    f.close()

    dbtype = config['type']
    hostname = config['hostname']
    username = config['username']
    password = config['password']
    dbname = config['dbname']
    tbl_prefix = config['tbl_prefix']

    if dbtype == 'pgsql':
        import psycopg2
        conn = psycopg2.connect(host=hostname, user=username, password=password,
                                database=dbname)
    elif dbtype == 'mysql':
        raise ValueError('Unsupported database type {}'.format(dbtype))
    else:
        raise ValueError('Unsupported database type {}'.format(dbtype))

    cur = conn.cursor()

    # Expect a users.pkl
    if sys.argv[1] == 'users':
        users = pickle.load(open(sys.argv[2], 'rb'))
        query_head = 'INSERT INTO {}users VALUES ('.format(tbl_prefix)
        query_body = ''.join(['%s, ' for _ in range(len(users[0]) - 1)])
        query_tail = '%s);'
        query = query_head + query_body + query_tail
        for user in users:
            cur.execute(query, user)
        conn.commit()
    # Expect a db.pkl
    elif sys.argv[1] == 'forums':
        db = pickle.load(open(sys.argv[2], 'rb'))
        for table, rows in db.items():
            query_head = 'INSERT INTO {}{} VALUES ('.format(tbl_prefix, table)
            query_body = ''.join(['%s, ' for _ in range(len(db[table][0]) - 1)])
            query_tail = '%s);'
            query = query_head + query_body + query_tail
            for row in rows:
                cur.execute(query, row)
            conn.commit()
    else:
        print('usage: ')
        cur.close()
        conn.close()
        sys.exit()
    cur.close()
    conn.close()

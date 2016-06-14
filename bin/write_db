#!/usr/bin/env python3
# enjinuity
# Written in 2016 by David H. Wei <https://github.com/spikeh/>
# and Italo Cotta <https://github.com/itcotta/>
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

def print_usage():
    print('Usage: write_db DBFILE')
    print('Writes a forum dump DBFILE from enjinuity to a database.')

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print_usage()
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
        import pymysql
        conn = pymysql.connect(host=hostname, user=username, password=password,
                               database=dbname, charset='utf8')
    else:
        raise ValueError('Unsupported database type {}'.format(dbtype))

    cur = conn.cursor()
    db = pickle.load(open(sys.argv[1], 'rb'))
    for table, rows in db.items():
        query_head = 'INSERT INTO {}{} VALUES ('.format(tbl_prefix, table)
        query_body = ''.join(['%s, ' for _ in range(len(rows[0]) - 1)])
        query_tail = '%s);'
        query = query_head + query_body + query_tail
        for row in rows:
            cur.execute(query, row)
    conn.commit()
    if dbtype == 'pgsql':
        cur.execute('SELECT sequence_name FROM information_schema.sequences;')
        query_max = 'SELECT MAX({}) FROM {};'
        query_as = 'ALTER SEQUENCE {} RESTART WITH {:d};'
        cur2 = conn.cursor()
        for seq in cur:
            seqlst = seq[0].split('_')
            table = seqlst[0] if len(seqlst) == 3 else seqlst[0] + seqlst[1]
            pkey = seqlst[-2]
            cur2.execute(query_max.format(pkey, table))
            max_pkey = cur2.fetchone()[0]
            if max_pkey:
                cur2.execute(query_as.format(seq[0], max_pkey + 1))
        conn.commit()
        cur2.close()
    cur.close()
    conn.close()

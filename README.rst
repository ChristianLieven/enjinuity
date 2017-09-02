enjinuity
=========
Export Enjin forum to MyBB 1.8 using Selenium with the PhantomJS driver to scrape and lxml to parse.

Supported
=========

Forums
------
- MyBB

Databases
---------
- MySQL

Install
=======

Prerequisites
-------------
Install the following dependencies using your favourite package manager, or pip/virtualenv:

- Python 3
- Selenium
- PhantomJS
- lxml
- PyMySQL (on the machine with the database)

Arch
~~~~
`# pacman -S python-selenium phantomjs python-lxml`

`python-pymysql` is in the AUR. Use your favourite pacman wrapper, or do it manually:

`$ yaourt -S python-pymysql`

Debian
~~~~~~
If you are on unstable (sid):

`# apt-get install python3-selenium phantomjs python3-lxml python3-pymysql`

If you are on stable (jessie) then you will need to enable the backports repository for `python3-selenium` and install PhantomJS using `npm`.

Usage
=====
Here's a simple script:

```
#!/usr/bin/env python3
import pickle
from enjinuity.users import Users
from enjinuity.scraper import Scraper
from enjinuity.parser import Parser

users = Users('http://yoursite.enjin.com/users', 'default@email.com', 'defaultpass'
        ['validtag1', 'validtag2'])
users.dump_mybb('users_db.pkl')
users_map = users.get_map()

scraper = Scraper('http://yoursite.enjin.com/forum', 'login@email.com', 'yourpassword')
site = scraper.get_site()

parser = Parser('http://yoursite.enjin.com/forum', site, users_map)
parser.dump('forum_db.pkl')
```

Copy `users_db.pkl` and `forum_db.pkl` to the server and run `write_db`.

`write_db -t mysql -a localhost -u dbusername -p dbpassword -n dbname {users_db.pkl, forum_db.pkl}`

Contributing
============
To extend support to other forum software, implement `format_xxx()` and `dump_xxx()` methods. Look at the existing MyBB implementation for inspiration.

Authors
=======
David H. Wei
Italo Cotta

License
=======
This project is licensed under the terms of the CC0 1.0 Universal license.

Please see the full license_.

.. _license: LICENSE.txt

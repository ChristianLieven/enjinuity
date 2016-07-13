# enjinuity
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
import pickle
from enjinuity.objects import EnjinForum
from lxml import html


class Parser:

    def __init__(self, url, site, users):
        if not isinstance(site, dict) and site:
            return ValueError
        elif not isinstance(users, dict) and users:
            return ValueError

        self.forum = EnjinForum(url, site, users)
        self.db = {}

    def dump(self, filename):
        for table in ['forums', 'threads', 'posts', 'polls', 'pollvotes']:
            self.db[table] = []
        self.forum.dump_mybb(self.db)
        pickle.dump(self.db, open(filename, 'wb'))

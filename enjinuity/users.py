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
import hashlib
import lxml.html
import pickle
import random
import string
import time
from enjinuity.objects import get_datetime
from selenium import webdriver
from urllib.parse import urlparse, urljoin

def random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase +
        string.ascii_uppercase + string.digits) for _ in range(length))

def md5(string):
    return hashlib.md5(string.encode()).hexdigest()


class Users:

    def __init__(self, users, email, passwd, uid, validtags):
        try:
            with open(users, 'r') as f:
                self.users = [u.rstrip() for u in f]
        except OSError:
            # users is a URL, scrape instead
            self.users = []
            users_to_get = []
            browser = webdriver.Chrome()
            browser.get(users)
            base_url = urljoin(users, '/')
            page = lxml.html.fromstring(browser.page_source, base_url=base_url)
            self._scrape_users(page, users_to_get, validtags)
            self._scrape_rep(users_to_get, browser)
            browser.quit()
        self.email = email
        self.passwd = passwd
        self.uid = uid

        # Database-specific output
        self.db = {}
        # Map of username->uid
        self.user_map = {}

    def _scrape_users(self, page, users_to_get, validtags):
        for row in page.xpath('.//tr[@class="row"]'):
            tags = row.xpath('td[contains(@class, "col-tags")]')
            tags = [t.text for t in tags[0].findall('span')]
            if validtags is not None:
                if set(tags).isdisjoint(validtags):
                    continue
            displayname = row.xpath(
              'td[contains(@class, "col-displayname")]/a')[0]
            name = displayname.text
            joindate = row.xpath(
              'td[contains(@class, "col-datejoined")]')[0].text
            joindate = int(get_datetime(joindate).timestamp())
            lastseen = row.xpath(
              'td[contains(@class, "col-lastseen")]')[0].text_content()
            if lastseen == 'Online Now':
                lastseen = int(time.time())
            else:
                lastseen = int(get_datetime(lastseen).timestamp())
            self.users.append((name, joindate, lastseen))
            url = urljoin(page.base_url, displayname.get('href'))
            users_to_get.append(url)

    def _scrape_rep(self, users_to_get, browser):
        for i, url in enumerate(users_to_get):
            browser.get(url)
            page = lxml.html.fromstring(browser.page_source)
            try:
                rep = int(page.xpath(
                  '//div[@class="widget_ministats"]/div[3]/h4')[0].text)
            except IndexError:
                # Deleted accounts are redirected to the home page
                rep = 0
            self.users[i] += (rep,)

    def get_uid(self, user):
        try:
            return self.user_map[user]
        except KeyError:
            return 0

    def dump(self, filename):
        pickle.dump(self.db, open(filename, 'wb'))


class MyBBUsers(Users):

    def __init__(self, users, email, passwd, uid, validtags=None):
        super().__init__(users, email, passwd, uid, validtags)
        self.db['users'] = []
        # http://docs.mybb.com/1.6/Database-Tables-mybb-users/
        for user in self.users:
            if isinstance(user, str):
                name = user
                joindate = int(time.time())
                lastseen = joindate
                rep = 0
            else:
                name, joindate, lastseen, rep = user
            salt = random_string(8)
            saltedpw = md5(md5(salt) + md5(self.passwd))
            loginkey = random_string(50)
            now = int(time.time())
            self.db['users'].append([
                self.uid,
                name,
                saltedpw,
                salt,
                loginkey,
                self.email,
                0,          # postnum
                0,          # threadnum
                '',         # avatar
                '',         # avatardimensions
                0,          # avatartype
                2,          # usergroup
                '',         # additionalgroups
                0,          # displaygroup
                '',         # usertitle
                joindate,   # regdate
                lastseen,   # lastactive
                lastseen,   # lastvisit
                0,          # lastpost
                '',         # website
                '',         # icq
                '',         # aim
                '',         # yahoo
                '',         # skype
                '',         # google
                '',         # birthday
                'all',      # birthdayprivacy
                '',         # signature
                1,          # allownotices
                0,          # hideemail
                0,          # subscriptionmethod
                0,          # invisible
                1,          # receivepms
                0,          # receivefrombuddy
                1,          # pmnotice
                1,          # pmnotify
                1,          # buddyrequestspm
                0,          # buddyrequestsauto
                'linear',   # threadmode
                1,          # showimages
                1,          # showvideos
                1,          # showsigs
                1,          # showavatars
                1,          # showquickreply
                1,          # showredirect
                0,          # ppp
                0,          # tpp
                0,          # daysprune
                '',         # dateformat
                '',         # timeformat
                0,          # timezone
                0,          # dst
                0,          # dstcorrection
                '',         # buddylist
                '',         # ignorelist
                0,          # style
                0,          # away
                0,          # awaydate
                0,          # returndate
                '',         # awayreason
                '',         # pmfolders
                '',         # notepad
                0,          # referrer
                0,          # referrals
                rep,        # reputation
                '',         # regip
                '',         # lastip
                '',         # language
                0,          # timeonline
                1,          # showcodebuttons
                0,          # totalpms
                0,          # unreadpms
                0,          # warningpoints
                0,          # moderateposts
                0,          # moderationtime
                0,          # suspendposting
                0,          # suspensiontime
                0,          # suspendsignature
                0,          # suspendsigtime
                0,          # coppauser
                0,          # classicpostbit
                1,          # loginattempts
                '',         # usernotes
                0           # sourceeditor
            ])
            self.user_map[name] = self.uid
            self.uid += 1


class phpBBUsers(Users):

    def __init__(self, users, email, passwd, uid):
        super().__init__(users, email, passwd, uid)
        # Create a list of rows to insert into table 'users'
        #self.db['users'] = []
        for user in users:
            # Create each row and insert it into the list of rows.
            #self.db['users'].append([...])
            self.user_map[user] = self.uid
            self.uid += 1

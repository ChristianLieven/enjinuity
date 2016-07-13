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
import base64
import binascii
import bcrypt
import hashlib
import pickle
import random
import string
import sys
import time
from enjinuity.objects import get_datetime
from lxml import html
from selenium import webdriver
from urllib.parse import urljoin, urlparse

def random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase +
        string.ascii_uppercase + string.digits) for _ in range(length))

def md5(string):
    return hashlib.md5(string.encode()).hexdigest()


class Users:

    def __init__(self, url, email, passwd, validtags=[]):
        self.url = url
        self.email = email
        self.passwd = passwd
        self.validtags = validtags

        # List of user tuples (name, joindate, lastseen, rep)
        self.users = []
        # Database-specific rows
        self.db = {}
        # Map of username->uid
        self.user_map = {}

        self.browser = webdriver.PhantomJS()
        self.browser.get(url)
        page = html.fromstring(self.browser.page_source, urljoin(url, '/'))
        self._scrape_users(page)
        self.browser.quit()

    def __del__(self):
        if self.browser:
            self.browser.quit()

    def _scrape_users(self, page):
        for row in page.xpath('.//tr[@class="row"]'):
            tags = row.xpath('td[contains(@class, "col-tags")]')
            tags = [t.text for t in tags[0].findall('span')]

            # Skip users that do not have any tags in validtags
            if set(tags).isdisjoint(self.validtags):
                continue

            displayname = row.xpath(
                    'td[contains(@class, "col-displayname")]/a')[0]
            name = displayname.text_content()

            joindate = row.xpath(
                    'td[contains(@class, "col-datejoined")]')[0].text_content()
            joindate = int(get_datetime(joindate).timestamp())

            lastseen = row.xpath(
                    'td[contains(@class, "col-lastseen")]')[0].text_content()
            if lastseen == 'Online Now':
                lastseen = int(time.time())
            else:
                lastseen = int(get_datetime(lastseen).timestamp())

            self.browser.get(urljoin(page.base_url, displayname.get('href')))
            user_page = html.fromstring(self.browser.page_source)
            try:
                rep = int(user_page.xpath(
                        '//div[@class="widget_ministats"]/div[3]/h4')[0].text)
            except IndexError:
                # Deleted accounts are redirected to the home page
                rep = 0

            print('INFO:\t', name, joindate, lastseen, rep)
            self.users.append((name, joindate, lastseen, rep))

    # http://docs.mybb.com/1.6/Database-Tables-mybb-users/
    def _format_mybb(self):
        # First available user id
        uid = 2
        # First available reputation id
        rid = 1
        # Name of users table
        self.db['users'] = []
        self.db['reputation'] = []
        for name, joindate, lastseen, rep in self.users:
            salt = random_string(8)
            saltedpw = md5(md5(salt) + md5(self.passwd))
            loginkey = random_string(50)
            self.db['users'].append([
                uid,
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
            now = int(time.time())
            self.db['reputation'].append([
                rid,
                uid,        # user ID of receiver
                0,          # user ID of giver
                0,          # pid
                rep,        # amount of reputation
                now,        # dateline
                ''          # comments
            ])
            self.user_map[name] = uid
            uid += 1
            rid += 1

    def dump_mybb(self, filename):
        if not self.db:
            self._format_mybb()
        pickle.dump(self.db, open(filename, 'wb'))

    def dump_map(self, filename):
        if not self.db:
            raise RuntimeError('ERROR: Call a dump_xxx function first.')
        pickle.dump(self.user_map, open(filename, 'wb'))

################################################################################


class phpBBUsers(Users):

    def __init__(self, users, email, passwd, validtags=None):
        super().__init__(users, validtags)
        # user_id 1 is for the Anonymous guest user, user_id 2 is for
        # the administrator on board installation, user_id 3-47 are for
        # search crawlers.
        self.uid = 48
        self.db['users'] = []
        self.db['user_group'] = []
        # https://wiki.phpbb.com/Table.phpbb_users
        for user in self.users:
            if isinstance(user, str):
                name = user
                joindate = int(time.time())
                lastseen = joindate
            else:
                name, joindate, lastseen = user
            # phpBB 3.1 uses bcrypt 2y with 10 rounds
            salt = bcrypt.gensalt(10, prefix=b'2a').replace(b'$2a', b'$2y')
            saltedpw = bcrypt.hashpw(passwd.encode(), salt).decode()
            now = int(time.time())
            # return sprintf('%u', crc32(strtolower($email))) . strlen($email);
            # Since crc32 returns a negative int on 32-bit platforms,
            # it's not clear what happens when phpBB 'concatenates' two
            # ints first before printing the unsigned representation.
            emailcrc32 = binascii.crc32(email.encode())
            if not sys.maxsize > 2**32:
                emailcrc32 & 0xffffffff
            emailcrc32 = int(str(emailcrc32) + str(len(email)))
            self.db['users'].append([
                self.uid,
                0,          # user_type: normal user
                2,          # group_id: registered
                '',         # user_permissions
                0,          # user_perm_from
                '0.0.0.0',  # user_ip
                joindate,   # user_regdate
                name,       # username
                name.lower(), # username_clean
                saltedpw,   # user_password
                now,        # user_passchg
                email,      # user_email
                emailcrc32, # user_email_hash
                '',         # user_birthday
                0,          # user_lastvisit
                0,          # user_lastmark
                0,          # user_lastpost_time
                '',         # user_lastpage
                '',         # user_last_confirm_key
                0,          # user_last_search
                0,          # user_warnings
                0,          # user_last_warnings
                0,          # user_login_attempts
                0,          # user_inactive_reason
                0,          # user_inactive_time
                0,          # user_posts
                'en',       # user_lang
                '',         # user_timezone
                'D M d, Y g:i a', # user_dateformat
                1,          # user_style
                0,          # user_rank
                '',         # user_colour
                0,          # user_new_privmsg
                0,          # user_unread_privmsg
                0,          # user_last_privmsg
                0,          # user_message_rules
                -3,         # user_full_folder
                0,          # user_emailtime
                0,          # user_topic_show_days
                't',        # user_topic_sortby_type
                'd',        # user_topic_sortby_dir
                0,          # user_post_show_days
                't',        # user_post_sortby_type
                'a',        # user_post_sortby_dir
                0,          # user_notify
                1,          # user_notify_pm
                0,          # user_notify_type
                1,          # user_allow_pm
                1,          # user_allow_viewonline
                1,          # user_allow_viewemail
                1,          # user_allow_massemail
                230271,     # user_options
                '',         # user_avatar
                '',         # user_avatar_type
                0,          # user_avatar_width
                0,          # user_avatar_height
                '',         # user_sig
                '',         # user_sig_bbcode_uid,
                '',         # user_sig_bbcode_bitfield
                '',         # user_jabber
                '',         # user_actkey
                '',         # user_newpasswd
                '',         # user_form_salt
                1,          # user_new
                0,          # user_reminded
                0           # user_reminded_time
            ])
            self.db['user_group'].append([2, self.uid, 0, 0])
            self.user_map[user] = self.uid
            self.uid += 1

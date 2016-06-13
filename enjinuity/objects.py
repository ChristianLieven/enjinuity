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
import lxml.etree
import lxml.html
import re
from datetime import datetime, timedelta, timezone
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse

def parse(tree, func, *args, **kwargs):
    result = []
    for e in tree.xpath('child::node()'):
        if isinstance(e, lxml.html.HtmlElement):
            children = parse(e, func, *args, **kwargs)
            child_result = func(e, children, *args, **kwargs)
            if child_result:
                result.append(child_result)
        elif isinstance(e, lxml.etree._ElementUnicodeResult):
            result.append(e)
    return ''.join(result)

fontpx_map = {
    '8px': 'xx-small',
    '10px': 'x-small',
    '12px': 'small',
    '14px': 'medium',
    '18px': 'x-large',
    '24px': 'xx-large'
}

def bbcode_formatter(element, children):
    if element.tag == 'br':
        return '\r'.rstrip()
    if element.tag == 'a':
        if children:
            return "[url={link}]{text}[/url]".format(link=element.get('href'),
                                                     text=children)
        else:
            return ''
    if element.tag == 'img':
        if element.get('class') == 'bbcode_smiley':
            return element.get('title')
        else:
            return "[img]{link}[/img]".format(link=element.get('src'))
    if element.tag in ['b', 'strong']:
        return "[b]{text}[/b]".format(text=children)
    if element.tag in ['em', 'i']:
        return "[i]{text}[/i]".format(text=children)
    if element.tag in ['del', 's']:
        return "[s]{text}[/s]".format(text=children)
    if element.tag == 'u':
        return "[u]{text}[/u]".format(text=children)
    if element.tag == 'title':
        return ''
    if element.tag == 'span':
        style_list = element.get('style')
        if not style_list:
            return children
        if 'font-size' in style_list:
            size = style_list.split(':')[1]
            return "[size={size}]{text}[/size]".format(text=children,
                                                       size=fontpx_map[size])
        elif 'color' in style_list:
            hexcolor = style_list.split('#')[1]
            return "[color=#{color}]{text}[/color]".format(text=children,
                                                           color=hexcolor)
    if (element.tag =='param' and element.get('name') == 'movie' and
            "youtube" in element.get('value')):
        firstSplit = element.get('value').split('&')
        secondSplit = firstSplit[0].split('/')
        return ("[video=youtube]http://youtube.com/watch?v={value}"
                "[/video]").format(value=secondSplit[4])
    # Numered list
    if element.tag == 'ol':
        return "[list=1]{text}[/list]".format(text=children)
    # Bullet list
    if element.tag == 'ul':
        return "[list]{text}[/list]".format(text=children)
    # List item
    if element.tag == 'li':
        return "[*]{text}".format(text=children)
    if element.tag == 'strike':
        return "[s]{text}[/s]".format(text=children)
    if element.tag == 'div':
        if element.get('style') == 'text-align:center':
            return "[align=center]{text}[align]".format(text=children)
        elif element.get('style') == 'text-align:left':
            return "[align=left]{text}[align]".format(text=children)
        elif element.get('style') == 'text-align:right':
            return "[align=right]{text}[align]".format(text=children)
    if children:
        return children.rstrip()

weekday_map = {
    'Mon': 0,
    'Tue': 1,
    'Wed': 2,
    'Thu': 3,
    'Fri': 4,
    'Sat': 5,
    'Sun': 6
}

def get_datetime(string):
    match = re.search(r'(?:^Posted|^Last edited) ([\w\s,:]*)', string)
    timestr = match.group(1)
    match = re.search(r'\s\d\d$', timestr)
    # Jan 23, 15
    if match:
        postdt = datetime.strptime(timestr, '%b %d, %y').replace(
          tzinfo=timezone.utc)
        return postdt
    match = re.search(r'^(\d+) (\w+) ago$', timestr)
    # 12 hours ago
    # 5 minutes ago
    if match:
        now = datetime.now(tz=timezone.utc)
        if match.group(2) == 'hours':
            td = timedelta(hours=int(match.group(1)))
        else:
            td = timedelta(minutes=int(match.group(1)))
        postdt = now - td
        return postdt
    match = re.search(
      r'^([a-zA-Z]{3}) at (?:(?P<half>[\w\s:]+m)$|(?P<full>[\w\s:]+)$)',
      timestr)
    # Sun at 03:52 pm or Tue at 21:20
    if match:
        post_wd = weekday_map[match.group(1)]
        now = datetime.now(tz=timezone.utc)
        lastweek = now.replace(day=now.day-7)
        lastweek_wd = lastweek.weekday()
        posttime = None
        if match.group('half'):
            posttime = datetime.strptime(
              match.group('half'), '%I:%M %p').replace(
              tzinfo=timezone.utc).time()
        else:
            posttime = datetime.strptime(
              match.group('full'), '%H:%M').replace(
              tzinfo=timezone.utc).time()
        postdt = None
        if post_wd == lastweek_wd:
            postdt = lastweek.replace(hour=posttime.hour,
                                      minute=posttime.minute,
                                      second=posttime.second)
        elif post_wd > lastweek_wd:
            diff = post_wd - lastweek_wd
            postdt = lastweek.replace(day=lastweek.day+diff, hour=posttime.hour,
                                      minute=posttime.minute,
                                      second=posttime.second)
        else:
            diff = lastweek_wd - post_wd
            postdt = now.replace(day=now.day-diff, hour=posttime.hour,
                                 minute=posttime.minute, second=posttime.second)
        postdt = postdt.replace(tzinfo=timezone(timedelta(hours=1)))
        return postdt
    return None


class FObject:

    def __init__(self, oid, parent):
        self.id = oid
        self.parent = parent
        self.children = []
        self.children_to_get = []

    def get_id(self):
        return self.id


class Poll(FObject):
    pid = 1

    def __init__(self, elem, parent):
        super().__init__(Poll.pid, parent)
        Poll.pid += 1
        polls_title = elem.find_elements_by_xpath(
          './/div[contains(@class, "answer-title")]')
        polls_votes = elem.find_elements_by_xpath(
          './/span[contains(@class, "text-alter")]')
        polls_votes.pop()
        self.poll_total_voters = int(elem.find_element_by_xpath(
          './/div[@class="number-votes"]').get_attribute(
          'innerHTML').split("span>")[1].strip())
        poll_option_type = elem.find_element_by_xpath(
          'div[2]/form/div[1]/div[1]/input').get_attribute('type')
        self.multiple = 0
        self.results = []

        if poll_option_type == "checkbox":
            self.multiple = 1

        for title, votes in zip(polls_title, polls_votes):
            self.results.append(
                (title.get_attribute('innerHTML'),
                 votes.get_attribute('innerHTML').split(' ')[0]))

    def format_mybb(self):
        tid = self.parent.get_id()
        optime = self.parent.get_optime()

        #Create option string
        res_list = [x[0] for x in self.results]
        options = res_list[0]
        for opt in res_list[1:]:
             options = options + "||~|~||" + opt

        #Create votes string
        vote_list = [x[1] for x in self.results]
        votes = vote_list[0]
        numvotes = vote_list[0]
        for vote in vote_list[1:]:
            numvotes = numvotes + vote
            votes = votes + "||~|~||" + vote

        #Set maxoptions, unlimited options if multiple choice
        maxoptions = 1
        if self.multiple == 1:
            maxoptions = 0

        numoptions = len(res_list)
        row = [
            self.pid,
            tid,
            '',
            optime,
            options,
            votes,
            numoptions,
            self.poll_total_voters,
            0,
            0,
            self.multiple,
            0,
            maxoptions
        ]
        return ('polls', row)

    def format_phpbb(self):
        raise NotImplementedError


class Post(FObject):
    pid = 1

    def __init__(self, elem, subject, users, parent):
        super().__init__(Post.pid, parent)
        Post.pid += 1
        self.subject = subject
        self.author = elem.find_element_by_xpath(
          'td[1]/div[@class="cell"]/div[@class="username"]/a').get_attribute(
          'innerHTML')
        self.uid = users.get_uid(self.author)

        # Posted Jan 23, 15 · OP · Last edited Apr 29, 16
        # Posted Sun at 03:52 pm · Last edited Sun at 15:53
        time_elem = elem.find_element_by_xpath('td[2]/div[2]/div[1]/div[1]')
        time_list = time_elem.text.split(' · ')

        self.posttime = int(get_datetime(time_list[0]).timestamp())
        # Ensure proper ordering if posts end up with the same or
        # smaller timestamp
        prev_posttime = self.parent.get_prev_posttime()
        if self.posttime <= prev_posttime:
            self.posttime = prev_posttime + 1

        # NOTE Enjin does not store the editor of a post, assume it's
        #      the poster
        self.edituid = 0
        self.edittime = 0
        if len(time_list) > 1 and len(time_list[-1]) > 2:
            self.edituid = self.uid
            self.edittime = int(get_datetime(time_list[-1]).timestamp())

        msg_elem = elem.find_element_by_xpath('td[2]/div[1]/div[1]')
        try:
            tree = lxml.html.fromstring(msg_elem.get_attribute('innerHTML'))
            self.message = parse(tree, bbcode_formatter)
        except lxml.etree.ParserError:
            self.message = ''

    def get_uid(self):
        return self.uid

    def get_author(self):
        return self.author

    def get_posttime(self):
        return self.posttime

    def do_dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)

    def format_mybb(self):
        tid = self.parent.get_id()
        fid = self.parent.parent.get_id()
        rt = self.parent.mybb_replyto(self)
        row = [
            self.id,    # pid
            tid,
            rt,         # replyto, 0 for OP, 1 otherwise
            fid,
            self.subject,
            0,          # icon
            self.uid,
            self.author,
            self.posttime,
            self.message,
            '',         # ipaddress
            0,          # includesig
            0,          # smilieoff
            self.edituid,
            self.edittime,
            '',         # editreason
            1           # visible
        ]
        return ('posts', row)

    def format_phpbb(self):
        raise NotImplementedError


class Thread(FObject):
    tid = 1

    def __init__(self, views, url, browser, users, parent):
        super().__init__(Thread.tid, parent)
        Thread.tid += 1
        self.views = views
        browser.get(url)
        posts_elem = browser.find_element_by_xpath(
          './/div[@class="contentbox posts"]')
        reply_cnt = posts_elem.find_element_by_xpath(
          'div[1]/div[@class="text-right"]').text.split(' ')[0]

        # Check for polls
        self.poll = None
        try:
            poll_block = browser.find_element_by_xpath(
              ('.//td[2]/div[@class="post-wrapper"]'
               '/div[@class="post-poll-area"]'))
            self.poll = Poll(poll_block, self)
        except NoSuchElementException:
            pass

        flags = posts_elem.find_element_by_xpath(
          'div[1]/div[3]/span/div[1]/div[1]').get_attribute('class').split(' ')
        self.is_sticky = 1 if 'sticky' in flags else 0
        self.is_locked = 1 if 'locked' in flags else 0

        self.subject = posts_elem.find_element_by_xpath(
          'div[1]/div[3]/span/h1').text

        posts = posts_elem.find_elements_by_xpath(
          'div[2]//tr[contains(@class, "row")]')

        # First post
        op = Post(posts[0], self.subject, users, self)
        self.opuid = op.get_uid()
        self.opauthor = op.get_author()
        self.optime = op.get_posttime()
        self.oppid = op.get_id()
        self.children.append(op)

        # Rest of the replies
        re_subject = 'RE: ' + self.subject
        for p in posts[1:]:
            reply = Post(p, re_subject, users, self)
            self.children.append(reply)

        # Are there more pages?
        try:
            pages = int(browser.find_element_by_xpath(
              ('.//div[@class="widgets top"]/div[@class="right"]'
               '/div[1]/span[2]')).text.split(' ')[1])
            for i in range(2, pages + 1):
                browser.get("{}/page/{}".format(url, i))
                next_posts = browser.find_elements_by_xpath(
                  ('.//div[@class="contentbox posts"]/div[2]'
                   '//tr[contains(@class, "row")]'))
                # OP is always visible in poll threads; ignore from page 2
                if self.poll:
                    next_posts = next_posts[1:]
                for p in next_posts:
                    reply = Post(p, re_subject, users, self)
                    self.children.append(reply)
        except NoSuchElementException:
            pass

        self.replies = len(self.children) - 1
        assert int(reply_cnt) == self.replies

        # Last post
        lp = self.children[-1]
        self.lptime = lp.get_posttime()
        self.lpauthor = lp.get_author()
        self.lpuid = lp.get_uid()

    def get_optime(self):
        return self.optime

    def get_prev_posttime(self):
        try:
            return self.children[-1].get_posttime()
        except IndexError:
            return 0

    def mybb_replyto(self, post):
        if post is self.children[0]:
            return 0
        else:
            return 1

    def do_dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        if self.poll:
            table, row = self.poll.format_mybb()
            db[table].append(row)
        for child in self.children:
            child.do_dump_mybb(db)

    def format_mybb(self):
        fid = self.parent.get_id()
        poll = self.poll.get_id() if self.poll else 0
        row = [
            self.id,        # tid
            fid,
            self.subject,
            0,              # prefix
            0,              # icon
            poll,
            self.opuid,
            self.opauthor,
            self.optime,
            self.oppid,
            self.lptime,
            self.lpauthor,
            self.lpuid,
            self.views,
            self.replies,
            self.is_locked,
            self.is_sticky,
            0,              # numratings
            0,              # totalratings
            '',             # notes
            1,              # visible
            0,              # unapprovedposts
            0,              # deletedposts
            0,              # attachmentcount
            0               # deletetime
        ]
        return ('threads', row)

    def format_phpbb(self):
        raise NotImplementedError


class Forum(FObject):
    fid = 1

    def __init__(self, name, desc, url, browser, parent):
        super().__init__(Forum.fid, parent)
        Forum.fid += 1
        self.name = name
        self.desc = desc
        self.parentlist = self.parent.get_parentlist() + ',{}'.format(self.id)
        self.linkto = ''
        if urlparse(url).hostname.split('.')[-2] != 'enjin':
            self.linkto = url
            return
        browser.get(url)
        body = browser.find_element_by_tag_name('body')

        # Are there subforums?
        try:
            self._do_init_subforums(body)
        except NoSuchElementException:
            pass

        # Make sure this forum contains threads before continuing
        nr_threads = body.find_element_by_xpath(
          ('.//div[@class="contentbox threads"]/div[1]'
           '/div[@class="text-right"]')).text
        nr_threads = re.split('\s+·\s+(\d+) threads', nr_threads)[1]
        if int(nr_threads) == 0:
            return

        # Get threads from the first page
        self._do_init_threads(body)

        # Are there more pages?
        try:
            pages = body.find_element_by_xpath(
              ('.//div[@class="widgets top"]/div[@class="right"]'
               '/div[1]/div[1]/input'))
            pages = int(pages.get_attribute('maxlength'))
            for i in range(2, pages + 1):
                browser.get("{}/page/{}".format(url, i))
                next_body = browser.find_element_by_tag_name('body')
                self._do_init_threads(next_body)
        except NoSuchElementException:
            pass

    def _do_init_subforums(self, body):
        subforums = body.find_elements_by_xpath(
          ('.//div[contains(@class, "contentbox") and '
           'contains(@class, "subforums-block")]/div[2]'
           '//tr[contains(@class, "row")]'))
        for sf in subforums:
            sf_name = sf.find_element_by_xpath('td[2]/div[1]/a')
            sf_desc = sf.find_element_by_xpath('td[2]/div[2]').text
            sf_url = sf_name.get_attribute('href')
            self.children_to_get.append((sf_name.text, sf_desc, sf_url))

    def _do_init_threads(self, body):
        threads = body.find_elements_by_xpath(
          ('.//div[@class="contentbox threads"]/div[2]'
           '//tr[contains(@class, "row")]'))
        for t in threads:
            # Ignore threads that are marked as 'moved', since we'll pick
            # them up from their destination
            if 'moved' in t.get_attribute('class').split(' '):
                continue
            t_name = t.find_element_by_xpath(
              ('td[2]/a[contains(@class, "thread-view") and '
                       'contains(@class, "thread-subject")]'))
            t_url = t_name.get_attribute('href')
            t_views = t.find_element_by_xpath(
              ('td[contains(@class, "views")]')).text
            self.children_to_get.append((t_views, t_url))

    def get_parentlist(self):
        return self.parentlist

    def get_children(self, browser, users):
        for child in self.children_to_get:
            # Check if the child is a subforum or thread
            if len(child) == 3:
                sf_name, sf_desc, sf_url = child
                forum = Forum(sf_name, sf_desc, sf_url, browser, self)
                self.children.append(forum)
            else:
                t_views, t_url = child
                thread = Thread(t_views, t_url, browser, users, self)
                self.children.append(thread)

        for child in self.children:
            try:
                child.get_children(browser, users)
            except AttributeError:
                return

    def do_dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        for child in self.children:
            child.do_dump_mybb(db)

    def format_mybb(self):
        # pid in this case is parent (category) id
        pid = self.parent.get_id()
        row = [
            self.id,    # fid
            self.name,
            self.desc,
            self.linkto,
            'f',        # type
            pid,
            self.parentlist,
            1,          # disporder
            1,          # active
            1,          # open
            0,          # threads
            0,          # posts
            0,          # lastpost
            0,          # lastposter
            0,          # lastposteruid
            0,          # lastposttid
            '',         # lastpostsubject
            0,          # allowhtml
            1,          # allowmycode
            1,          # allowsmilies
            1,          # allowimgcode
            1,          # allowvideocode
            1,          # allowpicons
            1,          # allowtratings
            1,          # usepostcounts
            1,          # usethreadcounts
            0,          # requireprefix
            '',         # password
            1,          # showinjump
            0,          # style
            0,          # overridestyle
            0,          # rulestype
            '',         # rulestitle
            '',         # rules
            0,          # unapprovedthreads
            0,          # unapprovedposts
            0,          # deletedthreads
            0,          # deletedposts
            0,          # defaultdatecut
            '',         # defaultsortby
            ''          # defaultsortorder
        ]
        return ('forums', row)

    def format_phpbb(self):
        raise NotImplementedError


class Category(FObject):

    def __init__(self, elem):
        # A category has no parents
        super().__init__(Forum.fid, None)
        Forum.fid += 1
        self.name = elem.find_element_by_xpath('div[1]/div[3]/span').text
        self.parentlist = str(self.id)

        forums = elem.find_elements_by_xpath('div[2]//td[@class="c forum"]')
        for f in forums:
            f_name = f.find_element_by_xpath('div[1]/a')
            f_desc = f.find_element_by_xpath('div[2]')
            f_url = f_name.get_attribute('href')
            self.children_to_get.append((f_name.text, f_desc.text, f_url))

    def get_parentlist(self):
        return self.parentlist

    def get_children(self, browser, users):
        for f_name, f_desc, f_url in self.children_to_get:
            forum = Forum(f_name, f_desc, f_url, browser, self)
            self.children.append(forum)

        for forum in self.children:
            forum.get_children(browser, users)

    def do_dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        for child in self.children:
            child.do_dump_mybb(db)

    def format_mybb(self):
        row = [
            self.id,    # fid
            self.name,
            '',         # description
            '',         # linkto
            'c',        # type
            0,          # pid
            self.parentlist,
            1,          # disporder
            1,          # active
            1,          # open
            0,          # threads
            0,          # posts
            0,          # lastpost
            0,          # lastposter
            0,          # lastposteruid
            0,          # lastposttid
            '',         # lastpostsubject
            0,          # allowhtml
            1,          # allowmycode
            1,          # allowsmilies
            1,          # allowimgcode
            1,          # allowvideocode
            1,          # allowpicons
            1,          # allowtratings
            1,          # usepostcounts
            1,          # usethreadcounts
            0,          # requireprefix
            '',         # password
            1,          # showinjump
            0,          # style
            0,          # overridestyle
            0,          # rulestype
            '',         # rulestitle
            '',         # rules
            0,          # unapprovedthreads
            0,          # unapprovedposts
            0,          # deletedthreads
            0,          # deletedposts
            0,          # defaultdatecut
            '',         # defaultsortby
            ''          # defaultsortorder
        ]
        return ('forums', row)

    def format_phpbb(self):
        raise NotImplementedError

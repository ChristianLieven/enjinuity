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
import calendar
import re
from datetime import datetime, timedelta, timezone
from lxml import etree, html
from urllib.parse import urljoin, urlparse

def parse_message(tree, func, *args, **kwargs):
    result = []
    for e in tree.xpath('child::node()'):
        if isinstance(e, html.HtmlElement):
            children = parse_message(e, func, *args, **kwargs)
            child_result = func(e, children, *args, **kwargs)
            if child_result:
                result.append(child_result)
        elif isinstance(e, etree._ElementUnicodeResult):
            result.append(e)
    return ''.join(result).strip()

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
        return '\r'
    if element.tag == 'a':
        if children:
            url = element.get('href')
            return "[url={link}]{text}[/url]".format(link=url, text=children)
        # Empty link
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
        elem_classes = element.get('class').split(' ')
        if 'bbcode_code_body' in elem_classes:
            return "[code]{text}[/code]".format(text=children)
        # Ignore unnecessary elements related to quote/code
        if 'bbcode_code_head' in elem_classes:
            return ''
        if 'bbcode_quote_decorator' in elem_classes:
            return ''
        elif 'element_avatar' in elem_classes:
            return ''
        elif 'user' in elem_classes:
            return ''
        # Ignore unnecessary elements related to spoiler tags
        elif 'spoiler-title' in elem_classes:
            return ''
        if 'bbcode' in elem_classes and 'spoiler' in elem_classes:
            return "[spoiler]{}[/spoiler]".format(children)
        if 'bbcode_quote' in elem_classes:
            quotes = list(element)
            quote_head = quotes[1]
            who = quote_head.find('div[2]/a')
            # Properly formatted quote block, with a linked author
            if who is not None:
                who = who.text
                txt = children.split('wrote:')[-1]
                return "[quote='{}']\r{}\r[/quote]\r\r".format(who, txt)
            else:
                child_split = children.strip().split('wrote:')
                if len(child_split) == 1:
                    child_split = children.strip().split('Quote:')
                child_split = [x.strip() for x in child_split]
                # Text on both sides of 'wrote:'
                if len(child_split) == 2 and child_split[0] and child_split[1]:
                    who = child_split[0]
                    txt = child_split[1]
                    return "[quote='{}']\r{}\r[/quote]\r\r".format(who, txt)
                else:
                    txt = ''.join(child_split)
                    return "[quote]\r{}\r[/quote]\r\r".format(txt)
        if element.get('style') == 'text-align:center':
            return "[align=center]{text}[/align]".format(text=children)
        elif element.get('style') == 'text-align:left':
            return "[align=left]{text}[/align]".format(text=children)
        elif element.get('style') == 'text-align:right':
            return "[align=right]{text}[/align]".format(text=children)
    if element.tag == 'hr' and element.get('class') == 'bbcode_rule' :
        return "[hr]"
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
    if match:
        timestr = match.group(1)
    else:
        timestr = string
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
        try:
            lastweek = now.replace(day=now.day-7)
        except ValueError:
            diff = now.day - 7
            prev_month_days = calendar.monthrange(now.year, now.month - 1)[1]
            lastweek = now.replace(month=now.month - 1,
                                   day=prev_month_days - diff)
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

    def get_id(self):
        return self.id


class Pollvote(FObject):

    vid = 1

    def __init__(self, voteoption, parent):
        super().__init__(Pollvote.vid, parent)
        Pollvote.vid += 1
        self.voteoption = voteoption

    def dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)

    def format_mybb(self):
        optime = self.parent.get_optime()
        pid = self.parent.id
        row = [
            self.id,
            pid,
            0, #guest user
            self.voteoption,
            optime
        ]
        return ('pollvotes', row)


class Poll(FObject):

    pid = 1

    def __init__(self, elem, parent):
        super().__init__(Poll.pid, parent)
        Poll.pid += 1
        polls_title = elem.xpath('.//div[contains(@class, "answer-title")]')
        polls_votes = elem.xpath(
                './/div[@class="clabel"]/span[contains(@class, "text-alter")]')
        self.poll_total_voters = int(elem.xpath(
                './/div[@class="number-votes"]/text()')[1].strip())
        poll_option_type = elem.xpath(
                'div[2]/form/div[1]/div[1]/input')[0].get('type')
        self.multiple = 0
        self.results = []

        if poll_option_type == "checkbox":
            self.multiple = 1

        voteindex = 1
        for titles, votes in zip(polls_title, polls_votes):
            vote = votes.text_content().split(' ')[0]
            title = titles.text_content()
            self.results.append((title, vote))
            for itr in range(1, int(vote) + 1):
                pv = Pollvote(voteindex, self)
                self.children.append(pv)
            voteindex += 1

    def get_pid(self):
        return self.id

    def get_optime(self):
        return self.parent.get_optime()

    def dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        for child in self.children:
            child.dump_mybb(db)

    def format_mybb(self):
        tid = self.parent.get_id()
        optime = self.get_optime()

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
            self.id,
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


class Post(FObject):

    pid = 1

    def __init__(self, elem, subject, parent):
        super().__init__(Post.pid, parent)
        Post.pid += 1
        self.subject = subject
        self.author = elem.xpath(
          'td[1]/div[@class="cell"]/div[@class="username"]/a')[0].text_content()
        try:
            self.uid = FObject.users[self.author]
        except KeyError:
            self.uid = 0

        # Posted Jan 23, 15 · OP · Last edited Apr 29, 16
        # Posted Sun at 03:52 pm · Last edited Sun at 15:53
        time_list = [x.strip() for x in elem.xpath(
                     'td[2]/div[2]/div[1]/div[1]')[0].text_content().split('·')]

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

        try:
            msg_elem = elem.xpath('td[2]/div[1]/div[1]')[0]
            tree = html.fragment_fromstring(
                etree.tostring(msg_elem, encoding=str), create_parent='div')
            self.message = parse_message(tree, bbcode_formatter)
        except etree.ParserError:
            self.message = ''

    def get_uid(self):
        return self.uid

    def get_author(self):
        return self.author

    def get_posttime(self):
        return self.posttime

    def dump_mybb(self, db):
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


class Thread(FObject):

    tid = 1

    def __init__(self, views, sticky, url, site, parent):
        super().__init__(Thread.tid, parent)
        Thread.tid += 1
        self.views = views
        self.is_sticky = sticky
        base_url = urljoin(url, '/')
        page = html.fromstring(site[url], base_url=base_url)

        posts_elem = page.xpath('//div[@class="contentbox posts"]')[0]
        reply_cnt = posts_elem.xpath('div[1]/div[@class="text-right"]')[0] \
                              .text_content().strip().split(' ')[0]

        # Check for polls
        self.poll = None
        poll_block = page.xpath(('.//td[2]/div[@class="post-wrapper"]'
                                 '/div[@class="post-poll-area"]'))
        if len(poll_block):
            self.poll = Poll(poll_block[0], self)

        flags = posts_elem.xpath('div[1]/div[3]/span/div[1]/div[1]')[0]
        flags = flags.get('class').split(' ')
        self.is_locked = 1 if 'locked' in flags else 0

        self.subject = ''.join([x.strip() for x in posts_elem.xpath('div[1]/div[3]/span/h1/text()')])

        posts = posts_elem.xpath('div[2]//tr[contains(@class, "row")]')

        # First post
        op = Post(posts[0], self.subject, self)
        self.opuid = op.get_uid()
        self.opauthor = op.get_author()
        self.optime = op.get_posttime()
        self.oppid = op.get_id()
        self.children.append(op)

        # Rest of the replies
        re_subject = 'RE: ' + self.subject
        for p in posts[1:]:
            reply = Post(p, re_subject, self)
            self.children.append(reply)

        # Are there more pages?
        pages = page.xpath(('.//div[@class="widgets top"]/div[@class="right"]'
                            '/div[1]/span[2]'))
        if len(pages):
            pages = int(pages[0].text_content().split(' ')[1])
            for i in range(2, pages + 1):
                next_html = site["{}/page/{}".format(url, i)]
                next_page = html.fromstring(next_html, base_url)
                next_posts = next_page.xpath(
                  ('.//div[@class="contentbox posts"]/div[2]'
                   '//tr[contains(@class, "row")]'))
                # OP is always visible in poll threads; ignore from page 2
                if self.poll:
                    next_posts = next_posts[1:]
                for p in next_posts:
                    reply = Post(p, re_subject, self)
                    self.children.append(reply)

        self.replies = len(self.children) - 1
        assert int(reply_cnt) == self.replies

        # Last post
        lp = self.children[-1]
        self.lpuid = lp.get_uid()
        self.lpauthor = lp.get_author()
        self.lptime = lp.get_posttime()
        self.lppid = lp.get_id()

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

    def dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        if self.poll:
            self.poll.dump_mybb(db)
        for child in self.children:
            child.dump_mybb(db)

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


class Forum(FObject):

    fid = 1

    #self.children.append(Forum(name, desc, url, site, self))
    def __init__(self, name, desc, url, site, parent):
        super().__init__(Forum.fid, parent)
        # [0] contains subforums, [1] contains threads
        Forum.fid += 1
        # TODO Make sure everything dump_mybb() needs is initialised
        # before checking for linkto
        self.children.extend([[], []])
        self.name = name
        self.desc = desc
        # TODO This is hard-coded for MyBB
        self.parentlist = self.parent.get_parentlist() + ',{}'.format(self.id)
        self.link = ''
        if urlparse(url).hostname.split('.')[-2] != 'enjin':
            self.link = url
            return
        base_url = urljoin(url, '/')
        page = html.fromstring(site[url], base_url)

        # Are there subforums?
        subforums = page.xpath(('//div[contains(@class, "contentbox") and '
                                'contains(@class, "subforums-block")]/div[2]'
                                '//tr[contains(@class, "row")]'))
        if len(subforums):
            for sf in subforums:
                sf_name_elem = sf.xpath('td[2]/div[1]/a')[0]
                sf_name = sf_name_elem.text.strip()
                sf_desc = sf.xpath('td[2]/div[2]')[0].text.strip()
                sf_url = urljoin(base_url, sf_name_elem.get('href'))
                subforum = Forum(sf_name, sf_desc, sf_url, site, self)
                self.children[0].append(subforum)

        # Make sure this forum contains threads before continuing
        nr_threads = page.xpath(('//div[@class="contentbox threads"]/div[1]'
                                 '/div[@class="text-right"]'))[0].text_content()
        nr_threads = re.split('\s+·\s+(\d+) threads', nr_threads.strip())[1]
        if int(nr_threads) == 0:
            return

        # Get threads from the first page
        self._do_init_threads(page, site)

        # Are there more pages?
        pages = page.xpath(('.//div[@class="widgets top"]/div[@class="right"]'
                            '/div[1]/div[1]/input'))
        if len(pages):
            pages = int(pages[0].get('maxlength'))
            for i in range(2, pages + 1):
                next_html = site["{}/page/{}".format(url, i)]
                next_page = html.fromstring(next_html, base_url)
                self._do_init_threads(next_page, site)

        assert int(nr_threads) == len(self.children[1])

    def _do_init_threads(self, page, site):
        threads = page.xpath(('.//div[@class="contentbox threads"]/div[2]'
                              '//tr[contains(@class, "row")]'))
        for t in threads:
            # Ignore threads that are marked as 'moved', since we'll pick
            # them up from their destination
            if 'moved' in t.get('class').split(' '):
                continue
            t_icons = t.xpath('td[1]/a/div')[0].get('class').split(' ')
            t_sticky = 1 if 'sticky' in t_icons else 0
            t_name = t.xpath(('td[2]/a[contains(@class, "thread-view") and '
                              'contains(@class, "thread-subject")]'))[0]
            t_url = urljoin(page.base_url, t_name.get('href'))
            t_views = t.xpath(('td[contains(@class, "views")]'))[0].text.strip()
            thread = Thread(t_views, t_sticky, t_url, site, self)
            self.children[1].append(thread)

    def get_parentlist(self):
        return self.parentlist

    def dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        for child in self.children[0] + self.children[1]:
            child.dump_mybb(db)

    def format_mybb(self):
        # pid in this case is parent (category) id
        pid = self.parent.get_id()
        row = [
            self.id,    # fid
            self.name,
            self.desc,
            self.link,
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


class Category(FObject):

    def __init__(self, elem, site, parent):
        super().__init__(Forum.fid, parent)
        Forum.fid += 1
        self.name = elem.xpath('div[1]/div[3]/span')[0].text.strip()
        self.parentlist = str(self.id)
        forums = elem.xpath('div[2]//td[@class="c forum"]')
        if len(forums):
            for f in forums:
                name_elem = f.xpath('div[1]/a')[0]
                name = name_elem.text.strip()
                desc = f.xpath('div[2]')[0].text.strip()
                url = urljoin(elem.base_url, name_elem.get('href'))
                self.children.append(Forum(name, desc, url, site, self))
        else:
            raise ValueError('Could not find any forums in {}'.format(
                    self.name))

    def get_parentlist(self):
        return self.parentlist

    def dump_mybb(self, db):
        table, row = self.format_mybb()
        db[table].append(row)
        for forum in self.children:
            forum.dump_mybb(db)

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


class EnjinForum(FObject):

    def __init__(self, url, site, users):
        super().__init__(0, None)
        FObject.users = users
        page = html.fromstring(site[url], urljoin(url, '/'))
        categories = page.xpath(
                ('//div[contains(@class, "contentbox") and '
                 'contains(@class, "category")]'))
        if len(categories):
            for c in categories:
                self.children.append(Category(c, site, self))
        else:
            raise ValueError('Could not find any categories in {}'.format(url))

    def dump_mybb(self, db):
        for child in self.children:
            child.dump_mybb(db)

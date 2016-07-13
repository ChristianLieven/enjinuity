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
from lxml import html
from selenium import webdriver
from urllib.parse import urljoin


class Scraper:

    def __init__(self, url, usr, pwd, debug=False):
        self.url = url
        self.debug = debug
        self.base_url = urljoin(url, '/')
        self.site = {}

        self.browser = webdriver.PhantomJS()
        self._login(usr, pwd)
        self._print_debug('INFO:\tSuccessfully logged in.')

        self.browser.get(url)
        main_elem = html.fromstring(self.browser.page_source, self.base_url)
        self.site[url] = html.tostring(main_elem)

        forums = main_elem.xpath('//td[@class="c forum"]')
        if len(forums):
            urls = [urljoin(self.base_url, e.xpath('div[1]/a')[0].get('href'))
                    for e in forums]
            for f_url in urls:
                self._scrape_forum(f_url)
        else:
            raise ValueError('Could not find forums in ', self.url)

    def __del__(self):
        if self.browser:
            self.browser.quit()

    def _print_debug(self, *args):
        if self.debug:
            print(*args)

    def _login(self, usr, pwd):
        login_url = urljoin(self.url, '/login')
        self.browser.get(login_url)
        username = self.browser.find_element_by_xpath(
                ('//*[@id="section-main"]/div/div[3]/div[2]/div[8]/table/tbody'
                 '/tr/td/div/div/div/div/table/tbody/tr/td[2]/form/div[2]'
                 '/input'))
        password = self.browser.find_element_by_xpath(
                ('//*[@id="section-main"]/div/div[3]/div[2]/div[8]/table/tbody'
                 '/tr/td/div/div/div/div/table/tbody/tr/td[2]/form/div[4]/'
                 'input'))
        username.send_keys(usr)
        password.send_keys(pwd)
        submit = self.browser.find_element_by_xpath(
                ('//*[@id="section-main"]/div/div[3]/div[2]/div[8]/table/tbody'
                 '/tr/td/div/div/div/div/table/tbody/tr/td[2]/form/div[5]/div'
                 '/input'))
        submit.click()

    def _scrape_thread(self, t_url, is_front=True):
        if t_url in self.site:
            print('WARN:\tAlready added thread:\t', t_url)
        self.browser.get(t_url)
        elem = html.fromstring(self.browser.page_source, self.base_url)
        self._print_debug('INFO:\tScraping thread:\t', elem.find('.//title').text)
        posts = elem.xpath('//div[@class="contentbox posts"]')
        attempts = 0
        while len(posts) == 0:
            if attempts == 2:
                print('ERROR:\tGiving up on:\t', t_url)
                return
            print('Could not find posts in:\t', t_url)
            self.browser.get(t_url)
            elem = html.fromstring(self.browser.page_source, self.base_url)
            posts = elem.xpath('//div[@class="contentbox posts"]')
            attempts += 1
        self.site[t_url] = html.tostring(elem)

        if not is_front:
            return

        pages = elem.xpath(
                ('.//div[@class="widgets top"]/div[@class="right"]/div[1]/'
                 'span[2]'))
        if len(pages):
            nr_pages = int(pages[0].text.split(' ')[1])
            for i in range(2, nr_pages + 1):
                next_url = "{}/page/{}".format(t_url, i)
                self._scrape_thread(next_url, False)

    def _scrape_threads(self, elem, f_url):
        threads = elem.xpath(
                ('.//div[@class="contentbox threads"]/div[2]'
                 '//tr[contains(@class, "row")]'))
        if len(threads):
            self._print_debug('INFO:\tScraping forum:\t\t', elem.find('.//title').text)
            urls = [urljoin(self.base_url, e.xpath(
                    ('td[2]/a[contains(@class, "thread-view") and '
                     'contains(@class, "thread-subject")]'))[0].get('href'))
                    for e in threads]
            for u in urls:
                self._scrape_thread(u, True)
        else:
            print('WARN:\tNo threads in forum:\t', elem.find('.//title').text)
            print(f_url)
            return

    # http://essencesunstrider.enjin.com/forum/m/.../viewforum/
    def _scrape_forum(self, f_url):
        if urljoin(f_url, '/') != self.base_url:
            print('WARN:\tSkipping external link:\t', f_url)
            return
        elif f_url in self.site:
            print('WARN:\tAlready added forum:\t', f_url)
            return
        self.browser.get(f_url)
        elem = html.fromstring(self.browser.page_source, self.base_url)
        self.site[f_url] = html.tostring(elem)

        forums = elem.xpath(
                ('//div[contains(@class, "contentbox") and '
                 'contains(@class, "subforums-block")]/div[2]'
                 '//tr[contains(@class, "row")]'))
        if len(forums):
            urls = [urljoin(self.base_url,
                    e.xpath('td[2]/div[1]/a')[0].get('href')) for e in forums]
            for sf_url in urls:
                self._scrape_forum(sf_url)

        self._scrape_threads(elem, f_url)

        pages = elem.xpath(
                ('.//div[@class="widgets top"]/div[@class="right"]'
                 '/div[1]/div[1]/input'))
        if len(pages):
            nr_pages = int(pages[0].get('maxlength'))
            print(elem.find('.//title').text, 'has', nr_pages, 'pages.')
            for i in range(2, nr_pages + 1):
                next_url = "{}/page/{}".format(f_url, i)
                self.browser.get(next_url)
                next_page = html.fromstring(self.browser.page_source,
                                            self.base_url)
                self.site[next_url] = html.tostring(next_page)
                self._scrape_threads(next_page, next_url)

    def dump(self, filename):
        pickle.dump(self.site, open(filename, 'wb'))

    # Unused

    def _dump_mybb(self, filename):
        for table in ['forums', 'threads', 'posts', 'polls', 'pollvotes']:
            self.db[table] = []
        self.forum.dump_mybb(self.db)
        pickle.dump(self.db, open(filename, 'wb'))

    def _dump_phpbb(self, filename):
        for table in ['forums', 'topics', 'posts']:
            self.db[table] = []
        self.forum.dump_phpbb(self.db)
        pickle.dump(self.db, open(filename, 'wb'))

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
import enjinuity.objects
import pickle
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from urllib.parse import urlparse

def dump_cookies(url, user, passwd, filename, driver='Firefox'):
    browser = None
    if driver == 'Firefox':
        browser = webdriver.Firefox()
    elif driver == 'Chrome':
        browser = webdriver.Chrome()
    else:
        raise AttributeError('Invalid Selenium WebDriver')
    browser.get(url)
    username = browser.find_element_by_xpath(
      ('//*[@id="section-main"]/div/div[3]/div[2]/div[8]/table/tbody/tr/td/div'
       '/div/div/div/table/tbody/tr/td[2]/form/div[2]/input'))
    password = browser.find_element_by_xpath(
      ('//*[@id="section-main"]/div/div[3]/div[2]/div[8]/table/tbody/tr/td/div'
       '/div/div/div/table/tbody/tr/td[2]/form/div[4]/input'))
    username.send_keys(user)
    password.send_keys(passwd)
    submit = browser.find_element_by_xpath(
      ('//*[@id="section-main"]/div/div[3]/div[2]/div[8]/table/tbody/tr/td/div'
       '/div/div/div/table/tbody/tr/td[2]/form/div[5]/div/input'))
    submit.click()
    cookies = browser.get_cookies()
    pickle.dump(cookies, open(filename, 'wb'))
    browser.quit()


class Scraper:

    def __init__(self, url, cookies, users, driver='Firefox'):
        self.browser = None
        if driver == 'Firefox':
            self.browser = webdriver.Firefox()
        elif driver == 'Chrome':
            self.browser = webdriver.Chrome()
        else:
            raise AttributeError('Invalid Selenium WebDriver: {}'.format(driver))
        self.browser.get('http://www.enjin.com/')
        for c in cookies:
            if c['domain'] == '.enjin.com':
                self.browser.add_cookie(c)
        self.browser.get(url)
        hostname = urlparse(url).hostname
        for c in cookies:
            if c['domain'] == hostname:
                self.browser.add_cookie(c)
        self.browser.refresh()
        self.users = users

        self.db = {}
        self.children = []
        try:
            self.categories = self.browser.find_elements_by_xpath(
              ('//div[contains(@class, "contentbox") and '
                     'contains(@class, "category")]'))
        except NoSuchElementException:
            raise ValueError(('Could not find any categories, '
                              'check the input URL?'))

    def __del__(self):
        if self.browser:
            self.browser.quit()

    def run(self):
        for c in self.categories:
            category = enjinuity.objects.Category(c)
            self.children.append(category)

        for child in self.children:
            child.get_children(self.browser, self.users)

    def run_single(self, category):
        for c in self.categories:
            c_name = c.find_element_by_xpath('div[1]/div[3]/span').text
            if c_name == category:
                cat = enjinuity.objects.Category(c)
                self.children.append(cat)
                cat.get_children(self.browser, self.users)
                return
        raise ValueError('Could not find category {}'.format(category))

    def dump_mybb(self, filename):
        for table in ['forums', 'threads', 'posts', 'polls', 'pollvotes']:
            self.db[table] = []
        for child in self.children:
            child.do_dump_mybb(self.db)
        pickle.dump(self.db, open(filename, 'wb'))

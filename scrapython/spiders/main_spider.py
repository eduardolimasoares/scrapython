from bs4 import BeautifulSoup
import sys
import scrapy
import re
import logging
import json
import os
from scrapy.utils.response import open_in_browser
from scrapy.utils.log import configure_logging
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlparse
from scrapy import Spider, Request, spidermiddlewares
from scrapy.spidermiddlewares.httperror import HttpError
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError
now = datetime.now()


class MainSpider(scrapy.Spider):
    name = 'main_spider'
    allowed_domains = []

    def start_requests(self):
        with sys.stdin as f:
            urls = [x.strip() for x in f.readlines()]

        self.allowed_domains = [urlparse(url).hostname for url in urls]

        for mw in self.crawler.engine.scraper.spidermw.middlewares:
            if isinstance(mw, spidermiddlewares.offsite.OffsiteMiddleware):
                mw.spider_opened(self)

        for url in urls:
            yield scrapy.Request(url, callback=self.parse,
                                 errback=self.errback_httpbin,
                                 dont_filter=True)

    def parse(self, response, **kwargs):
        html_str = response.text
        phone_no = self.extract_phone_number(html_str)
        main_url = self.extract_main_url(response.request.url)
        logo_img = self.extract_images(response, main_url)
        info = {"logo": logo_img, "phones": phone_no, "website": main_url}

        infos = json.dumps(info)
        logging.log(logging.WARNING, infos)
        yield {"logo": logo_img, "phones": phone_no, "website": main_url}

    def extract_phone_number(self, html_as_str):
        phone_no = []
        phones = re.findall(
            r'((?:^(?:\+\d{1})\s(?:\(\d{3}\))\s(?:\d{3})\-(?:\d{4})(?:\.))|(?:\(\d{3}\)\s*?\-?\.?(?:\d{3})\s*?\-?(?:\d{4}))|(?:(?:\+)(?:\d{2})\s*?(?:\d{2})\s*?)(?:\d{3,4})\s*\-?(?:\d{4})|(?:^(?:\(\d{2,3}\)\s*?(?:\d{3,5})\s*?\-?(?:\d{4})))|(?:^(?:\d{2,3})\s*?\-?(?:\d{3,5})\s*?\-?(?:\d{3,4})\s*?\-?\.*?(?:\d{3,4})?)|(?:^(?:\+?\s*?\d{1})\s*?\-?(?:\(\d{3}\))\s*?\-?\.?(?:\d{3,4})\s*?\-?\.?(?:\d{1,})\s*?\#?\.?(?:\d{1,}))|(?:^(?:\+?\s*?\d{1})\s*?\-?(?:\(\d{3}\))\s*?\-?\.?(?:\d{3,4})\s*?\-?\.?(?:\d{1,})\s*?\#?\.?(?:\d{1,})$)|(?:^(?:\+)\s*?\-?(?:\d{1,})\s*\-?(?:\d{1,})\s*\-?(?:\d{1,})\s*\-?(?:\d{1,})\s*\-?(?:\d{1,})$)|(?:^(?:\d{3,4})\s*?\-?(?:\d{3,4})$)|(?:^(?:\d{1})\s*?\-?(?:\d{3})\s*?\-?(?:\d{3})\s*?\-?(?:\d{3,4})$)|(?:(?:^\s*)\+\s*(?:\d{1})\s*?\-?(?:\(\d{3}\))\s*?\-?(?:\d{3})\s*?\-?(?:\d{2})\s*?\-?(?:\d{2})))', html_as_str, flags=re.M)
        # logging.log(logging.WARNING, phones)
        for num in phones:
            num = num.strip()
            num = num.lstrip()
            num = re.sub(r"^\s+", "", num)
            num = num.replace("-", " ")
            num = num.replace(".", " ")
            num = num.replace("/", " ")
            phone_no.append(num)
        return phone_no

    def extract_main_url(self, url_str):
        url = url_str
        main_url = "//".join([url.split('/')[0], url.split('/')[2]])
        return main_url

    def extract_images(self, response, main_url):
        soup = BeautifulSoup(response.body, 'lxml')
        imgs_parsed = soup.find_all("img", {"src": True})
        imgs = []
        for img in imgs_parsed:
            if 'http' in img['src']:
                if re.findall(r'[a-zA-z0-9logo]+', img['src'], flags=re.M):
                    imgs.append(img['src'])
                    return imgs
            else:
                if re.findall(r'[a-zA-z0-9logo]+', img['src'], flags=re.M):
                    src = str(main_url) + str(img['src'])
                    imgs.append(src)
                    return imgs

    def errback_httpbin(self, failure):
        # self.logger.error(repr(failure))
        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('-->HttpError on %s', response.url)

        elif failure.check(DNSLookupError):
            request = failure.request
            self.logger.error('-->DNSLookupError on %s', request.url)

        elif failure.check(TimeoutError, TCPTimedOutError):
            request = failure.request
            self.logger.error('-->TimeoutError on %s', request.url)

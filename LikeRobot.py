#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import requests
import re
import base64
import random
import time
import json

from bs4 import BeautifulSoup

from logger import logger
import config

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko",
    "Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
    "Mozilla/5.0 (Linux; U; Android 4.0.3; ko-kr; LG-L160L Build/IML74K) AppleWebkit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (Linux; U; Android 4.0.3; de-ch; HTC Sensation Build/IML74K) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
    "Mozilla/5.0 (Linux; U; Android 2.3; en-us) AppleWebKit/999+ (KHTML, like Gecko) Safari/999.9",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A",
    "Mozilla/5.0 (iPad; CPU OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Version/6.0 Mobile/10A5355d Safari/8536.25",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2"
]

# TODO: email notification (not necessary)
# TODO: use crontab for scheduling
class LikeRobot(object):

    LIKE_URL = "http://woxue.xdf.cn/Mobile_Teacher_Home/like?u=liutingting22@xdf.cn"

    def __init__(self):
        self.proxy_list = None
        self.url = None
        # self.idle = 0
        self.idle =self._get_idle_time()

    def _get_soup(self, count=10):
        try:
            proxy_response = requests.get(self.url)
            return BeautifulSoup(proxy_response.content, "html.parser")
        except requests.exceptions.ConnectionError:
            logger.info("Retry opening proxy website.")
            if count >= 0:
                return self._get_soup(count-1)
            else:
                raise Exception("Failed to open proxy website")

    @staticmethod
    def _get_type(type_tag, sep='/'):
        return [t.lower() for t in type_tag.string.split(sep) if t.lower() != 'socks4']

    # TODO: improve scheduling model
    @staticmethod
    def _get_idle_time(mean=config.MEAN, deviation=config.DEVIATION, maximum=config.MAXIMUM):
        guess = min(maximum, abs(random.gauss(mean, deviation)))
        if guess == maximum or guess == 0:
            rd = random.random()
            guess += (-1)**int(rd*10)*rd
        return int(guess*config.PERIOD)

    def _format_proxy(self):
        proxy = self.proxy_list.pop(0)
        if proxy['type'][0].startswith('socks'):
            return {"http":proxy['type'][0] + "://" + proxy['host'] + ":" + proxy['port']}
        else:
            return {proxy['type'][0]:proxy['type'][0] + "://" + proxy['host'] + ":" + proxy['port']}

    def _like_response(self):
        p = self._format_proxy()
        agent = random.choice(USER_AGENTS)
        logger.info("Using proxy: {0} and user-agent: {1}".format(p.values()[0], agent))
        return requests.get(self.LIKE_URL, proxies=p, headers={'User-Agent':agent})

    def _get_proxy_list(self):
        pass

    def get_proxy_list(self):
        return self._get_proxy_list()

    def _like(self):
        try:
            content = self._like_response().content
            response = json.loads(content)
            if response['Status'] == 1:
                logger.info("Successfully liked the link. Num of Like: {0}".format(response['Count']))
                if response['Count'] > 10000:
                    logger.info("Unexpected number. Respnse: {0}".format(content))
            else:
                logger.info("Failed to like. Response: {0}".format(content))

        except requests.exceptions.ConnectionError:
            logger.info("Failed to connect proxy.")
            self._like()
        except Exception:
            raise

    def like(self):
        try:
            self.proxy_list = self.get_proxy_list()
            self._like()

        # running out of proxies
        except IndexError:
            self.like()
        except Exception:
            raise

    def run(self, init=False):
        if init:
            self.idle = 0
        while 1:
            time.sleep(self.idle)

            try:
                self.like()

            except Exception as e:
                logger.info("Error -- Type: {0} ; Message: {1}".format(type(e), e))
                # break

            self.idle = self._get_idle_time()

            h = int(self.idle / 3600)
            m = int((self.idle % 3600) / 60)
            s = int(self.idle % 60)

            logger.info("Next action will be taken in {0}h {1}m {2}s\n\n".format(h, m, s))


class GoubanjiaProxyRobot(LikeRobot):

    URL = "http://proxy.goubanjia.com"

    def __init__(self):
        super(GoubanjiaProxyRobot, self).__init__()
        self.url = self.URL
        self.hidden_pattern = re.compile(".*display.*none.*")

    def _not_hidden_tag(self, tag):
        if tag.has_attr('style'):
            return not self.hidden_pattern.search(tag['style'])
        return True

    def _decode_port(self, tag):
        code = tag['class'][1]
        count = 0

        for i, l in enumerate(code[::-1]):
            count += (ord(l) - 65)*10**i if l != 'Z' else 9*10**i
        return str(count / 8)

    def _get_proxy_list(self):
        proxy_list = []
        soup = self._get_soup()

        plist = soup.find('div', id='list').table.tbody

        for tr in plist.find_all('tr')[:20]:
            td = tr.find_all('td')[:4]
            host = ""
            for block in td[0].find_all(self._not_hidden_tag):
                host += block.string or ""
            port = self._decode_port(td[1])
            protocol = self._get_type(td[3], sep=',')
            proxy_list.append({'host':host, 'port':port, 'type':protocol})

        return proxy_list


class MimvpProxyRobot(LikeRobot):

    URL = "http://proxy.mimvp.com/index.php"

    def __init__(self):
        super(MimvpProxyRobot, self).__init__()
        self.img_pattern = re.compile(".*port=(.*)")
        self.url = self.URL

    def _get_port(self, img_tag):
        encoded_port = self.img_pattern.search(img_tag['src']).group(1)
        encoded_port = (encoded_port[0] + encoded_port[2] + encoded_port[4]
                        + encoded_port[6] + encoded_port[8] + encoded_port[10:]).replace("O0O", "=")
        return base64.b64decode(encoded_port)[2:]

    def _get_proxy_list(self):
        proxy_list = []
        soup = self._get_soup()

        plist = soup.find('div', id='list').table.tbody

        for tr in plist.find_all('tr'):
            td = tr.find_all('td')[:4]
            host = td[1].string
            port = self._get_port(td[2].img)
            protocol = self._get_type(td[3])
            proxy_list.append({'host':host, 'port':port, 'type':protocol})

        return proxy_list


if __name__ == '__main__':

    if len(sys.argv) > 1:
        if sys.argv[1] == '2':
            gbj = GoubanjiaProxyRobot()
            gbj.run()

    mimvp = MimvpProxyRobot()
    mimvp.run()


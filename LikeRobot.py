#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import requests
import re
import base64
import random
import time
import json

from bs4 import BeautifulSoup

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

# TODO: email notification
# TODO: random user agent
# TODO: add logger
class LikeRobot(object):

    LIKE_URL = "http://woxue.xdf.cn/Mobile_Teacher_Home/like?u=liutingting22@xdf.cn"

    def __init__(self):
        self.proxy_list = None
        self.url = None
        self.idle = 0

    def _get_soup(self):
        proxy_response = requests.get(self.url)
        return BeautifulSoup(proxy_response.content, "html.parser")

    @staticmethod
    def _get_type(type_tag, sep='/'):
        return [t.lower() for t in type_tag.string.split(sep)]

    # TODO: handle boundary condition
    # TODO: improve generating model
    @staticmethod
    def _get_idle_time(mean=0, deviation=2.5, maximum=6):
        return int(min(maximum, abs(random.gauss(mean, deviation)))*3600)

    def _format_proxy(self):
        proxy = self.proxy_list.pop(0)
        if proxy['type'][0].startswith('socks'):
            return {"http":proxy['type'][0] + "://" + proxy['host'] + ":" + proxy['port']}
        else:
            return {proxy['type'][0]:proxy['type'][0] + "://" + proxy['host'] + ":" + proxy['port']}

    def _like_response(self):
        p = self._format_proxy()
        print "Using proxy -- {0}".format(p.values()[0])
        return requests.get(self.LIKE_URL, proxies=p, headers={'User-Agent':random.choice(USER_AGENTS)})

    def _get_proxy_list(self):
        pass

    def get_proxy_list(self):
        # print "Getting proxies..."
        return self._get_proxy_list()

    def like(self):
        while 1:
            try:
                print "Sending LIKE request..."
                content = self._like_response().content
                response = json.loads(content)

                if response['Status'] == 1:
                    print "Successfully like your object!"
                    print "Num of Like: {0}".format(response['Count'])
                else:
                    print "Failed to like! Response: {0}".format(content)

                break

            except requests.exceptions.ConnectionError:
                print "Connection failed! Trying another one..."
                continue

            except Exception:
                raise

    def run(self):
        print "Program started!"
        while 1:
            time.sleep(self.idle)

            try:
                self.proxy_list = self.get_proxy_list()
                self.like()

            except IndexError:
                print "Run out of proxies! Try to refresh proxy list..."
                self.idle = 0
                continue

            except Exception as e:
                print "Error -- Type: {0} ; Message: {1}".format(type(e), e)
                break

            self.idle = self._get_idle_time()
            # self.idle = 5

            h = int(self.idle / 3600)
            m = int((self.idle % 3600) / 60)
            s = int(self.idle % 60)

            print "Next action will be taken in {0}h {1}m {2}s\n\n".format(h, m, s)


class GoubanjiaProxy(LikeRobot):

    URL = "http://proxy.goubanjia.com"

    def __init__(self):
        super(GoubanjiaProxy, self).__init__()
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


class MimvpProxy(LikeRobot):

    URL = "http://proxy.mimvp.com/index.php"

    def __init__(self):
        super(MimvpProxy, self).__init__()
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
            gbj = GoubanjiaProxy()
            gbj.run()

    mimvp = MimvpProxy()
    mimvp.run()

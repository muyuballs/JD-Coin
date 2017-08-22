GET_QR_CODE = (
    "https://ssl.ptlogin2.qq.com/ptqrshow?appid=716027609&e=2&l=M&s=3&d=72&v=4&t=0.3262779565452971&daid=383",
    "https://xui.ptlogin2.qq.com/cgi-bin/xlogin?"
    "appid=716027609"
    "&daid=383"
    "&style=33"
    "&login_text=%E6%8E%88%E6%9D%83%E5%B9%B6%E7%99%BB%E5%BD%95"
    "&hide_title_bar=1"
    "&hide_border=1"
    "&target=self"
    "&s_url=https%3A%2F%2Fgraph.qq.com%2Foauth%2Flogin_jump&pt_3rd_aid=10027302"
    "0&pt_feedback_link=http%3A%2F%2Fsupport.qq.com%2Fwrite.shtml%3Ffid%3D780%26SSTAG%3Dwww.jd.com.appid100273020",
    "")
VERIFY_QR_CODE = (
    "https://ssl.ptlogin2.qq.com/ptqrlogin?"
    "u1=https%3A%2F%2Fgraph.qq.com%2Foauth%2Flogin_jump"
    "&ptqrtoken={ptqrtoken}"
    "&ptredirect=0"
    "&h=1"
    "&t=1"
    "&g=1"
    "&from_ui=1"
    "&ptlang=2052"
    "&action=0-0-{action}"
    "&js_ver=10228"
    "&js_type=1"
    "&login_sig=7btp7B8r-a0EVg3gITyajuGQGEb4b8a-h0MeKQckKVYR9hjx3TdbtIufzL1DJLfj"
    "&pt_uistyle=40"
    "&aid=716027609"
    "&daid=383"
    "&pt_3rd_aid=100273020"
    "&has_onekey=1&",
    "https://xui.ptlogin2.qq.com/cgi-bin/xlogin?"
    "appid=716027609"
    "&daid=383"
    "&style=33"
    "&login_text=%E6%8E%88%E6%9D%83%E5%B9%B6%E7%99%BB%E5%BD%95"
    "&hide_title_bar=1"
    "&hide_border=1"
    "&target=self"
    "&s_url=https%3A%2F%2Fgraph.qq.com%2Foauth%2Flogin_jump&pt_3rd_aid=10027302"
    "0&pt_feedback_link=http%3A%2F%2Fsupport.qq.com%2Fwrite.shtml%3Ffid%3D780%26SSTAG%3Dwww.jd.com.appid100273020",
    "")
CHECK_SIG = ("{1}", "", "")
AUTHORIZE = ("https://graph.qq.com/oauth2.0/authorize",
             "https://graph.qq.com/oauth/show?which=Login&display=pc&response_type=code&client_id=100273020&redirect_uri=https%3A%2F%2Fqq.jd.com%2Fnew%2Fqq%2Fcallback.action%3Fview%3Dnull",
             "https://graph.qq.com")

REDIRECT_URL = "https://qq.jd.com/new/qq/callback.action?view=null"
CLIENT_ID = "100273020"
OPEN_API = "80901010"
USER_AGENT = "Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36"

'''
https://graph.qq.com/oauth/show?which=Login&display=pc&response_type=code&client_id=100273020&redirect_uri=https%3A%2F%2Fqq.jd.com%2Fnew%2Fqq%2Fcallback.action%3Fview%3Dnull
1. 获取二维码
2. 循环调用 VERIFY_QR_CODE，直到 二维码失效 或者 扫描成功
3. 调用 CHECK_SIG 302 -> login_jump
4. 调用 AUTHORIZE 320 -> qq.jd.com -> 302 -> target
'''

import requests
import qrcode
import zbarlight
from PIL import Image
import os
import time
import random


def ptuiCB(a, b, url, *others):
    return url


class QQQrCode:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.session.proxies = {'http': '127.0.0.1:8888', 'https': '127.0.0.1:8888'}
        pass

    def genqrcode(self):
        try:
            resp = self.session.get(GET_QR_CODE[0])
            if resp.status_code != 200:
                print('gen qr code error', resp.status_code, resp.reason)
            else:
                with open("qr.png", "wb", ) as tf:
                    tf.write(resp.content)
                resp.close()
                img = Image.open("qr.png", "r")
                img.load()
                codes = zbarlight.scan_codes('qrcode', img)
                img.close()
                os.remove("qr.png")
                print('qrcode is', codes)
                img = qrcode.make(codes, box_size=1, error_correction=qrcode.ERROR_CORRECT_L, border=1)
                for i in range(0, img.size[1]):
                    for j in range(0, img.size[0]):
                        r = img.getpixel((j, i))
                        if r == 0:
                            print("  ", end="")
                        else:
                            print("\u2588\u2588", end='')
                    print('\n', end='')
                print('pls scan use mobile qq')
                return True
        except Exception as e:
            print(e)
            return False
        pass

    def verify_qrcode(self):
        try:
            qrsig = self.session.cookies.get("qrsig")
            ptqrtoken = self.hash33(qrsig)
            while True:
                resp = self.session.get(
                    VERIFY_QR_CODE[0].format(ptqrtoken=ptqrtoken, action=int(time.time() * 1000)),
                    headers={'Referer': VERIFY_QR_CODE[1]})
                if resp.status_code != 200:
                    raise Exception('%d %s' % (resp.status_code, resp.reason))
                if resp.text.find('成功') > -1:
                    text = resp.text.strip()
                    if text.endswith(";"):
                        return eval(text[:-1])
                    else:
                        return eval(text)
                elif resp.text.find('已失效') > -1:
                    return 2
                else:
                    time.sleep(0.05)
        except Exception as e:
            print(e)
            return -1
        pass

    def check_sig(self, sig):
        try:
            ui = self.uuid()
            print("UI", ui)
            self.session.cookies.set("ui", ui, domain=".graph.qq.com", path="/")
            resp = self.session.get(sig)
            if resp.status_code == 200:
                print(resp.text)
                return True
            else:
                print(resp.status_code, resp.reason)
                return False
        except Exception as e:
            print(e)
        pass

    def authorize(self):
        try:
            resp = self.session.post(AUTHORIZE[0], data={
                'response_type': 'code',
                'client_id': 100273020,
                'redirect_uri': REDIRECT_URL,
                'scope': '',
                'state': '',
                'switch': '',
                'from_ptlogin': 1,
                'src': 1,
                'update_auth': 1,
                'openapi': 80901010,
                'g_tk': self.g_tk(),
                'auth_time': int(time.time() * 1000),
                'ui': self.session.cookies.get('ui')
            }, headers={'Referer': AUTHORIZE[1], 'Origin': AUTHORIZE[2]})
            if resp.status_code != 200:
                print(resp.status_code, resp.reason)
                return False
            print(resp.url)
            if str(resp.url) == "http://www.jd.com/":
                return True

        except Exception as e:
            print(e)
            return False
        pass

    def uuid(self):
        p = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
        n = []
        for i in range(0, len(p)):
            x = int(random.random() * 16)
            if p[i] == 'x':
                n.append(hex(x)[2:])
            elif p[i] == 'y':
                n.append(hex(x & 0x3 | 0x8)[2:])
            else:
                n.append(p[i])

        return ''.join(n).upper()

    def g_tk(self):
        h = 5381
        cookies = self.session.cookies
        s = cookies.get('p_skey') or cookies.get('skey') or ''
        for c in s:
            h += (h << 5) + ord(c)
        return h & 0x7fffffff

    pass

    def hash33(self, s):
        e = 0
        n = len(s)
        for x in s:
            e += (e << 5) + ord(x)
        return 2147483647 & e


def get_cookies(url):
    qqr = QQQrCode()
    print("gen qrcode")
    if not qqr.genqrcode():
        return False
    print("verify qrcode")
    ret = qqr.verify_qrcode()
    if ret == -1:
        return False
    if ret == 2:
        print("qr code time out")
        return False
    print("check sig ", ret)
    if not qqr.check_sig(ret):
        print("check sig failed")
        return False
    print("call auth")
    if not qqr.authorize():
        print("authorize failed")
    return qqr.session.cookies
    pass


def proxy_patch():
    """
    Requests 似乎不能使用系统的证书系统, 方便起见, 不验证 HTTPS 证书, 便于使用代理工具进行网络调试...
    http://docs.python-requests.org/en/master/user/advanced/#ca-certificates
    """
    import warnings
    from requests.packages.urllib3.exceptions import InsecureRequestWarning

    class XSession(requests.Session):
        def __init__(self):
            super().__init__()
            self.verify = False

    requests.Session = XSession
    warnings.simplefilter('ignore', InsecureRequestWarning)


if __name__ == "__main__":
    proxy_patch()
    get_cookies('')

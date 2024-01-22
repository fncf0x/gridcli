#!/bin/python
import requests
import argparse
from tabulate import tabulate
import os
import sys
import urllib3

urllib3.disable_warnings()


class GridApi:
    def __init__(self, username, password, api_key, port=None):
        self.API_URL = 'https://gridpanel.net/api/'
        self.LOGIN_URL = 'https://gridpanel.net/login?next=/dashboard'
        self.PROXY_MANAGER_URL = 'https://gridpanel.net/dashboard/manage-order?o={}'
        self.PAGINATION_DASHBOARD = 'https://gridpanel.net/dashboard?page={}'
        self.REBOOT_URL = "https://gridpanel.net/api/reboot?token={}"
        self.EXTEND_PORT_URL = "https://gridpanel.net:443/dashboard/extend-order"
        self.ADD_USA_PROXY_URL = 'https://gridpanel.net/dashboard/order?product=5g-usa-mobile-proxies'
        self.headers = {
            "Upgrade-Insecure-Requests": "1",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Sec-Ch-Ua": "",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"\"",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.post_headers = {
            "Cache-Control": "max-age=0",
            "Sec-Ch-Ua": "",
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": "\"\"",
            "Upgrade-Insecure-Requests": "1",
            "Origin": "https://gridpanel.net",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                          " (KHTML, like Gecko) Chrome/114.0.5735.199 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
                      "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-User": "?1",
            "Sec-Fetch-Dest": "document",
            "Referer": "PLACEHOLDER",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9"
        }
        self.loggedIn = False
        self.username = username
        self.password = password
        self.api_key = api_key
        self.port = port
        self.proxy_host = ""
        self.proxy_user = ""
        self.proxy_pass = ""
        self.dashboard = ""
        self.proxy_token = ""
        self.sess = requests.Session()

    def login(self):
        r = self.sess.get(self.LOGIN_URL, headers=self.headers, verify=False)
        csrfmiddlewaretoken = r.text.split('"csrfmiddlewaretoken" value="')[1].split('"')[0]
        data = {
            "csrfmiddlewaretoken": csrfmiddlewaretoken,
            "username": self.username,
            "password": self.password}
        r = self.sess.post(self.LOGIN_URL, headers=self.headers, data=data, verify=False)
        self.dashboard = r.text
        if "/dashboard/manage-order" not in self.dashboard:
            return False
        if port:
            for i in range(2, 20):
                if str(self.port) in self.dashboard:
                    break
                else:
                    r = self.sess.get(self.PAGINATION_DASHBOARD.format(i), headers=self.headers, verify=False)
                    self.dashboard = r.text
            self.get_proxy_config()
        return True

    def get_proxy_config(self):
        proxy_part = self.dashboard.split(str(self.port))[1][:300]
        proxy_manage_id = proxy_part.split('/dashboard/manage-order?o=')[1].split('"')[0]
        r = self.sess.get(self.PROXY_MANAGER_URL.format(proxy_manage_id), headers=self.headers, verify=False)
        self.proxy_token = r.text.split('https://gridpanel.net/api/reboot?token=')[1].split('"')[0]
        proxy_curl = r.text.split(
            'connection_string" type="text" class="form-control" readonly value="'
        )[1].split('"')[0]
        self.proxy_host = proxy_curl.split('@')[1].split(':')[0]
        self.proxy_user = proxy_curl.split('@')[0].split('//')[1].split(':')[0]
        self.proxy_pass = proxy_curl.split('@')[0].split('//')[1].split(':')[1]
        return True

    def get_proxies_expired(self):
        params = {
            'api_key': self.api_key,
        }
        response = requests.get('https://gridpanel.net/api/proxies', params=params)
        proxies = response.json()['orders']
        count = 0
        data = [['PORT', 'STATUS', 'TYPE', 'PLAN', 'ROTATIVE']]
        for proxy in proxies:
            info = proxies[proxy]
            if 'insufficient_funds' in info['status']:
                count += 1
                data.append([proxy, info['status'], info['plan'], info['duration'], info['auto_rotate']])
        total = [["TOTAL", count]]
        print(tabulate(data, headers=[], tablefmt='grid'))
        print(tabulate(total, headers=[], tablefmt='grid'))

    def get_proxies_expired_quiet(self):
        params = {
            'api_key': self.api_key,
        }
        response = requests.get('https://gridpanel.net/api/proxies', params=params)
        proxies = response.json()['orders']
        for proxy in proxies:
            info = proxies[proxy]
            if 'USA' in info['plan'] and 'Monthly' in info['duration'] and info['port'] and 'insufficient_funds' in info['status']:
                print(info['port'])

    def extend_proxy(self):
        proxy_part = self.dashboard.split(str(self.port))[1][:300]
        proxy_manage_id = proxy_part.split('/dashboard/manage-order?o=')[1].split('"')[0]
        r = self.sess.get(self.PROXY_MANAGER_URL.format(proxy_manage_id), headers=self.headers, verify=False)
        csrfmiddlewaretoken = r.text.split('"csrfmiddlewaretoken" value="')[1].split('"')[0]
        data = {
            "csrfmiddlewaretoken": csrfmiddlewaretoken,
            "order_id": proxy_manage_id}
        self.post_headers.update({
            "Referer": f"https://gridpanel.net/dashboard/manage-order?o={proxy_manage_id}"
        })
        r = self.sess.post(self.EXTEND_PORT_URL, headers=self.post_headers, data=data, verify=False)
        if 'please top-up' in r.text:
            print("Insufficient funds")
        elif 'ready for use' in r.text:
            print(f'port [{self.port}] renewed successfully !')

    def get_proxies(self):
        params = {
            'api_key': self.api_key,
        }
        response = requests.get('https://gridpanel.net/api/proxies', params=params)
        proxies = response.json()['orders']
        count = 0
        data = [['PORT', 'STATUS', 'TYPE', 'PLAN', 'ROTATIVE']]
        for proxy in proxies:
            info = proxies[proxy]
            count += 1
            data.append([proxy, info['status'], info['plan'], info['duration'], info['auto_rotate']])
        total = [["TOTAL", count]]
        print(tabulate(data, headers=[], tablefmt='grid'))
        print(tabulate(total, headers=[], tablefmt='grid'))

    def get_proxies_quiet(self):
        params = {
            'api_key': self.api_key,
        }
        response = requests.get('https://gridpanel.net/api/proxies', params=params)
        proxies = response.json()['orders']
        us_proxies = []
        for proxy in proxies:
            info = proxies[proxy]
            if 'USA' in info['plan'] and 'Monthly' in info['duration'] and info['port']:
                us_proxies.append(info['port'])
        for i, port in enumerate(us_proxies):
            if (i + 1) % 5 == 0 and i != 0:
                print(f'"{port}"\n')
            else:
                print(f'"{port}",')
        print(f'\nTotal: {len(us_proxies)}')

    def reboot(self):
        r = self.sess.get(self.REBOOT_URL.format(self.proxy_token), headers=self.headers, verify=False)
        print(r.text)

    def test_proxy(self):
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}@{self.proxy_host}:{self.port}"
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }
        try:
            response = requests.get("https://ipinfo.io/json", proxies=proxies)
            ip = response.json()['ip']
            city = response.json()['city']
            region = response.json()['region']
            country = response.json()['country']
            org = response.json()['org']
            timezone = response.json()['timezone']
            location = f"{city}, {region}, {country}"
        except requests.exceptions.ProxyError:
            print(f'Connection error on PORT {self.port} ')
            exit(1)
        except Exception as e:
            print(f"{e} error on PORT {self.port}")
            exit(1)
        info = [
            ["PORT", self.port],
            ["IP", ip],
            ["LOCATION", location],
            ["OPERATOR", org],
            ["TIMEZONE", timezone],
        ]
        print(tabulate(info, headers=[], tablefmt='grid'))

    def add_proxy(self):
        r = self.sess.get(self.ADD_USA_PROXY_URL, headers=self.headers, verify=False)
        csrfmiddlewaretoken = r.text.split('"csrfmiddlewaretoken" value="')[1].split('"')[0]
        data = {
            "csrfmiddlewaretoken": csrfmiddlewaretoken,
            "payment_plan": "14",
            "addon_min_rotation_time": "5_MINUTES",
            "addon_setup": "STANDARD",
            "auto_renew": "on",
            "proxy_type": "HTTP",
            "auth-method": "user",
            "username": "proxy",
            "password": "L7DBwcF",
            "allowed_ips": '', "discount_code": ''}
        r = self.sess.post(self.ADD_USA_PROXY_URL, headers=self.headers, data=data, verify=False)
        if r.status_code == 200:
            print("New US Proxy Added")

    def get_config(self):
        return {
            "ip": self.proxy_host,
            "port": self.port,
            "user": self.proxy_user,
            "password": self.proxy_pass
        }


if __name__ == "__main__":
    # check argc
    if len(sys.argv) == 1:
        print(f"Use: {sys.argv[0]} -h for help menu.")
        exit(1)

    # init ArgumentParser
    parser = argparse.ArgumentParser(
                    prog='GridProxy-cli',
                    description='simple CLI to manage GridProxy')
    parser.add_argument('-p', '--port', help='port', type=int)
    parser.add_argument('-l', '--list-proxies', help='list available proxies', action='store_true')
    parser.add_argument('-x', '--list-expired-proxies', help='list expired proxies', action='store_true')
    parser.add_argument('-r', '--reboot', help='reboot a proxy',  action='store_true')
    parser.add_argument('-t', '--test-port', help='test a proxy port',  action='store_true')
    parser.add_argument('-e', '--extend-port', help='extend a proxy port',  action='store_true')
    parser.add_argument('-q', '--quiet', help='print only available port USA without grid',  action='store_true')
    parser.add_argument('-a', '--add', help='add one US proxy',  action='store_true')
    parser.add_argument('-c', '--count', help='number of proxies to add', type=int)
    args = parser.parse_args()

    port = args.port
    add = args.add
    count = args.count
    list_proxies = args.list_proxies
    list_expired_proxies = args.list_expired_proxies
    extend_port = args.extend_port
    quiet = args.quiet
    test_port = args.test_port
    reboot = args.reboot

    # check if any of the above commands is passed
    if not any([v for v in [list_proxies, list_expired_proxies, reboot, test_port, extend_port, add]]):
        exit(1)

    # check env var
    if not all(env in os.environ for env in ['grid_email', 'grid_passwd', 'grid_token']):
        print("Please set env variable: grid_email, grid_passwd, grid_token of your grid account")
        exit(1)

    # init GridApi
    username = os.environ['grid_email']
    passwd = os.environ['grid_passwd']
    grid_token = os.environ['grid_token']
    grid = GridApi(username, passwd, grid_token, port)
    grid.login()

    if list_expired_proxies:
        if quiet:
            grid.get_proxies_expired_quiet()
            exit(0)
        else:
            grid.get_proxies_expired()
            exit(0)
    if list_proxies:
        if quiet:
            grid.get_proxies_quiet()
            exit(0)
        else:
            grid.get_proxies()
            exit(0)
    if test_port:
        if not port:
            print("You must specify a port to test")
            exit(1)
        grid.test_proxy()
    if extend_port:
        if not port:
            print("You must specify a port to test")
            exit(1)
        grid.extend_proxy()
    if reboot:
        if not port:
            print("You must specify a port to reboot")
            exit(1)
        grid.reboot()
    if add:
        if count:
            print(f"Adding {count} US proxies")
            for _ in range(count):
                grid.add_proxy()
            exit(0)
        else:
            grid.add_proxy()

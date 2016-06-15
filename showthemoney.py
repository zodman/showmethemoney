#!/usr/bin/env python
# encoding=utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import mechanize
from webscraping import xpath
from decimal import Decimal
import ConfigParser
import requests


class Money:
    def __init__(self):
        br = mechanize.Browser()
        br.set_handle_robots(False)   # ignore robots
        br.set_handle_refresh(False)  # can sometimes hang without this
        ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0 (compatible;)'
        br.addheaders = [('User-Agent', ua), ('Accept', '*/*')]
        self.br = br
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read("config.ini")

    def _get_auth(self,section):
        user = self.cfg.get(section, "user")
        psw  = self.cfg.get(section, "pass")
        return user, psw
    def ouo(self):
        br = self.br
        br.open("http://ouo.io/auth/signin/")
        br.form = list(br.forms())[0]
        user, pswd = self._get_auth('ouo')
        br.form["username"]=user
        br.form["password"]=pswd
        br.submit()
        res = br.response().read()
        doc = xpath.Doc(res)
        return doc.get("//span[@class='h3 text-success font-bold m-t m-b-xs block']")

    def adfly(self):
        br = self.br
        br.open("https://login.adf.ly/login")

        br.form = list(br.forms())[0]   
        u,p = self._get_auth("adfly")
        br.form["email"]=u
        br.form["password"]=p
        br.submit()
        res = br.response().read()
        doc = xpath.Doc(res)
        return doc.get("//h4[@id='total-earnings']")

    def shink(self):
        br = self.br
        br.open("http://panel.shink.in/auth/login")
        br.form = list(br.forms())[0]
        u, p = self._get_auth("shink")
        br.form["identity"]=u
        br.form["password"]=p
        br.submit()
        br.open("http://panel.shink.in/")
        res = br.response().read()
        doc = xpath.Doc(res)
        return doc.search("//span[@class='h3 text-danger font-bold']")[1]

    def bcvc(self):
        br = self.br
        br.open("http://bc.vc")

        br.form = list(br.forms())[2]
        u,p = self._get_auth("bcvc")
        br.form["usr_email"]=u
        br.form["usr_pass"]=p
        br.submit()
        res = br.response().read()
        doc = xpath.Doc(res)
        t = doc.search("//div[@class='user_content']/text()")[0]
        return t.strip().split(" ")[-2]
    
     def shorte(self):
        br = self.br
        br.open("https://shorte.st/es/login")
        u, p = self._get_auth("shorte")
        br.form = list(br.forms())[1]
        br.form["_username"]=u
        br.form["_password"]=p
        br.submit()
        res = br.response().read()
        doc = xpath.Doc(res)
        return doc.get("//a[@class='total-income']")

    def popads(self):
        key = self.cfg.get("popads", "api_key")
        res = requests.get("https://www.popads.net/api/user_status?key={}".format(key))
        return "${}".format(res.json()["user"]["balance"])

    def show_all(self):
        total = 0
        for site in ("ouo", "adfly", "shink", "bcvc"):
            v = getattr(self,site)
            m = v()
            print "{} {}".format(site, m)
            num = m.replace("$","")
            total += Decimal(num)
        print "total ${}".format(total) 

if __name__ == "__main__":
    m = Money()
    m.show_all()

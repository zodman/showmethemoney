#!/usr/bin/env python
# encoding=utf8
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import mechanize
from webscraping import xpath
from decimal import Decimal
import ConfigParser
import requests
import datetime
import os
import plotly.plotly as py
import plotly.graph_objs as go
import dumper

BASE_DIR=os.path.dirname(os.path.realpath(__file__))


class Money:
    limit = 5
    sites = ("ouo", "adfly",  "bcvc","shorte","popads","publited")

    def __init__(self):
        br = mechanize.Browser()
        br.set_handle_robots(False)   # ignore robots
        br.set_handle_refresh(False)  # can sometimes hang without this
        ua = 'Mozilla/5.0 (X11; Linux x86_64; rv:18.0) Gecko/20100101 Firefox/18.0 (compatible;)'
        br.addheaders = [('User-Agent', ua), ('Accept', '*/*')]
        self.br = br
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read( os.path.join(BASE_DIR,"config.ini"))

    def _get_auth(self,section):
        user = self.cfg.get(section, "user")
        psw  = self.cfg.get(section, "pass")
        return user, psw

    def ouo(self):
        br = self.br
        br.open("http://ouo.press/auth/signin/")
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
        print res
        doc = xpath.Doc(res)
        res = doc.search("//span[@class='h3 text-success font-bold']")
        print res
        return res

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
        key = self.cfg.get("popads", "key_api")
        res = requests.get("https://www.popads.net/api/user_status?key={}".format(key))
        return "${}".format(res.json()["user"]["balance"])

    def show_all(self):
        total = 0
        results = []
        for site in self.sites:
            v = getattr(self,site)
            m = v()
            print "{} {}".format(site, m)
            results.append((site, m))
            num = m.replace("$","")
            total += Decimal(num)
        print "total: ${}".format(total) 
        now = datetime.datetime.now()
        print now
        return results, total

    def store(self):
        now = datetime.datetime.now()
        for site in self.sites:
            v = getattr(self, site)
            m = v()
            num = m.replace("$","")
            site_list = dumper.load(site,silent=True, path=BASE_DIR) or []
            site_list.append({'site':site,'datetime':now,'total':num})
            dumper.dump(site_list, site, path=BASE_DIR)
        print "store file {}".format(now)

    def publited(self):
        br = self.br
        br.open("http://www.publited.com/en/login")
        u, p = self._get_auth("publited")
        br.form = list(br.forms())[0]
        br.form["data[User][email]"]=u
        br.form["data[User][password]"]=p
        br.submit()
        res = br.response().read()
        doc = xpath.Doc(res)
        f =  doc.search("//dd[@class='em-price text-green']/a/text()")
        number = f[3].replace(",",".").split(" ")[0]
        return "$ {}".format(number)

    def graph_site(self,site):
        x,y,data = [],[],[]
        site_list = dumper.load(site, path=BASE_DIR)
        y_old = float(site_list[0]["total"])
        for i in site_list:
            t = float(i["total"])- y_old
            y_old = float(i["total"])
            if t != 0:
                x.append(i['datetime'])
                y.append(t)
        data.append(go.Scatter(x=x, y=y, name=site))
        l = dict(layout={'title':site},data=data)
        print (site, py.plot(l,filename=site,fileopt="overwrite",auto_open=False))

    def graph_all(self):
        for site in self.sites:
            self.graph_site(site)

    def graph_total(self):
        data = {}
        old_t = 0
        for site in self.sites:
            site_list = dumper.load(site, path=BASE_DIR)
            for i in site_list:
                wk = i["datetime"].isocalendar()[1]
                data.setdefault(wk,0)
                total  = i["total"].strip()
                if total == "":
                    total = 0
                total = float(total)  - old_t
                data[wk] += total
                old_t = data[wk]
        g = [go.Scatter(x=data.keys(), y=data.values())]
        py.plot(dict(data=g, layout={"title":"Growth"}),filename="nekototal",fileopt="overwrite",auto_open=False)
    def graph_pie(self):
        results, total = self.show_all()
        labels = [i[0] for i in results]
        values = [i[1].replace("$","") for i in results]
        g = [go.Pie(labels=labels, values=values)]
        py.plot(dict(data=g, layout={"title":"Growth"}),filename="nekototalpie",fileopt="overwrite",auto_open=False)
       
    def graph(self):
        data = []
        for site in self.sites:
            site_list = dumper.load(site, path=BASE_DIR)
            x = [i['datetime'] for i in site_list]
            y = [i["total"] for i in site_list]
            data.append(go.Scatter(x=x, y=y, name=site))
        data.append(go.Scatter(y=[self.limit for i in range(0,len(x))],x=x, name="limit"))
        py.plot(dict(data=data,layout={'title':'Total'}),filename="neko",sharing="secret",fileopt="overwrite",auto_open=False)


if __name__ == "__main__":
    import sys
    m = Money()
    if "store" in sys.argv[1:]:
        m.store()
    elif "graph" in  sys.argv[1:]:
        m.graph_pie()
        m.graph()
        m.graph_total()
    elif "dashboard" in sys.argv[1:]:
        m.graph_all()
    else:
        m.show_all()

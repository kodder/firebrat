#!/usr/bin/env python

######################################################
#@Author: Wissam Youssef                             #
#@Email: wissam.youssef@gmail.com                    #
#@version: 0.0.2a                                    #
#@title: Crawler                                     #
#@description: Basic web crawler, collects annchors, #
#              links and scripts url and print them  #
#              on screen (no robots.txt checking)    #
#@todo:  parallelization, better output , clean ups  #
#  #using sets instead of qeues for faster results   #
######################################################
import sys
import time
import argparse
import requests
from validators import url
from bs4 import BeautifulSoup
from termcolor import colored
from urlparse import urlparse,urljoin



class Crawler():

    def __init__(self,starting_url,wait=0.05):
        self.domain,self.base_url = self.extractDomain(starting_url)    #extracs domain name and base url
        self.urls = [starting_url]  #list of urls to process
        self.urlsprocessing = []   #urls getting processed (useful in parallel mode)
        self.urlsvisited = []   #list of visited urls
        self.urlsdead = []   #list of dead urls (404,403,etc... )
        self.scripts = []  #list of scripts
        self.links = []    #list of lists
        self.others = []  #other non text urls found...
        self.agent = "Firebrat/1.0"    #this was needed or else  alot of webpages give 403
        self.headers = {'User-Agent':self.agent}   #headers in http get request.
        self.WAIT = wait  #wait x seconds between http requests so I don't get blocked.

    def extractDomain(self, starting_url):
        '''
        :param starting_url: Starting url from commandline
        :return: 2 variables, thedomain name and the base url
        '''
        ob = urlparse(starting_url)
        if ob.scheme:
            return ob.netloc,ob.scheme+"://"+ob.netloc
        else:
            print "Not a fully compliant url"              #this an extra check, bad urls should been caught before

    def scrapPage(self,page):
        '''
        :param page: Insert url
        :return: none, just sends all the scraped targets to their queues
        '''
        self.urlsprocessing.append(page)
        r = requests.get(page,headers=self.headers)
        if r.status_code == requests.codes.ok:
            soup = BeautifulSoup(r.text,'html.parser')
            for anchor in soup.find_all('a'):
                self.processAnchor(anchor)
            for script in soup.find_all('script'):
                self.processScript(script)
            for link in soup.find_all('link'):
                self.processLink(link)
            self.urlsvisited.append(page)
        else:
            self.urlsdead.append(page)
        del self.urls[self.urls.index(page)]
        #del self.urls[0]
        del self.urlsprocessing[self.urlsprocessing.index(page)]

    def processAnchor(self,anchor):
        """
        :param anchor: the anchor to process
        :return: nothing, just sends targets to proper queues
        """

        url = self.getLocation(anchor.get('href'))
        #the following needs some prettifying some "all" and "generator"  or replace with series of ands...
        if url:
            if url not in self.urlsvisited:
                if url not in self.urlsprocessing:
                    if url not in self.urlsdead:
                        if url not in self.urls:
                            r = requests.head(url)
                            if "text" in r.headers["content-type"]:    #no need for get, head is enough and faster
                                self.urls.append(url)
                            elif "application" in r.headers["content-type"]:
                                self.others.append(url)



    def getLocation(self,url):
        """
        :param url: url to check
        :return: normalised url or none if it is outside the requirements (different domain)
        """
        ob = urlparse(url)
        if ob.scheme:
            if ob.netloc == self.domain:
                if ob.fragment:
                    url = url.split('#')[0]
                return url
        elif ob.path and not ob.netloc:
            thejoin = urljoin(self.base_url,ob.path)
            if ob.query:
                thejoin = thejoin+"?"+ob.query
            return thejoin
        else:
            return None


    def processScript(self,script):
        """
        :param script: script tag to process
        :return: url for script tags with src only to the proper queue
        """
        if script.get('src'):
            url = self.getLocation(script.get('src'))
            if url and  url not in self.scripts:
                #print self.scripts
                self.scripts.append(url)


    def processLink(self,link):
        """
        :param link: link tag
        :return: link url to the proper queue
        """
        url = self.getLocation(link.get('href'))
        if url and  url not in self.links:
            self.links.append(url)

    def start(self):
        """
        just a start of the crawler :):
        """
        while self.urls:
            sys.stdout.write("\rURLS visited:%d" %len(self.urlsvisited))
            sys.stdout.flush()
            self.scrapPage(self.urls[0])
            time.sleep(self.WAIT)

    def reportAll(self):
        """
        Report everything :)
        """
        print "\n"
        self.reportlinks()
        self.reportscripts()
        self.reportdeads()
        self.reporturls()
        self.reportothers()


    def reportscripts(self):
        if self.scripts:
            print colored("SCRIPT urls:",'green')
            print "\t".join(self.scripts)
            print "\n"
    def reporturls(self):
        if self.urlsvisited:
            print colored("Anchor urls:",'cyan')
            print "\t".join(self.urlsvisited)
            print "\n"

    def reportlinks(self):
        if self.links:
            print colored("Link urls:",'magenta')
            print "\t".join(self.links)
            print "\n"

    def reportdeads(self):
        if self.urlsdead:
            print colored("Dead urls","red")
            print "\t".join(self.urlsdead)
            print "\n"

    def reportothers(self):
        if self.others:
            print colored("Other urls","blue")
            print "\t".join(self.others)
            print "\n"


def main():
    """
    Main function with argparse for a nice commandline interface...
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("url",help="Starting url for the crawler")
    parser.add_argument("-w","--wait", type=float, help="sets waiting time between page scrape , default is 0.05")
    args = parser.parse_args()

    if url(args.url):
        if args.wait:
            crawler = Crawler(args.url,args.wait)
        else:
            crawler = Crawler(args.url)
        print "Domain : %s" %crawler.domain
        print "Base url : %s " %crawler.base_url
        crawler.start()
        crawler.reportAll()
    else:
        print("URL is invalid please write a fully compliant url , example: http://www.iron.io")




if __name__ == "__main__":
    main()

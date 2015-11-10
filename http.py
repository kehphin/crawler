#!/usr/bin/python

import socket
import urlparse
import re
import os
import pprint

socket.setdefaulttimeout = 5

CRLF = "\r\n\r\n"
LOGIN_ENDPOINT = "http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/"
USERNAME = "000507282"
PASSWORD = "HFE94HBL"

csrf_token = None
session_id = None
visited_pages = {}
pages_to_visit = []
flags = []

FAKEBOOK_HOST = "http://fring.ccs.neu.edu"

""""""""""""""""""""""""""""HTMLParser"""""""""""""""""""""""""""""
from HTMLParser import HTMLParser

# create a subclass and override the handler methods
class MyHTMLParser(HTMLParser):
    def handle_starttag(self, tag, attrs):
        for attr in attrs:
            attributeType = attr[0]
            attributeValue = attr[1]
            if attributeType == 'href' and '/fakebook/' in attributeValue:
                if attributeValue not in visited_pages:
                    pages_to_visit.append(attributeValue)
    def handle_data(self, data):
        if "FLAG:" in data:
            print '=========================================Found Flag==================================================='
            print data[6:]
            flags.append(data[6:])

# instantiate the parser and fed it some HTML
parser = MyHTMLParser()
""""""""""""""""""""""""""""HTMLParser"""""""""""""""""""""""""""""

def GET(url):
    url = urlparse.urlparse(url)
    path = url.path
    if path == "":
        path = "/"

    if url.query:
        path += '?' + url.query

    HOST = url.netloc  # The remote host
    PORT = 80          # The same port as used by the server
    # create an INET, STREAMing socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.settimeout(0.30)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((HOST, PORT))

    cookieString = "Cookie:" + generateCookieString()


    message = "GET %s HTTP/1.1\nHost: %s\n%s%s" % (path, HOST, cookieString, CRLF)
    pprint.pprint(message)
    s.send(message)

    data = (s.recv(1000000)).rstrip()

    # Close socket after request is done
    s.shutdown(1)
    s.close()

    return parseHttpResponse(data)

def POST(url, postData, cookieString):
    url = urlparse.urlparse(url)
    path = url.path
    if path == "":
        path = "/"

    if url.query:
        path += '?' + url.query

    HOST = url.netloc  # The remote host
    PORT = 80          # The same port as used by the server
    # create an INET, STREAMing socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.settimeout(0.30)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.connect((HOST, PORT))

    topOfMessage  = "POST %s HTTP/1.1\r\nHost: %s\r\nConnection: close" % (path, HOST)
    contentLength = "Content-Length: " + str(len(postData))
    contentType = "Content-Type: application/x-www-form-urlencoded"
    cookie = "Cookie: " + cookieString

    finalMessage = topOfMessage + "\r\n" + contentLength + "\r\n" + contentType + "\r\n" + cookie + CRLF + postData + CRLF


    pprint.pprint(finalMessage)
    s.send(finalMessage)

    data = (s.recv(1000000))

    # Close socket after request is done
    s.shutdown(1)
    s.close()

    return parseHttpResponse(data)


def parseHttpResponse(data):
    responseTable = {}
    data = data.split(CRLF) 
    header = filter(None, data[0].split("\r\n"))
    
    body = data[1] if len(data) > 1 else ""
    status = header[0].split(" ")[1]

    responseTable['Status'] = status
    responseTable['Body'] = body

    for x in range(1, len(header)):
        pair = header[x].split(": ")
        if pair[0] in responseTable:
            responseTable[pair[0]] += "| " + pair[1]
        else: 
            responseTable[pair[0]] = pair[1]

    return handleCookies(responseTable)

def handleCookies(table):
    if 'Set-Cookie' not in table.keys():
        return table
    cookieString = table['Set-Cookie']
    cookies = cookieString.split("| ")
    wantedCookie = {}
    newCookieString = ""
    for cookie in cookies:
        cookieParts = cookie.split("; ")
        newCookieString += cookieParts[0] + "; "
        firstCookiePart = cookieParts[0].split("=")
        wantedCookie[firstCookiePart[0]] = firstCookiePart[1]

    table['Cookies-Object'] = wantedCookie
    table['Cookie-String'] = newCookieString[:-2]

    return table

def generateCookieString():
    string = ""
    if csrf_token:
        if session_id:
            string = "csrftoken=%s; sessionid=%s" % (csrf_token, session_id)
        else:
            string = "csrftoken=%s" % (csrf_token)
    elif session_id:
        "sessionid=%s" % (session_id)
    return string


def login():
    global csrf_token
    global session_id

    loginPage = GET(LOGIN_ENDPOINT)
    csrf_token = loginPage['Cookies-Object']['csrftoken']
    session_id = loginPage['Cookies-Object']['sessionid']

    postMessage = "username=%s&password=%s&csrfmiddlewaretoken=%s&next=/fakebook/" % (USERNAME, PASSWORD, csrf_token)
    postLogin = POST(LOGIN_ENDPOINT, postMessage, loginPage['Cookie-String'])
    session_id = postLogin['Cookies-Object']['sessionid']

    homePage = GET(postLogin['Location'])
    pprint.pprint(homePage)

    return homePage

def crawlNextPage():
    global pages_to_visit
    global visited_pages

    nextPage = pages_to_visit.pop()
    print "Visiting " + nextPage
    htmlOfNextPage = GET(FAKEBOOK_HOST + nextPage)
    if htmlOfNextPage['Status'] == str(200):
        print "Success"
        parser.feed(htmlOfNextPage['Body'])
        visited_pages[nextPage] = True
    else:
        print "Status Code: " + str(htmlOfNextPage['Status'])
        pages_to_visit.append(nextPage)

def crawl():
    global visited_pages

    homePage = login()
    visited_pages['/fakebook/'] = True #mark homepage as visited
    parsed = parser.feed(homePage['Body'])

    print visited_pages
    print pages_to_visit

    while len(visited_pages) > 0:
        print len(pages_to_visit)
        crawlNextPage()

    print flags

"""
GET /fakebook HTTP/1.1
HOST: fring.ccs.neu.edu

POST /accounts/login/?next=/fakebook/ HTTP/1.1
Host: fring.ccs.neu.edu
Connection: close
Content-Length: 109
Content-Type: application/x-www-form-urlencoded
Cookie: csrftoken=919ccc307b1a07a41e3c12e5dd5aeaff; sessionid=cce8cb18de04172b5450e6e9d3d40a19

username=000507282&password=HFE94HBL&csrfmiddlewaretoken=919ccc307b1a07a41e3c12e5dd5aeaff&next=/fakebook/

"""

crawl()

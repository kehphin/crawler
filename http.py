#!/usr/bin/python

import socket
import urlparse
import re
import os
import pprint

socket.setdefaulttimeout = 0.50
#os.environ['no_proxy'] = '127.0.0.1,localhost'
#linkRegex = re.compile('<a\s*href=[\'|"](.*?)[\'"].*?>')
CRLF = "\r\n\r\n"
dest = "http://fring.ccs.neu.edu/accounts/login/?next=/fakebook/"

loginEndpoint = "http://fring.ccs.neu.edu/accounts/login/"

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
    #s.send("GET / HTTP/1.1\nAccept-Encoding: gzip%s" % (CRLF))
    s.send("GET %s HTTP/1.1\nHost: %s%s" % (path, HOST, CRLF))

    data = (s.recv(1000000)).rstrip()

    # Close socket after request is done
    s.shutdown(1)
    s.close()

    return parseHttpResponse(data)


def parseHttpResponse(data):
    responseTable = {}
    data = data.split("\r\n\n") 
    header = filter(None, data[0].split("\r\n"))
    
    body = data[1]
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
    cookieString = table['Set-Cookie']
    cookies = cookieString.split("| ")
    wantedCookie = {}
    for cookie in cookies:
        cookieParts = cookie.split("; ")
        firstCookiePart = cookieParts[0].split("=")
        wantedCookie[firstCookiePart[0]] = firstCookiePart[1]

    table['Set-Cookie'] = wantedCookie

    return table

def login():
    loginPage = GET(dest)
    pprint.pprint(loginPage)

"""
GET /fakebook HTTP/1.1
HOST: fring.ccs.neu.edu



POST /accounts/login/ HTTP/1.1
Content-Type: application/x-www-form-urlencoded
Content-Length: 109
Host: fring.ccs.neu.edu
Connection: close

username=000507282&password=HFE94HBL&csrfmiddlewaretoken=414aafc545a66d154f30a32da1e36fc1&next=%2Ffakebook%2F

"""

login()
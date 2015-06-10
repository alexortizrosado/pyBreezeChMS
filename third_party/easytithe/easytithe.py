#!/usr/bin/python

"""Python library for Easy Tithe Manager.

Easy Tithe is an online giving platform for churches and organizations that
makes accepting, tracking and reporting online tithing and donations, well...
easy.

The Easy Tithe Manager includes a range of reports, which can be viewed by
person, transaction, fund and date ranges. Access to the Easy Tithe Manager
is done through the Easy Tithe website at
https://www.easytithe.com/cp/default.asp.

Easy Tithe library provides an API for logging into the Easy Tithe Manager
and accessing contribution data.

Usage:
  import easytithe
  
  et = easytithe.EasyTithe('username', 'passsword')
  contributions = et.GetContributions(
    start_date='10/6/2013',
    end_date='10/13/2013')
  print contributions
"""

__author__ = 'alex@rohichurch.org (Alex Ortiz-Rosado)'

import cookielib
import csv
import urllib
import urllib2


class LoginException(Exception):
  pass


class EasyTithe(object):
  def __init__(self, username, password):
    cookie_jar = cookielib.CookieJar()

    self.opener = urllib2.build_opener(
      urllib2.HTTPHandler(debuglevel=0),
      urllib2.HTTPSHandler(debuglevel=0),
      urllib2.HTTPCookieProcessor(cookie_jar))

    self.opener.addheaders = [(
        'User-agent', ('Mozilla/4.0 (compatible; MSIE 6.0; '
                       'Windows NT 5.2; .NET CLR 1.1.4322)'))]
    self._Login(username, password, cookie_jar)

  def _Login(self, username, password, cookie_jar):
    login_data = urllib.urlencode({
      'login': username,
      'password': password,
      'submit': 'Login'
    })
    response = self.opener.open(
        'https://www.easytithe.com/cp/default.asp',
        login_data)
    processed_cookies = [(cookie.name, cookie.value) for cookie in cookie_jar
                         if not cookie.is_expired()]
    cookies = dict(processed_cookies)
    if 'mbadlogin' in cookies:
      if cookies['mbadlogin'] == '1':
        raise LoginException('Login failure. Check username and password.')

  def GetContributions(self, start_date, end_date):
    """Returns a list of contributions.

    Args:
      start_date: Starting date range.
      end_date: Ending date range.

    Returns:
      List of contributions as dict:
        [
          {
            'Name': 'John Doe',
            'Phone': '4085551234',
            'Env Num': '',
            'Fund': 'Offering',
            'Amount': '$50.00',
            'Txn ID #': '5555551',
            'Address': '1234 Main St // San Jose, CA 95135',
            'Date': '5/31/2015 11:30:16 AM',
            'Type': 'Card-5555 Visa',
            'Email': 'jdoe555@yahoo.com'
          }, 
          {
            'Name': 'Jane Types',
            'Phone': '+14085555678',
            'Env Num': '',
            'Fund': 'Tithes',
            'Amount': '$250.00',
            'Txn ID #': '5555552',
            'Address': '5555 Acme Drive // San Jose, CA 95138',
            'Date': '5/31/2015 1:02:33 PM',
            'Type': 'Card-4455 Visa',
            'Email': 'janetypes@gmail.com'
          }
        ]

    """
    report_url = ('https://www.easytithe.com/cp/report-custom_dated-export.asp?'
                  'sdate=%s&edate=%s&organize=comment') % (start_date, end_date)
    report_data = self.opener.open(report_url).readlines()
    report_data = report_data[2:] # Remove the first 2 comment lines.
    contributions = []
    reader = csv.DictReader(report_data)
    for row in reader:
      contributions.append(row)
    return contributions
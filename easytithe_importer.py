#!/usr/bin/python

import argparse
import re
import sys

from breeze import breeze
from datetime import datetime
from third_party.easytithe import easytithe


class Contribution(object):

  def __init__(self, contribution):
    self._contribution = contribution

  @property
  def first_name(self):
    return self._contribution['Name'].split()[0]

  @property
  def last_name(self):
    return self._contribution['Name'].split()[-1]

  @property
  def full_name(self):
    return '%s %s' % (self.first_name, self.last_name)

  @property
  def date(self):
    formatted_date = datetime.strptime(
        self._contribution['Date'], '%m/%d/%Y %I:%M:%S %p')
    return formatted_date.strftime('%d-%m-%Y')

  @property
  def fund(self):
    return self._contribution['Fund']

  @fund.setter
  def fund(self, fund_name):
    self._contribution['Fund'] = fund_name

  @property
  def amount(self):
    return self._contribution['Amount'].lstrip('$').replace(',', '')
  
  @property
  def card_type(self):
    return self._contribution['Type']
  
  @property
  def email_address(self):
    return self._contribution['Email']

def PareArgs():
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '-u', '--username',
    required=True,
    nargs='*',
    help='EasyTithe username.')

  parser.add_argument(
    '-p', '--password',
    required=True,
    nargs='*',
    help='EasyTithe password.')

  parser.add_argument(
    '-k', '--breeze_api_key',
    required=True,
    nargs='*',
    help='Breeze API key.')

  parser.add_argument(
    '-l', '--breeze_url',
    required=True,
    nargs='*',
    help='Fully qualified doman name for your organizations Breeze subdomain.')

  parser.add_argument(
    '-s', '--start_date',
    required=True,
    nargs='*',
    help='Start date to get contribution information for.')

  parser.add_argument(
    '-e', '--end_date',
    required=True,
    nargs='*',
    help='End date to get contribution information for.')

  parser.add_argument(
    '-d', '--dry_run',
    action='store_true',
    help='No-op, do not write anything')


  args = parser.parse_args()
  return args

def main():
  # 6b1c3babdf4eeccad9c7f41a5edcccbf
  args = PareArgs()
  start_date = args.start_date[0]
  end_date = args.end_date[0]

  # EasyTithe
  username = args.username[0]
  password = args.password[0]
  print 'Username: %s\nPassword: %s' % (username, password)
  et = easytithe.EasyTithe(username, password)
  contributions = [Contribution(contribution) for contribution in et.GetContributions(start_date, end_date)]
  
  # Breeze
  breeze_api_key = args.breeze_api_key[0]
  breeze_url = args.breeze_url[0]
  breeze_api = breeze.BreezeApi(breeze_url, breeze_api_key, debug=True, dry_run=args.dry_run)
  people = breeze_api.get_people();
  print 'Date range: %s - %s' % (start_date, end_date)
  print 'Found %d people in database.' % len(people)

  for person in people:
    person['full_name'] = '%s %s' % (person['force_first_name'].strip(),
                                     person['last_name'].strip())
 
  for contribution in contributions:
    person_match = filter(
      lambda person: re.search(person['full_name'],
                               contribution.full_name,
                               re.IGNORECASE), people)
    if person_match:
      # The 2014 Womens Retreat fund contains a non-ascii character.
      if 'Retreat' in contribution.fund:
        contribution.fund('2014 Womens Retreat')
      print 'Adding contribution for [%s] for fund [%s].' % (
          contribution.full_name, contribution.fund)

      # Add the contribution on the matching person's Breeze profile.
      breeze_api.add_contribution(
        date=contribution.date,
        name=contribution.full_name,
        person_id=person_match[0]['id'],
        method='Credit/Debit Online',
        funds_json=('[{"name": "%s", "amount": "%s"}]' % (
            contribution.fund, contribution.amount)),
        amount=contribution.amount,
        group=contribution.date)

    if not person_match:
      print 'WARNING: Unable to find match for [%s].' % full_name

if __name__ == '__main__':
    main()

#!/usr/bin/python
"""Import contributions from EasyTithe to BreezeChMS.

Logs into your EasyTithe account and imports contributions into BreezeChMS using
the Python Breeze API.

Usage:
  python easytithe_importer.py \\
    --username user@email.com \\
    --password easytithe_password \\
    --breeze_url https://demo.breezechms.com \\
    --breeze_api_key 5c2d2cbacg3 \\
    --start_date 01/01/2014 \\
    --end_date 12/31/2014 \\
    [--debug \\]
    [--dry_run \\]
"""
__author__ = 'alex@rohichurch.org (Alex Ortiz-Rosado)'

import argparse
import logging
import os
import re
import sys

from datetime import datetime
from easytithe import easytithe
try:
    from breeze import breeze
except ImportError:
    sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                 os.pardir))
    from breeze import breeze


class Contribution(object):
    """An object for storing a contribution from EasyTithe."""

    def __init__(self, contribution):
        """Instantiates a Contribution object.

    Args:
      contribution: a single contribution from EasyTithe.
    """
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
    def name(self):
        return self._contribution['Name']

    @property
    def date(self):
        formatted_date = datetime.strptime(
            self._contribution['Date'], '%m/%d/%Y')
        return formatted_date.strftime('%Y-%m-%d')

    @property
    def fund(self):
        return self._contribution['Fund']

    @fund.setter
    def fund(self, fund_name):
        self._contribution['Fund'] = fund_name

    @property
    def amount(self):
        # Removes leading $ and any thousands seperator.
        return self._contribution['Amount'].lstrip('$').replace(',', '')

    @property
    def card_type(self):
        return self._contribution['Type']

    @property
    def email_address(self):
        return self._contribution['Email']

    @property
    def uid(self):
        return self._contribution['PersonID']


def parse_args():
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
        help=('Fully qualified doman name for your organizations Breeze '
              'subdomain.'))

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
        help='No-op, do not write anything.')

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Print debug output.')

    args = parser.parse_args()
    return args


def enable_console_logging(default_level=logging.INFO):
    logger = logging.getLogger()
    console_logger = logging.StreamHandler()
    console_logger.setLevel(default_level)

    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)8s] %(filename)s:%(lineno)s - %(message)s ',
        '%Y-%m-%d %H:%M:%S')
    console_logger.setFormatter(formatter)

    logger.addHandler(console_logger)
    logging.Formatter()
    logger.setLevel(default_level)


def main():
    args = parse_args()
    if args.debug:
        enable_console_logging(logging.DEBUG)
    else:
        enable_console_logging()
    start_date = args.start_date[0]
    end_date = args.end_date[0]

    # Log into EasyTithe and get all contributions for date range.
    username = args.username[0]
    password = args.password[0]
    logging.info('Connecting to EasyTithe as [%s]', username)
    easytithe_api = easytithe.EasyTithe(username, password)
    contributions = [
        Contribution(contribution)
        for contribution in easytithe_api.GetContributions(
            start_date, end_date)
    ]

    if not contributions:
        logging.info('No contributions found between %s and %s.', start_date,
                     end_date)
        sys.exit(0)

    logging.info('Found %s contributions between %s and %s.',
                 len(contributions), start_date, end_date)

    # Log into Breeze using API.
    breeze_api_key = args.breeze_api_key[0]
    breeze_url = args.breeze_url[0]
    breeze_api = breeze.BreezeApi(breeze_url, breeze_api_key,
                                  dry_run=args.dry_run)
    people = breeze_api.get_people()
    if not people:
        logging.info('No people in Breeze database.')
        sys.exit(0)
    logging.info('Found %d people in Breeze database.', len(people))

    for person in people:
        person['full_name'] = '%s %s' % (person['force_first_name'].strip(),
                                         person['last_name'].strip())

    for contribution in contributions:
        person_match = [person for person in people
                        if re.search(person['full_name'],
                                     contribution.full_name, re.IGNORECASE) and 
                        person['full_name'] != ' ']

        contribution_params = {
            'date': contribution.date,
            'name': contribution.name,
            'uid': contribution.uid,
            'method': 'Credit/Debit Online',
            'funds_json': (
                '[{"name": "%s", "amount": "%s"}]' % (contribution.fund,
                                                      contribution.amount)),
            'amount': contribution.amount,
            'group': contribution.date,
            'processor': 'EasyTithe',
            'batch_name': 'EasyTithe (%s)' % contribution.date
        }

        if not person_match:
            logging.warning(
                'Unable to find a matching person in Breeze for [%s]. '
                'Adding contribution to Breeze as Anonymous.',
                contribution.full_name)
            breeze_api.add_contribution(**contribution_params)

        else:

            def is_duplicate_contribution(person_id, date, amount):
                """Predicate that checks if a contribution is a duplicate."""
                return breeze_api.list_contributions(
                    start_date=date,
                    end_date=date,
                    person_id=person_id,
                    amount_min=amount,
                    amount_max=amount)

            if is_duplicate_contribution(date=contribution.date,
                                         person_id=person_match[0]['id'],
                                         amount=contribution.amount):
                logging.warning(
                    'Skipping duplicate contribution for [%s] paid on [%s] '
                    'for [%s]', contribution.full_name, contribution.date,
                    contribution.amount)
                continue
            logging.info('Person:[%s]', person_match)

            logging.info(
                'Adding contribution for [%s] to fund [%s] in the amount of '
                '[%s] paid on [%s].', contribution.full_name,
                contribution.fund, contribution.amount, contribution.date)

            # Add the contribution on the matching person's Breeze profile.
            contribution_params['person_id'] = person_match[0]['id']
            breeze_api.add_contribution(**contribution_params)


if __name__ == '__main__':
    main()

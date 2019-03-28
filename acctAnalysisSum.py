#!/usr/bin/env python

# acctAnalysisSum.py -- Output all the credits and debits on an account
#
# Copyright (C) 2009, 2010 ParIT Worker Co-operative <transparency@parit.ca>
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, contact:
# Free Software Foundation           Voice:  +1-617-542-5942
# 51 Franklin Street, Fifth Floor    Fax:    +1-617-542-2652
# Boston, MA  02110-1301,  USA       gnu@gnu.org
#
# @original account_analysis.py for Python 2
# @author Mark Jenkins, ParIT Worker Co-operative <mark@parit.ca>
#
# @revised Mark Sattolo <epistemik@gmail.com>
# @version Python 3.6
# @created 2018
# @updated 2019-03-23

from sys import argv, stdout
from datetime import date, timedelta, datetime
from bisect import bisect_right
from decimal import Decimal
from math import log10
import csv

from gnucash import Session, GncNumeric

"""
Invoke this script like the following example
$ gnucash-env python account_analysis.py gnucash_file.gnucash \
  2010 1 monthly 12 debits-show credits-show Assets 'Test Account'

That will do an analysis on the account 'Assets:Test Account' from
gnucash_file.xac, all of the debits and all of the credits will be shown
and summed on for 12 monthly periods starting from January (1st month) 2010

if you just want to see the credit and debit sums for each period,
use the debits-noshow and credits-noshow argument

The output goes to stdout and is in csv format.

Account path arguments are space separated, so you need to quote parts of
the account path with spaces in them

available period types are monthly, quarterly and yearly

At the moment this script only supports GnuCash files of the sqllite3 type
its an easy edit to switch to xml: etc...
"""

# a dictionary with a period name as key, and number of months in that
# kind of period as the value
PERIODS = {
    "monthly"  :  1,
    "quarterly":  3,
    # mhs | add thirdly, halfly, biyearly
    "thirdly"  :  4,
    "halfly"   :  6,
    "yearly"   : 12,
    "biyearly" : 24
}

NUM_MONTHS = 12
ONE_DAY = timedelta(days=1)
DEBITS_SHOW, CREDITS_SHOW = "debits-show", "credits-show"
ZERO = Decimal(0)


# noinspection PyUnresolvedReferences
def gnc_numeric_to_python_decimal(numeric):
    negative = numeric.negative_p()
    if negative:
        sign = 1
    else:
        sign = 0

    copy = GncNumeric(numeric.num(), numeric.denom())
    result = copy.to_decimal(None)
    if not result:
        raise Exception("gnc numeric value {} can't be converted to decimal".format(copy.to_string()))

    digit_tuple = tuple(int(char) for char in str(copy.num()) if char != '-')
    denominator = copy.denom()
    exponent = int(log10(denominator))
    assert( (10 ** exponent) == denominator )
    return Decimal((sign, digit_tuple, -exponent))


def next_period_start(start_year, start_month, period_type):
    # add numbers of months for the period length
    end_month = start_month + PERIODS[period_type]

    # use integer division to find out if the new end month is in a different year, what year it is,
    # and what the end month number should be changed to.
    # Because this depends on modular arithmetic, we have to convert the month
    # values from 1-12 to 0-11 by subtracting 1 and putting it back after
    #
    # the really cool part is that this whole thing is implemented without
    # any branching; if end_month > NUM_MONTHS
    #
    # Another super nice thing is that you can add all kinds of period lengths to PERIODS
    # fix Python 2 to Python 3 -- need '//' to do integer division
    end_year = start_year + ((end_month - 1) // NUM_MONTHS)
    end_month = ((end_month - 1) % NUM_MONTHS) + 1

    return end_year, end_month


def period_end(start_year, start_month, period_type):
    if period_type not in PERIODS:
        raise Exception("{} is not a valid period, should be {}".format(period_type, str(PERIODS.keys())))

    end_year, end_month = next_period_start(start_year, start_month, period_type)

    # last step, the end date is day back from the start of the next period
    # so we get a period end like
    # 2010-03-31 for period starting 2010-01 instead of 2010-04-01
    # fix Python 2 to Python 3 -- need to fix next_period_start() so end_year is an int rather than a float
    # print("end_year({}) = {}; end_month({}) = {}; ONE_DAY({}) = {}"
    #       .format(type(end_year), end_year, type(end_month), end_month, type(ONE_DAY), ONE_DAY))
    return date(end_year, end_month, 1) - ONE_DAY


def generate_period_boundaries(start_year, start_month, period_type, periods):
    for i in range(periods):
        yield (date(start_year, start_month, 1), period_end(start_year, start_month, period_type))
        start_year, start_month = next_period_start(start_year, start_month, period_type)


def account_from_path(top_account, account_path, original_path=None):
    # mhs | debug
    # print("top_account = %s, account_path = %s, original_path = %s" % (top_account, account_path, original_path))
    if original_path is None:
        original_path = account_path
    account, account_path = account_path[0], account_path[1:]
    # mhs | debug
    # print("account = %s, account_path = %s" % (account, account_path))

    account = top_account.lookup_by_name(account)
    # mhs | debug
    # print("account = " + str(account))
    if account is None:
        raise Exception("path " + str(original_path) + " could not be found")
    if len(account_path) > 0:
        return account_from_path(account, account_path, original_path)
    else:
        return account


def get_splits(acct, period_starts, period_list):
    # insert and add all splits in the periods of interest
    for split in acct.GetSplitList():
        trans = split.parent
        # fix Python 2 to Python 3 -- Gnucash Py3 bindings: GetDate() returns a datetime, not a timestamp
        tx_date = trans.GetDate()
        # print("tx_date({}) = {}".format(type(tx_date), tx_date))
        # trans_date = date.fromtimestamp(tx_date)
        trans_date = tx_date.date()

        # use binary search to find the period that starts before or on the transaction date
        period_index = bisect_right(period_starts, trans_date) - 1

        # ignore transactions with a date before the matching period start
        # (after subtracting 1 above start_index would be -1)
        # and after the last period_end
        if period_index >= 0 and trans_date <= period_list[len(period_list) - 1][1]:

            # get the period bucket appropriate for the split in question
            period = period_list[period_index]

            # more specifically, we'd expect the transaction date to be on or after the period start and before or on
            # the period end, assuming the binary search (bisect_right) assumptions from above are right...
            # in other words, we assert our use of binary search
            # and the filtered results from the above 'if' provide all the protection we need
            assert( period[1] >= trans_date >= period[0] )

            split_amount = gnc_numeric_to_python_decimal(split.GetAmount())

            # if the amount is negative this is a credit, else a debit
            debit_credit_offset = 1 if split_amount < ZERO else 0

            # store the debit or credit Split with its transaction, using the above offset to get in the right bucket
            # if we wanted to be really cool we'd keep the transactions
            period[2 + debit_credit_offset].append((trans, split))

            # add the debit or credit to the sum, using the above offset to get in the right bucket
            period[4 + debit_credit_offset] += split_amount

            # add the debit or credit to the overall total
            period[6] += split_amount


# noinspection PyUnresolvedReferences
def aa_sum_main():
    global gnucash_session
    exe = argv[0].split('/')[-1]
    if len(argv) < 9:
        print("NOT ENOUGH parameters!")
        print("usage: {} <book url> <start year> <start month, numeric> <period type: 'monthly', 'quarterly', etc>".format(exe))
        print("\t\t\t <number of periods to show, from start year and month>")
        print("\t\t\t <whether to show debits: debits-show for true, all other values false>")
        print("\t\t\t <whether to show credits: credits-show for true, all other values false>")
        print("\t\t\t <space-separated account path, as many nested levels as desired>")
        print("examples:\n")
        print("The following example analyzes 12 months of Assets:TestAccount from <...>/test.gnucash, starting in January of 2018, and shows both credits and debits:")
        print("{} <...>/test.gnucash 2018 1 monthly 12 debits-show credits-show Assets TestAccount\n".format(exe))
        print("The following example analyzes 2 quarters of Liabilities:FirstLevel:SecondLevel from <...>/test.gnucash, starting March 2016, and shows credits but not debits:")
        print("{} <...>/test.gnucash 2016 3 quarterly 2 debx credits-show Liabilities <FirstLevel> <SecondLevel>".format(exe))
        print("PROGRAM EXIT!")
        return

    try:
        (gnucash_file, start_year, start_month, period_type, periods, debits_show, credits_show) = argv[1:8]
        # mhs | debug
        print("showing {} periods of {} starting from {}-{}".format(periods, period_type, start_year, start_month))

        start_year, start_month, periods = [int(blah) for blah in (start_year, start_month, periods)]

        # mhs | debug
        print("run-time: {}".format(str(datetime.now())))
        print("running: {}".format(exe))
        print("using gnucash file: {}".format(gnucash_file))

        debits_show = debits_show == DEBITS_SHOW
        credits_show = credits_show == CREDITS_SHOW

        account_path = argv[8:]
        # mhs | debug
        print("account_path = {}".format(str(account_path)))

        gnucash_session = Session(gnucash_file, is_new=False)

        root_account = gnucash_session.book.get_root_account()
        # mhs | debug
        # print( "root_account = " + root_account.GetName() )

        account_of_interest = account_from_path(root_account, account_path)
        # mhs | debug
        print("account_of_interest = {}".format(account_of_interest.GetName()))

        # a list of all the periods of interest
        # for each period keep the start date, end date, a list to store debits and credits,
        # and sums for tracking the sum of all debits and sum of all credits
        period_list = [
            [
                start_date, end_date,
                [],    # debits
                [],    # credits
                ZERO,  # debits sum
                ZERO,  # credits sum
                ZERO   # TOTAL
            ]
            for start_date, end_date in generate_period_boundaries(start_year, start_month, period_type, periods)
        ]
        # a copy of the above list with just the period start dates
        period_starts = [e[0] for e in period_list]

        # mhs | get the list of all descendant accounts
        descendants = account_of_interest.get_descendants()

        if len(descendants) == 0:
            # mhs | account has no descendants so just calculate the splits directly
            get_splits(account_of_interest, period_starts, period_list)
        else:
            # mhs | calculate the sums of debits and credits for EACH sub-account but just keep the overall total
            print("Descendants of {}:".format(account_of_interest.GetName()))
            for subAcct in descendants:
                print("{} balance = {}".format(subAcct.GetName(), subAcct.GetBalance()))
                get_splits(subAcct, period_starts, period_list)

        # write out the column headers
        csv_writer = csv.writer(stdout)
        csv_writer.writerow(())
        csv_writer.writerow(('period start', 'period end', 'debits', 'credits', 'TOTAL'))

        def generate_detail_rows(values):
            return (
                ('', '', '', '', trans.GetDescription(), gnc_numeric_to_python_decimal(split.GetAmount()))
                for trans, split in values )

        # write out the overall totals for the account of interest
        for start_date, end_date, debits, creds, debit_sum, credit_sum, total in period_list:
            csv_writer.writerow((start_date, end_date, debit_sum, credit_sum, total))

            # write the details for each credit or debit if requested on the command line
            if debits_show and len(debits) > 0:
                csv_writer.writerow(('DEBITS', '', '', '', 'description', 'value'))
                csv_writer.writerows(generate_detail_rows(debits))
                csv_writer.writerow(())
            if credits_show and len(creds) > 0:
                csv_writer.writerow(('CREDITS', '', '', '', 'description', 'value'))
                csv_writer.writerows(generate_detail_rows(creds))
                csv_writer.writerow(())

        # no save needed, we're just reading..
        gnucash_session.end()
    except Exception as ae:
        if "gnucash_session" in locals() and gnucash_session is not None:
            gnucash_session.end()
        raise

    print("\n >>> PROGRAM ENDED.")


if __name__ == "__main__":
    aa_sum_main()

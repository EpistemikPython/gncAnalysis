#
# findAssetValue.py -- Find the value of an asset or liability at a certain date
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
# @created 2019-03-23
# @updated 2019-03-24

from sys import argv
from datetime import date, datetime
from decimal import Decimal
from math import log10
from gnucash import Session, GncNumeric


# noinspection PyUnresolvedReferences
def gnc_numeric_to_python_decimal(numeric):
    negative = numeric.negative_p()
    sign = 1 if negative else 0

    copy = GncNumeric(numeric.num(), numeric.denom())
    result = copy.to_decimal(None)
    if not result:
        raise Exception("gnc numeric value {} CAN'T be converted to decimal!".format(copy.to_string()))

    digit_tuple = tuple(int(char) for char in str(copy.num()) if char != '-')
    denominator = copy.denom()
    exponent = int(log10(denominator))
    assert( (10 ** exponent) == denominator )
    return Decimal((sign, digit_tuple, -exponent))


def account_from_path(top_account, account_path, original_path=None):
    if original_path is None:
        original_path = account_path

    account, account_path = account_path[0], account_path[1:]

    account = top_account.lookup_by_name(account)
    if account is None:
        raise Exception("path " + str(original_path) + " could not be found")
    if len(account_path) > 0:
        return account_from_path(account, account_path, original_path)
    else:
        return account


def show_asset_info(acct, idate, cur):
    acct_name = acct.GetName()
    acct_bal = acct.GetBalanceAsOfDate(idate)
    acct_bal_dec = gnc_numeric_to_python_decimal(acct_bal)
    acct_comm = acct.GetCommodity()
    print("{} balance of shares on {} = {}".format(acct_name, idate, acct_bal_dec))

    acct_cad = gnc_numeric_to_python_decimal(acct.ConvertBalanceToCurrencyAsOfDate(acct_bal, acct_comm, cur, idate))
    print("{} balance on 2018-12-31 = CAD${}".format(acct_name, acct_cad))


# noinspection PyUnresolvedReferences, PyBroadException
def find_av_main():
    global gnucash_session
    exe = argv[0].split('/')[-1]
    if len(argv) < 6:
        print("NOT ENOUGH parameters!")
        print("usage: {} <book url> <year> <month> <day> <space-separated path to the account of interest>".format(exe))
        print("PROGRAM EXIT!")
        return

    print("\nrunning {} at run-time: {}\n".format(exe, str(datetime.now())))

    try:
        (gnucash_file, str_year, str_month, str_day) = argv[1:5]
        print("find asset values in {} on {}-{}-{}".format(gnucash_file, str_year, str_month, str_day))

        val_year, val_month, val_day = [int(blah) for blah in (str_year, str_month, str_day)]
        date_of_interest = date(val_year, val_month, val_day)

        account_path = argv[5:]
        print("account_path = {}\n".format(str(account_path)))

        gnucash_session = Session(gnucash_file, is_new=False)
        book = gnucash_session.book

        commod_tab = book.get_table()
        # noinspection PyPep8Naming
        CAD = commod_tab.lookup("ISO4217", "CAD")

        root_account = book.get_root_account()

        account_of_interest = account_from_path(root_account, account_path)
        iname = account_of_interest.GetName()

        show_asset_info(account_of_interest, date_of_interest, CAD)

        # get the list of all descendant accounts
        descendants = account_of_interest.get_descendants()

        if len(descendants) > 0:
            # get the values for EACH sub-account too
            print("\nDescendants of {}:".format(iname))
            for subAcct in descendants:
                show_asset_info(subAcct, date_of_interest, CAD)

        # no save needed, we're just reading...
        gnucash_session.end()

    except Exception as ae:
        if "gnucash_session" in locals() and gnucash_session is not None:
            gnucash_session.end()

    print("\n >>> PROGRAM ENDED.")


if __name__ == "__main__":
    find_av_main()

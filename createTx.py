#!/usr/bin/env python

# test_imbalance_transaction.py -- Test the transaction imbalace viewing
# mechanisms
#
# Copyright (C) 2010 ParIT Worker Co-operative <transparency@parit.ca>
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of
# the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received tx copy of the GNU General Public License
# along with this program; if not, contact:
# Free Software Foundation           Voice:  +1-617-542-5942
# 51 Franklin Street, Fifth Floor    Fax:    +1-617-542-2652
# Boston, MA  02110-1301,  USA       gnu@gnu.org
#
# @author Mark Jenkins, ParIT Worker Co-operative <mark@parit.ca>

##  @file
#   @brief Test the transaction imbalace viewing mechanisms
#   @author Mark Jenkins, ParIT Worker Co-operative <mark@parit.ca>
#   @ingroup python_bindings_examples

__created__ = "2018"
__updated__ = "2019-01-05 10:16"

from sys import argv, exit

from gnucash import Session, Transaction, Split, Account, GncNumeric, GncCommodity, ACCT_TYPE_BANK, GUID
from gnucash.gnucash_core_c import guid_new_return, guid_to_string

# argv[1] should be the path to an existing gnucash file/database
# for tx file, simply pass the pathname, for tx database you can use
# these forms:
# mysql://user:password@host/dbname
# postgres://user:password@host[:port]/dbname (the port is optional)
#
# You should try it out with tx gnucash file with tranding accounts enabled
# and trading accounts disabled

if len(argv) < 6:    
    print("NOT ENOUGH parameters!")
    print("usage: createTx.py <gnucash file> <acct1> <acct2> <amount> <descr>")
    print("example:")
    print("[gnucash-env] [python] createTx.py 'HouseHold.gnucash' 'Dining' 'CIBC Visa' '1313' 'Test'|'Prod'")
    exit()
    
try:
    session = Session(argv[1])
    book = session.book
    
    root = book.get_root_account()
    root.get_instance()
    
    commod_tab = book.get_table()
    session.save()
    
    CAD = commod_tab.lookup("ISO4217", "CAD")
#     USD = commod_tab.lookup("ISO4217","USD")
    
    amount = int(argv[4])
    print("amount = {0}".format(amount))
    amount2 = amount * (-1)
    print("amount2 = {0}".format(amount2))
    
#     print("new guid = {0}".format(guid_to_string(guid_new_return())))
    
    acct1_name = argv[2]
    acct2_name = argv[3]
    acct1 = root.lookup_by_name(acct1_name)
    acct2 = root.lookup_by_name(acct2_name)
#     acct1 = root.lookup_by_code(acct1_code)
    
#     type_acct1 = acct1.GetTypeStr()
#     type_acct2 = acct2.GetTypeStr()
    
    # create a new Tx
    tx = Transaction(book)
    # gets a guid on construction
    print("tx guid = {0}".format(tx.GetGUID().to_string()))

    tx.BeginEdit()
    
    # create two splits for the Tx
    s1 = Split(book)
    s1.SetParent(tx)
    # gets a guid on construction
    print("s1 guid = {0}".format(s1.GetGUID().to_string()))
    s2 = Split(book)
    s2.SetParent(tx)
    # gets a guid on construction
    print("s2 guid = {0}".format(s2.GetGUID().to_string()))
    
    tx.SetCurrency(CAD)
    tx.SetDate(13, 2, 2013)
    tx.SetDescription(argv[5])
    tx.SetNotes("Python {0}".format(argv[0]))
#     tx: set action ?
    
    # set the account and amount of split1
    s1.SetAccount(acct1)
    s1.SetValue(GncNumeric(amount, 100))
#     s1.SetAmount(GncNumeric(amount, 100))
    
    # set the account and amount of split2
    s2.SetAccount(acct2)
    s2.SetValue(GncNumeric(amount2, 100))
#     s2.SetAmount(GncNumeric(amount2, 100))
    
    print("Tx imbalance = {0}".format(tx.GetImbalanceValue().to_string()))
    
    mode = argv[5].upper()
    if mode != "PROD":
        print("Mode = {}: Roll back changes!".format(mode))
        tx.RollbackEdit()
    else:
        print("Mode = {}: Commit and save changes.".format(mode))
        tx.CommitEdit()
        session.save()

    session.end()
#     session.destroy()
except:
    print("createGnuTxs() EXCEPTION!")
    if "session" in locals():
        session.end()
    raise

print("\n >>> PROGRAM ENDED.")

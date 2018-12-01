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

from sys import argv, exit

from gnucash import Session, Transaction, Split, Account, GncNumeric, GncCommodity, ACCT_TYPE_BANK

# argv[1] should be the path to an existing gnucash file/database
# for tx file, simply pass the pathname, for tx database you can use
# these forms:
# mysql://user:password@host/dbname
# postgres://user:password@host[:port]/dbname (the port is optional)
#
# You should try it out with tx gnucash file with tranding accounts enabled
# and trading accounts disabled

if len(argv) < 5:    
    print('not enough parameters!')
    print('usage: createTx.py <gnucash file> <acct1> <acct2> <amount>')
    print('examples:')
    print("gnucash-env python createTx.py 'HouseHold.gnucash' 'dining' 'CIBC Visa' '9.95'")
    exit()

try:
    session = Session(argv[1])
    book = session.book

    root = book.get_root_account()
    root.get_instance()
    
    commod_tab = session.book.get_table()
    CAD = commod_tab.lookup("ISO4217","CAD")
    USD = commod_tab.lookup("ISO4217","USD")
    
    amount = argv[4]
    acct1_name = argv[2]
    acct2_name = argv[3]
    acct1 = root.lookup_by_name(acct1_name)
    acct1 = root.lookup_by_name(acct2_name)
#     acct1 = root.lookup_by_code(acct1_code)
    
    acct1 = Account(book)
    acct2 = Account(book)
    root.append_child(acct1)
    root.append_child(acct2)
    
    acct1.SetCommodity(CAD)
    acct1.SetName("blahblah")
    acct1.SetType(ACCT_TYPE_BANK)
    acct = acct1.GetTypeStr()
    
    acct2.SetCommodity(CAD)
    acct2.SetName("blahblahsdfs ")
    acct2.SetType(3)
    acct2 = acct2.GetTypeStr()

    tx = Transaction(book)
    tx.BeginEdit()

    s = Split(book)
    s.SetParent(tx)
    s2 = Split(book)
    s2.SetParent(tx)

    tx.SetCurrency(CAD)
    s.SetAccount(acct1)
    s.SetValue(GncNumeric(2))
    s.SetAmount(GncNumeric(2))

    s2.SetAccount(acct2)
    s2.SetValue(GncNumeric(4))
    s2.SetAmount(GncNumeric(4))
    print('overall imbalance', tx.GetImbalanceValue().to_string())

    print('per-currency imbalances')
    imbalance_list = tx.GetImbalance()
    for (commod, value) in imbalance_list:
        print(value.to_string(), commod.get_mnemonic())

    tx.CommitEdit()


    session.end()
    session.destroy()
except:
    if "session" in locals():
        session.end()
    raise

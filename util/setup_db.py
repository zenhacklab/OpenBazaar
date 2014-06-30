#!/usr/bin/env python
#
# This library is free software, distributed under the terms of
# the GNU Lesser General Public License Version 3, or any later version.
# See the COPYING file included in this archive
#
# The docstrings in this module contain epytext markup; API documentation
# may be created by processing this file with epydoc: http://epydoc.sf.net
import sqlite3
from os import path

DB_PATH = "db/ob.db"

# TODO: Move DB_PATH to constants file. 
# TODO: Use actual foreign keys.
# TODO: Use indexes.

if not path.isfile(DB_PATH):
    con = sqlite3.connect(DB_PATH)
    with con: 
        cur = con.cursor()
        cur.execute("CREATE TABLE markets(" \
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                    "key TEXT, " \
                    "value TEXT, " \
                    "lastPublished TEXT, " \
                    "originallyPublished TEXT, " \
                    "originallyPublisherID INT, " \
                    "secret TEXT)")

        cur.execute("CREATE TABLE products(" \
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                    "description TEXT, " \
                    "price INT, " \
                    "shippingPrice TEXT, " \
                    "imageData BLOB, " \
                    "quantity INT, " \
                    "key TEXT)")

        cur.execute("CREATE TABLE tags(" \
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                    "name TEXT, " \
                    "productID INT)")

        cur.execute("CREATE TABLE orders(" \
                    "id INTEGER PRIMARY KEY " \
                    "AUTOINCREMENT, " \
                    "state TEXT, " \
                    "address TEXT, " \
                    "buyer TEXT, " \
                    "seller TEXT, " \
                    "escrows TEXT, " \
                    "text TEXT, " \
                    "created TEXT)")

        cur.execute("CREATE TABLE settings(" \
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                    "nickname TEXT, " \
                    "secret TEXT, " \
                    "pubKey TEXT, " \
                    "guid TEXT, " \
                    "email TEXT, " \
                    "pgpPubKey TEXT, " \
                    "bcAddress TEXT, " \
                    "storeDescription TEXT, " \
                    "street1 TEXT, " \
                    "street2 TEXT, " \
                    "city TEXT, " \
                    "stateProvinceRegion TEXT, " \
                    "zip TEXT, " \
                    "country TEXT, " \
                    "actAsArbiter INT, " \
                    "experienceDescription TEXT)")

        cur.execute("CREATE TABLE arbiters(" \
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                    "address TEXT)")

        cur.execute("CREATE TABLE reviews(" \
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                    "pubKey TEXT, " \
                    "subject TEXT, " \
                    "signature TEXT, " \
                    "text TEXT, " \
                    "rating INT)")

"""
This module manages all market related activities
"""

import json
import logging
import hashlib
import random
from threading import Thread

from protocol import proto_page, query_page
from reputation import Reputation
from orders import Orders
import protocol
import lookup
from pymongo import MongoClient
from db_store import Obdb 
from data_uri import DataURI
from PIL import Image, ImageOps
from StringIO import StringIO
import base64

class Market(object):

    def __init__(self, transport):

        """This class manages the active market for the application

        Attributes:
          _transport (CryptoTransportLayer): Transport layer for messaging between nodes.
          _dht (DHT): For storage across the network.
          _market_id (int): Indicates which local market we're working with.

        """

        # Current
        self._transport = transport
        self._dht = transport.getDHT()
        self._market_id = transport.getMarketID()
        self._myself = transport.getMyself()
        self._peers = self._dht.getActivePeers()

        # Legacy for now
        self.query_ident = None
        self.reputation = Reputation(self._transport)
        self.orders = Orders(self._transport)
        self.order_entries = self.orders._orders
        self.nicks = {}
        self.pages = {}
        self.welcome = False
        self.mypage = None
        self.signature = None
        self.nickname = None

        self._log = logging.getLogger('[%s] %s' % (self._market_id, self.__class__.__name__))
        self._log.info("Loading Market %s" % self._market_id)

        self._db = Obdb()
        self.settings = self._transport.settings

        welcome = True

        if self.settings:
            if  'welcome' in self.settings.keys() and self.settings['welcome']:
                welcome = False

        # Register callbacks for incoming events
        self._transport.add_callback('query_myorders', self.on_query_myorders)
        self._transport.add_callback('peer', self.on_peer)
        self._transport.add_callback('query_page', self.on_query_page)
        self._transport.add_callback('page', self.on_page)
        self._transport.add_callback('negotiate_pubkey', self.on_negotiate_pubkey)
        self._transport.add_callback('proto_response_pubkey', self.on_response_pubkey)

        self.load_page(welcome)


    def load_page(self, welcome):

        nickname = self.settings['nickname'] if self.settings.has_key("nickname") else ""
        store_description = self.settings['storeDescription'] if self.settings.has_key("storeDescription") else ""

        tagline = "%s: %s" % (nickname, store_description)
        self.mypage = tagline
        self.nickname = nickname
        self.signature = self._transport._myself.sign(tagline)

        if welcome:
            self._db.updateEntries("settings", {'market_id': self._transport._market_id}, {"welcome":"noshow"})
        else:
            self.welcome = False


    def save_product(self, msg):
        #self._log.debug("Saving product: %s" % msg)

        msg['market_id'] = self._market_id


        product_id = msg['id'] if msg.has_key("id") else ""

        if product_id == "":
            product_id = random.randint(0, 1000000)

        if not msg.has_key("productPrice") or not msg['productPrice'] > 0:
            msg['productPrice'] = 0

        if not msg.has_key("productQuantity") or not msg['productQuantity'] > 0:
            msg['productQuantity'] = 1


        if msg.has_key('productImageData'):

            uri = DataURI(msg['productImageData'])
            imageData = uri.data
            mime_type = uri.mimetype
            charset = uri.charset

            image = Image.open(StringIO(imageData))
            croppedImage = ImageOps.fit(image, (100, 100), centering=(0.5, 0.5))
            data = StringIO()
            croppedImage.save(data, format='PNG')


            new_uri = DataURI.make('image/png', charset=charset, base64=True, data=data.getvalue())
            data.close()
            msg['productImageData'] = new_uri

        # Save product listing to DHT
        listing = json.dumps(msg)
        listing_key = hashlib.sha1(listing).hexdigest()

        hash_value = hashlib.new('ripemd160')
        hash_value.update(listing_key)
        listing_key = hash_value.hexdigest()

        msg['key'] = listing_key
        self._db.insertEntry("products", msg)
        self._log.debug('New Listing Key: %s' % listing_key)

        # Store listing



        self._transport._dht.iterativeStore(self._transport, listing_key, listing, self._transport._guid)

        self.update_listings_index()

        # If keywords store them in the keyword index

    def republish_listing(self, msg):

        listing_id = msg.get('productID')
        listing_ids = self._db.selectEntries("products", {"id": listing_id})
        key = listing['key']

        listing = json.loads(listing)

        self._transport._dht.iterativeStore(self._transport, key, listing, self._transport._guid)


    def update_listings_index(self):

        # Store to marketplace listing index
        listing_index_key = hashlib.sha1('listings-%s' % self._transport._guid).hexdigest()
        hashvalue = hashlib.new('ripemd160')
        hashvalue.update(listing_index_key)
        listing_index_key = hashvalue.hexdigest()

        # Calculate index of listings
        my_listings = []
        listing_ids = self._db.selectEntries("products", {"market_id": self._transport._market_id, 'key':1})
        for listing_id in listing_ids: 
            my_listings.append(listing_id['key'])

        self._log.debug('My Listings: %s' % my_listings)

        # Sign listing index for validation and tamper resistance
        data_string = str({'guid':self._transport._guid, 'listings': my_listings})
        signature = self._myself.sign(data_string).encode('hex')

        value = {'signature': signature, 'data': {'guid':self._transport._guid, 'listings': my_listings}}

        # Pass off to thread to keep GUI snappy
        Thread(target=self._transport._dht.iterativeStore, args=(self._transport, listing_index_key, value, self._transport._guid,)).start()


    def remove_product(self, msg):
        self._log.info("Removing product: %s" % msg)
        self._db.deleteEntries("products", {'id':msg['productID']})
        self.update_listings_index()


    def get_products(self):
        self._log.info('Getting products for market: %s' % self._transport._market_id)
        products = self._db.selectEntries("products", {"market_id": self._transport._market_id})
        return {"products": products}



    # SETTINGS

    def save_settings(self, msg):
        self._log.info("Settings to save %s" % msg)
        self._log.info(self._transport)
        self._db.updateEntries("settings", {'market_id': self._transport._market_id}, msg)

    def get_settings(self):
        self._log.info(self._transport._market_id) 
        settings = self._db.getOrCreate("settings", {"market_id": self._transport._market_id})
        if settings:
            return settings


    # PAGE QUERYING

    def query_page(self, find_guid):

        self._log.info('Querying page: %s' % find_guid)
        msg = query_page(find_guid)
        msg['uri'] = self._transport._uri
        msg['senderGUID'] = self._transport.guid
        msg['pubkey'] = self._transport.pubkey

        self._transport.send(msg, find_guid)


    def on_page(self, page):

        self._log.info("Page received and being stored in Market")

        #pubkey = page.get('pubkey')
        guid = page.get('senderGUID')
        page = page.get('text')

        if guid and page:
            self.pages[guid] = page


    # Return your page info if someone requests it on the network
    def on_query_page(self, peer):
        self._log.info("Someone is querying for your page")
        self.settings = self.get_settings()
        #self._log.info(base64.b64encode(self.settings['storeDescription']))
        self._transport.send(proto_page(self._transport._uri,
                                        self._transport.pubkey,
                                        self._transport.guid,
                                        self.settings['storeDescription'],
                                        self.signature,
                                        self.settings['nickname'],
                                        self.settings['PGPPubKey'] if self.settings.has_key('PGPPubKey') else '',
                                        self.settings['email'] if self.settings.has_key('email') else '',
                                        self.settings['bitmessage'] if self.settings.has_key('bitmessage') else ''),
                                        peer['senderGUID']
                                        )

    def on_query_myorders(self, peer):
        self._log.info("Someone is querying for your page: %s" % peer)


    def on_peer(self, peer):
        pass

    def on_negotiate_pubkey(self, ident_pubkey):
        self._log.info("Someone is asking for your real pubKey")
        assert "nickname" in ident_pubkey
        assert "ident_pubkey" in ident_pubkey
        nickname = ident_pubkey['nickname']
        ident_pubkey = ident_pubkey['ident_pubkey'].decode("hex")
        self._transport.respond_pubkey_if_mine(nickname, ident_pubkey)

    def on_response_pubkey(self, response):
        self._log.info("got a pubkey!")
        assert "pubkey" in response
        assert "nickname" in response
        assert "signature" in response
        pubkey = response["pubkey"].decode("hex")
        #signature = response["signature"].decode("hex")
        nickname = response["nickname"]
        # Cache mapping for later.
        if nickname not in self._transport.nick_mapping:
            self._transport.nick_mapping[nickname] = [None, pubkey]
        # Verify signature here...
        # Add to our dict.
        self._transport.nick_mapping[nickname][1] = pubkey
        self._log.info("[market] mappings: ###############")
        for key, value in self._transport.nick_mapping.iteritems():
            self._log.info("'%s' -> '%s' (%s)" % (
                key, value[1].encode("hex") if value[1] is not None else value[1],
                value[0].encode("hex") if value[0] is not None else value[0]))
        self._log.info("##################################")




    def lookup(self, msg):

        if self.query_ident is None:
            self._log.info("Initializing identity query")
            self.query_ident = lookup.QueryIdent()

        nickname = str(msg["text"])
        key = self.query_ident.lookup(nickname)
        if key is None:
            self._log.info("Key not found for this nickname")
            return "Key not found for this nickname", None

        self._log.info("Found key: %s " % key.encode("hex"))
        if nickname in self._transport.nick_mapping:
            self._log.info("Already have a cached mapping, just adding key there.")
            response = {'nickname': nickname,
                        'pubkey': self._transport.nick_mapping[nickname][1].encode('hex'),
                        'signature': self._transport.nick_mapping[nickname][0].encode('hex'),
                        'type': 'response_pubkey',
                       }
            self._transport.nick_mapping[nickname][0] = key
            return None, response

        self._transport.nick_mapping[nickname] = [key, None]

        self._transport.send(protocol.negotiate_pubkey(nickname, key))

import random
import logging
import time

from protocol import order
from pyelliptic import ECC
from multisig import Multisig
from db_store import Obdb
import gnupg
import hashlib
import string
import json
import datetime

class Orders(object):
    def __init__(self, transport, market_id):

        self._transport = transport
        self._priv = transport._myself
        self._market_id = market_id

        self._gpg = gnupg.GPG()

        # TODO: Make user configurable escrow addresses
        self._escrows = [
            "02ca0020a9de236b47ca19e147cf2cd5b98b6600f168481da8ec0ca9ec92b59b76db1c3d0020f9038a585b93160632f1edec8278ddaeacc38a381c105860d702d7e81ffaa14d",
            "02ca0020c0d9cd9bdd70c8565374ed8986ac58d24f076e9bcc401fc836352da4fc21f8490020b59dec0aff5e93184d022423893568df13ec1b8352e5f1141dbc669456af510c"]
        self._db = Obdb()
        self._orders = self.get_orders()
        self.orders = self._orders

        self._transport.add_callback('order', self.on_order)

        self._log = logging.getLogger('[%s] %s' % (self._market_id, self.__class__.__name__))

    def get_order(self, orderId):

        order = self._db.selectEntries("orders", {"id": orderId})[0]
        order["escrows"] = self._db.selectEntries("escrows", {"id": order["id"]}) 
        order_escrows = ""
        for e in order["escrows"]:
            for key, val in e.iteritems():
                order_escrows = order_escrows + ", " + val
        order["escrows"] = order_escrows
        return order

    def get_orders(self):
        orders = self._db.selectEntries("orders", order_field="created", order="DESC")
        for o in orders:
            o["escrows"] = self._db.selectEntries("escrows", {"id": o["id"]})
        return orders



    # Create a new order
    def create_order(self, seller, text):
        self._log.info('CREATING ORDER')
        id = random.randint(0, 1000000)
        buyer = self._transport._myself.get_pubkey()
        new_order = order(id, buyer, seller, 'new', text, self._escrows)

        # Add a timestamp
        new_order['created'] = time.time()

        self._transport.send(new_order, seller)
        self._db.insertEntry("orders", new_order)
        for escrow in self._escrows:
            self._db.getOrCreate("escrows", {"address": escrow}) 


    def accept_order(self, new_order):

        # TODO: Need to have a check for the vendor to agree to the order

        new_order['state'] = 'accepted'
        seller = new_order['seller'].decode('hex')
        buyer = new_order['buyer'].decode('hex')

        new_order['escrows'] = [new_order.get('escrows')[0]]
        escrow = new_order['escrows'][0].decode('hex')

        # Create 2 of 3 multisig address
        self._multisig = Multisig(None, 2, [buyer, seller, escrow])

        new_order['address'] = self._multisig.address
        self._db.updateEntries("orders", {"id": new_order['id']}, {new_order})
        self._transport.send(new_order, new_order['buyer'].decode('hex'))

    def pay_order(self, new_order):  # action
        new_order['state'] = 'paid'
        self._db.updateEntries("orders",{"id": new_order['id']},new_order)
        new_order['type'] = 'order'
        self._transport.send(new_order, new_order['seller'].decode('hex'))

    def send_order(self, order_id, contract):  # action
        self._log.info('Verify Contract and Store in Orders Table')
        self._log.debug('Contract: %s' % contract)

        contract_data = ''.join(contract.split('\n')[6:])
        index_of_signature = contract_data.find('- -----BEGIN PGP SIGNATURE-----', 0, len(contract_data))
        contract_data_json = contract_data[0:index_of_signature]
        #self._log.info('data %s' % contract_data_json)

        try:
            contract_data_json = json.loads(contract_data_json)
            seller_pubkey = contract_data_json.get('Seller').get('seller_PGP')

            self._gpg.import_keys(seller_pubkey)

            split_results = contract.split('\n')
            #self._log.debug('DATA: %s' % split_results[3])

            v = self._gpg.verify(contract)
            if v:
                self._log.info('Verified Contract')
                #self._db.orders.update({"id": order_id}, {"$set": {"state": "sent", "updated": time.time()}}, True)
                self._db.updateEntries("orders", {"id": order_id}, {"state": "sent", "updated": str(time.time())})
            else:
                self._log.error('Could not verify signature of contract.')
        except:
            self._log.debug('Error getting JSON contract')

            # new_order['state'] = 'sent'
            # self._db.orders.update({"id": new_order['id']}, {"$set": new_order}, True)
            # new_order['type'] = 'order'
            # self._transport.send(new_order, new_order['buyer'].decode('hex'))

    def receive_order(self, new_order):  # action
        new_order['state'] = 'received'
        self._db.updateEntries("orders",{"id": new_order['id']},new_order)
        self._transport.send(new_order, new_order['seller'].decode('hex'))


    def new_order(self, msg):

        buyer = {}
        buyer['buyer_GUID'] = self._transport._guid
        buyer['buyer_BTC_uncompressed_pubkey'] = ""
        buyer['buyer_pgp'] = self._transport.settings['PGPPubKey']
        buyer['buyer_deliveryaddr'] = ""
        buyer['note_for_seller'] = msg['message']

        self._log.debug(buyer)

        # Add to contract and sign
        seed_contract = msg.get('rawContract')

        gpg = self._gpg

        # Prepare contract body
        json_string = json.dumps(buyer, indent=0)
        seg_len = 52
        out_text = string.join(map(lambda x: json_string[x:x + seg_len],
                                   range(0, len(json_string), seg_len)), "\n")

        # Append new data to contract
        out_text = "%s\n%s" % (seed_contract, out_text)

        signed_data = gpg.sign(out_text, passphrase='P@ssw0rd',
                               keyid=self._transport.settings.get('PGPPubkeyFingerprint'))

        self._log.debug('Double-signed Contract: %s' % signed_data)

        # Hash the contract for storage
        contract_key = hashlib.sha1(str(signed_data)).hexdigest()
        hash_value = hashlib.new('ripemd160')
        hash_value.update(contract_key)
        contract_key = hash_value.hexdigest()

        # Save order locally in database
        #order_id = random.randint(0, 1000000)
        #while self._db.contracts.find({'id': order_id}).count() > 0:
        #    order_id = random.randint(0, 1000000)

        #self._db.orders.update({'id': order_id}, {
        #    '$set': {'market_id': self._transport._market_id, 'contract_key': contract_key,
        #             'signed_contract_body': str(signed_data), 'state': 'new'}}, True)

        order_id = self._db.insertEntry("orders", {
                            'market_id': self._transport._market_id, 'contract_key': contract_key,
                            'signed_contract_body': str(signed_data), 'state': 'new'})

        # Push buy order to DHT and node if available
        # self._transport._dht.iterativeStore(self._transport, contract_key, str(signed_data), self._transport._guid)
        #self.update_listings_index()

        # Send order to seller
        self.send_order(order_id, str(signed_data))


    # Order callbacks
    def on_order(self, msg):

        self._log.debug(msg)

        state = msg.get('state')

        if state == 'new':
            self.new_order(msg)


            #
            #
            # state = msg.get('state')
            #
            # buyer = msg.get('buyer').decode('hex')
            # seller = msg.get('seller').decode('hex')
            # myself = self._transport._myself.get_pubkey()
            #
            # if not buyer or not seller or not state:
            # self._log.info("Malformed order")
            #     return
            #
            # if not state == 'new' and not msg.get('id'):
            #     self._log.info("Order with no id")
            #     return
            #
            # # Check order state
            # if state == 'new':
            #     if myself == buyer:
            #         self.create_order(seller, msg.get('text', 'no comments'))
            #     elif myself == seller:
            #         self._log.info(msg)
            #         self.accept_order(msg)
            #     else:
            #         self._log.info("Not a party to this order")
            #
            # elif state == 'cancelled':
            #     if myself == seller or myself == buyer:
            #         self._log.info('Order cancelled')
            #     else:
            #         self._log.info("Order not for us")
            #
            # elif state == 'accepted':
            #     if myself == seller:
            #         self._log.info("Bad subjects [%s]" % state)
            #     elif myself == buyer:
            #         # wait for confirmation
            #         self._db.orders.update({"id": msg['id']}, {"$set": msg}, True)
            #         pass
            #     else:
            #         self._log.info("Order not for us")
            # elif state == 'paid':
            #     if myself == seller:
            #         # wait for  confirmation
            #         pass
            #     elif myself == buyer:
            #         self.pay_order(msg)
            #     else:
            #         self._log.info("Order not for us")
            # elif state == 'sent':
            #     if myself == seller:
            #         self.send_order(msg)
            #     elif myself == buyer:
            #         # wait for confirmation
            #         pass
            #     else:
            #         self._log.info("Order not for us")
            # elif state == 'received':
            #     if myself == seller:
            #         pass
            #         # ok
            #     elif myself == buyer:
            #         self.receive_order(msg)
            #     else:
            #         self._log.info("Order not for us")
            #
            # # Store order
            # if msg.get('id'):
            #     if self.orders.find({id: msg['id']}):
            #         self.orders.update({'id': msg['id']}, {"$set": {'state': msg['state']}}, True)
            #     else:
            #         self.orders.update({'id': msg['id']}, {"$set": {msg}}, True)

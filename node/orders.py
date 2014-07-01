import random
import logging
import time

from protocol import order
from pyelliptic import ECC
from pymongo import MongoClient
from multisig import Multisig
from db_store import Obdb


class Orders(object):
    def __init__(self, order_transport):
        self._transport = order_transport
        self._priv = order_transport._myself

        # TODO: Make user configurable escrow addresses
        self._escrows = [
            "02ca0020a9de236b47ca19e147cf2cd5b98b6600f168481da8ec0ca9ec92b59b76db1c3d0020f9038a585b93160632f1edec8278ddaeacc38a381c105860d702d7e81ffaa14d",
            "02ca0020c0d9cd9bdd70c8565374ed8986ac58d24f076e9bcc401fc836352da4fc21f8490020b59dec0aff5e93184d022423893568df13ec1b8352e5f1141dbc669456af510c"]
        self._db = Obdb()
        self._orders = self.get_orders()
        order_transport.add_callback('order', self.on_order)
        self._log = logging.getLogger(self.__class__.__name__)

    def get_order(self, orderId):

        order = self._db.selectEntries("orders", {"id": orderId})[0]
        order["escrows"] = self._db.selectEntries("escrows", {"id": order["id"]}) 
        order_escrows = ""
        for e in order["escrows"]:
            for key, val in e.iteritems():
                order_escrows = order_escrows + ", " + val
        order["escrows"] = order_escrows
        return order

    def get_orders:

        orders = self._db.selectEntries("orders", order_field="created", order="DESC")
        for o in orders:
            o["escrows"] = self._db.selectEntries("escrows", {"id": o["id"]})
        return orders

    # Create a new order
    def create_order(self, seller, text):
        self._log.info('CREATING ORDER')
        id = random.randint(0, 1000000)
        buyer = self._transport._myself.get_pubkey()
        new_order = order(id, buyer, seller, 'new', text)

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

    def send_order(self, new_order):  # action
        new_order['state'] = 'sent'
        self._db.updateEntries("orders",{"id": new_order['id']},new_order)
        new_order['type'] = 'order'
        self._transport.send(new_order, new_order['buyer'].decode('hex'))

    def receive_order(self, new_order):  # action
        new_order['state'] = 'received'
        self._db.updateEntries("orders",{"id": new_order['id']},new_order)
        self._transport.send(new_order, new_order['seller'].decode('hex'))


    # Order callbacks
    def on_order(self, msg):

        state = msg.get('state')

        buyer = msg.get('buyer').decode('hex')
        seller = msg.get('seller').decode('hex')
        myself = self._transport._myself.get_pubkey()

        if not buyer or not seller or not state:
            self._log.info("Malformed order")
            return

        if not state == 'new' and not msg.get('id'):
            self._log.info("Order with no id")
            return

        # Check order state
        if state == 'new':
            if myself == buyer:
                self.create_order(seller, msg.get('text', 'no comments'))
            elif myself == seller:
                self._log.info(msg)
                self.accept_order(msg)
            else:
                self._log.info("Not a party to this order")

        elif state == 'cancelled':
            if myself == seller or myself == buyer:
                self._log.info('Order cancelled')
            else:
                self._log.info("Order not for us")

        elif state == 'accepted':
            if myself == seller:
                self._log.info("Bad subjects [%s]" % state)
            elif myself == buyer:
                # wait for confirmation
                self._db.updateEntries("orders",{"id": new_order['id']},msg)
                pass
            else:
                self._log.info("Order not for us")
        elif state == 'paid':
            if myself == seller:
                # wait for  confirmation
                pass
            elif myself == buyer:
                self.pay_order(msg)
            else:
                self._log.info("Order not for us")
        elif state == 'sent':
            if myself == seller:
                self.send_order(msg)
            elif myself == buyer:
                # wait for confirmation
                pass
            else:
                self._log.info("Order not for us")
        elif state == 'received':
            if myself == seller:
                pass
                # ok
            elif myself == buyer:
                self.receive_order(msg)
            else:
                self._log.info("Order not for us")

        # Store order
        if msg.get('id'):
            if self.orders.find({id: msg['id']}):
                self.orders.update({'id': msg['id']}, {"$set": {'state': msg['state']}}, True)
            else:
                self.orders.update({'id': msg['id']}, {"$set": {msg}}, True)


if __name__ == '__main__':
    seller = ECC(curve='secp256k1')

    class FakeTransport():
        _myself = ECC(curve='secp256k1')

        def add_callback(self, section, cb):
            pass

        @staticmethod
        def send(msg, to=None):
            print 'sending', msg

        @staticmethod
        def log(msg):
            print msg

    transport = FakeTransport()
    rep = Orders(transport)
    rep.on_order(order(None, transport._myself.get_pubkey(), seller.get_pubkey(), 'new', 'One!', ["dsasd", "deadbeef"]))

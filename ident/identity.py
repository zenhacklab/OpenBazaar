import zmq
import sys
import hashlib
import obelisk
import broadcast
import forge
import shelve
from twisted.internet import reactor
from twisted.internet.task import LoopingCall
import logging
from logging import FileHandler, StreamHandler

class Blockchain:

    def __init__(self):
        self.blocks = []
        self.processor = []
        self.registry = {}
        db = shelve.open("blockchain")
        try:
            for block in db["chain"]:
                self.accept(block)
        except KeyError:
            pass
        db.close()
        self._regenerate_lookup()
        logging.getLogger().info("[Blockchain] Starting identity blockchain %s:" % self.blocks)

	# Accept block(s) for processing
    def accept(self, block):
        self.processor.append(block)

	#
    def update(self):
        process = self.processor
        self.processor = []
        for block in process:
            self.process(block)

    def process(self, block):
        if not block.complete:
            self.postpone(block)
            return
        logging.getLogger().info("Processing block...", block)

        # Check hash of keys + values matches root hash
        if not block.verify():
            # Invalid block so reject it.
            print >> sys.stderr, "Rejecting invalid block."
            return

        # Fetch tx to check it's valid
        assert block.header.tx_hash

        # Forging callback
        def tx_fetched(ec, tx):
            print ec
            if ec is not None:
                print >> sys.stderr, "Block doesn't exist (yet)."
                self.postpone(block)
                return
            self._tx_fetched(block, tx, block.header.tx_hash)

        if forge.client is None:
            forge.client = obelisk.ObeliskOfLightClient("tcp://obelisk.unsystem.net:8081")
        forge.client.fetch_transaction(block.header.tx_hash, tx_fetched)

    def _tx_fetched(self, block, tx, tx_hash):

        # Continuing on with block validation...
        tx = obelisk.Transaction.deserialize(tx)
        if len(tx.outputs) != 2:
            print >> sys.stderr, "Tx outputs not 2, incorrect."
            return

        # Incorrect output size
        if len(tx.outputs[0].script) != 22:
            print >> sys.stderr, "Incorrect output script size."
            return

        # Transaction scriptPubKey doesn't start with OP_RETURN + push
        if tx.outputs[0].script[:2] != "\x6a\x14":
            print >> sys.stderr, "OP_RETURN + push"
            return

        root_hash = tx.outputs[0].script[2:]

        # Root hashes don't match
        if block.header.root_hash != root_hash:
            print >> sys.stderr, "Non matching root hash with tx."
            return

        # Fetch tx height/index associated with block

        # Fetch tx callback
        def txidx_fetched(ec, height, offset):
            if ec is not None:
                print >> sys.stderr, "Dodgy error, couldn't find tx off details."
                return
            self._txidx_fetched(block, height, offset)

        forge.client.fetch_transaction_index(tx_hash, txidx_fetched)

    def _txidx_fetched(self, block, height, offset):

        # Continue on... Block seems fine...
        # Check prev hash is in the list.
        if not self._block_hash_exists(block.prev_hash):
            print >> sys.stderr, "Previous block does not exist. Re-processing later."
            reactor.callLater(5, self.accept, block)
            return

        # Check for duplicate priority
        block.priority = height * 10**8 + offset
        if self._priority_exists(block.priority):
            print >> sys.stderr, "Blocks cannot have matching priorities."
            return

        # Add new block and sort on priority
        self.blocks.append(block)
        self.blocks.sort(key=lambda b: b.priority)
        self._regenerate_lookup()

        # add to blockchain
        logging.getLogger().info("Done!")
        db = shelve.open("blockchain")
        db["chain"] = self.blocks
        db.close()

    def _regenerate_lookup(self):
        for block in self.blocks:
            for name, key in block.txs:
                if name not in self.registry:
                    logging.getLogger().info("Adding:", name)
                    self.registry[name] = key
                else:
                    logging.getLogger().info("Name already in registry")

    def postpone(self, block):
        # read for later processing
        self.accept(block)

    def _priority_exists(self, priority):
        for block in self.blocks:
            if block.priority == priority:
                return True
        return False

    @property
    def genesis_hash(self):
        return "*We are butterflies*"

    @property
    def last_hash(self):
        if not self.blocks:
            return self.genesis_hash
        return self.blocks[-1].header.tx_hash

    def _block_hash_exists(self, block_hash):
        if block_hash == self.genesis_hash:
            return True
        for block in self.blocks:
            if block.header.tx_hash == block_hash:
                return True
        return False

    def lookup(self, name):
        print self.registry
        return self.registry.get(name)

class Pool:

    def __init__(self, chain):
        self.txs = []
        self.chain = chain

    def add(self, tx):

        self.txs.append(tx)

        # TODO: Wait for more registrations and then forge block
        # add timeout/limit logic here.
        # for now create new block for every new registration.

        self.fabricate_block()

    def fabricate_block(self):
        logging.getLogger().info("[Pool] Fabricating new block!")
        txs = self.txs
        self.txs = []
        block = Block(txs, self.chain.last_hash)
        block.register()
        self.chain.accept(block)

class BlockHeader:

    def __init__(self, tx_hash, root_hash):
        self.tx_hash = tx_hash
        self.root_hash = root_hash

class Block:

    def __init__(self, txs, prev_hash, header=None):
        self.txs = txs
        self.prev_hash = prev_hash
        self.header = header
        self.complete = False

    def register(self):

        """Register block in the bitcoin blockchain
        """

        # Calculate Merkle root
        root_hash = self.calculate_root_hash()

        # Create tx with root_hash as output
        self.header = BlockHeader("", root_hash)
        forge.send_root_hash(root_hash, self._registered)

    def _registered(self, tx_hash):
        self.header.tx_hash = tx_hash
        self.complete = True
        logging.getLogger().info("Registered block, awaiting confirmation:", tx_hash.encode("hex"))

    def calculate_root_hash(self):
        h = hashlib.new("ripemd160")
        h.update(self.prev_hash)
        for key, value in self.txs:
            h.update(key)
            h.update(value)
        return h.digest()

    def verify(self):
        if self.header is None:
            return False
        root_hash = self.calculate_root_hash()
        return self.header.root_hash == root_hash

    def is_next(self, block):
        return block.header.tx_hash == self.prev_hash

    def __repr__(self):
        return "<Block tx_hash=%s root_hash=%s prev=%s txs=%s>" % (
            self.header.tx_hash.encode("hex") if self.header else None,
            self.header.root_hash.encode("hex") if self.header else None,
            self.prev_hash.encode("hex"),
            [(k, v.encode("hex")) for k, v in self.txs])

class ZmqPoller:

    def __init__(self, pool, chain):
        self.pool = pool
        self.chain = chain
        self.context = zmq.Context()
        self.recvr = self.context.socket(zmq.PULL)
        self.recvr.bind("tcp://*:5557")
        logging.getLogger().info("Started on port 5557")
        self.query = self.context.socket(zmq.REP)
        self.query.bind("tcp://*:5558")

    def update(self):
        self._recv_tx()
        self._recv_query()

    def _recv_tx(self):
        try:
            name_reg = self.recvr.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError:
            return
        value = self.recvr.recv()
        self.pool.add((name_reg, value))


    def _recv_query(self):

        """ Receive query for identity
	    """

        try:
            name = self.query.recv(flags=zmq.NOBLOCK)
        except zmq.ZMQError:
            return
        logging.getLogger().info("[ZMQ] Lookup:  %s" % name)
        value = self.chain.lookup(name)
        if value is None:
            self.query.send("__NONE__")
            return
        self.query.send(value)


def main(argv):

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='logs/identity.log')

    chain = Blockchain()
    pool = Pool(chain)
    zmq_poller = ZmqPoller(pool, chain)
    lc_zmq = LoopingCall(zmq_poller.update)
    lc_zmq.start(0.1)
    lc_chain = LoopingCall(chain.update)
    lc_chain.start(6)
    reactor.run()
    logging.getLogger().info("Identity server stopped")

if __name__ == "__main__":
    main(sys.argv)

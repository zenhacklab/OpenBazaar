from pprint import pformat
from urlparse import urlparse
from zmq.eventloop import ioloop, zmqstream
from zmq.error import ZMQError
import logging
import pyelliptic as ec
import socket
import zlib
import obelisk
import zmq
import errno
import json
import network_util
import platform
from crypto_util import (makePubCryptor, hexToPubkey, makePrivCryptor,
    pubkey_to_pyelliptic)

ioloop.install()


class PeerConnection(object):
    def __init__(self, transport, address, nickname=""):

        self.timeout = 10  # [seconds]
        self.transport = transport
        self.address = address
        self.nickname = nickname
        self.responses_received = {}

        self.ctx = zmq.Context()

        self.log = logging.getLogger(
            '[%s] %s' % (self.transport.market_id, self.__class__.__name__)
        )

    def create_zmq_socket(self):
        try:
            socket = self.ctx.socket(zmq.REQ)
            socket.setsockopt(zmq.LINGER, 0)
            return socket
        except Exception as e:
            self.log.error('Cannot create socket %s' % e)
            raise
        # self._socket.setsockopt(zmq.SOCKS_PROXY, "127.0.0.1:9051");

    def cleanup_context(self):
        self.ctx.destroy()

    def send(self, data, callback):
        self.send_raw(json.dumps(data), callback)

    def send_raw(self, serialized, callback=lambda msg: None):

        compressed_data = zlib.compress(serialized, 9)

        try:
            s = self.create_zmq_socket()
            try:
                s.connect(self.address)
            except zmq.ZMQError as e:
                if e.errno != errno.EINVAL:
                    raise
                s.ipv6 = True
                s.connect(self.address)

            stream = zmqstream.ZMQStream(s, io_loop=ioloop.IOLoop.current())
            stream.send(compressed_data)

            def cb(stream, msg):
                response = json.loads(msg[0])
                self.log.debug('[send_raw] %s' % pformat(response))

                # Update active peer info

                if 'senderNick' in response and\
                   response['senderNick'] != self.nickname:
                    self.nickname = response['senderNick']

                if callback is not None:
                    self.log.debug('%s' % msg)
                    callback(msg)
                stream.close()

            stream.on_recv_stream(cb)
        except Exception as e:
            self.log.error(e)
            # Shouldn't we raise the exception here?
            # I think not doing this could cause buggy behavior on top.
            raise


class CryptoPeerConnection(PeerConnection):

    def __init__(self, transport, address, pub=None, guid=None, nickname="",
            sin=None):

        # self._priv = transport._myself
        self.pub = pub

        # Convert URI over
        url = urlparse(address)
        self.ip = url.hostname
        self.port = url.port

        self.sin = sin
        self._peer_alive = False  # unused; might remove later if unnecessary
        self.guid = guid
        self.address = "tcp://%s:%s" % (self.ip, self.port)

        PeerConnection.__init__(self, transport, address, nickname)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.guid == other.guid
        elif isinstance(other, str):
            return self.guid == other
        return False

    def start_handshake(self, handshake_cb=None):

        if self.check_port():
            def cb(msg, handshake_cb=None):
                if msg:

                    self.log.debug('ALIVE PEER %s' % msg[0])
                    msg = msg[0]
                    msg = json.loads(msg)

                    # Update Information
                    self.guid = msg['senderGUID']
                    self.sin = self.generate_sin(self.guid)
                    self.pub = msg['pubkey']
                    self.nickname = msg['senderNick']

                    self._peer_alive = True

                    # Add this peer to active peers list
                    for idx, peer in enumerate(self.transport.dht.activePeers):
                        if peer.guid == self.guid or peer.address == self.address:
                            self.transport.dht.activePeers[idx] = self
                            self.transport.dht.add_peer(
                                self.transport,
                                self.address,
                                self.pub,
                                self.guid,
                                self.nickname
                            )
                            return

                    self.transport.dht.activePeers.append(self)
                    self.transport.dht.routingTable.addContact(self)

                    if handshake_cb is not None:
                        handshake_cb()

            self.send_raw(
                json.dumps({
                    'type': 'hello',
                    'pubkey': self.transport.pubkey,
                    'uri': self.transport.uri,
                    'senderGUID': self.transport.guid,
                    'senderNick': self.transport.nickname
                }),
                cb
            )
        else:
            self.log.error('CryptoPeerConnection.check_port() failed.')

    def __repr__(self):
        return '{ guid: %s, ip: %s, port: %s, pubkey: %s }' % (
            self.guid, self.ip, self.port, self.pub
        )

    @staticmethod
    def generate_sin(guid):
        return obelisk.EncodeBase58Check('\x0F\x02%s' + guid.decode('hex'))

    def check_port(self):

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(10)
            s.connect((self.ip, self.port))
        except socket.error:
            try:
                s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                s.settimeout(10)
                s.connect((self.ip, self.port))
            except socket.error as e:
                self.log.error("socket error on %s: %s" % (self.ip, e))
                return False
        except TypeError:
            self.log.error("tried connecting to invalid address: %s" % self.ip)
            return False

        if s:
            s.close()
        return True

    def sign(self, data):
        cryptor = makePrivCryptor(self.transport.settings['secret'])
        return cryptor.sign(data)

    def encrypt(self, data):
        try:
            if self.pub is not None:
                hexkey = hexToPubkey(self.pub)
                return ec.ECC.encrypt(data, hexkey)
            else:
                self.log.error('Public Key is missing')
                return False
        except Exception as e:
            self.log.error('Encryption failed. %s' % e)

    def send(self, data, callback=lambda msg: None):

        if hasattr(self, 'guid'):

            if self.check_port():

                # Include guid
                data['guid'] = self.guid
                data['senderGUID'] = self.transport.guid
                data['uri'] = self.transport.uri
                data['pubkey'] = self.transport.pubkey
                data['senderNick'] = self.transport.nickname

                self.log.debug(
                    'Sending to peer: %s %s' % (self.ip, pformat(data))
                )

                if self.pub == '':
                    self.log.info('There is no public key for encryption')
                else:
                    signature = self.sign(json.dumps(data))
                    data = self.encrypt(json.dumps(data))

                    try:
                        if data is not None:
                            self.send_raw(
                                json.dumps({
                                    'sig': signature.encode('hex'),
                                    'data': data.encode('hex')
                                }),
                                callback
                            )
                        else:
                            self.log.error('Data was empty')
                    except Exception as e:
                        self.log.error(
                            "Was not able to encode empty data: %s" % e
                        )
            else:
                self.log.error('Peer is not available for sending data')
        else:
            self.log.error('Cannot send to peer')

    def peer_to_tuple(self):
        return self.ip, self.port, self.guid

    def get_guid(self):
        return self.guid

class PeerListener(object):
    def __init__(self, ip, port, data_cb):
        self.ip = ip
        self.port = port
        self._data_cb = data_cb

        self.uri = network_util.get_peer_url(self.ip, self.port)
        self.is_listening = False
        self.ctx = None
        self.socket = None
        self.stream = None
        self._ok_msg = None

        self.log = logging.getLogger(self.__class__.__name__)

    def set_ip_address(self, new_ip):
        self.ip = new_ip
        self.uri = network_util.get_peer_url(self.ip, self.port)
        if not self.is_listening:
            return

        try:
            self.stream.close()
            self.listen()
        except Exception as e:
            self.log.error('[Requests] error: %s' % e)

    def set_ok_msg(self, ok_msg):
        self._ok_msg = ok_msg

    def listen(self):
        self.log.info("Listening at: %s:%s" % (self.ip, self.port))
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.REP)

        if network_util.is_loopback_addr(self.ip):
            try:
                # we are in local test mode so bind that socket on the
                # specified IP
                self.socket.bind(self.uri)
            except ZMQError as e:
                error_message = "".join(
                    "PeerListener.listen() error:",
                    "Could not bind socket to %s" % self.uri,
                    "Details:\n",
                    "(%s)" % e)

                if platform.system() == 'Darwin':
                    error_message.join(
                        "\n\nPerhaps you have not added a ",
                        "loopback alias yet.\n",
                        "Try this on your terminal and restart ",
                        "OpenBazaar in development mode again:\n",
                        "\n\t$ sudo ifconfig lo0 alias 127.0.0.2",
                        "\n\n")
                raise Exception(error_message)

        else:
            if self.ip.find('[') != -1:
                self.socket.ipv6 = True
                self.socket.bind('tcp://[*]:%s' % self.port)
            else:
                self.socket.bind('tcp://*:%s' % self.port)

        self.stream = zmqstream.ZMQStream(
            self.socket, io_loop=ioloop.IOLoop.current()
        )

        def handle_recv(messages):
            #FIXME: investigate if we really get more than one messages here
            for msg in messages:
                self._on_raw_message(msg)

            if self._ok_msg:
                self.stream.send(json.dumps(self._ok_msg))

        self.is_listening = True

        self.stream.on_recv(handle_recv)

    def _on_raw_message(self, serialized):
        self.log.info("connected %d", len(serialized))
        try:
            msg = json.loads(serialized[0])
        except ValueError:
            self.log.info("incorrect msg! %s", serialized)
            return

        self._data_cb(msg)

    def stop(self):
        if self.ctx:
            print "PeerListener.stop() destroying zmq socket."
            self.ctx.destroy(linger=None)
            self.is_listening = False

class CryptoPeerListener(PeerListener):

    def __init__(self, ip, port, pubkey, secret, data_cb):

        PeerListener.__init__(self, ip, port, data_cb)

        self.pubkey = pubkey
        self.secret = secret

        #fixme: refactor this mess
        #this was copied as is from CryptoTransportLayer
        #soon all crypto code will be refactored and this will be removed
        self._myself = ec.ECC(
            pubkey=pubkey_to_pyelliptic(self.pubkey).decode('hex'),
            raw_privkey=self.secret.decode('hex'),
            curve='secp256k1'
        )

    def _on_raw_message(self, serialized):
        try:
            # Decompress message
            serialized = zlib.decompress(serialized)

            msg = json.loads(serialized)
            self.log.info("Message Received [%s]" % msg.get('type', 'unknown'))

            if msg.get('type') is None:

                data = msg.get('data').decode('hex')
                sig = msg.get('sig').decode('hex')

                try:
                    cryptor = makePrivCryptor(self.secret)

                    try:
                        data = cryptor.decrypt(data)
                    except Exception as e:
                        self.log.info('Exception: %s' % e)

                    self.log.debug('Signature: %s' % sig.encode('hex'))
                    self.log.debug('Signed Data: %s' % data)

                    # Check signature
                    data_json = json.loads(data)
                    sigCryptor = makePubCryptor(data_json['pubkey'])
                    if sigCryptor.verify(sig, data):
                        self.log.info('Verified')
                    else:
                        self.log.error('Message signature could not be verified %s' % msg)
                        # return

                    msg = json.loads(data)
                    self.log.debug('Message Data %s ' % msg)
                except Exception as e:
                    self.log.error('Could not decrypt message properly %s' % e)

        except ValueError:
            try:
                msg = self._myself.decrypt(serialized)
                msg = json.loads(msg)

                self.log.info(
                    "Decrypted Message [%s]" % msg.get('type', 'unknown')
                )
            except:
                self.log.error("Could not decrypt message: %s" % msg)

                return

        if msg.get('type') is not None:
            self._data_cb(msg)
        else:
            self.log.error('Received a message with no type')

from pymongo import MongoClient


class DataStore():

  def keys(self):
    """ Return a list of keys """

  def lastPublished(self, key):
    """ Return last published time """

  def originalPublisherId(self, key):
    """ Return original publisher's id """

  def originalPublishTime(self, key):
    """ Return original publish time """

  def setItem(self, key, value, lastPublished, originallyPublished, originalPublisherId):
    """ Set values for a key in the datastore """

  def __getitem__(self, key):
    """ Get a key's values """

  def __setitem__(self, key, value):
    """ Set a value for a key """

  def __delitem__(self, key):
    """ Delete an item from the store """



class MongoDataStore(DataStore):

  def __init__(self):

    MONGODB_URI = 'mongodb://localhost:27017'
    _dbclient = MongoClient()
    self._db = _dbclient.openbazaar

  def keys(self):

    keys = []

    for key in self._db.data.find({}, { 'key':1 }):
      keys.append(key)

    return keys

  def lastPublished(self, key):

    return self._dbQuery(key, 'lastPublished')

  def originalPublisherID(self, key):

    return self._dbQuery(key, 'originalPublisherID')

  def originalPublishTime(self, key):

    return self._dbQuery(key, 'originalPublished')

  def setItem(self, key, value, lastPublished, originallyPublished, originalPublisherID):

    encodedKey = key.encode('hex')
    self._db.data.update({ 'key': key.encode('hex')}, { '$set': { 'key':key.encode('hex'),
                                                                'value': value,
                                                                'lastPublished':lastPublished,
                                                                'originalPublisherID':originalPublisherID,
                                                                'originalPublished':originallyPublished } }, True )


  def _dbQuery(self, key, columnName):
    return self._db.data.find({ 'key': key.encode('hex') }, { columnName: 1 })


  def __getitem__(self, key):
    return self._dbQuery(key, 'value')

  def __delitem__(self, key):
    self._db.data.remove({ 'key':key.encode('hex') })

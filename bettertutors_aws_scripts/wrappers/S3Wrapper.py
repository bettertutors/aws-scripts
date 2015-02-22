#!/usr/bin/env python

from os.path import expanduser, join as path_join
from xml.etree import ElementTree

from boto.s3 import regions, connect_to_region
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from boto.exception import S3CreateError

from ..__init__ import fabric_env


class S3Wrapper(object):
    aws_keys = {i[0].rstrip(): i[1].lstrip()
                for i in tuple(e.rstrip('\n').split('=') for e in
                               open(path_join(expanduser('~'), '.aws', 'credentials')).readlines()[1:])}
    bucket = None

    def __init__(self, bucket_name, persist=False):
        self.bucket_name = bucket_name
        self.conn = self.configure()
        self.persist = persist  # Delete bucket in destructor?

    def __enter__(self):
        return self

    def __exit__(self, ext, exv, trb):
        self.delete()

    def configure(self, region='ap-southeast-2'):
        connect_to_region(filter(lambda x: x.name == region, regions())[0])
        self.conn = S3Connection(**self.aws_keys)
        return self.conn

    def create_bucket(self):
        try:
            self.conn.create_bucket(self.bucket_name)
        except S3CreateError as e:
            err = "{0}".format(e)
            tree = ElementTree.fromstring(err[err.find('<?xml'):])

            unavailable = 'The requested bucket name is not available.'
            if tree.getchildren()[1].text[:len(unavailable)] == unavailable:
                print unavailable.replace(' name', ': "{0}"'.format(self.bucket_name))
                return False
            else:
                raise e
        self.bucket = self.get_bucket()
        return True

    def get_bucket(self):
        # self.bucket = connect_s3(**self.aws_keys).get_bucket(self.bucket_name)
        self.bucket = self.conn.get_bucket(self.bucket_name)
        return self.bucket

    def add_to_bucket(self, key, value, from_='filename'):
        uni_err = lambda: ('Unable to add', from_, 'of some', key, 'due to Unicode error')
        try:
            print 'Adding: `"{0}":"{1}"` (value limited :39)'.format(key, value[:39])
        except (UnicodeEncodeError, UnicodeDecodeError):
            print uni_err()
            return
        k = Key(self.bucket)
        k.key = key
        try:
            getattr(k, 'set_contents_from_{0}'.format(from_))(value)
        except (UnicodeEncodeError, UnicodeDecodeError):
            print uni_err()
            return
        return k

    def get_file_from_key(self, key):
        pass

    def get_keys(self):
        if not self.bucket:
            return []
        return map(lambda k: k.key, self.bucket.get_all_keys())

    @staticmethod
    def delete_key(key):
        print 'Deleting: {key}'.format(key=key)
        key.delete()

    def delete(self):
        """ Recursively deletes all keys--including folders--then deletes the bucket """
        if not self.persist and self.bucket:
            return tuple(self.delete_key(key) for key in self.bucket.list()), self.conn.delete_bucket(self.bucket_name)


if __name__ == '__main__':
    with S3Wrapper(bucket_name='cscie90_hw5_throwaway', persist=False) as s3:
        if not s3.create_bucket():
            pass  # E.g.: add a random bucket name here
        s3.add_to_bucket('foo', 'bar', 'string')
        print s3.get_keys()

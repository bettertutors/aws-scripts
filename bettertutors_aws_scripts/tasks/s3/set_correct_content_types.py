#!/usr/bin/env python

from pprint import PrettyPrinter
from json import dumps

import boto3

pp = PrettyPrinter(indent=4).pprint

s3 = boto3.resource('s3')

to_dict = lambda obj: {k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')}

# Just want a simple dictionary of my S3 buckets
buckets_dict = lambda: {bucket.name: to_dict(bucket) for bucket in s3.buckets.all()}

def correct_content_type(bucket):
    # TODO: Get it working!
    last = None
    for obj in bucket.objects.all():
        print obj('bettertutors-web-frontend')
        object.copy_from()
        CopySource='string'
        #last = obj.copy_from()
    pp(last)


if __name__ == '__main__':
    print correct_content_type(s3.Bucket('bettertutors-web-frontend'))

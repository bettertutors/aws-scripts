#!/usr/bin/env python

from pprint import PrettyPrinter

import boto3

pp = PrettyPrinter(indent=4).pprint

s3 = boto3.resource('s3')

to_dict = lambda obj: {k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')}

# Just want a simple dictionary of my S3 buckets
buckets_dict = lambda: {bucket.name: to_dict(bucket) for bucket in s3.buckets.all()}


def verbose_delete(obj_from_s3_bucket):
    print 'Deleting: "{key}" from "{bucket}"...'.format(key=obj_from_s3_bucket.key,
                                                        bucket=obj_from_s3_bucket.bucket_name)
    obj_from_s3_bucket.delete()
    return True


clear_bucket = lambda bucket_name: map(verbose_delete, s3.Bucket(bucket_name).objects.all())

if __name__ == '__main__':
    all_buckets = buckets_dict()
    print tuple(clear_bucket(bucket_name) for bucket_name in all_buckets)

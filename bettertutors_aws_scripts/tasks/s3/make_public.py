#!/usr/bin/env python

from pprint import PrettyPrinter
from json import dumps

import boto3

pp = PrettyPrinter(indent=4).pprint

s3 = boto3.resource('s3')

to_dict = lambda obj: {k: getattr(obj, k) for k in dir(obj) if not k.startswith('_')}

# Just want a simple dictionary of my S3 buckets
buckets_dict = lambda: {bucket.name: to_dict(bucket) for bucket in s3.buckets.all()}


def make_public(bucket_name):
    bucket_policy = s3.BucketPolicy(bucket_name)
    return bucket_policy.put(Policy=dumps({
        "Statement": [
            {
                "Sid": "AllowPublicRead",
                "Effect": "Allow",
                "Principal": {
                    "AWS": "*"
                },
                "Action": "s3:GetObject",
                "Resource": "arn:aws:s3:::{bucket_name}/*".format(bucket_name=bucket_name)
            }
        ]
    }))


if __name__ == '__main__':
    print make_public(bucket_name='bettertutors-web-frontend')

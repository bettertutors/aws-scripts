#!/usr/bin/env python

from os.path import expanduser, join as path_join
from sys import stderr
from random import randint
from inspect import getargspec
from functools import partial
from pprint import PrettyPrinter

from boto.ec2 import connect_to_region
from boto.manage.cmdshell import sshclient_from_instance
from boto.exception import EC2ResponseError

from fabric.tasks import execute

from ..__init__ import fabric_env

pp = PrettyPrinter(indent=4).pprint


class EC2Wrapper(object):
    aws_keys =
    instance = None
    image_id = None

    def __init__(self, ami_image_id, name='', random_rename=False, persist=False):
        self.ami_image_id = ami_image_id
        self.instance_name = name
        if random_rename:  # To handle 'You must wait 60 seconds after deleting a instance' error
            self.instance_name += str(randint(1, 100))
        self.conn = self.configure()
        tuple(setattr(self, method, partial(getattr(self, 'conn', method), image_id=self.image_id))
              for method in dir(self.conn)
              if not any((method.startswith('_'),
                          (lambda args: 'image_id' not in args[0]
                                        or 'kwargs' not in args[1:])(getargspec(getattr(self, 'conn', method))))))
        self.persist = persist

    def __enter__(self):
        if self.instance:
            self.start_instance()
        else:
            print >> stderr, 'Warning: No instance instantiated'
        return self

    def __exit__(self, ext, exv, trb):
        if not self.persist:
            self.delete()

    def configure(self, region='ap-southeast-2'):
        self.conn = connect_to_region(region_name=region, **self.aws_keys)
        return self.conn  # Hmm, if only I could inherit a class from this connection

    def list_all_images(self, filters=None):
        if not filters:  # Not as default arguments, as they should be immutable
            filters = {
                'architecture': 'x86_64',
                'name': 'ubuntu*ssd*14.04*20140724'
            }
        return self.conn.get_all_images(owners=['099720109477'], filters=filters)

    def create_image_from_instance(self, name, description=None, instance_id=None):
        if not instance_id:
            instance_id = self.instance.id
        self.image_id = self.conn.create_image(instance_id, name, description)
        return self.image_id

    def create_instance(self, security_group='ssh_http_rdp', placement='ap-southeast-2'):
        if not self.ami_image_id:
            raise ValueError('self.ami_image_id must be set')
        print 'image_id =', self.ami_image_id
        print 'security_groups =', [security_group]
        return self.conn.run_instances(image_id=self.ami_image_id, instance_type='t1.micro',
                                       placement=placement,
                                       security_groups=[security_group], monitoring_enabled=True)

    def get_instances(self):
        return self.conn.get_all_instances(filters={'architecture': 'x86_64'})

    def set_instance(self, instance):  # Eww, Java-style method
        self.instance = instance
        return self.instance

    def start_instance(self, instance_id=None):
        if not instance_id:
            instance_id = self.instance.id
        self.conn.start_instances(instance_id)
        self.instance = self.conn.start_instances(instance_id)[0]
        return self.instance

    def list_security_groups(self):
        return self.conn.get_all_security_groups()

    def delete(self):
        if not self.instance:
            print "No instance to remove"
            return []
        return self.conn.stop_instances(self.instance.id)  # Stop, don't delete (for now)
        # self.conn.terminate_instances(self.instance.id)

    @staticmethod
    def run(inst, commands, username='ubuntu'):
        """
        Uses boto to figure out how to SSH in and run commands

        :return a tuple of tuples consisting of:
        #    The integer status of the command
        #    A string containing the output of the command
        #    A string containing the stderr output of the command
        """
        ssh_client = sshclient_from_instance(inst, user_name=username,
                                             ssh_key_file=fabric_env.key_filename)
        return tuple(ssh_client.run(command) for command in commands)

    @staticmethod
    def run2(commands, host):
        """
        Uses Fabric to execute commands over SSH

        :param commands: callable with one or more usages of run/sudo/cd
        :param host: DNS name or IP address
        """
        return execute(commands, host=host)


if __name__ == '__main__':
    with EC2Wrapper('') as ec2:
        print tuple(group for group in ec2.list_security_groups() if group.name == 'ssh_http_rdp')[0]
        print map(lambda elem: elem.name, ec2.list_all_images())

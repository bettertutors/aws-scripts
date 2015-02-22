#!/usr/bin/env python

# Scavenged from one of my old assignments :P

from os import path
from functools import partial
from time import sleep
from contextlib import contextmanager

from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4).pprint

from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.api import sudo, prefix, run

from bettertutors_aws_scripts.wrappers.EC2Wrapper import EC2Wrapper

from bettertutors_aws_scripts import fabric_env


class TimeoutError(BaseException):
    pass


@contextmanager
def virtualenv():
    # From: http://stackoverflow.com/a/5359988/587021
    with prefix('source "$HOME/.venv/bin/activate"'):
        yield


def _create_virtualenv(directory, name='.venv'):
    with cd(directory):
        sudo('virtualenv {name}'.format(name=name), user='ubuntu')


def install_requirements(root):
    with virtualenv():
        sudo('pip install -r "{root}/requirements.txt"'.format(root=root), user='ubuntu')


def upgrade_packages():
    sudo('apt-get update -qq')
    sudo('apt-get -y --force-yes upgrade')
    # sudo('apt-get -y --force-yes dist-upgrade')
    # ^Definitely don't leave this line in for regular (non AMI creation) use!

    # IRL you'll want to setup a base AMI image and upgrade it frequently, then push along your new application
    # Your DB is somewhere else, so there's no worries with turning on/off all your instances (gradually)


def first_run(root='$HOME/rest-api'):
    fabric_env.sudo_user = 'root'
    if exists('"{root}"'.format(root=root), use_sudo=True):
        return deploy(root)

    sudo('apt-get update -qq')
    upgrade_packages()  # Leave this commented out for regular use
    sudo('apt-get install -q -y --force-yes libpython2.7-dev python-pip python-virtualenv libpq-dev git')
    # libpq-dev is for the Postgres driver, could do python-psycopg2, but that's not as isolated as a virtualenv.
    sudo('git clone https://github.com/bettertutors/rest-api', user='ubuntu')
    _create_virtualenv('"$HOME"')
    setup_ports()


# TODO: Set this all up in a virtualenv
# TODO: Deploy to a proper directory (e.g.: /wwwroot), with its own user

def deploy(root='$HOME/rest-api', daemon='bettertutorsd'):
    if not exists('"{root}"'.format(root=root), use_sudo=True):
        return first_run(root)

    with cd('"{root}"'.format(root=root)):
        sudo('git pull', user='ubuntu')
        install_requirements(root)

    with cd('/etc/init'):
        fabric_env.sudo_user = 'root'

        sudo('> {name}.conf'.format(name=daemon))
        sudo('chmod 644 {name}.conf'.format(name=daemon))
        sudo('''cat << EOF >> {name}.conf
description "bettertutorsd"

start on (filesystem)
stop on runlevel [016]

respawn
setuid nobody
setgid nogroup
chdir "{root}"
exec "$HOME/.venv/bin/gunicorn" -w 4 "bettertutors_rest_api:rest_api" -b 0.0.0.0
EOF
            '''.format(name=daemon, root=root))
        sudo('initctl reload-configuration')


def setup_ports():
    sudo('iptables -A INPUT -p tcp --dport ssh -j ACCEPT', user='root')
    sudo('iptables -A INPUT -p tcp --dport 80 -j ACCEPT', user='root')
    sudo('iptables -A INPUT -p tcp --dport 8000 -j ACCEPT', user='root')
    # Handled ^ by AWS firewall stuff, but in general I don't want to rely on them for when I go multicloud approach.
    sudo('iptables -A PREROUTING -t nat -p tcp --dport 80 -j REDIRECT --to-port 8000', user='root')
    # Make permanent with iptables-persistent package


def serve(root='$HOME/rest-api', daemon='bettertutorsd'):
    if not exists('"{root}"'.format(root=root)):
        raise OSError('Folder: "{root}" doesn\'t exists but should'.format(root=root))

    fabric_env.sudo_user = 'root'
    sudo('stop {name}'.format(name=daemon), warn_only=True)
    sudo('start {name}'.format(name=daemon))  # Restart is less reliable, especially if it's in a stopped state


def tail():
    daemon = 'bettertutorsd'
    return sudo('tail /var/log/upstart/{name}.log -n 50 -f'.format(name=daemon))


if __name__ == '__main__':
    my_instance_name = 'bettertutors'
    ami_image_id = 'ami-e3eb9fd9'  # Ubuntu 14.04 LTS; Canonical release for Asia Pacific (Sydney) data-centre

    ec2 = EC2Wrapper(ami_image_id=ami_image_id)

    key_pair = ec2.get_key_pair(my_instance_name) or ec2.create_key_pair(
        my_instance_name, path.join(path.expanduser('~'), '.ssh', my_instance_name, 'private.pem')
    )
    ec2.key_name = key_pair.name

    run3 = partial(ec2.run2, host='ap-southeast-2.compute.amazonaws.com')
    print run3(deploy)
    print run3(serve)

    '''
    with EC2Wrapper(ami_image_id=ami_image_id, key_name=key_pair.name, persist=False) as ec2:
        creating = ec2.create_instance()
        print 'Creating:', creating, 'with instances:', creating.instances
        pp(dir(creating.instances[0]))

        for instance in creating.instances:
            run3 = partial(ec2.run2, host=instance.public_dns_name)
            instance.start()
            tried = 0
            previous_state = None
            while instance.state != 'running':
                if previous_state != instance.state:
                    print 'Waiting (up to) ~2 minutes for instance to start...',
                    previous_state = instance.state
                elif tried > 59:
                    raise TimeoutError
                print 'state:', instance.state
                print 'reason:', instance.reason
                print 'state_reason:', instance.state_reason
                print 'monitoring_state:', instance.monitoring_state
                print 'launch_time:', instance.launch_time
                print '\n------------------------------\n'
                sleep(2)
                tried += 1
            print run3(deploy)
            print run3(serve)
    '''
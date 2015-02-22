#!/usr/bin/env python

# Scavenged from one of my old assignments :P

from functools import partial
from time import sleep
from pprint import PrettyPrinter

pp = PrettyPrinter(indent=4).pprint

from fabric.context_managers import cd
from fabric.contrib.files import exists
from fabric.api import sudo

from bettertutors_aws_scripts.wrappers.EC2Wrapper import EC2Wrapper

from bettertutors_aws_scripts import fabric_env


class TimeoutError(BaseException):
    pass


def first_run(root='$HOME/rest-api'):
    fabric_env.sudo_user = 'root'
    if exists('"{root}"'.format(root=root), use_sudo=True):
        return deploy(root)

    sudo('apt-get update')
    sudo('apt-get install -q -y --force-yes python-pip git')
    sudo('git clone https://github.com/bettertutors/rest-api', user='ubuntu')
    sudo('pip install -r "{root}/requirements.txt"'.format(root=root))


# TODO: Set this all up in a virtualenv
# TODO: Deploy to a proper directory (e.g.: /wwwroot)

def deploy(root='$HOME/rest-api', daemon='bettertutorsd'):
    if not exists('"{root}"'.format(root=root), use_sudo=True):
        return first_run(root)
    with cd('"{root}"'.format(root=root)):
        sudo('git pull', user='ubuntu')

    with cd('/etc/init'):
        fabric_env.sudo_user = 'root'

        sudo('> {name}.conf'.format(name=daemon))
        sudo('chmod 700 {name}.conf'.format(name=daemon))
        sudo('''cat << EOF >> {name}.conf
start on runlevel [2345]
stop on runlevel [016]

respawn
setuid nobody
setgid nogroup
exec python "{root}/bettertutors_rest_api.py"
EOF
            '''.format(name=daemon, root=root))
        sudo('initctl reload-configuration')


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

    run3 = partial(ec2.run2, host='ap-southeast-2.compute.amazonaws.com')
    print run3(deploy)
    print run3(serve)

    '''
    with EC2Wrapper(ami_image_id=ami_image_id, persist=False) as ec2:
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

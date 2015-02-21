from os import environ
from os.path import expanduser, join as path_join

from fabric.api import env as fabric_env


fabric_env.skip_bad_hosts = True
fabric_env.user = environ.get('AWS_NIX_USERNAME', 'ubuntu')
fabric_env.sudo_user = fabric_env.user
fabric_env.key_filename = environ.get(
    'SSH_KEY_FILENAME', expanduser(path_join(expanduser('~'), '.ssh', 'aws', 'private', 'cscie90.pem'))
)

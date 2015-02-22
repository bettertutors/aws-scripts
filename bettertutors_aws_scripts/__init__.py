from os import environ, path

from fabric.api import env as fabric_env


fabric_env.skip_bad_hosts = True
fabric_env.user = environ.get('AWS_NIX_USERNAME', 'ubuntu')
fabric_env.sudo_user = fabric_env.user
fabric_env.key_filename = environ.get(
    'SSH_KEY_FILENAME', path.expanduser(path.join(path.expanduser('~'), '.ssh', 'aws', 'private', 'cscie90.pem'))
)

_creds_path = path.join(path.expanduser('~'), '.aws', 'credentials')
if path.exists(_creds_path):
    aws_keys = {i[0].rstrip(): i[1].lstrip()
                for i in tuple(e.rstrip('\n').split('=') for e in
                               open(_creds_path).readlines()[1:])}
else:
    aws_keys = {k: environ[k] for k in 'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY'}

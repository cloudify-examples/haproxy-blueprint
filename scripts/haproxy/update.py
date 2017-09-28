try:
    from cloudify.context import RELATIONSHIP_INSTANCE
except ImportError:
    from cloudify.constants import RELATIONSHIP_INSTANCE

from cloudify import ctx
from cloudify.exceptions import NonRecoverableError
from cloudify.state import ctx_parameters as inputs
from jinja2 import Template
from cloudify_rest_client import exceptions as rest_exceptions
import shutil
import StringIO
import subprocess
from tempfile import NamedTemporaryFile


def execute(command):
    ctx.logger.debug('RUNNING: {0}'.format(command))
    out = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        shell=True)
    ctx.logger.debug('OUT: {0}'.format(out))
    return out


def systemctl(state):
    execute('sudo systemctl {0} haproxy'.format(state))


def read_file_as_sudo(filepath):
    cat_filepath = 'sudo cat {0}'.format(filepath)
    file_as_string = StringIO.StringIO()
    process = execute(cat_filepath)
    for line in iter(process.stdout.readline, ''):
        file_as_string.write(line)
    return file_as_string


def new_backup(original_file):
    backup = NamedTemporaryFile(delete=False)
    if not ctx.instance.runtime_properties.get('backups'):
        ctx.instance.runtime_properties['backup_location'] = []
    backups = ctx.instance.runtime_properties['backup_location']
    backups.append(backup.name)

    with open(backup.name, 'w') as outfile:
        original_file.seek(0)
        shutil.copyfileobj(original_file, outfile)

    ctx.logger.location('new backup: {0}'.format(backup.name))


if __name__ == '__main__':

    # Find out if the update script is being called from a relationship or a node operation.
    if ctx.type == RELATIONSHIP_INSTANCE:
        subject = ctx.target
    else:
        subject = ctx

    ctx.logger.info('{0}'.format(subject.instance.id))

    # Find out if we are adding or removing backends.
    action = inputs.get('action', 'add')

    # Get the current backends.
    backends = subject.instance.runtime_properties.get('backends', {})
    if not backends:
        subject.instance.runtime_properties['backends'] = {}

    # Find out this lifecyle operations backends.
    update_backends = inputs.get('update_backends')

    # Update the backends in the context.
    if action == 'add':
        backends.update(update_backends)
    else:
        for key in update_backends.keys():
            backends.pop(key)
    subject.instance.runtime_properties['backends'] = backends
    try:
        subject.instance.update()
    except rest_exceptions.CloudifyClientError as e:
        if 'conflict' in str(e):
            # cannot 'return' in contextmanager
            ctx.operation.retry(
                message='Backends updated concurrently, retrying.',
                retry_after=1)
        else:
            raise

    ctx.logger.debug("backends: {0}".format(backends))

    # Create the template config.
    config = {
        'frontend_id': inputs.get('frontend_id', subject.instance.id),
        'frontend_port': inputs.get('frontend_port', '80'),
        'default_backend': inputs.get('default_backend', 'servers'),
        'backends': backends,
    }

    # Get the HAProxy config file path.
    haproxy_cfg_path = inputs.get('haproxy.cfg', '/etc/haproxy/haproxy.cfg')
    # Get the HAProxy config file template path.
    haproxy_cfg_template_path = inputs.get('haproxy.cfg.template', '/etc/haproxy/haproxy.cfg.template')
    # Read the HAProxy config file.
    original_haproxy_cfg_path = read_file_as_sudo(haproxy_cfg_path)
    template_content = read_file_as_sudo(haproxy_cfg_template_path)
    template_content.seek(0)
    template = Template(template_content.getvalue())
    # Render the template and write the rendered file to a temporary file.
    with NamedTemporaryFile(delete=False) as temp_config:
        temp_config.write(template.render(config))
    # Test the temporary file.
    out = execute('sudo /usr/sbin/haproxy -f {0} -c'.format(temp_config.name))
    if out.returncode:
        raise NonRecoverableError('Invalid config.')
    # Replace the HAProxy configuration file with the temporary file.
    execute('sudo cp {0} {1}'.format(temp_config.name, haproxy_cfg_path))
    execute('sudo chmod {0} {1}'.format( '0600', haproxy_cfg_path))
    # Reload the HAProxy process.
    systemctl('restart')

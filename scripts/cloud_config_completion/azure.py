#!/usr/bin/env python

import subprocess
from cloudify import ctx
from cloudify.exceptions import OperationRetry


def execute_command(_command):

    ctx.logger.debug('_command {0}.'.format(_command))

    subprocess_args = {
        'args': _command.split(),
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }

    ctx.logger.debug('subprocess_args {0}.'.format(subprocess_args))

    process = subprocess.Popen(**subprocess_args)
    output, error = process.communicate()

    ctx.logger.debug('command: {0} '.format(_command))
    ctx.logger.debug('error: {0} '.format(error))
    ctx.logger.debug('process.returncode: {0} '.format(process.returncode))

    if process.returncode:
        ctx.logger.error('Running `{0}` returns error.'.format(_command))
        return False

    return output


if __name__ == '__main__':

    haproxy_process = '/usr/sbin/haproxy -f /etc/haproxy/haproxy.cfg -p /run/haproxy.pid -Ds'

    ps = execute_command('ps -ef')
    for line in ps.split('\n'):
        haproxy_started = True if haproxy_process in line else False
        if haproxy_started is True:
            break

    if haproxy_started is not True:
        raise OperationRetry(
            'You provided a VirtualMachineExtension to configure instances. '
            'Waiting for process to complete.')

    ctx.logger.info('HAProxy Started.')

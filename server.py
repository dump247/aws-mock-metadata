#!/usr/bin/python

import os
import os.path
import bottle
from bottle import route, response, view, delete, post, request
from boto import sts
import boto.iam
from datetime import datetime
import subprocess
import argparse


def get(d, *keys):
    return reduce(lambda a, b: a[b], keys, d)


def first(l):
    return l[0] if len(l) > 0 else None


@route('/')
def list_api_versions():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'latest'


@route('/latest/meta-data/iam/security-credentials/')
def list_profiles():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'local-credentials'


@route('/latest/meta-data/iam/security-credentials/local-credentials')
def get_credentials():
    session = metadata.get_session()

    return {
        'AccessKeyId':     session.access_key,
        'SecretAccessKey': session.secret_key,
        'Token':           session.session_token,
        'Expiration':      session.expiration
    }


@route('/manage')
@view('manage')
def manage():
    return {
        'session': metadata.session
    }


@route('/manage/session')
def get_session():
    if metadata.session_expired:
        response.status = 404
        return {
            'error': {
                'message': 'No session has been created or session expired.'
            }
        }

    return {
        'session': {
            'accessKey':    metadata.session.access_key,
            'secretKey':    metadata.session.secret_key,
            'sessionToken': metadata.session.session_token,
            'expiration':   metadata.session.expiration
        }
    }


@delete('/manage/session')
def delete_session():
    metadata.clear_session()


@post('/manage/session')
def create_session():
    token = request.forms.get('token')

    if token is None and request.json:
        token = request.json.get('token')

    if not token:
        response.status = 400
        return {
            'error': {
                'message': 'token is required'
            }
        }

    metadata.get_session(token)
    return get_session()


class cache(object):
    '''Computes attribute value and caches it in the instance.
    Python Cookbook (Denis Otkidach)
        http://stackoverflow.com/users/168352/denis-otkidach
    This decorator allows you to create a property which can be computed once
    and accessed many times. Sort of like memoization.
    '''
    def __init__(self, method, name=None):
        # record the unbound-method and the name
        self.method = method
        self.name = name or method.__name__
        self.__doc__ = method.__doc__

    def __get__(self, inst, cls):
        if inst is None:
            # instance attribute accessed on class, return self
            # You get here if you write `Foo.bar`
            return self
        # compute, cache and return the instance's attribute value
        result = self.method(inst)
        # setattr redefines the instance's attribute so this doesn't get called
        # again
        setattr(inst, self.name, result)
        return result


class Metadata(object):
    def __init__(self, region=None, access_key=None, secret_key=None,
                 token_duration=None):
        self.region = region or 'us-east-1'
        self.access_key = access_key
        self.secret_key = secret_key
        self.token_duration = int(token_duration) if token_duration else None

        self.user = None
        self.session = None
        self.session_expiration = datetime.min
        self.mfa_serial_number = None

        self._load_user()

    @cache
    def iam(self):
        return boto.iam.connect_to_region(
            self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key)

    @cache
    def sts(self):
        return sts.connect_to_region(
            self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key)

    @property
    def session_expired(self):
        return datetime.utcnow() > self.session_expiration

    def _load_user(self):
        self.user = get(
            self.iam.get_user(),
            'get_user_response',
            'get_user_result',
            'user')
        self._load_mfa_device()

    def _load_mfa_device(self):
        mfa_device = first(get(
            self.iam.get_all_mfa_devices(self.user.user_name),
            'list_mfa_devices_response',
            'list_mfa_devices_result',
            'mfa_devices'))

        self.mfa_serial_number = mfa_device.serial_number\
            if mfa_device\
            else None

    def _prompt_token(self):
        script = os.path.join(os.path.dirname(__file__), 'prompt.py')
        return subprocess.check_output(['/usr/bin/python', script]).strip()

    def clear_session(self):
        self.session = None
        self.session_expiration = datetime.min

    def get_session(self, token_value=None):
        if self.session_expired or token_value:
            try:
                while self.mfa_serial_number and not token_value:
                    token_value = self._prompt_token()

                self.session = self.sts.get_session_token(
                    duration=self.token_duration,
                    force_new=True,
                    mfa_serial_number=self.mfa_serial_number,
                    mfa_token=token_value if self.mfa_serial_number else None)

                # Needs testing, but might be worth subtracting X seconds
                # to prevent returning outdated session token. SDKs and AWS
                # may already handle this, so it may not be worth it.
                self.session_expiration = datetime.strptime(
                    self.session.expiration,
                    '%Y-%m-%dT%H:%M:%SZ')
            except:
                self.clear_session()
                raise

        return self.session


if __name__ == '__main__':
    app = bottle.default_app()
    config_file_path = os.path.join(os.path.dirname(__file__), 'server.conf')
    app.config.load_config(config_file_path)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--host',
        default=app.config.get('metadata.host', '169.254.169.254'))
    parser.add_argument(
        '--port', type=int,
        default=int(app.config.get('metadata.port', 45000)))
    args = parser.parse_args()

    metadata = Metadata(
        region=app.config.get('aws.region', 'us-east-1'),
        access_key=app.config.get('aws.access_key'),
        secret_key=app.config.get('aws.secret_key'),
        token_duration=app.config.get('metadata.token_duration'))

    app.run(host=args.host, port=args.port)

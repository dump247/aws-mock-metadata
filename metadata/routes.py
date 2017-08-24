from __future__ import absolute_import

from boto.exception import BotoServerError

from metadata.bottle import route, response, view, delete, post, request


@route('/latest/meta-data/local-hostname')
def localhost():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'localhost'


@route('/latest/meta-data/hostname')
def host():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'localhost'


@route('/latest/meta-data/public-hostname')
def public_host():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'localhost'


@route('/latest/meta-data/mac')
def vpc_id():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'mac1234'


@route('/latest/meta-data/network/interfaces/macs/mac1234/vpc-id')
def vpc_id():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'vpc-1234'


@route('/latest/meta-data/local-ipv4')
def localip4():
    response.content_type = 'text/plain; charset=UTF-8'
    return '127.0.1.1'


@route('/latest/meta-data/instance-type')
def instance_type():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'r3.2xlarge'

@route('/latest/meta-data/iam/security-credentials')
@route('/latest/meta-data/iam/security-credentials/')
def list_profiles():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'local-credentials'


@route('/latest/meta-data/iam/security-credentials/local-credentials')
def get_credentials():
    try:
        session = request.app.config.meta_get('metadata', 'obj').get_session()

        return {
            'Code':           'Success',
            'AccessKeyId':     session.access_key,
            'SecretAccessKey': session.secret_key,
            'Token':           session.session_token,
            'Expiration':      session.expiration
        }
    except BotoServerError as e:
        response.status = e.status
        return {'error': {'message': e.message}}

@route('/latest/dynamic/instance-identity/document')
def get_identity_document():
    return {
        'privateIp' : '127.0.0.1',
        'devpayProductCodes' : None,
        'availabilityZone' : 'us-east-1a',
        'version' : '2010-08-31',
        'instanceId' : 'i-12345678',
        'billingProducts' : None,
        'instanceType' : 't2.nano',
        'accountId' : '123456789012',
        'architecture' : 'x86_64',
        'kernelId' : None,
        'ramdiskId' : None,
        'imageId' : 'ami-12345678',
        'pendingTime' : '2016-01-01T00:00:00Z',
        'region' : 'us-east-1'
    }

@route('/manage')
@view('manage')
def manage():
    metadata = request.app.config.meta_get('metadata', 'obj')

    return {
        'session':      metadata.session,
        'profile_name': metadata.profile_name,
        'profiles':     metadata.profiles
    }


@route('/manage/profiles')
def get_profiles():
    metadata = request.app.config.meta_get('metadata', 'obj')

    return {'profiles': [
        _profile_info(metadata, name, profile)
        for name, profile in metadata.profiles.items()
    ]}


@route('/manage/profiles/<name>')
def get_profile(name):
    metadata = request.app.config.meta_get('metadata', 'obj')

    if name not in metadata.profiles:
        response.status = 404
        return {'error': {'message': 'profile does not exist'}}

    return {'profile': _profile_info(metadata, name, metadata.profiles[name])}


@route('/manage/session')
def get_session():
    metadata = request.app.config.meta_get('metadata', 'obj')
    result = {
        'profile': _profile_response(metadata.profile_name,
                                     metadata.profile)
    }

    if not metadata.session_expired:
        result['session'] = _session_response(metadata.session)

    return result


@delete('/manage/session')
def delete_session():
    request.app.config.meta_get('metadata', 'obj').clear_session()


@post('/manage/session')
def create_session():
    metadata = request.app.config.meta_get('metadata', 'obj')
    token = _get_value(request, 'token')
    profile = _get_value(request, 'profile')

    if not token and not profile:
        response.status = 400
        return {
            'error': {
                'message': 'token and/or profile is required'
            }
        }

    if profile:
        metadata.profile_name = profile

    if token:
        try:
            request.app.config.meta_get('metadata', 'obj').get_session(token)
        except BotoServerError as e:
            response.status = e.status
            return {'error': {'message': e.message}}

    return get_session()


def _get_value(request, key):
    value = request.forms.get(key)

    if value is None and request.json:
        value = request.json.get(key)

    return value


def _session_response(session):
    return {
        'accessKey':    session.access_key,
        'secretKey':    session.secret_key,
        'sessionToken': session.session_token,
        'expiration':   session.expiration
    }


def _profile_info(metadata, name, profile):
    result = _profile_response(name, profile)

    if not profile.session_expired:
        result['session'] = _session_response(profile.session)

    if metadata.profile_name == name:
        result['active'] = True

    return result


def _profile_response(name, profile):
    response = {
        'accessKey': profile.access_key,
        'region':    profile.region
    }

    if profile.token_duration:
        response['tokenDuration'] = profile.token_duration

    if profile.role_arn:
        response['roleArn'] = profile.role_arn

    return response

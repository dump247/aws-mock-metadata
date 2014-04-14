from __future__ import absolute_import

from metadata.bottle import route, response, view, delete, post, request


@route('/latest/meta-data/iam/security-credentials/')
def list_profiles():
    response.content_type = 'text/plain; charset=UTF-8'
    return 'local-credentials'


@route('/latest/meta-data/iam/security-credentials/local-credentials')
def get_credentials():
    session = request.app.config.meta_get('metadata', 'obj').get_session()

    return {
        'AccessKeyId':     session.access_key,
        'SecretAccessKey': session.secret_key,
        'Token':           session.session_token,
        'Expiration':      session.expiration
    }


@route('/manage')
@view('manage')
def manage():
    metadata = request.app.config.meta_get('metadata', 'obj')

    return {
        'session': metadata.session
    }


@route('/manage/session')
def get_session():
    metadata = request.app.config.meta_get('metadata', 'obj')

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
    request.app.config.meta_get('metadata', 'obj').clear_session()


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

    request.app.config.meta_get('metadata', 'obj').get_session(token)
    return get_session()

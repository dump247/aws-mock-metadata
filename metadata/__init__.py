from __future__ import absolute_import

from datetime import datetime
import boto.iam
import boto.sts
import subprocess
import os.path
from metadata.util import cache, first_item, get_value
from metadata import otp

class NoSuchProfileError(Exception):
    def __init__(self, name):
        super(NoSuchProfileError, self).__init__(
            'Profile {} not found.'.format(name))


class Metadata(object):
    def __init__(self, profiles, profile_name):
        self.profiles = profiles
        self.profile_name = profile_name

    @property
    def profile_name(self):
        return self.__profile_name

    @profile_name.setter
    def profile_name(self, name):
        if name not in self.profiles:
            raise NoSuchProfileError(name)

        self.__profile_name = name

    @property
    def profile(self):
        return self.profiles[self.profile_name]

    # Replace uses of the following methods with metadata.profile.x

    @property
    def session(self):
        return self.profile.session

    @property
    def session_expired(self):
        return self.profile.session_expired

    def clear_session(self, *args, **kw):
        return self.profile.clear_session(*args, **kw)

    def get_session(self, *args, **kw):
        return self.profile.get_session(*args, **kw)


class Profile(object):
    def __init__(self, region='us-east-1', access_key=None, secret_key=None,
                 token_duration=None, role_arn=None, mfa_secret=None):
        self.region = region
        self.access_key = access_key
        self.secret_key = secret_key
        self.token_duration = token_duration
        self.role_arn = role_arn
        self.otp = otp.Totp(mfa_secret) if mfa_secret is not None else None

        self.user = None
        self.session = None
        self.session_expiration = datetime.min
        self.mfa_serial_number = None

        self._load_user()

        if role_arn:
            self.role_arn = role_arn.replace('${aws:username}',
                                             self.user.user_name)

    @cache
    def iam(self):
        return boto.iam.connect_to_region(
            self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key)

    @cache
    def sts(self):
        return boto.sts.connect_to_region(
            self.region,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key)

    @property
    def session_expired(self):
        return datetime.utcnow() > self.session_expiration

    def _load_user(self):
        self.user = get_value(
            self.iam.get_user(),
            'get_user_response',
            'get_user_result',
            'user')
        self._load_mfa_device()

    def _load_mfa_device(self):
        mfa_device = first_item(get_value(
            self.iam.get_all_mfa_devices(self.user.user_name),
            'list_mfa_devices_response',
            'list_mfa_devices_result',
            'mfa_devices'))

        self.mfa_serial_number = mfa_device.serial_number\
            if mfa_device\
            else None

    def _prompt_token(self):
        if self.otp:
            return str(self.otp.generate())
        else:
            script = os.path.join(os.path.dirname(__file__), 'prompt.py')
            return subprocess.check_output(['/usr/bin/python', script]).strip()

    def _create_session(self, token_value):
        if self.role_arn:
            role = self.sts.assume_role(
                role_arn=self.role_arn,
                role_session_name='some_session_id',
                duration_seconds=self.token_duration,
                mfa_serial_number=self.mfa_serial_number,
                mfa_token=token_value if self.mfa_serial_number else None)

            return role.credentials
        else:
            return self.sts.get_session_token(
                duration=self.token_duration,
                force_new=True,
                mfa_serial_number=self.mfa_serial_number,
                mfa_token=token_value if self.mfa_serial_number else None)

    def clear_session(self):
        self.session = None
        self.session_expiration = datetime.min

    def get_session(self, token_value=None):
        if self.session_expired or token_value:
            try:
                while self.mfa_serial_number and not token_value:
                    token_value = self._prompt_token()

                self.session = self._create_session(token_value)

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

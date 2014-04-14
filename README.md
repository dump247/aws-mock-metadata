aws-mock-metadata
=================

Mock EC2 metadata service that can run on a developer machine.

It is possible in AWS to protect [API access with
MFA](http://docs.aws.amazon.com/IAM/latest/UserGuide/MFAProtectedAPI.html).
However, this is not convenient to setup or use since you must regularly refresh
your credentials.

Amazon EC2 instances have a metadata service that can be accessed to
retrieve the instance profile credentials. Those credentials are
rotated regularly and have an associated expiration. Most AWS SDKs
check this service to use the instance profile credentials.

This service runs on a developer machine and masquerades as the
Amazon metadata service. This allows it to integrate with the SDKs
and provide session credentials when needed. When the metadata
service is queried for security credentials, this service will prompt
the user to enter the MFA device token. Those credentials are cached
until they expire and the user is prompted again to provide an updated
token.

# Installation

Currently only works on OSX, but should be trivial to make it work on
other platforms.

This should be changed to run as a launchd daemon at some point.

1. Clone the repo
2. Add AWS access key and secret key to *server.conf* in the repo
   directory
  * See Configuration section
  * These permanent keys are used to generate the session keys using the MFA token
  * There must be an MFA device associated with the account
3. Run `bin/server-macos`
  * Prompts for password to setup an IP alias and firewall forwarding rule.
  * You can examine the script and run the commands separately. The
    script is only provided for convenience.

# Configuration

*server.conf*

```
[aws]
access_key=...   # Required. Access key to generate temp keys with.
secret_key=...   # Required. Secret key to generate temp keys with.
region=us-east-1 # Optional. Not generally necessary since IAM and STS
                 # are not region specific. Default is us-east-1.

[metadata]
host=169.254.169.254 # Optional. Interface to bind to. Default is
                     # 169.254.169.254.
port=45000           # Optional. Port to bind to. Default is 45000.
token_duration=43200 # Optional. Timeout, in seconds, for the generated
                     # keys. Minimum is 15 minutes.
                     # Default is 12 hours for sts:GetSessionToken and
                     # 1 hour for sts:AssumeRole. Maximum is 36 hours
                     # for sts:GetSessionToken and 1 hour for
                     # sts:AssumeRole.
role_arn=arn:aws:iam::123456789012:role/${aws:username}
                     # Optional. ARN of a role to assume. If specified,
                     # the metadata server uses sts:AssumeRole to create
                     # the temporary credentials. Otherwise, the
                     # metadata server uses sts:GetSessionToken.
                     # The string '${aws:username}' will be replaced
                     # with the name of the user requesting the
                     # credentials. No other variables are currently
                     # supported.
```

## AWS CLI

It is recommended to update the local metadata service timeout for the
AWS command line interface. This ensures that you have enough time to
enter the MFA token before the request expires and your script can
continue without interruption.

*~/.aws/config*

```
[default]
metadata_service_timeout = 15.0  # 15 second timeout to enter MFA token
```

# Mock Endpoints

The following EC2 metadata service endpoints are implemented.

```
169.254.169.254/latest/meta-data/iam/security-credentials/
169.254.169.254/latest/meta-data/iam/security-credentials/local-credentials
```

When `/latest/meta-data/iam/security-credentials/local-credentials` is
requested, and there are no session credentials available, a dialog pops
up prompting for the MFA token. The dialog blocks the request until the
correct token is entered. Once the token is provided, the session
credentials are generated and cached until they expire. Once they
expire, a new token prompt will appear on the next request for
credentials.

# User Interface

A simple UI to view, reset, and update the session credentials is
available by loading *http://169.254.169.254/manage* in your
browser.

# API

There is an API available to query and update the MFA session
credentials.

## Get Credentials

`GET 169.254.169.254/manage/session`

### Response: 404

There is no current session.

### Response: 200

There is a valid session. Returns the session credentials.

```json
{
    "session": {
        "accessKey": "....",
        "secretKey": "....",
        "sessionToken": "...",
        "expiration": "2014-04-09T09:00:44Z"
    }
}
```

## Clear Credentials

`DELETE 169.254.169.254/manage/session`

### Response: 200

Session credentials were cleared or no session exists.

## Create Credentials

`POST 169.254.169.254/manage/session`

Example: `curl -X POST -d code=123456 169.254.169.254/manage/session`

### Body

*Content-Type: application/x-www-form-urlencoded*

```
token=123456
```

*Content-Type: application/json*

```json
{
    "token": "123456"
}
```

### Response: 400

Invalid MFA token string format or token was not provided.

### Response: 401

Specified MFA token does not match expected token for the MFA device.

### Response: 200

Session was created successfully. Returns the session credentials.

```json
{
    "session": {
        "accessKey": "....",
        "secretKey": "....",
        "sessionToken": "...",
        "expiration": "2014-04-09T09:00:44Z"
    }
}
```
# License

The MIT License (MIT)
Copyright (c) 2014 Cory Thomas

See [LICENSE](LICENSE)

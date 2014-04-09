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
2. Run `macos-server`
  * Prompts for password to setup an IP alias and firewall forwarding rule

# Mock Endpoints

The following EC2 metadata service endpoints are implemented.

```
/latest/meta-data/iam/security-credentials/
/latest/meta-data/iam/security-credentials/local-credentials
```

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

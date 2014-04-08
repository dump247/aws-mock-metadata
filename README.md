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

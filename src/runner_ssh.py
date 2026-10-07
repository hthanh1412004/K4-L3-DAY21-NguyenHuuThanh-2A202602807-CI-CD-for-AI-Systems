"""Allow SSH from this CI runner only, then revoke its rule after deployment."""
import argparse
import ipaddress
import os
import urllib.request

import boto3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['allow', 'revoke'])
    args = parser.parse_args()
    client = boto3.client('ec2')
    group = os.environ['SERVER_SECURITY_GROUP']
    if args.action == 'allow':
        ip = urllib.request.urlopen('https://checkip.amazonaws.com', timeout=20).read().decode().strip()
        ipaddress.IPv4Address(ip)
        result = client.authorize_security_group_ingress(
            GroupId=group,
            IpPermissions=[{'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22,
                            'IpRanges': [{'CidrIp': ip + '/32',
                                          'Description': 'Income lab CI run ' + os.environ['GITHUB_RUN_ID']}]}],
        )
        rule = result['SecurityGroupRules'][0]['SecurityGroupRuleId']
        with open(os.environ['GITHUB_OUTPUT'], 'a') as output:
            output.write(f'rule_id={rule}\n')
        print(f'SSH allowed from runner {ip}/32; rule {rule}')
    else:
        rule = os.environ['SSH_RULE_ID']
        client.revoke_security_group_ingress(GroupId=group, SecurityGroupRuleIds=[rule])
        print(f'Removed temporary SSH rule {rule}')


if __name__ == '__main__':
    main()

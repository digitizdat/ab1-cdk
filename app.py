#!/usr/bin/env python3

import os
from aws_cdk import core

from cdk_vpc_ec2.cdk_vpc_stack import CdkVpcStack
from cdk_vpc_ec2.cdk_ec2_stack import CdkEc2Stack
from cdk_vpc_ec2.cdk_rds_stack import CdkRdsStack

# Defaults
APPENV_DEFAULT_ACCOUNT = "964152837058"
APPENV_DEFAULT_REGION = "us-east-2"

# Override defaults
APPENV_ACCOUNT = os.environ.get("APPENV_ACCOUNT") or APPENV_DEFAULT_ACCOUNT
APPENV_REGION = os.environ.get("APPENV_REGION") or APPENV_DEFAULT_REGION

app = core.App()

env_USA = core.Environment(account=APPENV_ACCOUNT, region=APPENV_REGION)

vpc_stack = CdkVpcStack(app, "cdk-vpc", env=env_USA)
ec2_stack = CdkEc2Stack(app, "cdk-ec2",
                        vpc=vpc_stack.vpc, env=env_USA)
rds_stack = CdkRdsStack(app, "cdk-rds",
                        vpc=vpc_stack.vpc,
                        asg_security_groups=ec2_stack.asg.connections.security_groups,
                        env=env_USA)

app.synth()

#!/usr/bin/env python3

from aws_cdk import core

from ab1_cdk.ab1_cdk_stack import Ab1CdkStack


app = core.App()
Ab1CdkStack(app, "ab1-cdk")

app.synth()

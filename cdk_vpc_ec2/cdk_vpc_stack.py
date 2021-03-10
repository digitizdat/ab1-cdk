from aws_cdk import core
import aws_cdk.aws_ec2 as ec2


class CdkVpcStack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

#        self.vpc = ec2.Vpc(
#            self,
#            "VPC",
#            max_azs=3,
#            cidr="10.1.0.0/20",
#            # configuration will create 3 groups in 2 AZs = 6 subnets.
#            subnet_configuration=[
#                ec2.SubnetConfiguration(
#                    subnet_type=ec2.SubnetType.PUBLIC,
#                    name="Public",
#                    cidr_mask=24,
#                ),
#                ec2.SubnetConfiguration(
#                    subnet_type=ec2.SubnetType.PRIVATE,
#                    name="Private",
#                    cidr_mask=24,
#                ),
#                ec2.SubnetConfiguration(
#                    subnet_type=ec2.SubnetType.ISOLATED,
#                    name="DB",
#                    cidr_mask=24,
#                ),
#            ],
#            nat_gateway_provider=ec2.NatProvider.gateway(),
#            nat_gateways=3,
#        )

        self.vpc = ec2.Vpc.from_lookup(self, "MOStateAppVPC",
                vpc_name="aws-controltower-VPC")
        core.CfnOutput(self, "Output", value=self.vpc.vpc_id)

from aws_cdk import core
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_elasticloadbalancingv2 as elb
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_route53 as r53
import aws_cdk.aws_waf as waf
import aws_cdk.aws_iam as iam

from cdk_ec2_key_pair import KeyPair

ec2_type = "t2.micro"
linux_ami = ec2.AmazonLinuxImage(
    generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX,
    edition=ec2.AmazonLinuxEdition.STANDARD,
    virtualization=ec2.AmazonLinuxVirt.HVM,
    storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE,
)  # Indicate your AMI, no need a specific id in the region
with open("./user_data/user_data.sh") as f:
    user_data = f.read()


class CdkEc2Stack(core.Stack):
    def __init__(self, scope: core.Construct, id: str, vpc, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        admin_role = iam.Role.from_role_arn(self, 'admin_role', 'arn:aws:iam::989584467037:role/Admin')

        # Create EC2 key pair
        key = KeyPair(self, "app-instances",
            name="app-instances",
            description="Used for application instances",
            store_public_key=True
        )

        key.grant_read_on_private_key(admin_role)
        key.grant_read_on_public_key(admin_role)

        # Create Bastion
        #bastion = ec2.BastionHostLinux(
        #    self,
        #    "myBastion",
        #    vpc=vpc,
        #    subnet_selection=ec2.SubnetSelection(
        #        subnet_type=ec2.SubnetType.PUBLIC
        #    ),
        #    instance_name="myBastionHostLinux",
        #    instance_type=ec2.InstanceType(
        #        instance_type_identifier="t2.micro"
        #    ),
        #)

        ## Setup key_name for EC2 instance login if you don't use Session Manager
        ## bastion.instance.instance.add_property_override("KeyName", key_name)

        #bastion.connections.allow_from_any_ipv4(
        #    ec2.Port.tcp(22), "Internet access SSH"
        #)

        # Create public hosted zone
        #zone = r53.PublicHostedZone(self, "myZone", zone_name="randomhuman.org")
        # There's an issue with timeouts around ACM and Route53, so for
        # demonstration purposes, it will be best to use a pre-baked zone....
        zone = r53.HostedZone.from_lookup(self, "MOStateAppZone", domain_name="randomhuman.org")

        # Create certificate
        cert = acm.DnsValidatedCertificate(
            self,
            "MOStateAppCert",
            hosted_zone=zone,
            domain_name="*.randomhuman.org",
        )

        # Create ALB
        alb = elb.ApplicationLoadBalancer(
            self,
            "MOStateAppALB",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name="MOStateAppALB",
        )
        alb.connections.allow_from_any_ipv4(
            ec2.Port.tcp(443), "Internet access ALB 443"
        )
        listener = alb.add_listener(
            "https", certificates=[cert], port=443, open=True
        )

        # Create Autoscaling Group with fixed 2*EC2 hosts
        self.asg = autoscaling.AutoScalingGroup(
            self,
            "MOStateAppASG",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE
            ),
            instance_type=ec2.InstanceType(instance_type_identifier=ec2_type),
            machine_image=linux_ami,
            key_name=key.key_pair_name,
            user_data=ec2.UserData.custom(user_data),
            desired_capacity=2,
            min_capacity=1,
            max_capacity=6,
            # block_devices=[
            #     autoscaling.BlockDevice(
            #         device_name="/dev/xvda",
            #         volume=autoscaling.BlockDeviceVolume.ebs(
            #             volume_type=autoscaling.EbsDeviceVolumeType.GP2,
            #             volume_size=12,
            #             delete_on_termination=True
            #         )),
            #     autoscaling.BlockDevice(
            #         device_name="/dev/sdb",
            #         volume=autoscaling.BlockDeviceVolume.ebs(
            #             volume_size=20)
            #         # 20GB, with default volume_type gp2
            #     )
            # ]
        )

        self.asg.connections.allow_from(
            alb,
            ec2.Port.tcp(443),
            "ALB access 443 port of EC2 in Autoscaling Group",
        )
        listener.add_targets("addTargetGroup", port=443, targets=[self.asg])

        core.CfnOutput(self, "Output", value=alb.load_balancer_dns_name)

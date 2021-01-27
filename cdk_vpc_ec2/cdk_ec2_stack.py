from aws_cdk import core
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_elasticloadbalancingv2 as elb
import aws_cdk.aws_autoscaling as autoscaling
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_route53 as r53

ec2_type = "t2.micro"
key_name = "id_rsa"  # Setup key_name for EC2 instance login
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

        # Create Bastion
        bastion = ec2.BastionHostLinux(
            self,
            "myBastion",
            vpc=vpc,
            subnet_selection=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            instance_name="myBastionHostLinux",
            instance_type=ec2.InstanceType(
                instance_type_identifier="t2.micro"
            ),
        )

        # Setup key_name for EC2 instance login if you don't use Session Manager
        # bastion.instance.instance.add_property_override("KeyName", key_name)

        bastion.connections.allow_from_any_ipv4(
            ec2.Port.tcp(22), "Internet access SSH"
        )

        # Create certificate
        #zone = r53.HostedZone.from_hosted_zone_id(self, "zone", hosted_zone_id="Z102373822XHCWHEQJWIJ")
        zone = r53.HostedZone.from_lookup(self, "myZone", domain_name="randomhuman.org")
        cert = acm.DnsValidatedCertificate(
            self,
            "myAppCert",
            hosted_zone=zone,
            domain_name="*.randomhuman.org",
        )

        # Create ALB
        alb = elb.ApplicationLoadBalancer(
            self,
            "myALB",
            vpc=vpc,
            internet_facing=True,
            load_balancer_name="myALB",
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
            "myASG",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE
            ),
            instance_type=ec2.InstanceType(instance_type_identifier=ec2_type),
            machine_image=linux_ami,
            key_name=key_name,
            user_data=ec2.UserData.custom(user_data),
            desired_capacity=3,
            min_capacity=2,
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

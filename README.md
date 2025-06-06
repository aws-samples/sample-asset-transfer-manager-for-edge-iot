# Asset Transfer Manager for Edge IoT

This solution demonstrates how to transfer data from Amazon S3 to IoT Edge devices using AWS IoT Greengrass V2 and AWS IoT Jobs. It enables seamless file transfers for use cases such as software updates, firmware updates, and content distribution to edge devices.

## Getting started

You are welcome to follow the upcoming steps in your own AWS account, in the region of your choice or directly on your edge device. Before you get started installing AWS IoT Greengrass core on your edge device, make sure you check the [hardware and OS requirements](https://docs.aws.amazon.com/greengrass/latest/developerguide/what-is-gg.html#gg-platforms).

In this post, you will do the initial setup of AWS IoT Core and use the AWS IoT Greengrass, Version 2 (V2) installer to install Greengrass V2 on an EC2 instance  running [Amazon Linux 2023](https://docs.aws.amazon.com/linux/al2023/release-notes/relnotes.html), emulating edge gateway.

Follow the steps in the [Visual Studio Code on EC2 for Prototyping repository](https://github.com/aws-samples/vscode-on-ec2-for-prototyping/blob/main/README.md) to deploy an EC2 instance. Use the browser-based VS Code IDE to edit files and execute the instructions.

The EC2 instance is created with an IAM Role that grants unrestricted access to all AWS resources. It is recommended that you review the role attached to the EC2 instance and modify it to limit permissions to SSM, S3, IoT Core and IoT Greengrass.

## AWS IoT GreenGrass Core Device Setup

1. Install AWS IoT Greengrass Core software

```
curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip > greengrass-nucleus-latest.zip
unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && rm greengrass-nucleus-latest.zip
java -jar ./GreengrassInstaller/lib/Greengrass.jar --version
```

2. Create the Greengrass Core Device

Replace ```REGION``` with your region e.g.```us-west-2```

```
sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
-jar ./GreengrassInstaller/lib/Greengrass.jar \
--aws-region REGION \
--thing-name MyGreengrassCore \
--thing-group-name MyGreengrassCoreGroup \
--thing-policy-name GreengrassV2IoTThingPolicy \
--tes-role-name GreengrassV2TokenExchangeRole \
--tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
--component-default-user ggc_user:ggc_group \
--provision true \
--setup-system-service true
```

3. Install the IoT Greengrass Development Kit CLI

```
python3 -m pip install -U git+https://github.com/aws-greengrass/aws-greengrass-gdk-cli.git@v1.6.2
export PATH=$PATH:/home/ec2-user/.local/bin
```

## Build and Publish the Component

1. Clone the repository

```
git clone [https://github.com/aws-samples/asset-transfer-manager-for-edge-iot.git]
cd download-manager
```

2. Update the configuration file

Edit ```gdk-config.json``` and replace ```us-west-2``` with your AWS region. Replace ```1.3.0``` with the version of the GDK CLI you installed.

3. Build and publish the component

```
gdk component build
gdk component publish
```

## Deploy the Component

Navigate to AWS IoT Core Console → Greengrass Devices → Components and create a new deployment to your core device using the DownloadManager component

Include aws.greengrass.Nucleus, aws.greengrass.Cli and aws.greengrass.TokenExchangeService components in the deployment.

The Nucleus component should be configured with:

```
{
    "interpolateComponentConfiguration": true
}
```

## Testing the Component

1. Upload a test file to the S3 bucket named ```greengrass-artifacts-YOUR_REGION-YOUR_AWS_ACCOUNT_ID``` in the ```uploads``` folder

2. Create an AWS IoT Job

Navigate to AWS IoT Core → Remote actions → Jobs

Create a custom job

Select your core device as target

Use the AWS-Download-File template

Configure the S3 URI and local file path (images)

Monitor job status in AWS IoT Console

3. Verify the file download

```
cd /opt/downloads/images
```

## Authors and acknowledgment

Nilo Bustani , Senior Solutions Architect
Rashmi Varshney , Senior Solutions Architect
Tamil Jayakumar, Senior Solutions Architect

## License

Amazon Software License

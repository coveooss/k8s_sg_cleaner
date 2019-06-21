# Presentation

Until you are using Kubernetes 1.14 fix the [following](https://github.com/kubernetes/kubernetes/pull/74311) fix in the aws provider you may leak some security group when service is deleted.

## How it works

This script will compare all security group present in AWS for the Kubernetes cluster with all security group in AWS taggued with the corresponding "KubernetesCluster" tag.

## Requierement

This script need the following IAM policy

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "elasticloadbalancing:DescribeLoadBalancers",
                "elasticloadbalancing:DescribeTags",
                "ec2:DeleteSecurityGroup",
                "ec2:DescribeSecurityGroups"
            ],
            "Resource": "*"
        }
    ]
}
```

## Usage

Deploy a cronJob in Kubernetes

```
apiVersion: batch/v1beta1
kind: CronJob
metadata:
  labels:
    app: sg-cleaner
  name: sg-cleaner
  namespace: infrastructure
spec:
  jobTemplate:
    spec:
      template:
        metadata:
          annotations:
            iam.amazonaws.com/role: sg-cleaner-iam-role
          namespace: infrastructure
        spec:
          containers:
            image: coveo/k8s_sg_cleaner:1.0.0
            name: sg-cleaner
            resources:
              limits:
                cpu: 50m
                memory: 100Mi
  schedule: '*/30 * * * *'
```
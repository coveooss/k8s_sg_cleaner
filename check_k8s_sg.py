import boto3
import click
from kubernetes import config
import logging
import urllib.request

def get_k8s_sg(cluster_name, region, groupname_filter='k8s-elb'):
    ec2 = boto3.client('ec2',region_name=region)
    security_groups = []

    sgs = ec2.describe_security_groups(
        Filters=[
            {
                'Name':'tag:KubernetesCluster',
                'Values':[cluster_name]
            }
        ]
    )

    for sg in sgs['SecurityGroups']:
        if sg['GroupName'].startswith(groupname_filter):
            security_groups.append(sg['GroupId'])
    return set(security_groups)

def get_k8s_cluster():
    contexts = config.list_kube_config_contexts()
    return contexts[1]['context']['cluster']

def get_inuse_elb_sg(region):
    continue_iter = True
    marker = None
    elb_client = boto3.client('elb', region_name=region)
    elb_list = []
    elb_sg_list = []

    # Retrieve all ELB
    while continue_iter:
        if marker:
            response = elb_client.describe_load_balancers(Marker=marker)
        else:
            response = elb_client.describe_load_balancers()
        elb_list += response['LoadBalancerDescriptions']
        if 'NextMarker' in response:
            marker = response['NextMarker']
        else:
            continue_iter = False
    for elb in elb_list:
        elb_sg_list += elb['SecurityGroups']
    return set(elb_sg_list)


@click.command()
@click.option("--region", "-r", default=None,help="Region where to run the script")
@click.option("--cluster_name", default=None,help="Specify the k8s cluster name.")
def clean_sg(region, cluster_name):

    # Check region
    if not region:
        try:
            region = urllib.request.urlopen('http://169.254.169.254/latest/dynamic/instance-identity/document', timeout=2).read().decode()['region']
        except:
            region = boto3.session.Session().region_name
            logging.warning('Cannot detect region from metadata, use default region({})'.format(region))

    ec2 = boto3.client('ec2', region_name=region)
    ec2r = boto3.resource('ec2', region_name=region)

    # Check cluster name
    if not cluster_name:
        try:
            cluster_name = get_k8s_cluster()
        except:
            logging.error('Cannot load cluster name from kubeconfig or cluster name option not specify')

    # Get all sg attach to running service in k8s
    elb_sgs = get_inuse_elb_sg(region)

    # Get all sg from ec2 for the following cluster
    k8s_sg = get_k8s_sg(cluster_name, region)

    sg_to_delete = k8s_sg - elb_sgs

    if sg_to_delete:
        logging.info("{} - {} sg are currently in use by k8s services, {} will be deleted.".format(cluster_name, len(elb_sgs),len(sg_to_delete)))

        for sg in sg_to_delete:
            sg_def = ec2r.SecurityGroup(sg)
            logging.info('Deleting {}'.format(sg_def.description))
            try:
                ec2.delete_security_group(GroupId=sg)
                logging.info('{} deleted'.format(sg))
            except Exception as e:
                    logging.error('Unable to delete following SG : {}: {}'.format(sg, e))

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
    clean_sg()


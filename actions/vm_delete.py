import os
from st2common.runners.base_action import Action
from smtplib import SMTP
from email.header import Header
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from haikunator import Haikunator

haikunator = Haikunator()
# Azure Datacenter
LOCATION = 'Southeast Asia'

# Resource Group
GROUP_NAME = 'azure-sample-group-virtual-machines'

# Network
VNET_NAME = 'azure-sample-vnet'
SUBNET_NAME = 'azure-sample-subnet'

# VM
OS_DISK_NAME = 'Cloudera-CentOS-OS-Image'
STORAGE_ACCOUNT_NAME = haikunator.haikunate(delimiter='')

IP_CONFIG_NAME = '203.18.137.2'
NIC_NAME = 'azure-sample-nic'
USERNAME = 'mukesh.kumar_5375@nihilent.com'
PASSWORD = 'nihilent@123'
VM_NAME = 'Testvm1'

VM_REFERENCE = {
    'linux': {
        'publisher': 'Canonical',
        'offer': 'UbuntuServer',
        'sku': '16.04.0-LTS',
        'version': 'latest'
    },
    'windows': {
        'publisher': 'MicrosoftWindowsServerEssentials',
        'offer': 'WindowsServerEssentials',
        'sku': 'WindowsServerEssentials',
        'version': 'latest'
    }
}

class SendEmail(Action):
    def run(self):

        subscription_id = os.environ.get(
            'AZURE_SUBSCRIPTION_ID',
            'ef80a466-7372-49e9-b247-57b95886881c')  # your Azure Subscription Id
        credentials = ServicePrincipalCredentials(
            client_id='445a1911-819a-41e8-a093-adfd66ca5ccd',
            secret='rJ--cHsg@=fucrddh3svx1VUe91q2h1N',
            tenant='8ee0f3e4-b788-4efa-bd84-e6bfe7fe9943'
        )
        compute_client = ComputeManagementClient(credentials, subscription_id)
        #Delete VM
        print('\nDelete VM')
        async_vm_delete = compute_client.virtual_machines.delete(
            GROUP_NAME, VM_NAME)
        async_vm_delete.wait()
        return
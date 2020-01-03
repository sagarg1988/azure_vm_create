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

        # if mime not in ['plain', 'html']:
        #     raise ValueError('Invalid mime provided: ' + mime)
        #
        # accounts = self.config.get('smtp_accounts', None)
        # if accounts is None:
        #     raise ValueError('"smtp_accounts" config value is required to send email.')
        # if not accounts:
        #     raise ValueError('at least one account is required to send email.')
        #
        # try:
        #     kv = {}
        #     for a in accounts:
        #         kv[a['name']] = a
        #     account_data = kv[account]
        # except KeyError:
        #     raise KeyError('The account "{}" does not seem to appear in the configuration. '
        #                    'Available accounts are: {}'.format(account, ",".join(kv.keys())))
        #
        # msg = MIMEMultipart()
        # msg['Subject'] = Header(subject, 'utf-8')
        # msg['From'] = email_from
        # msg['To'] = ", ".join(email_to)
        # msg.attach(MIMEText(message, mime, 'utf-8'))
        # if email_cc is None:
        #     email_cc = []
        #
        # if email_cc:
        #     msg['Cc'] = ", ".join(email_cc)
        #     email_to += email_cc
        #
        # attachments = attachments or tuple()
        # for filepath in attachments:
        #     filename = os.path.basename(filepath)
        #     with open(filepath, 'rb') as f:
        #         part = MIMEApplication(f.read(), Name=filename)
        #     part['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        #     msg.attach(part)
        #
        # s = SMTP(account_data['server'], int(account_data['port']), timeout=20)
        # s.ehlo()
        # if account_data.get('secure', True) is True:
        #     s.starttls()
        # if account_data.get('smtp_auth', True) is True:
        #     s.login(account_data['username'], account_data['password'])
        # s.sendmail(email_from, email_to, msg.as_string())
        # s.quit()
        # return


        #----
        """Resource Group management example."""
        #
        # Create all clients with an Application (service principal) token provider
        #
        subscription_id = os.environ.get(
            'AZURE_SUBSCRIPTION_ID',
            'ef80a466-7372-49e9-b247-57b95886881c')  # your Azure Subscription Id
        credentials = ServicePrincipalCredentials(
            client_id='445a1911-819a-41e8-a093-adfd66ca5ccd',
            secret='rJ--cHsg@=fucrddh3svx1VUe91q2h1N',
            tenant='8ee0f3e4-b788-4efa-bd84-e6bfe7fe9943'
        )
        resource_client = ResourceManagementClient(credentials, subscription_id)
        compute_client = ComputeManagementClient(credentials, subscription_id)
        storage_client = StorageManagementClient(credentials, subscription_id)
        network_client = NetworkManagementClient(credentials, subscription_id)

        ###########
        # Prepare #
        ###########

        # Create Resource group
        print('\nCreate Resource Group')
        resource_client.resource_groups.create_or_update(
            GROUP_NAME, {'location': LOCATION})

        # Create a storage account
        print('\nCreate a storage account')
        storage_async_operation = storage_client.storage_accounts.create(
            GROUP_NAME,
            STORAGE_ACCOUNT_NAME,
            {
                'sku': {'name': 'standard_lrs'},
                'kind': 'storage',
                'location': LOCATION
            }
        )
        storage_async_operation.wait()

        # Create a NIC
        nic = create_nic(network_client)

        #############
        # VM Sample #
        #############

        # Create Linux VM
        print('\nCreating Linux Virtual Machine')
        vm_parameters = create_vm_parameters(nic.id, VM_REFERENCE['linux'])
        async_vm_creation = compute_client.virtual_machines.create_or_update(
            GROUP_NAME, VM_NAME, vm_parameters)
        async_vm_creation.wait()

        # Tag the VM
        print('\nTag Virtual Machine')
        async_vm_update = compute_client.virtual_machines.create_or_update(
            GROUP_NAME,
            VM_NAME,
            {
                'location': LOCATION,
                'tags': {
                    'who-rocks': 'python',
                    'where': 'on azure'
                }
            }
        )
        async_vm_update.wait()

        # Attach data disk
        print('\nAttach Data Disk')
        async_vm_update = compute_client.virtual_machines.create_or_update(
            GROUP_NAME,
            VM_NAME,
            {
                'location': LOCATION,
                'storage_profile': {
                    'data_disks': [{
                        'name': 'mydatadisk1',
                        'disk_size_gb': 1,
                        'lun': 0,
                        'vhd': {
                            'uri': "http://{}.blob.core.windows.net/vhds/mydatadisk1.vhd".format(
                                STORAGE_ACCOUNT_NAME)
                        },
                        'create_option': 'Empty'
                    }]
                }
            }
        )
        async_vm_update.wait()

        # Get one the virtual machine by name
        print('\nGet Virtual Machine by Name')
        virtual_machine = compute_client.virtual_machines.get(
            GROUP_NAME,
            VM_NAME
        )

        # Detach data disk
        print('\nDetach Data Disk')
        data_disks = virtual_machine.storage_profile.data_disks
        data_disks[:] = [disk for disk in data_disks if disk.name != 'mydatadisk1']
        async_vm_update = compute_client.virtual_machines.create_or_update(
            GROUP_NAME,
            VM_NAME,
            virtual_machine
        )
        virtual_machine = async_vm_update.result()

        # Deallocating the VM (resize prepare)
        print('\nDeallocating the VM (resize prepare)')
        async_vm_deallocate = compute_client.virtual_machines.deallocate(
            GROUP_NAME, VM_NAME)
        async_vm_deallocate.wait()

        # Update OS disk size by 10Gb
        print('\nUpdate OS disk size')
        # Server is not returning the OS Disk size (None), possible bug in server
        if not virtual_machine.storage_profile.os_disk.disk_size_gb:
            print("\tServer is not returning the OS disk size, possible bug in the server?")
            print("\tAssuming that the OS disk size is 256 GB")
            virtual_machine.storage_profile.os_disk.disk_size_gb = 256

        virtual_machine.storage_profile.os_disk.disk_size_gb += 10
        async_vm_update = compute_client.virtual_machines.create_or_update(
            GROUP_NAME,
            VM_NAME,
            virtual_machine
        )
        virtual_machine = async_vm_update.result()

        # Start the VM
        print('\nStart VM')
        async_vm_start = compute_client.virtual_machines.start(GROUP_NAME, VM_NAME)
        async_vm_start.wait()

        # Restart the VM
        print('\nRestart VM')
        async_vm_restart = compute_client.virtual_machines.restart(
            GROUP_NAME, VM_NAME)
        async_vm_restart.wait()

        # Stop the VM
        print('\nStop VM')
        async_vm_stop = compute_client.virtual_machines.power_off(
            GROUP_NAME, VM_NAME)
        async_vm_stop.wait()

        # List VMs in subscription
        print('\nList VMs in subscription')
        for vm in compute_client.virtual_machines.list_all():
            print("\tVM: {}".format(vm.name))

        # List VM in resource group
        print('\nList VMs in resource group')
        for vm in compute_client.virtual_machines.list(GROUP_NAME):
            print("\tVM: {}".format(vm.name))

        # Delete VM
        # print('\nDelete VM')
        # async_vm_delete = compute_client.virtual_machines.delete(
        #     GROUP_NAME, VM_NAME)
        # async_vm_delete.wait()
        return

def create_nic(network_client):
    """Create a Network Interface for a VM.
    """
    # Create VNet
    print('\nCreate Vnet')
    async_vnet_creation = network_client.virtual_networks.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        {
            'location': LOCATION,
            'address_space': {
                'address_prefixes': ['10.0.0.0/17']
            }
        }
    )
    async_vnet_creation.wait()

    # Create Subnet
    print('\nCreate Subnet')
    async_subnet_creation = network_client.subnets.create_or_update(
        GROUP_NAME,
        VNET_NAME,
        SUBNET_NAME,
        {'address_prefix': '10.0.0.0/24'}
    )
    subnet_info = async_subnet_creation.result()

    # Create NIC
    print('\nCreate NIC')
    async_nic_creation = network_client.network_interfaces.create_or_update(
        GROUP_NAME,
        NIC_NAME,
        {
            'location': LOCATION,
            'ip_configurations': [{
                'name': IP_CONFIG_NAME,
                'subnet': {
                    'id': subnet_info.id
                }
            }]
        }
    )
    return async_nic_creation.result()


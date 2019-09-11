# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from time import sleep

from knack.util import CLIError

from azure.cli.testsdk import ScenarioTest, ResourceGroupPreparer, JMESPathCheck


class TestMonitorLogAlert(ScenarioTest):
    @DomainPreparer()
    @ResourceGroupPreparer(location='westcentralus')
    def test_monitor_create_log_alert(self, resource_group, domainvm):
        data_sorce_id = '/subscriptions/{}/resourceGroups/{}/providers/microsoft.operationalinsights/workspaces/{}'.format(self.get_subscription_id(), resource_group, domainvm)
        severity = 2
        threshold = 5
        threshold_operator = 'GreaterThan'
        frequency= 30
        time_window = 60
        alert_query = "Perf"

        alert_name = self.create_random_name('clilogalert', 32)
        self.cmd('az monitor log-alert create -n {} -g {} -l {} --severity {} --threshold {} --threshold-operator {} --frequency {} --time-window {} --alert-query {} --data-source-id {} '
                 '-ojson'.format(alert_name, resource_group, 'westcentralus', severity, threshold, threshold_operator, frequency, time_window, alert_query, data_sorce_id),
                 checks=[JMESPathCheck('name', alert_name),
                         JMESPathCheck('enabled', 'true1'),
                         JMESPathCheck('action.severity', severity),
                         JMESPathCheck('action.trigger.threshold', threshold),
                         JMESPathCheck('action.trigger.thresholdOperator', threshold_operator),
                         JMESPathCheck('schedule.frequencyInMinutes', frequency),
                         JMESPathCheck('schedule.timeWindowInMinutes', time_window),
                         JMESPathCheck('source.query', alert_query),
                         JMESPathCheck('source.dataSourceId', data_sorce_id)])

    
    @ResourceGroupPreparer(location='westcentralus')
    def test_monitor_create_full_fledged_log_alert(self, resource_group):
        description = 'Alert description'
        data_sorce_id = '/subscriptions/{}/resourceGroups/{}/providers/microsoft.operationalinsights/workspaces/{}'.format(self.get_subscription_id(), resource_group, 'testLAWorkSpace')
        severity = 2
        threshold = 5
        threshold_operator = 'GreaterThan'
        frequency= 30
        time_window = 60
        alert_query = "Perf"

        alert_name = self.create_random_name('clilogalert', 34)
        self.cmd('az monitor log-alert create -n {} -g {} -l {} --description {} --severity {} --threshold {} --threshold-operator {} --frequency {} --time-window {} --alert-query {} --data-source-id {} '
                 '-ojson'.format(alert_name, resource_group, 'westcentralus', description, severity, threshold, threshold_operator, frequency, time_window, alert_query, data_sorce_id),
                 checks=[JMESPathCheck('name', alert_name),
                         JMESPathCheck('enabled', 'true'),
                         JMESPathCheck('action.severity', severity),
                         JMESPathCheck('action.trigger.threshold', threshold),
                         JMESPathCheck('action.trigger.thresholdOperator', threshold_operator),
                         JMESPathCheck('schedule.frequencyInMinutes', frequency),
                         JMESPathCheck('schedule.timeWindowInMinutes', time_window),
                         JMESPathCheck('source.query', alert_query),
                         JMESPathCheck('source.dataSourceId', data_sorce_id)])


from azure.cli.core.util import CLIError
from azure.cli.core.mock import DummyCli
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.exceptions import CliTestError
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
#constants
log_alert_domain_prefix = 'domainvm'
la_vm_max_length = 15

class DomainPreparer(AbstractPreparer, SingleValueReplacer):
    import string

    def __init__(self, name_prefix=log_alert_domain_prefix, location='westus',
                 vm_user='admin123', vm_password='SecretPassword123', parameter_name='domainvm',
                 resource_group_parameter_name='resource_group', skip_delete=True):
        super(DomainPreparer, self).__init__(name_prefix, la_vm_max_length)
        self.location = location
        self.parameter_name = parameter_name
        self.vm_user = vm_user
        self.vm_password = vm_password
        self.resource_group_parameter_name = resource_group_parameter_name
        self.skip_delete = skip_delete

    def id_generator(self, size=6, chars=string.ascii_lowercase + string.digits):
        import random
        return ''.join(random.choice(chars) for _ in range(size))

    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        dns_name = self.id_generator()
        parameters = ('adminUsername=admin123 adminPassword=SecretPassword123 location=westus '
                      'domainName=domain.com dnsPrefix={}').format(dns_name)
        template = 'az group deployment create --name {} -g {} --template-uri {} --parameters {}'
        execute(DummyCli(), template.format('domaintemplate', group,
                                            'https://raw.githubusercontent.com/Azure/azure-quickstart-templates/master/active-directory-new-domain/azuredeploy.json',
                                            parameters))
        return {self.parameter_name: name}

    def remove_resource(self, name, **kwargs):
        if not self.skip_delete:
            group = self._get_resource_group(**kwargs)
            execute(DummyCli(), 'az group delete -g {}'.format(group))

    def _get_resource_group(self, **kwargs):
        try:
            return kwargs.get(self.resource_group_parameter_name)
        except KeyError:
            template = 'To create a virtual machine a resource group is required. Please add ' \
                       'decorator @{} in front of this preparer.'
            raise CliTestError(template.format(ResourceGroupPreparer.__name__,
                                               self.resource_group_parameter_name))

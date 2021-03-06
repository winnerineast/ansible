#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: aci_epg_contract_binding
short_description: Manage EPG to Contract bindings on Cisco ACI fabrics
description:
- Manage EPG to Contract bindings on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob Mcgill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
notes:
- The C(tenant), C(app_profile), C(EPG), and C(Contract) used must exist before using this module in your playbook.
  The M(aci_tenant), M(aci_anp), M(aci_epg), and M(aci_contract) modules can be used for this.
options:
  app_profile:
    description:
    - Name of an existing application network profile, that will contain the EPGs.
    aliases: [ app_profile_name ]
  contract:
    description:
    - The name of the contract.
    aliases: [ contract_name ]
  contract_type:
    description:
    - Determines if the EPG should Provide or Consume the Contract.
    required: yes
    choices: [ consumer, proivder ]
  epg:
    description:
    - The name of the end point group.
    aliases: [ epg_name ]
  priority:
    description:
    - QoS class.
    - The APIC defaults new EPG to Contract bindings to unspecified.
    choices: [ level1, level2, level3, unspecified ]
    default: unspecified
  provider_match:
    description:
    - The matching algorithm for Provided Contracts.
    - The APIC defaults new EPG to Provided Contracts to at_least_one.
    choices: [ all, at_least_one, at_most_one, none ]
    default: at_least_one
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
  tenant:
    description:
    - Name of an existing tenant.
    aliases: [ tenant_name ]
extends_documentation_fragment: aci
'''

EXAMPLES = r''' # '''

RETURN = r''' # '''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule

ACI_CLASS_MAPPING = {"consumer": "fvRsCons", "provider": "fvRsProv"}
ACI_MO_MAPPING = {"consumer": "rscons", "provider": "rsprov"}
PROVIDER_MATCH_MAPPING = {"all": "All", "at_least_one": "AtleastOne", "at_most_one": "AtmostOne", "none": "None"}


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        app_profile=dict(type='str', aliases=['app_profile_name']),
        epg=dict(type='str', aliases=['epg_name']),
        contract=dict(type='str', aliases=['contract_name']),
        contract_type=dict(type='str', required=True, choices=['consumer', 'provider']),
        priority=dict(type='str', choices=['level1', 'level2', 'level3', 'unspecified']),
        provider_match=dict(type='str', choices=['all', 'at_least_one', 'at_most_one', 'none']),
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        tenant=dict(type='str', aliases=['tenant_name']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_if=[['state', 'absent', ['app_profile', 'contract', 'epg', 'tenant']],
                     ['state', 'present', ['app_profile', 'contract', 'epg', 'tenant']]]
    )

    app_profile = module.params['app_profile']
    epg = module.params['epg']
    contract = module.params['contract']
    contract_type = module.params['contract_type']
    aci_class = ACI_CLASS_MAPPING[contract_type]
    aci_mo = ACI_MO_MAPPING[contract_type]
    priority = module.params['priority']
    provider_match = module.params['provider_match']
    state = module.params['state']
    tenant = module.params['tenant']

    if contract_type == "consumer" and provider_match is not None:
        module.fail_json(msg="the 'provider_match' is only configurable for Provided Contracts")

    aci = ACIModule(module)

    # TODO: Add logic to handle multiple input variations when query
    if state != 'query':
        # Work with a specific EPG to Contract Binding
        path = 'api/mo/uni/tn-{}/ap-{}/epg-{}/{}-{}.json'.format(tenant, app_profile, epg, aci_mo, contract)
        filter_string = '?rsp-prop-include=config-only'
    else:
        # Query all EPGs
        path = 'api/class/{}.json'.format(aci_class)
        filter_string = ''

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing(filter_string=filter_string)

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class=aci_class, class_config=dict(matchT=provider_match, prio=priority, tnVzBrCPName=contract))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class=aci_class)

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()

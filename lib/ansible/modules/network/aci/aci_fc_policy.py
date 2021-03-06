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
module: aci_fc_policy
short_description: Manage Fibre Channel interface policies on Cisco ACI fabrics
description:
- Manage ACI Fiber Channel interface policies on Cisco ACI fabrics.
author:
- Swetha Chunduri (@schunduri)
- Dag Wieers (@dagwieers)
- Jacob McGill (@jmcgill298)
version_added: '2.4'
requirements:
- ACI Fabric 1.0(3f)+
options:
  fc_policy:
    description:
    - Name of the Fiber Channel interface policy.
    required: yes
    aliases: [ name ]
  description:
    description:
    - Description of the Fiber Channel interface policy.
    aliases: [ descr ]
  port_mode:
    description:
    - Port Mode
    choices: [ f, np ]
    default: f
  state:
    description:
    - Use C(present) or C(absent) for adding or removing.
    - Use C(query) for listing an object or multiple objects.
    choices: [ absent, present, query ]
    default: present
extends_documentation_fragment: aci
'''

EXAMPLES = r'''
- aci_fc_policy:
    hostname: '{{ hostname }}'
    username: '{{ username }}'
    password: '{{ password }}'
    fc_policy: '{{ fc_policy }}'
    port_mode: '{{ port_mode }}'
    description: '{{ description }}'
    state: present
'''

RETURN = r'''
#
'''

from ansible.module_utils.aci import ACIModule, aci_argument_spec
from ansible.module_utils.basic import AnsibleModule


def main():
    argument_spec = aci_argument_spec
    argument_spec.update(
        fc_policy=dict(type='str', required=False, aliases=['name']),  # Not required for querying all objects
        description=dict(type='str', aliases=['descr']),
        port_mode=dict(type='str', choices=['f', 'np']),  # No default provided on purpose
        state=dict(type='str', default='present', choices=['absent', 'present', 'query']),
        method=dict(type='str', choices=['delete', 'get', 'post'], aliases=['action'], removed_in_version='2.6'),  # Deprecated starting from v2.6
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )

    fc_policy = module.params['fc_policy']
    port_mode = module.params['port_mode']
    description = module.params['description']
    state = module.params['state']

    aci = ACIModule(module)

    if fc_policy is not None:
        # Work with a specific object
        path = 'api/mo/uni/infra/fcIfPol-%(fc_policy)s.json' % module.params
    elif state == 'query':
        # Query all objects
        path = 'api/infra/class/fcIfPol.json'
    else:
        module.fail_json(msg="Parameter 'fc_policy' is required for state 'absent' or 'present'")

    aci.result['url'] = '%(protocol)s://%(hostname)s/' % aci.params + path

    aci.get_existing()

    if state == 'present':
        # Filter out module parameters with null values
        aci.payload(aci_class='fcIfPol', class_config=dict(name=fc_policy, descr=description, portMode=port_mode))

        # Generate config diff which will be used as POST request body
        aci.get_diff(aci_class='fcIfPol')

        # Submit changes if module not in check_mode and the proposed is different than existing
        aci.post_config()

    elif state == 'absent':
        aci.delete_config()

    module.exit_json(**aci.result)


if __name__ == "__main__":
    main()

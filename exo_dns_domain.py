#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# (c) 2016, René Moser <mail@renemoser.net>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible. If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
module: exo_dns_domain
short_description: Manages domain records on Exoscale DNS API.
description:
    - Create and remove domain records.
version_added: "2.2"
author: "René Moser (@resmo)"
options:
  name:
    description:
      - Name of the record.
    required: true
  state:
    description:
      - State of the resource.
    required: false
    default: 'present'
    choices: [ 'present', 'absent' ]
  api_key:
    description:
      - API key of the Exoscale DNS API.
    required: false
    default: null
  api_secret:
    description:
      - Secret key of the Exoscale DNS API.
    required: false
    default: null
  api_timeout:
    description:
      - HTTP timeout to Exoscale DNS API.
    required: false
    default: 10
  api_region:
    description:
      - Name of the ini section in the C(cloustack.ini) file.
    required: false
    default: cloudstack
  validate_certs:
    description:
      - Validate SSL certs of the Exoscale DNS API.
    required: false
    default: true
requirements:
  - "python >= 2.6"
notes:
  - As Exoscale DNS uses the same API key and secret for all services, we reuse the config used for Exscale Compute based on CloudStack.
    The config is read from several locations, in the following order.
    The C(CLOUDSTACK_KEY), C(CLOUDSTACK_SECRET) environment variables.
    A C(CLOUDSTACK_CONFIG) environment variable pointing to an C(.ini) file,
    A C(cloudstack.ini) file in the current working directory.
    A C(.cloudstack.ini) file in the users home directory.
    Optionally multiple credentials and endpoints can be specified using ini sections in C(cloudstack.ini).
    Use the argument C(api_region) to select the section name, default section is C(cloudstack).
  - This module does not support multiple A records and will complain properly if you try.
  - More information Exoscale DNS can be found on https://community.exoscale.ch/documentation/dns/.
  - This module supports check mode and diff.
'''

EXAMPLES = '''
# Create a domain.
- local_action:
    module: exo_dns_domain
    name: example.com

# Remove a domain.
- local_action:
    module: exo_dns_domain
    name: example.com
    state: absent
'''

RETURN = '''
exo_dns_domain:
    description: API domain results
    returned: success
    type: dictionary
    contains:
        account_id:
            description: Your account ID
            returned: success
            type: int
            sample: 34569
        auto_renew:
            description: Whether domain is auto renewed or not
            returned: success
            type: bool
            sample: false
        created_at:
            description: When the domain was created
            returned: success
            type: string
            sample: "2016-08-12T15:24:23.989Z"
        expires_on:
            description: When the domain expires
            returned: success
            type: string
            sample: "2016-08-12T15:24:23.989Z"
        id:
            description: ID of the domain
            returned: success
            type: int
            sample: "2016-08-12T15:24:23.989Z"
        lockable:
            description: Whether the domain is lockable or not
            returned: success
            type: bool
            sample: true
        name:
            description: Domain name
            returned: success
            type: string
            sample: example.com
        record_count:
            description: Number of records related to this domain
            returned: success
            type: int
            sample: 5
        registrant_id:
            description: ID of the registrant
            returned: success
            type: int
            sample: null
        service_count:
            description: Number of services
            returned: success
            type: int
            sample: 0
        state:
            description: State of the domain
            returned: success
            type: string
            sample: "hosted"
        token:
            description: Token
            returned: success
            type: string
            sample: "r4NzTRp6opIeFKfaFYvOd6MlhGyD07jl"
        unicode_name:
            description: Domain name as unicode
            returned: success
            type: string
            sample: "example.com"
        updated_at:
            description: When the domain was updated last.
            returned: success
            type: string
            sample: "2016-08-12T15:24:23.989Z"
        user_id:
            description: ID of the user
            returned: success
            type: int
            sample: null
        whois_protected:
            description: Wheter the whois is protected or not
            returned: success
            type: bool
            sample: false
'''

try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        # Let snippet from module_utils/basic.py return a proper error in this case
        pass

import urllib
from ConfigParser import ConfigParser, NoSectionError

EXO_DNS_BASEURL="https://api.exoscale.ch/dns/v1"

def exo_dns_argument_spec():
    return dict(
        api_key=dict(default=None, no_log=True),
        api_secret=dict(default=None, no_log=True),
        api_timeout=dict(type='int', default=10),
        api_region=dict(default='cloudstack'),
        validate_certs=dict(default='yes', type='bool'),
    )

def exo_dns_required_together():
    return [['api_key', 'api_secret']]


class ExoDns(object):

    def __init__(self, module):
        self.module = module

        self.api_key = self.module.params. get('api_key')
        self.api_secret = self.module.params.get('api_secret')
        if not (self.api_key and self.api_secret):
            try:
                region = self.module.params.get('api_region')
                config = self.read_config(ini_group=region)
                self.api_key = config['key']
                self.api_secret = config['secret']
            except Exception:
                e = get_exception()
                self.module.fail_json(msg=str(e))

        self.headers = {
            'X-DNS-Token': "%s:%s" % (self.api_key, self.api_secret),
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        self.result = {
            'changed': False,
            'diff': {
                'before': {},
                'after': {},
            }
        }

    def read_config(self, ini_group=None):
        if not ini_group:
            ini_group = os.environ.get('CLOUDSTACK_REGION', 'cloudstack')

        keys = ['key', 'secret']
        env_conf = {}
        for key in keys:
            if 'CLOUDSTACK_{0}'.format(key.upper()) not in os.environ:
                break
            else:
                env_conf[key] = os.environ['CLOUDSTACK_{0}'.format(key.upper())]
        else:
            return env_conf

        # Config file: $PWD/cloudstack.ini or $HOME/.cloudstack.ini
        # Last read wins in configparser
        paths = (
            os.path.join(os.path.expanduser('~'), '.cloudstack.ini'),
            os.path.join(os.getcwd(), 'cloudstack.ini'),
        )
        # Look at CLOUDSTACK_CONFIG first if present
        if 'CLOUDSTACK_CONFIG' in os.environ:
            paths += (os.path.expanduser(os.environ['CLOUDSTACK_CONFIG']),)
        if not any([os.path.exists(c) for c in paths]):
            raise SystemExit("Config file not found. Tried {0}".format(
                ", ".join(paths)))

        conf = ConfigParser()
        conf.read(paths)
        return dict(conf.items(ini_group))

    def api_query(self, resource="/domains", method="GET", data=None):
        url = EXO_DNS_BASEURL + resource
        if data:
            data = json.dumps(data)

        response, info = fetch_url(
            module = self.module,
            url = url,
            data = data,
            method = method,
            headers = self.headers,
            timeout = self.module.params.get('api_timeout'),
        )

        if info['status'] not in (200, 201, 204):
            self.module.fail_json(msg="%s returned %s, with body: %s" % (url, info['status'], info['msg']))

        try:
            return json.load(response)
        except Exception as e:
            return {}

    def _has_changed(self, want_dict, current_dict, only_keys=None):
        changed = False
        for key, value in want_dict.iteritems():
            # Optionally limit by a list of keys
            if only_keys and key not in only_keys:
                continue
            # Skip None values
            if value is None:
                continue
            if key in current_dict:
                if isinstance(current_dict[key], (int, long, float, complex)):
                    if value != current_dict[key]:
                        self.result['diff']['before'][key] = current_dict[key]
                        self.result['diff']['after'][key] = value
                        changed = True
                elif value.lower() != current_dict[key].encode('utf-8').lower():
                    self.result['diff']['before'][key] = current_dict[key]
                    self.result['diff']['after'][key] = value
                    changed = True
            else:
                self.result['diff']['after'][key] = value
                changed = True
        return changed

class ExoDnsDomain(ExoDns):

    def __init__(self, module):
        super(ExoDnsDomain, self).__init__(module)
        self.name = self.module.params.get('name').lower()

    def get_domain(self):
        domains = self.api_query("/domains", "GET")
        for z in domains:
            if z['domain']['name'].lower() == self.name:
                return z
        return None

    def present_domain(self):
        domain = self.get_domain()
        data = {
            'domain': {
                'name': self.name,
            }
        }
        if not domain:
            self.result['diff']['after'] = data['domain']
            self.result['changed'] = True
            if not self.module.check_mode:
                domain = self.api_query("/domains", "POST", data)
        return domain

    def absent_domain(self):
        domain = self.get_domain()
        if domain:
            self.result['diff']['before'] = domain
            self.result['changed'] = True
            if not self.module.check_mode:
                self.api_query("/domains/%s" % domain['domain']['name'], "DELETE")
        return domain

    def get_result(self, resource):
        if resource:
            self.result['exo_dns_domain'] = resource['domain']
        return self.result


def main():
    argument_spec = exo_dns_argument_spec()
    argument_spec.update(dict(
        name=dict(required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    ))

    module = AnsibleModule(
        argument_spec=argument_spec,
        required_together=exo_dns_required_together(),
        supports_check_mode=True
    )

    exo_dns_domain = ExoDnsDomain(module)
    if module.params.get('state') == "present":
        resource = exo_dns_domain.present_domain()
    else:
        resource = exo_dns_domain.absent_domain()
    result = exo_dns_domain.get_result(resource)

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()

# Ansible Exoscale DNS Modules

Manages domains and records on Exoscale. The modules support `--check_mode` and `--diff` as well

## Summary

Ansible does not include any modules to manage Exoscale DNS.

But no worries, I created them for your :). With a few simple installation steps you can already use them in Ansible 2.1. These steps become obsolete in future versions of Ansible when the modules `exo_dns_domain` and `exo_dns_record` are shipped with Ansible in 2.2.

## Installation

For using customs modules, Ansible will check for modules in a `./library` directory along with your playbooks. So let's create a diretory `library`:

    cd my_ansible_project
    mkdir library

Download the modules into `library`:

    wget -P library https://raw.githubusercontent.com/resmo/ansible-exoscale-dns/master/exo_dns_domain.py
    wget -P library https://raw.githubusercontent.com/resmo/ansible-exoscale-dns/master/exo_dns_record.py

After this setup, we will be able to read the docs of these modules including examples, e.g.:

    ansible-doc exo_dns_domain
    ansible-doc exo_dns_record

## Authentication

Exoscale's computing and DNS API share the same API keys and secret, that is why the modules support the same authentication methods as the cloudstack modules.

### cloudstack.ini
If you have an existing `cloudstack.ini` file, the configration will be also used by the DNS modules. Please see [Ansible CloudStack Guide](http://docs.ansible.com/ansible/guide_cloudstack.html) for more information.

In the simplest setup you create a `cloudstack.ini` file with the following structure nearby your playbooks:

~~~ini
[cloudstack]
endpoint = https://api.exoscale.ch/compute
key = api key
secret = api secret
~~~

#### Note

The endpoint is used for the compute API and must **not** point to the DNS API. The modules just read and use the same keys.

Alternatively the modules allows to pass the `api_key` and `api_secret`as arguments along with the module arguments:

~~~yaml
# Create or update an A record.
- local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.4
    api_key: "{{ your_api_key }}"
    api_secret: "{{ your_api_secret }}"
~~~

## Examples

### exo_dns_domain

~~~yaml
# Create a domain.
- local_action:
    module: exo_dns_domain
    name: example.com

# Remove a domain.
- local_action:
    module: exo_dns_domain
    name: example.com
    state: absent
~~~

### exo_dns_record

After creating the domain, we are able to add records to it:

~~~yaml
# Create or update an A record.
- local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.4

# Update an existing A record with a new IP.
- local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.5

# Create another A record with same name.
- local_action:
    module: exo_dns_record
    name: web-vm-1
    domain: example.com
    content: 1.2.3.6
    multiple: yes

# Create or update a CNAME record.
- local_action:
    module: exo_dns_record
    name: www
    domain: example.com
    record_type: CNAME
    content: web-vm-1

# Create or update a MX record.
- local_action:
    module: exo_dns_record
    domain: example.com
    record_type: MX
    content: mx1.example.com
    prio: 10

# delete a MX record.
- local_action:
    module: exo_dns_record
    domain: example.com
    record_type: MX
    content: mx1.example.com
    state: absent

# Remove a record.
- local_action:
    module: exo_dns_record
    name: www
    domain: example.com
    state: absent
~~~

## Integration Tests

Integration Tests can be found in the `test` directory:

Run the tests (cloudstack.ini must exist and be setup):

    cd test
    ansible-playbook exoscale.yml -e "exo_dns_domain_name=example.com" -vv --diff

## Donations

Use it? I would appreciate a donaton for my works [Paypal](https://www.paypal.me/resmo)

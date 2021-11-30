# Junos Templatify
Generate Junos configuration into a jinja2 template and YAML variable file.
Target to templatify is simply used by configuration hierarchy path.

# Example

## Usage
```
usage: junos-templatify.py [-h] [--address ADDRESS] [--user USER] [--password PASSWORD] [--port PORT] [--pathlist PATHLIST [PATHLIST ...]]
                           [--templatefile TEMPLATEFILE] [--paramfile PARAMFILE] [--mode-templatify] [--mode-configure]

optional arguments:
  -h, --help            show this help message and exit
  --address ADDRESS, -a ADDRESS
                        Device host address
  --user USER, -u USER  Device Username
  --password PASSWORD, -w PASSWORD
                        Device Password
  --port PORT, -p PORT  Device Port
  --pathlist PATHLIST [PATHLIST ...], -l PATHLIST [PATHLIST ...]
                        To templatify configuration path list. For example: ['configuration/protocols/bgp/group', 'interfaces/interface']
  --templatefile TEMPLATEFILE, -t TEMPLATEFILE
                        output or input jinja2 template file name
  --paramfile PARAMFILE, -m PARAMFILE
                        output or input yaml param file name
  --mode-templatify
  --mode-configure

```

## Running the utility
```
% python3 junos-templatify.py -a 10.10.10.10 -u 'username' -w 'password' -p port_num --mode-templatify -l 'protocols/bgp/group' 'configuration/interfaces'         
Templatify target to PATHLIST ['protocols/bgp/group', 'configuration/interfaces']       
Connecting device..
Getting configuration..
Parsing configuration..
Generating template..
jinja2 template written into template.jinja2
yaml file written into param.yaml

```

## Examine the resulting template and variable file
### template.jinja2
```
interfaces {
    {{ data["interfaces/interface/<ge-0/0/1>:name"] }} {
        unit {{ data["interfaces/interface/<ge-0/0/1>/unit/<0>:name"] }} {
            family inet {
                address {{ data["interfaces/interface/<ge-0/0/1>/unit/<0>/family/inet/address/<10.100.13.1/24>:name"] }};
            }
            family iso;
        }
    }
    {{ data["interfaces/interface/<ge-0/0/2>:name"] }} {
        unit {{ data["interfaces/interface/<ge-0/0/2>/unit/<0>:name"] }} {
            family inet {
                address {{ data["interfaces/interface/<ge-0/0/2>/unit/<0>/family/inet/address/<10.100.14.1/24>:name"] }};
            }
        }
    }
    
....

protocols {
....
    bgp {
        group {{ data["protocols/bgp/group/<EBGP-to-vMX4>:name"] }} {
            type {{ data["protocols/bgp/group/<EBGP-to-vMX4>:type"] }};
            peer-as {{ data["protocols/bgp/group/<EBGP-to-vMX4>:peer-as"] }};
            neighbor {{ data["protocols/bgp/group/<EBGP-to-vMX4>/neighbor/<10.100.14.2>:name"] }} {
                description "{{ data["protocols/bgp/group/<EBGP-to-vMX4>/neighbor/<10.100.14.2>:description"] }}";
            }
        }
        group {{ data["protocols/bgp/group/<IBGP-to-vRR>:name"] }} {
            type {{ data["protocols/bgp/group/<IBGP-to-vRR>:type"] }};
            local-address {{ data["protocols/bgp/group/<IBGP-to-vRR>:local-address"] }};
            export {{ data["protocols/bgp/group/<IBGP-to-vRR>:export"] }};
            neighbor {{ data["protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.1>:name"] }} {
                description "{{ data["protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.1>:description"] }}";
            }
            neighbor {{ data["protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.2>:name"] }} {
                description "{{ data["protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.2>:description"] }}";
            }
        }
    }
}
```
### param.yaml
```
interfaces/interface/<ge-0/0/0>:name: ge-0/0/0
interfaces/interface/<ge-0/0/0>/unit/<0>:name: '0'
interfaces/interface/<ge-0/0/0>/unit/<0>/family/inet/address/<10.100.12.1/24>:name: 10.100.12.1/24
interfaces/interface/<ge-0/0/1>:name: ge-0/0/1
interfaces/interface/<ge-0/0/1>/unit/<0>:name: '0'
interfaces/interface/<ge-0/0/1>/unit/<0>/family/inet/address/<10.100.13.1/24>:name: 10.100.13.1/24
interfaces/interface/<ge-0/0/2>:name: ge-0/0/2
interfaces/interface/<ge-0/0/2>/unit/<0>:name: '0'
interfaces/interface/<ge-0/0/2>/unit/<0>/family/inet/address/<10.100.14.1/24>:name: 10.100.14.1/24
interfaces/interface/<ge-0/0/3>:name: ge-0/0/3
interfaces/interface/<ge-0/0/3>/unit/<0>:name: '0'
interfaces/interface/<ge-0/0/3>/unit/<0>/family/inet/address/<10.100.111.1/24>:name: 10.100.111.1/24
interfaces/interface/<ge-0/0/4>:name: ge-0/0/4
interfaces/interface/<ge-0/0/4>/unit/<0>:name: '0'
interfaces/interface/<ge-0/0/4>/unit/<0>/family/inet/address/<10.100.112.1/24>:name: 10.100.112.1/24
interfaces/interface/<fxp0>:name: fxp0
interfaces/interface/<fxp0>/unit/<0>:name: '0'
interfaces/interface/<fxp0>/unit/<0>/family/inet/address/<100.123.1.0/16>:name: 100.123.1.0/16
interfaces/interface/<lo0>:name: lo0
interfaces/interface/<lo0>/unit/<0>:name: '0'
interfaces/interface/<lo0>/unit/<0>/family/inet/address/<10.100.100.1/32>:name: 10.100.100.1/32
interfaces/interface/<lo0>/unit/<0>/family/iso/address/<49.0001.1010.0100.0001.00>:name: 49.0001.1010.0100.0001.00
protocols/bgp/group/<EBGP-to-vMX4>:name: EBGP-to-vMX4
protocols/bgp/group/<EBGP-to-vMX4>:type: external
protocols/bgp/group/<EBGP-to-vMX4>:peer-as: '64544'
protocols/bgp/group/<EBGP-to-vMX4>/neighbor/<10.100.14.2>:name: 10.100.14.2
protocols/bgp/group/<EBGP-to-vMX4>/neighbor/<10.100.14.2>:description: to vMX4
protocols/bgp/group/<IBGP-to-vRR>:name: IBGP-to-vRR
protocols/bgp/group/<IBGP-to-vRR>:type: internal
protocols/bgp/group/<IBGP-to-vRR>:local-address: 10.100.100.1
protocols/bgp/group/<IBGP-to-vRR>:export: NHS
protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.1>:name: 10.100.150.1
protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.1>:description: to vRR1
protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.2>:name: 10.100.150.2
protocols/bgp/group/<IBGP-to-vRR>/neighbor/<10.100.150.2>:description: to vRR2

```

## Using template to configure
```
% python3 junos-templatify.py -a 10.10.10.10 -u 'username' -w 'password' -p port_num --mode-configure -t template.jinja2 -m param.yaml


```

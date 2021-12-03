from jnpr.junos import Device
from jnpr.junos.utils.config import Config 
from jnpr.junos.exception import * 
from lxml import etree
import re
import yaml
import jxmlease
import os
import sys
import jinja2
import argparse


def convert_pure_dict(xml, *args, **kwargs):
    currdepth = kwargs.pop("currdepth", 0)
    depth = kwargs.get("depth", None)
    if depth is not None and depth < currdepth:
        return {}
    # Construct a new item, recursively.
    newdict = dict()
    for (k, v) in xml.items():
        if hasattr(v, "prettyprint"):
            newdict[k] = v.prettyprint(*args, currdepth=currdepth+1,
                                        **kwargs)
        else:
            newdict[k] = v
    if currdepth == 0:
        return newdict
    else:
        return newdict

def generate_regix(path_list, key, value):

    #In case of hard to handle regex. To be develped
    if re.match('(?<=[a-zA-Z])\\-(?=[a-zA-Z])', value) or value == '::/0':
        return None

    pattern = ''

    #In case of identifier duplicate regex modification
    #(?:protocols {.+?bgp.+?group.+?\b(Duplicate).+?\b(Duplicate)(?:;|\b))
    leaf = path_list[-1]
    if re.match(r'<|>', leaf) and value==re.sub(r'<|>', '', leaf) :
        path_list.pop()
    
    if value == '': #If leaf value is '' then key is value
        path_list.pop()
        value = key

    #For meta word to escape
    value = re.escape(value)

    #Hack in case omitted "interface"
    #"interfaces" : {  "interface" : [ { "name" : "xe-1/0/0", }
    # interfaces xe-1/0/0 
    path_list = '(split)'.join(path_list).replace('interfaces(split)interface(split)', 'interfaces(split)').split('(split)')

    #Generate regex pattern in accordance to path and searching value
    #Ex. (?:protocols {.+?bgp.+?group.+?(?:IDC_BB).+?neighbor.+?\b(VALUE)(?:;|\b))
    for idx, val in enumerate(path_list):
        val = re.escape(val)
        if idx==0 and len(path_list) > 1:
            pattern = r'(?:' + val + r' {.+?'
        elif idx==0 and len(path_list) == 1:
            pattern = r'(?:' + val + r' {.+?' + val + r'.+?\b(' + value + r')(?:;|\b))'
        elif idx==len(path_list) - 1:
            pattern += val + r'.+?\b(' + value + r')(?:;|\b))'
        else:
            pattern += val + r'.+?'

    #Identifier <...> to (?:...)
    pattern = re.sub(r'<', '(?:', pattern)
    pattern = re.sub(r'>', ')', pattern)

    return pattern


def reculsive_dict_callback(**kwargs):
    obj = kwargs.get('obj')
    path = kwargs.get('path')
    callback = kwargs.get('callback')

    for k, v in obj.items():
        if isinstance(v, list):
            for i in v:
                if isinstance(i, dict):
                    if 'name' in i: 
                        nested_path = '{}/{}/<{}>'.format(path, k, i['name'])
                    else:
                        nested_path = '{}/{}'.format(path, k)
                    reculsive_dict_callback(obj=i, path=nested_path, callback=callback)
                else: 
                    callback(value=i, key=k, path=path)
        elif isinstance(v, dict):
            if 'name' in v:
                nested_path = '{}/{}/<{}>'.format(path, k, v['name'])
            else:
                nested_path = '{}/{}'.format(path, k)
            reculsive_dict_callback(obj=v, path=nested_path, callback=callback)
        else:
            callback(value=v, key=k, path=path)

def test_callback(**kwargs):
    global result_text
    global count
    global variable_template

    path = kwargs.get('path')
    value = kwargs.get('value')
    key = kwargs.get('key')

    if 'value' in kwargs and 'path' in kwargs:
        config_path = path.replace('/configuration/', '')

        identifiers = re.findall('<.+?>', config_path)
        for idx, val in enumerate(identifiers):
            config_path = config_path.replace(val, '[{}]'.format(idx))
        #print(config_path)
        path_list = re.split('/', config_path)
        for idx, val in enumerate(identifiers):
            config_path = config_path.replace('[{}]'.format(idx), val)
        #print(config_path)
        for idx, val in enumerate(path_list):
            r = re.match('\[(\d+)\]', val)
            if r is not None:
                path_list[idx] = identifiers[int(r.group(1))]
        #print(path_list)
     
        if value == '': #If leaf value is '' then key is value
            variable_template['{}:{}'.format(config_path, key)] = key
        else:
            variable_template['{}:{}'.format(config_path, key)] = value

        pattern = generate_regix(path_list, key, value)
        
        #print(pattern)
        if pattern is None: 
            return

        p = re.compile(pattern, flags=re.S)

        if p.search(result_text):
            span = p.search(result_text).span(1)

            repl_wold = r'{{ ' r'data["' + '{}:{}'.format(config_path, key) + r'"]' + r' }}'

            repl_text = result_text[:span[0]] + repl_wold + result_text[span[1]:]
            result_text = repl_text
            count += 1
        else:
            return
        

def render(full_filename, context):
    #render template(jinja2) and param(yaml)

    path, filename = os.path.split(full_filename)
    template = jinja2.Environment(
        loader=jinja2.FileSystemLoader(path or './')).get_template(filename)
    return template.render(data=context)

def config_by_template(host, port, user, passwd, template_file, param_file):
    #Try to configure to device by template(jinja2) and param(yaml)
    
    try:
        with Device(host=host, port=port, user=user, password=passwd) as dev:
            with Config(dev) as conf:
                with open(param_file) as var_file:
                    data = yaml.load(var_file, Loader=yaml.FullLoader)
                    rendered_conf= render(template_file, data)

                conf.load(rendered_conf, format="text", merge=True)
                diff = conf.diff()

                if diff is None:
                    print("Configuration is up to date.") 
                else:
                    print("Config diff to be committed on device:") 
                    print(diff)
                    conf.commit(timeout=360)
    except LockError:
        print("\nError applying config: configuration was locked!")
    except ConnectRefusedError:
        print("\nError: Device connection refused!")
    except ConnectTimeoutError:
        print("\nError: Device connection timed out!")
    except ConnectAuthError:
        print("\nError: Authentication failure!")
    except ConfigLoadError as ex: 
        print("\nError: " + str(ex))
    else:
        if diff is not None:
            print("Config committed successfully!")
    
def generate_template(host, port, user, passwd, pathlist, templatefile, paramfile):
    #Generate templated jinja2 text configuration file and yaml file for variable
    #Created by flexible pathlist from user defined
    #['configuration/interfaces/interface', 'policy-options/policy-statement', 'configuration/protocols/ospf3', 'protocols/bgp/group']

    template_file = templatefile or 'template.jinja2'
    param_file = paramfile or 'param.yaml'

    print(('Templatify target to PATHLIST {}').format(pathlist))

    print('Connecting device..')
    with Device(host=host, port=port, user=user, password=passwd) as dev:
        print('Getting configuration..')
        xml_data = dev.rpc.get_config()
        xml = etree.tostring(xml_data, encoding='unicode')
        result = jxmlease.parse(xml)

        text_data = dev.rpc.get_config(options={'format':'text'})
        text_config = etree.tostring(text_data, encoding='unicode')
        text_config = re.sub('<configuration-text>|</configuration-text>', '', text_config)


        myparser = jxmlease.parse(xml, generator=pathlist)
        #'configuration/interfaces/interface', 'policy-options/policy-statement', 'configuration/protocols/ospf3', 'protocols/bgp/group'

        print('Parsing configuration..')
        yaml_dict = {}
        for (path, match, value) in myparser:
            pure_dict = convert_pure_dict(value)
            if 'name' in pure_dict:
                yaml_dict['{}/<{}>'.format(path, pure_dict['name'])] = pure_dict
            else:
                yaml_dict[path] = pure_dict
               
        yaml_data = yaml.dump(yaml_dict, sort_keys=False)
        yaml_load_dict = yaml.load(yaml_data, Loader=yaml.FullLoader)
        print(yaml_data)
       
        global result_text
        global count
        global variable_template
        count = 0
        result_text = text_config
        variable_template = {}
 
        print('Generating template..')
        for k, v in yaml_load_dict.items():
            reculsive_dict_callback(obj=v, path=k, callback=test_callback)
        
        yaml_variable_template = yaml.dump(variable_template, sort_keys=False)

        #with open(r'original_xml.yaml', 'w') as file:
        #    yaml.dump(yaml_dict, file, sort_keys=False)

        with open(template_file, 'w') as file:
            file.write(result_text)
            print('jinja2 template written into {}'.format(template_file))

        with open(param_file, 'w') as file:
            file.write(yaml_variable_template)
            print('yaml file written into {}'.format(param_file))
            

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--address', '-a', help='Device host address')
    parser.add_argument('--user', '-u', help='Device Username')
    parser.add_argument('--password', '-w', help='Device Password')
    parser.add_argument('--port', '-p', help='Device Port')
    parser.add_argument('--pathlist', '-l', nargs='+', help="To templatify configuration path list. For example: ['configuration/protocols/bgp/group', 'interfaces/interface']")
    parser.add_argument('--templatefile', '-t', help="output or input jinja2 template file name")
    parser.add_argument('--paramfile', '-m', help="output or input yaml param file name")

    parser.add_argument('--mode-templatify', dest='mode', action='store_true')
    parser.add_argument('--mode-configure', dest='mode', action='store_false')
    parser.set_defaults(mode=True)


    args = parser.parse_args()
    
    USER = args.user 
    PASSWD = args.password
    HOST = args.address
    PORT = args.port or 830
    PATHLIST = args.pathlist
    TEMPLATEFILE = args.templatefile
    PARAMFILE = args.paramfile
    MODE = args.mode

    #print(USER, PASSWD, HOST, PORT, PATHLIST, TEMPLATEFILE, PARAMFILE, MODE)

    if MODE is True:
        if HOST is None or USER is None or PASSWD is None or PATHLIST is None:
            print(parser.print_help())
            sys.exit(1)
        else:
            generate_template(HOST, PORT, USER, PASSWD, PATHLIST, TEMPLATEFILE, PARAMFILE)
    else:
        if HOST is None or USER is None or PASSWD is None or TEMPLATEFILE is None or PARAMFILE is None:
            print(parser.print_help())
            sys.exit(1)
        else:
            config_by_template(HOST, PORT, USER, PASSWD, TEMPLATEFILE, PARAMFILE)

        
if __name__ == '__main__':
    main()

import sys
import json
import subprocess
import re


def get_unused_names(path):
    p = subprocess.Popen(
        ["eslint", path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    stdout_data, stderr_data = p.communicate()
    unused_names = []
    for line in stdout_data.decode().split("\n"):
        if line.endswith("no-unused-vars"):
            m = re.search(r'"(\w+)" is defined but never used', line)
            assert m
            unused_names.append(m.group(1))

    return unused_names


def parse_imports(path):
    p = subprocess.Popen(
        ["node", "parse.js", path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    )
    stdout_data, stderr_data = p.communicate()

    tree = json.loads(open("out.json").read())
    imports = []

    for e in tree["body"]:
        if e['type'] != "ImportDeclaration":
            break
        assert e['source']['type'] == 'Literal'

        source = e['source']['raw']

        local_default = None
        local_list = []

        for d in e['specifiers']:
            assert local_default is None
            if d['type'] == 'ImportDefaultSpecifier':
                assert d['local']['type'] == 'Identifier'
                local = d['local']['name']
                local_default = local
            else:
                assert d['imported']['type'] == 'Identifier'
                assert d['local']['type'] == 'Identifier'
                imported = d['imported']['name']
                local = d['local']['name']
                local_list.append((imported, local))

        assert (local_default is not None) != (local_list != [])

        if local_default is not None:
            imports.append({
                'type': 'default',
                'local': local_default,
                'source': source
            })
        else:
            imports.append({
                'type': 'non_default',
                'locals': local_list,
                'source': source
            })

    return imports


def print_import(imp):
    if imp['type'] == 'default':
        print("import {} from {};".format(
            imp['local'],
            imp['source']
        ))
    else:
        print("import {{ {} }} from {};".format(
            ", ".join([
               "{} as {}".format(imported, local) 
               if imported != local 
               else local 
               for (imported, local) in imp['locals']
            ]),
            imp['source']
        ))

            
def print_used_imports(path):
    imports = parse_imports(path)
    unused_names = get_unused_names(path)

    for imp in imports:
        if imp['type'] == 'default':
            if imp['local'] not in unused_names:
                print_import(imp)
        else:
            transformed_import = {
                'type': imp['type'],
                'locals': [
                    (imported, local)
                    for (imported, local) in imp['locals']
                    if local not in unused_names
                ],
                'source': imp['source']
            }
            if transformed_import['locals'] != []:
                print_import(imp)


if __name__ == "__main__":
    path = sys.argv[1]
    print_used_imports(path)

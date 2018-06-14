#!/usr/bin/env python3

# Evans YAML to PDDL converter
# Written by Igor Tikhonin in 2018

import sys, getopt
import yaml
import pprint
from boolparser import *

def usage ():
    print ('evyml2pddl.py [-h | --help] [-o <outputfile> | --output=<outputfile>] input_file.yml')

def btree_to_pddl (root):
    left, right = None, None
    if 'left' in root:
        left = btree_to_pddl(root['left'])
    if 'right' in root:
        right = btree_to_pddl(root['right'])
    if 'left' not in root and 'right' not in root:
        return root['value']
    if left != None and right != None:
        if root['tokenType'] == TokenType.EQ:  # only simple comparisons are supported for now
            var = left
            cmp = right
            if root['left']['tokenType'] != TokenType.VAR:
                var = right
                cmp = left
            if cmp.lower() == 'true':
                cmp = None
            elif cmp.lower() == 'false':
                var = 'not (' + var + ')'
            else:
                cmp = cmp[1:-1]  # strp quotes
            if cmp != None:
                var = var + '_' + cmp
            return var
    else:
        raise Exception("Complex logical expressions not implemented yet.")

def main (argv):
# Parse options
    try:
        opts, args = getopt.getopt(argv, "ho:", ["help", "output="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    output = None
    input = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
    if len(args) == 1:
        input = args[0]
    else:
        usage()
        sys.exit()
# Read YAML file
    with open(input, 'r') as stream:
        try:
            code = yaml.load(stream)
            domain = ['(define (domain MINE)', '(:requirements :adl)']
            types = ['(types: ']
            predicates = ['(:predicates']
            actions = []
            # pddl_predicates = {}
            derived_predicates = {}
            if not 'classes' in code:
                raise Exception("SYNTAX ERROR: no 'classes' section found in source file.")
            for cl_nm, cl_def in code['classes'].items():
                types.append(cl_nm)
                if not 'state' in cl_def:
                    continue
                for st_nm, st_def in cl_def['state'].items():
                    # state variables are translated into PDDL predicates
                    if st_nm == 'vars':
                        for var_nm, var_def in st_def.items():
                            if isinstance(var_def, str) and var_def == 'Boolean':
                                prd_name = '_'.join([cl_nm, var_nm])
                                predicates.append('(' + prd_name + ' ?this - ' + cl_nm + ')')
                                # pddl_predicates[prd_name] = {'this': cl_nm}
                            elif isinstance(var_def, list):
                                for var_state in var_def:
                                    prd_name = '_'.join([cl_nm, var_nm, var_state])
                                    predicates.append('(' + prd_name + ' ?this - ' + cl_nm + ')')
                                    # pddl_predicates[prd_name] = {'this': cl_nm}
                            else:
                                raise Exception("SYNTAX ERROR: class " + cl_nm +
                                    ", variable " + var_nm + " --- variable type is expected to be either Boolean or list")
                    # operators are translated into PDDL actions
                    elif st_nm == 'operators':
                        for op_nm, op_def in st_def.items():
                            actions.append('(:action ' + cl_nm + '_' + op_nm)
                            actions.append(':parameters (?this - ' + cl_nm)
                            if 'parameters' in op_def:
                                if not isinstance(op_def['parameters'], dict):
                                    raise Exception("SYNTAX ERROR: class " + cl_nm +
                                        ", operator " + op_nm + " --- parameters expected to be dictionary type")
                                for par_nm, par_type in op_def['parameters'].items():
                                    actions.append('?'+ par_nm + ' - ' + par_type)
                            actions.append(')')
                            if 'when' in op_def:
                                pass
                            actions.append(')')
                    # predicates are translated into inline logical expressions
                    elif st_nm == 'predicates':
                        for pr_nm, pr_def in st_def.items():
                            for st_var_nm in cl_def['state']['vars']: # here we add class name to state variables in boolean expressions
                                pr_def = pr_def.replace(st_var_nm, cl_nm + '_' + st_var_nm)
                            parsed_expr = BooleanParser(pr_def).root
                            derived_predicates['_'.join([cl_nm, pr_nm])] = btree_to_pddl(parsed_expr)
            predicates.append(')')
            types.append(')')
            body = domain + types + predicates + actions
            body.append(')')
            print('\n'.join(body))
            # print('=== PDDL predicates ===')
            # pprint.pprint (pddl_predicates)
            print('=== Derived predicates ===')
            pprint.pprint (derived_predicates)
        except yaml.YAMLError as exc:
            print(exc)
            sys.exit(2)

if __name__ == "__main__":
    main(sys.argv[1:])

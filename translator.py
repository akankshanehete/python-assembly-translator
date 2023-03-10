import argparse
import ast
from visitors.GlobalVariables import GlobalVariableExtraction
from visitors.LocalVariables import LocalVariableExtraction
from visitors.TopLevelProgram import TopLevelProgram
from visitors.FunctionVisitor import FunctionVisitor
from generators.StaticMemoryAllocation import StaticMemoryAllocation
from generators.LocalMemoryAllocation import LocalMemoryAllocation
from generators.EntryPoint import EntryPoint
from generators.FuncEntryPoint import FuncEntryPoint

def main():
    input_file, print_ast = process_cli()
    with open(input_file) as f:
        source = f.read()
    node = ast.parse(source)
    if print_ast:
        print(ast.dump(node, indent=2))
    else:
        process(input_file, node)
    
def process_cli():
    """"Process Command Line Interface options"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', help='filename to compile (.py)')
    parser.add_argument('--ast-only', default=False, action='store_true')
    args = vars(parser.parse_args())
    return args['f'], args['ast_only']

def process(input_file, root_node):
    print(f'; Translating {input_file}')
    extractor = GlobalVariableExtraction()
    extractor.visit(root_node)
    memory_alloc = StaticMemoryAllocation(extractor.results)
    print('; Branching to top level (tl) instructions')
    print('\t\tBR tl')
    memory_alloc.generate()
    all_locals = [] # storing all local variables so that TopLevelProgram has a copy of all local vars
    top_level = TopLevelProgram('tl')
    for s in range(len(root_node.body)):
        if isinstance(root_node.body[s], ast.FunctionDef):
                local_ext = LocalVariableExtraction(extractor.results)
                local_ext.visit(root_node.body[s])
                all_locals.append(local_ext.results)
    top_level.set_local_vars(all_locals)

    top_level.visit(root_node)
    ep = EntryPoint(top_level.finalize())
    for s in root_node.body:
            if isinstance(s, ast.FunctionDef):
                func_process(s,extractor.results)
    ep.generate() 

def func_process(funcdef_node, global_vars):
    print(f'; ***** {funcdef_node.name} function definition')
    extractor = LocalVariableExtraction(global_vars)
    extractor.visit(funcdef_node)
    memory_alloc = LocalMemoryAllocation(extractor.results)
    memory_alloc.generate()
    func_level = FunctionVisitor(f'{funcdef_node.name}',extractor)
    func_level.visit(funcdef_node)
    ep_func = FuncEntryPoint(func_level.finalize())
    ep_func.generate()
    
if __name__ == '__main__':
    main()

from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import ModuleDef, Decl, Parameter

with open('input/sample_fsm.v', 'r') as f:
    code = f.read()

parser = VerilogParser()
ast = parser.parse(code, debug=0)

print("Looking for parameters...")
for definition in ast.description.definitions:
    if isinstance(definition, ModuleDef):
        for item in definition.items:
            if isinstance(item, Decl):
                print(f"Decl list length: {len(item.list)}")
                for decl_item in item.list:
                    print(f"  Decl item type: {type(decl_item).__name__}")
                    if isinstance(decl_item, Parameter):
                        print(f"    Parameter name: {decl_item.name}")
                        print(f"    Parameter value: {decl_item.value}")
                    elif hasattr(decl_item, 'name'):
                        print(f"    Name: {decl_item.name}")
                    if hasattr(decl_item, '__dict__'):
                        print(f"    Attributes: {list(decl_item.__dict__.keys())}")

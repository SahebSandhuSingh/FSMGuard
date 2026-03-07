from pyverilog.vparser.parser import VerilogParser
from pyverilog.vparser.ast import ModuleDef, Parameter, Localparam, Decl

with open('input/sample_fsm.v', 'r') as f:
    code = f.read()

parser = VerilogParser()
ast = parser.parse(code, debug=0)

print("Looking for parameters...")
for definition in ast.description.definitions:
    if isinstance(definition, ModuleDef):
        print(f"Module: {definition.name}")
        for idx, item in enumerate(definition.items):
            item_type = type(item).__name__
            print(f"  Item {idx}: {item_type}")
            
            if isinstance(item, Decl):
                print(f"    Decl has {len(item.list)} items")
                for decl_item in item.list:
                    decl_type = type(decl_item).__name__
                    print(f"      {decl_type}: {decl_item.name if hasattr(decl_item, 'name') else 'no name'}")

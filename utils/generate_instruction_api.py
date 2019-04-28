import json
import sys

enums = json.load(open(sys.argv[1]))['spv']['enum']
grammar = json.load(open(sys.argv[2]))
out_type = sys.argv[3]

extra = set([
  # Instructions we want to customize with hand-written code, e.g.
  #'MemberDecorate',
])

WordType = 'val', 'uint32_t'
WordPairType = 'val', 'std::pair<uint32_t, uint32_t>'
StringType = 'str', 'const char *'

# map operand types to C++ types
typemap = dict(
  IdResultType=WordType,
  IdResult=WordType,
  IdRef=WordType,
  IdScope=WordType,
  IdMemorySemantics=WordType,

  PairIdRefIdRef=WordPairType,
  PairLiteralIntegerIdRef=WordPairType,
  PairIdRefLiteralInteger=WordPairType,

  LiteralString=StringType,
  LiteralInteger=WordType,
  # TODO(fjhenigman): check these types
  LiteralExtInstInteger=WordType,
  LiteralContextDependentNumber=WordType,
  LiteralSpecConstantOpInteger=WordType,
)

for i in enums:
    name = i['Name']
    if i['Type'] == 'Value':
        typemap[name] = 'val', 'Spv' + name
    elif i['Type'] == 'Bit':
        typemap[name] = 'val', 'uint32_t'

template = dict(

hpp='''
{instruction_classes}

template<typename... Args>
struct Dispatch {{
  virtual ~Dispatch() {{}}
  virtual spv_result_t do_default(const Instruction&, Args...) {{ return SPV_SUCCESS; }}
  virtual spv_result_t do_missing(const Instruction&, Args...) {{ return SPV_UNSUPPORTED; }}

  {handlers}

  spv_result_t operator()(const Instruction *i, Args... args) {{
    switch(i->c_inst().opcode) {{
      {dispatch_cases}
      default:;
    }}
    return do_missing(*i, args...);
  }}
}};
''',

cpp='''
std::shared_ptr<Instruction> Instruction::Make(const spv_parsed_instruction_t *inst) {{
  switch(inst->opcode) {{
    {make_cases}
  }}
  return nullptr;
}}
'''
)

instruction_template = '''struct {basename} : public Instruction {{
  static constexpr SpvOp Opcode = SpvOp{name};
  {basename}(const spv_parsed_instruction_t *i) : Instruction(i) {{}}
  {getters}
}};'''

getter_template = '{type} Get{opname}() const {{ return get{getter}({pos}); }}'

handler_template = 'virtual spv_result_t do_{name}(const {classname} &i, Args... args) {{ return do_default(i, args...); }}'

dispatch_case_template = 'case SpvOp{name}: return do_{name}(*i->get<{classname}>(), args...);'

make_case_template = 'case SpvOp{name}: return std::make_shared<{classname}>(inst);'

# characters to strip out of operand names
strip = {ord(i):None for i in "' "}

def make_inst(inst):
    name = inst['opname']
    assert name[:2] == 'Op'
    name = name[2:]
    classname = "I" + name
    basename = ("B" + name) if name in extra else classname
    ops = []
    for pos, op in enumerate(inst.get('operands', [])):
        opkind = op['kind']
        opname = op.get('name', opkind).translate(strip)
        getter, cpptype = typemap[opkind]
        returntype = cpptype
        if getter == 'val':
            getter = 'val<%s>' % cpptype
            returntype = cpptype
        if not opname.isalnum():
            # TODO(fjhenigman): Deal with this case more robustly.
            opname = 'OptionalImageOperands'
        quant = op.get('quantifier')
        if quant is None:
            pass
        elif quant == "*":
            getter = 'vec<%s>' % cpptype
            cpptype = 'std::vector<%s>' % cpptype
            returntype = 'const ' + cpptype
        elif quant == "?":
            pass
        else:
            assert 0, 'unexpected quantifier'
        ops.append(dict(opname=opname, getter=getter, type=returntype, pos=pos))
    return dict(name=name, basename=basename, classname=classname, ops=ops)

def fill(template, dicts):
    return '\n'.join(template.format(**i) for i in dicts)

instructions={i['name'] : i for i in map(make_inst, grammar['instructions'])}

# fix bogus op names
instructions['ExtInst'     ]['ops'][4]['opname'] = 'Operands'
instructions['TypeStruct'  ]['ops'][1]['opname'] = 'Members'
instructions['TypeOpaque'  ]['ops'][1]['opname'] = 'TypeName'
instructions['TypeFunction']['ops'][2]['opname'] = 'ParameterTypes'
instructions['FunctionCall']['ops'][3]['opname'] = 'Arguments'
instructions['SubgroupAvcImeSetDualReferenceINTEL']['ops'][4]['opname'] = 'SearchWindowConfig'

for i in instructions.values():
    i['getters'] = fill(getter_template, i['ops'])

# sort for repeatable results
sorted_inst = sorted(instructions.values(), key=lambda d:d['name'])

print(template[out_type].format(
    instruction_classes=fill(instruction_template, sorted_inst),
    handlers=fill(handler_template, sorted_inst),
    dispatch_cases=fill(dispatch_case_template, sorted_inst),
    make_cases=fill(make_case_template, sorted_inst),
))

from z3 import *

entities_sort, (cat, cow, rabbit, squirrel) = EnumSort('entities', ['cat', 'cow', 'rabbit', 'squirrel'])
properties_sort, (round, green, kind, rough, cold) = EnumSort('properties', ['round', 'green', 'kind', 'rough', 'cold'])
entities = [cat, cow, rabbit, squirrel]
properties = [round, green, kind, rough, cold]
sees = Function('sees', entities_sort, entities_sort, BoolSort())
eats = Function('eats', entities_sort, entities_sort, BoolSort())
needs = Function('needs', entities_sort, entities_sort, BoolSort())
has_property = Function('has_property', entities_sort, properties_sort, BoolSort())

pre_conditions = []
pre_conditions.append(eats(cat, squirrel) == True)
pre_conditions.append(sees(cat, squirrel) == True)
pre_conditions.append(eats(cow, squirrel) == True)
pre_conditions.append(sees(cow, cat) == True)
pre_conditions.append(has_property(rabbit, round) == True)
pre_conditions.append(sees(rabbit, cat) == True)
pre_conditions.append(eats(squirrel, rabbit) == True)
pre_conditions.append(has_property(squirrel, cold) == True)
pre_conditions.append(needs(squirrel, rabbit) == True)
pre_conditions.append(sees(squirrel, cat) == True)
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(sees(x, cat) == True, has_property(x, green) != True), sees(x, cow) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(has_property(rabbit, kind) == True, sees(rabbit, squirrel) == True), needs(squirrel, rabbit) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(has_property(x, rough) == True, has_property(x, cold) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(sees(x, rabbit) == True, has_property(x, round) != True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(sees(x, squirrel) == True, has_property(x, green) != True), needs(x, squirrel) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(eats(x, cow) == True, sees(x, rabbit) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(eats(x, squirrel) == True, has_property(x, rough) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(has_property(x, cold) == True, eats(x, cow) == True)))

def is_valid(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(Not(option_constraints))
    return solver.check() == unsat

def is_unsat(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(option_constraints)
    return solver.check() == unsat

def is_sat(option_constraints):
    solver = Solver()
    solver.add(pre_conditions)
    solver.add(option_constraints)
    return solver.check() == sat

def is_accurate_list(option_constraints):
    return is_valid(Or(option_constraints)) and all([is_sat(c) for c in option_constraints])

def is_exception(x):
    return not x


if is_valid(has_property(cat, round) != True): print('(A)')
if is_unsat(has_property(cat, round) != True): print('(B)')
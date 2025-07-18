from z3 import *

entities_sort, (cat, cow, rabbit, squirrel) = EnumSort('entities', ['cat', 'cow', 'rabbit', 'squirrel'])
properties_sort, (eats, sees, round, cold, needs, green, kind, rough) = EnumSort('properties', ['eats', 'sees', 'round', 'cold', 'needs', 'green', 'kind', 'rough'])
entities = [cat, cow, rabbit, squirrel]
properties = [eats, sees, round, cold, needs, green, kind, rough]
relation = Function('relation', entities_sort, properties_sort, entities_sort, BoolSort())
attribute = Function('attribute', entities_sort, properties_sort, BoolSort())

pre_conditions = []
pre_conditions.append(relation(cat, eats, squirrel) == True)
pre_conditions.append(relation(cat, sees, squirrel) == True)
pre_conditions.append(relation(cow, eats, squirrel) == True)
pre_conditions.append(relation(cow, sees, cat) == True)
pre_conditions.append(attribute(rabbit, round) == True)
pre_conditions.append(relation(rabbit, sees, cat) == True)
pre_conditions.append(relation(squirrel, eats, rabbit) == True)
pre_conditions.append(attribute(squirrel, cold) == True)
pre_conditions.append(relation(squirrel, needs, rabbit) == True)
pre_conditions.append(relation(squirrel, sees, cat) == True)
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(relation(x, sees, cat) == True, attribute(x, green) == False), relation(x, sees, cow) == True)))
pre_conditions.append(Implies(And(attribute(rabbit, kind) == True, relation(rabbit, sees, squirrel) == True), relation(squirrel, needs, rabbit) == True))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(attribute(x, rough) == True, attribute(x, cold) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, sees, rabbit) == True, attribute(x, round) == False)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(relation(x, sees, squirrel) == True, attribute(x, green) == False), relation(x, needs, squirrel) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, eats, cow) == True, relation(x, sees, rabbit) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, eats, squirrel) == True, attribute(x, rough) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(attribute(x, cold) == True, relation(x, eats, cow) == True)))

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


if is_valid(attribute(cat, round) == False): print('(A)')
if is_unsat(attribute(cat, round) == False): print('(B)')
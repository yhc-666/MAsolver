from z3 import *

entities_sort, (cat, cow, rabbit, squirrel) = EnumSort('entities', ['cat', 'cow', 'rabbit', 'squirrel'])
properties_sort, (eats, sees, is_round, is_cold, needs, is_green, is_kind, is_rough) = EnumSort('properties', ['eats', 'sees', 'is_round', 'is_cold', 'needs', 'is_green', 'is_kind', 'is_rough'])
entities = [cat, cow, rabbit, squirrel]
properties = [eats, sees, is_round, is_cold, needs, is_green, is_kind, is_rough]
relation = Function('relation', entities_sort, entities_sort, properties_sort, BoolSort())

pre_conditions = []
pre_conditions.append(relation(cat, squirrel, eats) == True)
pre_conditions.append(relation(cat, squirrel, sees) == True)
pre_conditions.append(relation(cow, squirrel, eats) == True)
pre_conditions.append(relation(cow, cat, sees) == True)
pre_conditions.append(relation(rabbit, rabbit, is_round) == True)
pre_conditions.append(relation(rabbit, cat, sees) == True)
pre_conditions.append(relation(squirrel, rabbit, eats) == True)
pre_conditions.append(relation(squirrel, squirrel, is_cold) == True)
pre_conditions.append(relation(squirrel, rabbit, needs) == True)
pre_conditions.append(relation(squirrel, cat, sees) == True)
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(relation(x, cat, sees) == True, relation(x, x, is_green) != True), relation(x, cow, sees) == True)))
pre_conditions.append(Implies(And(relation(rabbit, rabbit, is_kind) == True, relation(rabbit, squirrel, sees) == True), relation(squirrel, rabbit, needs) == True))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, x, is_rough) == True, relation(x, x, is_cold) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, rabbit, sees) == True, relation(x, x, is_round) != True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(And(relation(x, squirrel, sees) == True, relation(x, x, is_green) != True), relation(x, squirrel, needs) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, cow, eats) == True, relation(x, rabbit, sees) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, squirrel, eats) == True, relation(x, x, is_rough) == True)))
x = Const('x', entities_sort)
pre_conditions.append(ForAll([x], Implies(relation(x, x, is_cold) == True, relation(x, cow, eats) == True)))

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


if is_valid(relation(cat, cat, is_round) != True): print('(A)')
if is_unsat(relation(cat, cat, is_round) != True): print('(B)')
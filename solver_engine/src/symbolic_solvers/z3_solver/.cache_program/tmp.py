from z3 import *

objects_sort, (Anne, Charlie, Erin, Fiona) = EnumSort('objects', ['Anne', 'Charlie', 'Erin', 'Fiona'])
attributes_sort, (green, big, quiet, round, kind, nice, blue) = EnumSort('attributes', ['green', 'big', 'quiet', 'round', 'kind', 'nice', 'blue'])
objects = [Anne, Charlie, Erin, Fiona]
attributes = [green, big, quiet, round, kind, nice, blue]
has_attribute = Function('has_attribute', objects_sort, attributes_sort, BoolSort())

pre_conditions = []
pre_conditions.append(has_attribute(Anne, green) == True)
pre_conditions.append(has_attribute(Charlie, big) == True)
pre_conditions.append(has_attribute(Charlie, quiet) == True)
pre_conditions.append(has_attribute(Charlie, round) == True)
pre_conditions.append(has_attribute(Erin, green) == True)
pre_conditions.append(has_attribute(Erin, kind) == True)
pre_conditions.append(has_attribute(Erin, nice) == True)
pre_conditions.append(has_attribute(Erin, quiet) == True)
pre_conditions.append(has_attribute(Fiona, blue) == True)
pre_conditions.append(has_attribute(Fiona, kind) == True)
pre_conditions.append(has_attribute(Fiona, quiet) == True)
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, kind) == True, has_attribute(x, nice) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, round) == True, has_attribute(x, quiet) == True), has_attribute(x, blue) == True)))
pre_conditions.append(Implies(has_attribute(Charlie, kind) == True, has_attribute(Charlie, big) == True))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, big) == True, has_attribute(x, blue) == True), has_attribute(x, kind) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, nice) == True, has_attribute(x, quiet) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, quiet) == True, has_attribute(x, kind) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, big) == True, has_attribute(x, kind) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, green) == True, has_attribute(x, big) == True)))
pre_conditions.append(Implies(has_attribute(Anne, green) == True, has_attribute(Anne, round) == True))

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


if is_valid(has_attribute(Erin, blue) == False): print('(A)')
if is_unsat(has_attribute(Erin, blue) == False): print('(B)')
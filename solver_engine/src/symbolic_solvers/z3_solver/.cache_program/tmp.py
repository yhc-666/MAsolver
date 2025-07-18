from z3 import *

objects_sort, (Anne, Charlie, Erin, Fiona) = EnumSort('objects', ['Anne', 'Charlie', 'Erin', 'Fiona'])
attributes_sort, (kind, big, green, white, quiet, red, rough) = EnumSort('attributes', ['kind', 'big', 'green', 'white', 'quiet', 'red', 'rough'])
objects = [Anne, Charlie, Erin, Fiona]
attributes = [kind, big, green, white, quiet, red, rough]
has_attribute = Function('has_attribute', objects_sort, attributes_sort, BoolSort())

pre_conditions = []
pre_conditions.append(has_attribute(Anne, kind) == True)
pre_conditions.append(has_attribute(Charlie, big) == False)
pre_conditions.append(has_attribute(Charlie, green) == False)
pre_conditions.append(has_attribute(Charlie, white) == True)
pre_conditions.append(has_attribute(Erin, big) == True)
pre_conditions.append(has_attribute(Erin, green) == True)
pre_conditions.append(has_attribute(Erin, white) == True)
pre_conditions.append(has_attribute(Fiona, green) == True)
pre_conditions.append(has_attribute(Fiona, kind) == True)
pre_conditions.append(has_attribute(Fiona, quiet) == True)
pre_conditions.append(has_attribute(Fiona, red) == True)
pre_conditions.append(has_attribute(Fiona, white) == True)
pre_conditions.append(Implies(And(has_attribute(Erin, big) == True, has_attribute(Erin, red) == True), has_attribute(Erin, kind) == True))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, rough) == True, has_attribute(x, green) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, kind) == True, has_attribute(x, green) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, quiet) == True, has_attribute(x, green) == True), has_attribute(x, big) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, rough) == True, has_attribute(x, green) == True), has_attribute(x, red) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, green) == True, has_attribute(x, rough) == True)))
pre_conditions.append(Implies(has_attribute(Erin, red) == True, has_attribute(Erin, green) == True))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, red) == True, has_attribute(x, rough) == True), has_attribute(x, quiet) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, quiet) == True, has_attribute(x, red) == False), has_attribute(x, white) == False)))

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


if is_valid(has_attribute(Anne, white) == True): print('(A)')
if is_unsat(has_attribute(Anne, white) == True): print('(B)')
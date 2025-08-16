from z3 import *

objects_sort, (Charlie, Dave, Erin, Harry) = EnumSort('objects', ['Charlie', 'Dave', 'Erin', 'Harry'])
attributes_sort, (green, quiet, red, white, big, cold, blue) = EnumSort('attributes', ['green', 'quiet', 'red', 'white', 'big', 'cold', 'blue'])
objects = [Charlie, Dave, Erin, Harry]
attributes = [green, quiet, red, white, big, cold, blue]
has_attribute = Function('has_attribute', objects_sort, attributes_sort, BoolSort())

pre_conditions = []
pre_conditions.append(has_attribute(Charlie, green) == True)
pre_conditions.append(has_attribute(Dave, quiet) == True)
pre_conditions.append(has_attribute(Dave, red) == True)
pre_conditions.append(has_attribute(Dave, white) == False)
pre_conditions.append(has_attribute(Erin, big) == False)
pre_conditions.append(has_attribute(Erin, cold) == False)
pre_conditions.append(has_attribute(Erin, green) == True)
pre_conditions.append(has_attribute(Harry, big) == True)
pre_conditions.append(has_attribute(Harry, cold) == True)
pre_conditions.append(has_attribute(Harry, green) == True)
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, red) == True, has_attribute(x, white) == False)))
pre_conditions.append(Implies(has_attribute(Charlie, quiet) == True, has_attribute(Charlie, blue) == True))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, quiet) == True, has_attribute(x, red) == True), has_attribute(x, blue) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, white) == True, has_attribute(x, cold) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, green) == True, has_attribute(x, quiet) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, blue) == True, has_attribute(x, green) == True), has_attribute(x, red) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, red) == True, has_attribute(x, white) == False), has_attribute(x, big) == True)))

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


if is_valid(has_attribute(Charlie, red) == False): print('(A)')
if is_unsat(has_attribute(Charlie, red) == False): print('(B)')
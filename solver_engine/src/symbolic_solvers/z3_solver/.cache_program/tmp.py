from z3 import *

objects_sort, (Charlie, Dave, Erin, Fiona) = EnumSort('objects', ['Charlie', 'Dave', 'Erin', 'Fiona'])
attributes_sort, (cold, young, white, nice, blue, green, round) = EnumSort('attributes', ['cold', 'young', 'white', 'nice', 'blue', 'green', 'round'])
objects = [Charlie, Dave, Erin, Fiona]
attributes = [cold, young, white, nice, blue, green, round]
has_attribute = Function('has_attribute', objects_sort, attributes_sort, BoolSort())

pre_conditions = []
pre_conditions.append(has_attribute(Charlie, cold) == True)
pre_conditions.append(has_attribute(Charlie, young) == True)
pre_conditions.append(has_attribute(Dave, cold) == True)
pre_conditions.append(has_attribute(Erin, white) == True)
pre_conditions.append(has_attribute(Fiona, nice) == True)
pre_conditions.append(has_attribute(Fiona, white) == True)
pre_conditions.append(has_attribute(Fiona, young) == True)
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, blue) == True, has_attribute(x, white) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, nice) == True, has_attribute(x, blue) == True), has_attribute(x, white) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, young) == True, has_attribute(x, blue) == True), has_attribute(x, green) == False)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, white) == True, has_attribute(x, nice) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, nice) == True, has_attribute(x, round) == True)))
pre_conditions.append(Implies(has_attribute(Charlie, round) == True, has_attribute(Charlie, white) == True))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, blue) == True, has_attribute(x, young) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, cold) == True, has_attribute(x, green) == True), has_attribute(x, young) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, round) == True, has_attribute(x, blue) == True)))

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


if is_valid(has_attribute(Fiona, cold) == False): print('(A)')
if is_unsat(has_attribute(Fiona, cold) == False): print('(B)')
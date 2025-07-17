from z3 import *

objects_sort, (Ted, W) = EnumSort('objects', ['Ted', 'W'])
objects = [Ted, W]
Cow = Function('Cow', objects_sort, BoolSort())
Bovine = Function('Bovine', objects_sort, BoolSort())
Pet = Function('Pet', objects_sort, BoolSort())
Domesticated = Function('Domesticated', objects_sort, BoolSort())
Alligator = Function('Alligator', objects_sort, BoolSort())

pre_conditions = []
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(Cow(x), Bovine(x))))
x = Const('x', objects_sort)
pre_conditions.append(Exists([x], And(Pet(x), Cow(x))))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(Bovine(x), Domesticated(x))))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(Domesticated(x), Not(Alligator(x)))))
pre_conditions.append(Alligator(Ted))

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


if is_valid(Implies(Cow(Ted), Not(Pet(Ted)))): print('(A)')
if is_valid(Not(Implies(Cow(Ted), Not(Pet(Ted))))): print('(B)')
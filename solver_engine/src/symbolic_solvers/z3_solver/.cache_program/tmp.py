from z3 import *

objects_sort, (Anne, Erin, Fiona, Harry) = EnumSort('objects', ['Anne', 'Erin', 'Fiona', 'Harry'])
attributes_sort, (furry, nice, rough, white, big, round, red) = EnumSort('attributes', ['furry', 'nice', 'rough', 'white', 'big', 'round', 'red'])
objects = [Anne, Erin, Fiona, Harry]
attributes = [furry, nice, rough, white, big, round, red]
has_attribute = Function('has_attribute', objects_sort, attributes_sort, BoolSort())

pre_conditions = []
pre_conditions.append(has_attribute(Anne, furry) == True)
pre_conditions.append(has_attribute(Anne, nice) == True)
pre_conditions.append(has_attribute(Anne, rough) == True)
pre_conditions.append(has_attribute(Anne, white) == True)
pre_conditions.append(has_attribute(Erin, furry) == True)
pre_conditions.append(has_attribute(Erin, rough) == True)
pre_conditions.append(has_attribute(Erin, white) == True)
pre_conditions.append(has_attribute(Fiona, big) == True)
pre_conditions.append(has_attribute(Fiona, nice) == True)
pre_conditions.append(has_attribute(Fiona, round) == True)
pre_conditions.append(has_attribute(Harry, nice) == True)
pre_conditions.append(has_attribute(Harry, rough) == True)
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, furry) == True, has_attribute(x, white) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, red) == True, has_attribute(x, round) == True), has_attribute(x, furry) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, nice) == True, has_attribute(x, white) == True), has_attribute(x, red) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, round) == True, has_attribute(x, furry) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(has_attribute(x, rough) == True, has_attribute(x, round) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, nice) == True, has_attribute(x, red) == True), has_attribute(x, big) == True)))
x = Const('x', objects_sort)
pre_conditions.append(ForAll([x], Implies(And(has_attribute(x, round) == True, has_attribute(x, red) == True), has_attribute(x, white) == True)))

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


if is_valid(has_attribute(Erin, big) == False): print('(A)')
if is_unsat(has_attribute(Erin, big) == False): print('(B)')
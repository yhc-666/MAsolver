# rules_fc.py

from pyke import contexts, pattern, fc_rule, knowledge_base

pyke_version = '1.1.1'
compiler_version = 1

def rule1(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Quiet', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'Cold', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            engine.assert_('facts', 'Smart',
                           (rule.pattern(0).as_data(context),
                            rule.pattern(1).as_data(context),)),
            rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule2(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Red', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'Cold', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            engine.assert_('facts', 'Round',
                           (rule.pattern(0).as_data(context),
                            rule.pattern(1).as_data(context),)),
            rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule3(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Kind', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'Rough', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            engine.assert_('facts', 'Red',
                           (rule.pattern(0).as_data(context),
                            rule.pattern(1).as_data(context),)),
            rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule4(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Quiet', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        engine.assert_('facts', 'Rough',
                       (rule.pattern(0).as_data(context),
                        rule.pattern(1).as_data(context),)),
        rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule5(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Cold', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'Smart', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            engine.assert_('facts', 'Red',
                           (rule.pattern(0).as_data(context),
                            rule.pattern(1).as_data(context),)),
            rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule6(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Rough', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        engine.assert_('facts', 'Cold',
                       (rule.pattern(0).as_data(context),
                        rule.pattern(1).as_data(context),)),
        rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule7(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Red', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        engine.assert_('facts', 'Rough',
                       (rule.pattern(0).as_data(context),
                        rule.pattern(1).as_data(context),)),
        rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule8(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'Smart', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'Kind', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            engine.assert_('facts', 'Quiet',
                           (rule.pattern(0).as_data(context),
                            rule.pattern(1).as_data(context),)),
            rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def populate(engine):
  This_rule_base = engine.get_create('rules')
  
  fc_rule.fc_rule('rule1', This_rule_base, rule1,
    (('facts', 'Quiet',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'Cold',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule2', This_rule_base, rule2,
    (('facts', 'Red',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'Cold',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule3', This_rule_base, rule3,
    (('facts', 'Kind',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'Rough',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule4', This_rule_base, rule4,
    (('facts', 'Quiet',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule5', This_rule_base, rule5,
    (('facts', 'Cold',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'Smart',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule6', This_rule_base, rule6,
    (('facts', 'Rough',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule7', This_rule_base, rule7,
    (('facts', 'Red',
      (contexts.variable('x'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('x'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule8', This_rule_base, rule8,
    (('facts', 'Smart',
      (pattern.pattern_literal('Dave'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'Kind',
      (pattern.pattern_literal('Dave'),
       pattern.pattern_literal(True),),
      False),),
    (pattern.pattern_literal('Dave'),
     pattern.pattern_literal(True),))


Krb_filename = '../symbolic_solvers/pyke_solver/.cache_program/rules.krb'
Krb_lineno_map = (
    ((12, 16), (3, 3)),
    ((17, 21), (4, 4)),
    ((22, 24), (6, 6)),
    ((33, 37), (10, 10)),
    ((38, 42), (11, 11)),
    ((43, 45), (13, 13)),
    ((54, 58), (17, 17)),
    ((59, 63), (18, 18)),
    ((64, 66), (20, 20)),
    ((75, 79), (24, 24)),
    ((80, 82), (26, 26)),
    ((91, 95), (30, 30)),
    ((96, 100), (31, 31)),
    ((101, 103), (33, 33)),
    ((112, 116), (37, 37)),
    ((117, 119), (39, 39)),
    ((128, 132), (43, 43)),
    ((133, 135), (45, 45)),
    ((144, 148), (49, 49)),
    ((149, 153), (50, 50)),
    ((154, 156), (52, 52)),
)

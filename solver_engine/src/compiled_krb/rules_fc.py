# rules_fc.py

from pyke import contexts, pattern, fc_rule, knowledge_base

pyke_version = '1.1.1'
compiler_version = 1

def rule1(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'LeftOf', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        engine.assert_('facts', 'RightOf',
                       (rule.pattern(0).as_data(context),
                        rule.pattern(1).as_data(context),
                        rule.pattern(2).as_data(context),)),
        rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule2(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'RightOf', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        engine.assert_('facts', 'LeftOf',
                       (rule.pattern(0).as_data(context),
                        rule.pattern(1).as_data(context),
                        rule.pattern(2).as_data(context),)),
        rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule3(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'RightOf', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'RightOf', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            engine.assert_('facts', 'RightOf',
                           (rule.pattern(0).as_data(context),
                            rule.pattern(1).as_data(context),
                            rule.pattern(2).as_data(context),)),
            rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def rule4(rule, context = None, index = None):
  engine = rule.rule_base.engine
  if context is None: context = contexts.simple_context()
  try:
    with knowledge_base.Gen_once if index == 0 \
             else engine.lookup('facts', 'RightOf', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'RightOf', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            with knowledge_base.Gen_once if index == 2 \
                     else engine.lookup('facts', 'RightOf', context,
                                        rule.foreach_patterns(2)) \
              as gen_2:
              for dummy in gen_2:
                with knowledge_base.Gen_once if index == 3 \
                         else engine.lookup('facts', 'RightOf', context,
                                            rule.foreach_patterns(3)) \
                  as gen_3:
                  for dummy in gen_3:
                    engine.assert_('facts', 'RightMost',
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
             else engine.lookup('facts', 'RightMost', context,
                                rule.foreach_patterns(0)) \
      as gen_0:
      for dummy in gen_0:
        with knowledge_base.Gen_once if index == 1 \
                 else engine.lookup('facts', 'RightOf', context,
                                    rule.foreach_patterns(1)) \
          as gen_1:
          for dummy in gen_1:
            with knowledge_base.Gen_once if index == 2 \
                     else engine.lookup('facts', 'RightOf', context,
                                        rule.foreach_patterns(2)) \
              as gen_2:
              for dummy in gen_2:
                with knowledge_base.Gen_once if index == 3 \
                         else engine.lookup('facts', 'RightOf', context,
                                            rule.foreach_patterns(3)) \
                  as gen_3:
                  for dummy in gen_3:
                    with knowledge_base.Gen_once if index == 4 \
                             else engine.lookup('facts', 'RightOf', context,
                                                rule.foreach_patterns(4)) \
                      as gen_4:
                      for dummy in gen_4:
                        engine.assert_('facts', 'SecondFromRight',
                                       (rule.pattern(0).as_data(context),
                                        rule.pattern(1).as_data(context),)),
                        rule.rule_base.num_fc_rules_triggered += 1
  finally:
    context.done()

def populate(engine):
  This_rule_base = engine.get_create('rules')
  
  fc_rule.fc_rule('rule1', This_rule_base, rule1,
    (('facts', 'LeftOf',
      (contexts.variable('a'),
       contexts.variable('b'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('b'),
     contexts.variable('a'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule2', This_rule_base, rule2,
    (('facts', 'RightOf',
      (contexts.variable('a'),
       contexts.variable('b'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('b'),
     contexts.variable('a'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule3', This_rule_base, rule3,
    (('facts', 'RightOf',
      (contexts.variable('a'),
       contexts.variable('b'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('b'),
       contexts.variable('c'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('a'),
     contexts.variable('c'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule4', This_rule_base, rule4,
    (('facts', 'RightOf',
      (contexts.variable('b'),
       pattern.pattern_literal('white'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('b'),
       pattern.pattern_literal('orange'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('b'),
       pattern.pattern_literal('yellow'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('b'),
       pattern.pattern_literal('blue'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('b'),
     pattern.pattern_literal(True),))
  
  fc_rule.fc_rule('rule5', This_rule_base, rule5,
    (('facts', 'RightMost',
      (contexts.variable('rm'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('rm'),
       contexts.variable('s'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('s'),
       pattern.pattern_literal('white'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('s'),
       pattern.pattern_literal('orange'),
       pattern.pattern_literal(True),),
      False),
     ('facts', 'RightOf',
      (contexts.variable('s'),
       pattern.pattern_literal('yellow'),
       pattern.pattern_literal(True),),
      False),),
    (contexts.variable('s'),
     pattern.pattern_literal(True),))


Krb_filename = '../symbolic_solvers/pyke_solver/cache_program/rules.krb'
Krb_lineno_map = (
    ((12, 16), (3, 3)),
    ((17, 20), (5, 5)),
    ((29, 33), (9, 9)),
    ((34, 37), (11, 11)),
    ((46, 50), (15, 15)),
    ((51, 55), (16, 16)),
    ((56, 59), (18, 18)),
    ((68, 72), (22, 22)),
    ((73, 77), (23, 23)),
    ((78, 82), (24, 24)),
    ((83, 87), (25, 25)),
    ((88, 90), (27, 27)),
    ((99, 103), (31, 31)),
    ((104, 108), (32, 32)),
    ((109, 113), (33, 33)),
    ((114, 118), (34, 34)),
    ((119, 123), (35, 35)),
    ((124, 126), (37, 37)),
)

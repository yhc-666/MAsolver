import os
import re
import sys
from nltk.inference.prover9 import *
from nltk.sem.logic import NegatedExpression
import subprocess, shutil
import tempfile, textwrap, itertools as it

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..', '..')
sys.path.insert(0, project_root)

from src.symbolic_solvers.fol_solver.fol_prover9_parser import Prover9_FOL_Formula
from src.symbolic_solvers.fol_solver.Formula import FOL_Formula

# set the path to the prover9 executable
PROVER9_PATH = os.path.join(os.path.dirname(__file__), '..', 'Prover9', 'bin')
os.environ['PROVER9'] = PROVER9_PATH # Linux version
# os.environ['PROVER9'] = '/opt/homebrew/bin'  # macOS version installed via Homebrew


# --- helper utilities for raw prover9 interaction starts (for result with unkown)---
def _build_p9_input(assumptions: list[str], goal: str, max_seconds: int = 10) -> str:
    """Build a prover9 input string using NLTK's conversion utilities."""
    from nltk.inference.prover9 import Expression, convert_to_prover9

    ass_exprs = [Expression.fromstring(a) for a in assumptions]
    goal_expr = Expression.fromstring(goal)
    ass_strs = convert_to_prover9(ass_exprs)
    goal_str = convert_to_prover9(goal_expr)

    ass_block = "\n".join(a + "." for a in ass_strs)
    return textwrap.dedent(
        f"""
        assign(max_seconds,{max_seconds}).
        clear(auto_denials).

        formulas(assumptions).
        {ass_block}
        end_of_list.

        formulas(goals).
        {goal_str}.
        end_of_list.
    """
    )


def _run_prover9_raw(p9_input: str, timeout: int = 12) -> str:
    with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tf:
        tf.write(p9_input)
        tf.flush()
        cmd = [os.path.join(PROVER9_PATH, "prover9"), "-f", tf.name]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    os.unlink(tf.name)
    return proc.stdout


_LINE_PAT = re.compile(r"^(Derived:|kept:|given\s+#\d+|-\w|\w).*?\[.*\]")


def _clean_prefix(line: str) -> str:
    """Strip technical prefixes so duplicates are detected."""
    line = re.sub(r"^(Derived:|kept:|given\s+#\d+)\s*", "", line.strip())
    line = re.sub(r"^\d+\s+", "", line)
    return line


def _summarise_log(log: str, max_lines: int | None = None) -> str:
    seen, text_seen, selected = set(), set(), []
    mapping: dict[int, int] = {}
    key_to_index: dict[str, int] = {}
    for ln in log.splitlines():
        if ln.startswith(("Predicate symbol precedence",
                          "Function symbol precedence",
                          "given #")):
            continue
        if _LINE_PAT.match(ln):
            m = re.match(r"\s*(\d+)\s+(.*)", ln.strip())
            if m:
                orig_no, raw_output = int(m.group(1)), m.group(2)
            else:
                orig_no, raw_output = None, re.sub(r"^\d+\s+", "", ln.strip())
            if raw_output.startswith("kept:"):
                raw_output = re.sub(r"^kept:\s*\d+\s*", "kept: ", raw_output)
            dedup_key = " ".join(_clean_prefix(raw_output).split())
            text_key = _clean_prefix(raw_output).split("[", 1)[0].strip()
            if raw_output.startswith("kept:") and text_key in text_seen:
                continue
            if dedup_key not in seen:
                selected.append((orig_no, raw_output))
                idx = len(selected)
                if orig_no is not None:
                    mapping[orig_no] = idx
                seen.add(dedup_key)
                key_to_index[dedup_key] = idx
                text_seen.add(text_key)
            else:
                # duplicate line, map its original number to existing index
                if orig_no is not None and dedup_key in key_to_index:
                    mapping[orig_no] = key_to_index[dedup_key]
    if max_lines:
        selected = selected[:max_lines]
        # rebuild mapping for truncated output
        mapping = {orig: idx + 1 for idx, (orig, _) in enumerate(selected) if orig is not None}
    out = []
    for idx, (orig_no, ln) in enumerate(selected, 1):
        clause, label = ln.rsplit("[", 1)
        clause_part = re.sub(r"^\d+\s+", "", clause)
        label = re.sub(r'(?<=\(|,)\d+(?=\)|,)', lambda m: str(mapping.get(int(m.group(0)), int(m.group(0)))), '[' + label)
        out.append(f"{idx} {clause_part.strip()} {label}")
    reason = "-- Search terminated, no contradiction found --" if "sos_empty" in log else \
             "-- Timeout terminated, no contradiction found --" if "max_seconds" in log else \
             "-- Search terminated, no contradiction found --"
    return "\n".join(out) + f"\n{reason}"

# --- helper utilities for raw prover9 interaction ends ---



class FOL_Prover9_Program:
    def __init__(self, logic_program:str, dataset_name = 'FOLIO') -> None:
        self.logic_program = logic_program
        self.flag = self.parse_logic_program()
        self.dataset_name = dataset_name

    def parse_logic_program(self):
        try:        
            # Split the string into premises and conclusion
            premises_string = self.logic_program.split("Conclusion:")[0].split("Premises:")[1].strip()
            conclusion_string = self.logic_program.split("Conclusion:")[1].strip()

            # Extract each premise and the conclusion using regex
            premises = premises_string.strip().split('\n')
            conclusion = conclusion_string.strip().split('\n')

            self.logic_premises = [premise.split(':::')[0].strip() for premise in premises]
            self.logic_conclusion = conclusion[0].split(':::')[0].strip()

            # convert to prover9 format
            self.prover9_premises = []
            for premise in self.logic_premises:
                fol_rule = FOL_Formula(premise)
                if fol_rule.is_valid == False:
                    return False
                prover9_rule = Prover9_FOL_Formula(fol_rule)
                self.prover9_premises.append(prover9_rule.formula)

            fol_conclusion = FOL_Formula(self.logic_conclusion)
            if fol_conclusion.is_valid == False:
                return False
            self.prover9_conclusion = Prover9_FOL_Formula(fol_conclusion).formula
            return True
        except:
            return False

    def execute_program(self):
        try:
            goal = Expression.fromstring(self.prover9_conclusion)
            assumptions = [Expression.fromstring(a) for a in self.prover9_premises]
            timeout = 10
            #prover = Prover9()
            #result = prover.prove(goal, assumptions)
            
            prover = Prover9Command(goal, assumptions, timeout=timeout)
            result = prover.prove()
            # print(prover.proof())

            proof_trace = ''

            if result:
                # 证明成功：记录原结论的推导路径
                proof_core = self._extract_proof_steps_ture_false(prover.proof(simplify=True))
                proof_trace = 'prove original conclusion:\n' + proof_core
                return 'True', '', proof_trace
            else:
                # 证明失败，尝试证明结论的否定
                proof_trace += 'prove original conclusion:\n' + prover.proof(simplify=False) + '\n'

                negated_goal = NegatedExpression(goal)
                prover_neg = Prover9Command(negated_goal, assumptions, timeout=timeout)
                negation_result = prover_neg.prove()

                if negation_result:
                    # 证明否定成功 => 原结论为 False，只输出成功证明路径
                    proof_core = self._extract_proof_steps_ture_false(prover_neg.proof(simplify=True))
                    proof_trace = 'prove negation of original conclusion:\n' + proof_core
                    return 'False', '', proof_trace
                else:
                    # 两次证明都失败，结论未知 → 调命令行版抓完整日志
                    orig_in  = _build_p9_input(self.prover9_premises, self.prover9_conclusion)
                    orig_log = _run_prover9_raw(orig_in, timeout=timeout+2)
                    orig_tr  = _summarise_log(orig_log)

                    neg_goal = f"-({self.prover9_conclusion})"
                    neg_in   = _build_p9_input(self.prover9_premises, neg_goal)
                    neg_log  = _run_prover9_raw(neg_in, timeout=timeout+2)
                    neg_tr   = _summarise_log(neg_log)

                    proof_trace = (f"trying to prove original conclusion:\n{orig_tr}\n\n"
                                   f"trying to prove negation of original conclusion:\n{neg_tr}\n\n"
                                   f"So: Unknown")
                    return 'Unknown', '', proof_trace
        except Exception as e:
            return None, str(e), '' 
        
    def answer_mapping(self, answer):
        if answer == 'True':
            return 'A'
        elif answer == 'False':
            return 'B'
        elif answer == 'Unknown':
            return 'C'
        else:
            raise Exception("Answer not recognized")
        
    @staticmethod
    def _extract_proof_steps_ture_false(proof_str: str) -> str:
        """Extract only the numbered step lines from a Prover9 proof output.

        Prover9 proof outputs often contain headers, footers, and comments in
        addition to the essential step lines that begin with an integer index.
        This helper keeps only lines that start with digits (optionally
        preceded by whitespace), which correspond to the step annotations we
        are interested in displaying.
        """
        step_lines = []
        for line in proof_str.splitlines():
            if re.match(r"^\s*\d+", line):
                step_lines.append(line)
        return "\n".join(step_lines)

if __name__ == "__main__":
    ## ¬∀x (Movie(x) → HappyEnding(x))
    ## ∃x (Movie(x) → ¬HappyEnding(x))
    # ground-truth: True
    logic_program_t = """Premises:
    ¬∀x (Movie(x) → HappyEnding(x)) ::: Not all movie has a happy ending.
    Movie(titanic) ::: Titanic is a movie.
    ¬HappyEnding(titanic) ::: Titanic does not have a happy ending.
    Movie(lionKing) ::: Lion King is a movie.
    HappyEnding(lionKing) ::: Lion King has a happy ending.
    Conclusion:
    ∃x (Movie(x) ∧ ¬HappyEnding(x)) ::: Some movie does not have a happy ending.
    """

    # ground-truth: True
    logic_program = """Premises:
    ∀x (Drinks(x) → Dependent(x)) ::: All people who regularly drink coffee are dependent on caffeine.
    ∀x (Drinks(x) ⊕ Jokes(x)) ::: People either regularly drink coffee or joke about being addicted to caffeine.
    ∀x (Jokes(x) → ¬Unaware(x)) ::: No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. 
    (Student(rina) ∧ Unaware(rina)) ⊕ ¬(Student(rina) ∨ Unaware(rina)) ::: Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. 
    ¬(Dependent(rina) ∧ Student(rina)) → (Dependent(rina) ∧ Student(rina)) ⊕ ¬(Dependent(rina) ∨ Student(rina)) ::: If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
    Conclusion:
    Jokes(rina) ⊕ Unaware(rina) ::: Rina is either a person who jokes about being addicted to caffeine or is unaware that caffeine is a drug.
    """

    # ground-truth: True
    logic_program = """Premises:
    ∀x (Drinks(x) → Dependent(x)) ::: All people who regularly drink coffee are dependent on caffeine.
    ∀x (Drinks(x) ⊕ Jokes(x)) ::: People either regularly drink coffee or joke about being addicted to caffeine.
    ∀x (Jokes(x) → ¬Unaware(x)) ::: No one who jokes about being addicted to caffeine is unaware that caffeine is a drug. 
    (Student(rina) ∧ Unaware(rina)) ⊕ ¬(Student(rina) ∨ Unaware(rina)) ::: Rina is either a student and unaware that caffeine is a drug, or neither a student nor unaware that caffeine is a drug. 
    ¬(Dependent(rina) ∧ Student(rina)) → (Dependent(rina) ∧ Student(rina)) ⊕ ¬(Dependent(rina) ∨ Student(rina)) ::: If Rina is not a person dependent on caffeine and a student, then Rina is either a person dependent on caffeine and a student, or neither a person dependent on caffeine nor a student.
    Conclusion:
    ((Jokes(rina) ∧ Unaware(rina)) ⊕ ¬(Jokes(rina) ∨ Unaware(rina))) → (Jokes(rina) ∧ Drinks(rina)) ::: If Rina is either a person who jokes about being addicted to caffeine and a person who is unaware that caffeine is a drug, or neither a person who jokes about being addicted to caffeine nor a person who is unaware that caffeine is a drug, then Rina jokes about being addicted to caffeine and regularly drinks coffee.
    """

    # ground-truth: Unknown
    logic_program = """Premises:
    Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
    ∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
    ∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
    Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
    Conclusion:
    Love(miroslav, music) ::: Miroslav Venhoda loved music.
    """

    # ground-truth: True
    logic_program = """Premises:
    Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
    ∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
    ∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
    Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
    Conclusion:
    ∃y ∃x (Czech(x) ∧ Author(x, y) ∧ Book(y) ∧ Publish(y, year1946)) ::: A Czech person wrote a book in 1946.
    """

    # ground-truth: False
    logic_program_f = """Premises:
    Czech(miroslav) ∧ ChoralConductor(miroslav) ∧ Specialize(miroslav, renaissance) ∧ Specialize(miroslav, baroque) ::: Miroslav Venhoda was a Czech choral conductor who specialized in the performance of Renaissance and Baroque music.
    ∀x (ChoralConductor(x) → Musician(x)) ::: Any choral conductor is a musician.
    ∃x (Musician(x) ∧ Love(x, music)) ::: Some musicians love music.
    Book(methodOfStudyingGregorianChant) ∧ Author(miroslav, methodOfStudyingGregorianChant) ∧ Publish(methodOfStudyingGregorianChant, year1946) ::: Miroslav Venhoda published a book in 1946 called Method of Studying Gregorian Chant.
    Conclusion:
    ¬∃x (ChoralConductor(x) ∧ Specialize(x, renaissance)) ::: No choral conductor specialized in the performance of Renaissance.
    """

    # ground-truth: Unknown
    # Premises:\nall x.(perform_in_school_talent_shows_often(x) -> (attend_school_events(x) & very_engaged_with_school_events(x))) ::: If people perform in school talent shows often, then they attend and are very engaged with school events.\nall x.(perform_in_school_talent_shows_often(x) ^ (inactive_member(x) & disinterested_member(x))) ::: People either perform in school talent shows often or are inactive and disinterested members of their community.\nall x.(chaperone_high_school_dances(x) -> not student_attend_school(x)) ::: If people chaperone high school dances, then they are not students who attend the school.\nall x.((inactive_member(x) & disinterested_member(x)) -> chaperone_high_school_dances(x)) ::: All people who are inactive and disinterested members of their community chaperone high school dances.\nall x.((young_child(x) | teenager(x)) & wish_to_further_academic_careers(x) & wish_to_further_educational_opportunities(x) -> student_attend_school(x)) ::: All young children and teenagers who wish to further their academic careers and educational opportunities are students who attend the school.\n(attend_school_events(bonnie) & very_engaged_with_school_events(bonnie) & student_attend_school(bonnie)) ^ (not attend_school_events(bonnie) & not very_engaged_with_school_events(bonnie) & not student_attend_school(bonnie)) ::: Bonnie either both attends and is very engaged with school events and is a student who attends the school, or she neither attends and is very engaged with school events nor is a student who attends the school.\nConclusion:\nperform_in_school_talent_shows_often(bonnie) ::: Bonnie performs in school talent shows often."
    logic_program = """Premises:
    ∀x (TalentShows(x) → Engaged(x)) ::: If people perform in school talent shows often, then they attend and are very engaged with school events.
    ∀x (TalentShows(x) ∨ Inactive(x)) ::: People either perform in school talent shows often or are inactive and disinterested members of their community.
    ∀x (Chaperone(x) → ¬Students(x)) ::: If people chaperone high school dances, then they are not students who attend the school.
    ∀x (Inactive(x) → Chaperone(x)) ::: All people who are inactive and disinterested members of their community chaperone high school dances.
    ∀x (AcademicCareer(x) → Students(x)) ::: All young children and teenagers who wish to further their academic careers and educational opportunities are students who attend the school.
    Conclusion:
    TalentShows(bonnie) ::: Bonnie performs in school talent shows often.
    """

    # ground-truth: False
    logic_program_u = """Premises:
    MusicPiece(symphonyNo9) ::: Symphony No. 9 is a music piece.
    ∀x ∃z (¬Composer(x) ∨ (Write(x,z) ∧ MusicPiece(z))) ::: Composers write music pieces.
    Write(beethoven, symphonyNo9) ::: Beethoven wrote Symphony No. 9.
    Lead(beethoven, viennaMusicSociety) ∧ Orchestra(viennaMusicSociety) ::: Vienna Music Society is an orchestra and Beethoven leads the Vienna Music Society.
    ∀x ∃z (¬Orchestra(x) ∨ (Lead(z,x) ∧ Conductor(z))) ::: Orchestras are led by conductors.
    Conclusion:
    ¬Conductor(beethoven) ::: Beethoven is not a conductor."""

    # ground-truth: True
    logic_program = """Predicates:
    JapaneseCompany(x) ::: x is a Japanese game company.
    Create(x, y) ::: x created the game y.
    Top10(x) ::: x is in the Top 10 list.
    Sell(x, y) ::: x sold more than y copies.
    Premises:
    ∃x (JapaneseCompany(x) ∧ Create(x, legendOfZelda)) ::: A Japanese game company created the game the Legend of Zelda.
    ∀x ∃z (¬Top10(x) ∨ (JapaneseCompany(z) ∧ Create(z,x))) ::: All games in the Top 10 list are made by Japanese game companies.
    ∀x (Sell(x, oneMillion) → Top10(x)) ::: If a game sells more than one million copies, then it will be selected into the Top 10 list.
    Sell(legendOfZelda, oneMillion) ::: The Legend of Zelda sold more than one million copies.
    Conclusion:
    Top10(legendOfZelda) ::: The Legend of Zelda is in the Top 10 list."""

    logic_program = """Premises:
    ∀x (Listed(x) → ¬NegativeReviews(x)) ::: If the restaurant is listed in Yelp's recommendations, then the restaurant does not receive many negative reviews.
    ∀x (GreaterThanNine(x) → Listed(x)) ::: All restaurants with a rating greater than 9 are listed in Yelp's recommendations.
    ∃x (¬TakeOut(x) ∧ NegativeReviews(x)) ::: Some restaurants that do not provide take-out service receive many negative reviews.
    ∀x (Popular(x) → GreaterThanNine(x)) ::: All restaurants that are popular among local residents have ratings greater than 9.
    GreaterThanNine(subway) ∨ Popular(subway) ::: Subway has a rating greater than 9 or is popular among local residents.
    Conclusion:
    TakeOut(subway) ∧ ¬NegativeReviews(subway) ::: Subway provides take-out service and does not receive many negative reviews."""
    
    logic_program_byfx = "Premises:\nCold(bob) ::: Bob is cold.\nQuiet(bob) ::: Bob is quiet.\nRed(bob) ::: Bob is red.\nSmart(bob) ::: Bob is smart.\nKind(charlie) ::: Charlie is kind.\nQuiet(charlie) ::: Charlie is quiet.\nRed(charlie) ::: Charlie is red.\nRough(charlie) ::: Charlie is rough.\nCold(dave) ::: Dave is cold.\nKind(dave) ::: Dave is kind.\nSmart(dave) ::: Dave is smart.\nQuiet(fiona) ::: Fiona is quiet.\n∀x (Quiet(x) ∧ Cold(x) → Smart(x)) ::: If something is quiet and cold then it is smart.\n∀x (Red(x) ∧ Cold(x) → Round(x)) ::: Red, cold things are round.\n∀x (Kind(x) ∧ Rough(x) → Red(x)) ::: If something is kind and rough then it is red.\n∀x (Quiet(x) → Rough(x)) ::: All quiet things are rough.\n∀x (Cold(x) ∧ Smart(x) → Red(x)) ::: Cold, smart things are red.\n∀x (Rough(x) → Cold(x)) ::: If something is rough then it is cold.\n∀x (Red(x) → Rough(x)) ::: All red things are rough.\n(Smart(dave) ∧ Kind(dave)) → Quiet(dave) ::: If Dave is smart and Dave is kind then Dave is quiet.\nConclusion:\nKind(charlie) ::: Charlie is kind."
    # ground-truth: True
    prover9_program = FOL_Prover9_Program(logic_program_byfx)
    result, error_message, reasoning = prover9_program.execute_program()
    print('result:', result)
    print('reasoning:', reasoning)

    
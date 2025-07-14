# Utility to pretty print Z3 proof S-expressions with comments for LET abbreviations
import re
from collections import deque
from typing import Dict, Iterable


def tokens(sexpr: str) -> Iterable[str]:
    """Yield tokens from S-expression string."""
    buf = ''
    for ch in sexpr:
        if ch in '()':
            if buf.strip():
                yield buf.strip()
            yield ch
            buf = ''
        elif ch in '\r\n\t':
            buf += ' '
        else:
            buf += ch
    if buf.strip():
        yield buf.strip()


def collect_let_abbrevs(sexpr: str, max_summary: int = 80) -> Dict[str, str]:
    """Return mapping from a!1 / pb!123 to a short summary of its definition."""
    abbrev: Dict[str, str] = {}
    toks = deque(tokens(sexpr))
    while toks:
        tok = toks.popleft()
        if tok == '(' and toks and toks[0] == 'let':
            toks.popleft()  # consume 'let'
            if not toks or toks.popleft() != '(':  # opening '('
                break
            while toks and toks[0] == '(':  # each binding
                toks.popleft()  # '('
                if not toks:
                    break
                name = toks.popleft()
                depth = 0
                parts = []
                while toks:
                    t = toks.popleft()
                    if t == '(':
                        depth += 1
                    elif t == ')':
                        if depth == 0:
                            break
                        depth -= 1
                    parts.append(t)
                summary = ' '.join(parts)[:max_summary].strip()
                abbrev[name] = summary
                # consume closing ')' of binding already
            # remainder ignored
    return abbrev


def pretty_sexpr_with_comments(sexpr: str, indent: int = 2, abbrev_comment: bool = True) -> str:
    """Pretty print S-expression with indentation and inline abbrev comments."""
    abbrev = collect_let_abbrevs(sexpr)
    out = []
    depth = 0
    for tok in tokens(sexpr):
        if tok == '(':
            out.append(' ' * indent * depth + '(')
            depth += 1
        elif tok == ')':
            depth -= 1
            out.append(' ' * indent * depth + ')')
        else:
            s = tok
            if abbrev_comment and tok in abbrev:
                s += f'  ;; {abbrev[tok]}'
            out.append(' ' * indent * depth + s)
    return '\n'.join(out)

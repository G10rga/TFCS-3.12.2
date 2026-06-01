from itertools import combinations
from typing import List, Dict, FrozenSet


def tokenize(raw: str):
    s = raw.replace('¬', '~').replace('∧', '&').replace('∨', '|').replace('→', '->').replace('↔', '<->')
    i = 0
    while i < len(s):
        if s[i].isspace():
            i += 1
        elif s[i:i + 3] == '<->':
            yield 'IFF', '<->'
            i += 3
        elif s[i:i + 2] == '->':
            yield 'IMP', '->'
            i += 2
        elif s[i] == '(':
            yield 'LP', '('
            i += 1
        elif s[i] == ')':
            yield 'RP', ')'
            i += 1
        elif s[i] == '~':
            yield 'NOT', '~'
            i += 1
        elif s[i] == '&':
            yield 'AND', '&'
            i += 1
        elif s[i] == '|':
            yield 'OR', '|'
            i += 1
        elif s[i].isalpha() or s[i] == '_':
            j = i
            while j < len(s) and (s[j].isalnum() or s[j] == '_'):
                j += 1
            yield 'VAR', s[i:j]
            i = j
        else:
            raise ValueError(f"Unknown character: '{s[i]}'")
    yield 'EOF', ''


# Parser

class Parser:
    def __init__(self, raw):
        self.tokens = list(tokenize(raw))
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos][0]

    def eat(self):
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def parse(self):
        node = self.iff()
        if self.peek() != 'EOF': raise ValueError("Unexpected token")
        return node

    def iff(self):
        l = self.imp()
        while self.peek() == 'IFF': self.eat(); l = ('IFF', l, self.imp())
        return l

    def imp(self):
        l = self.oor()
        while self.peek() == 'IMP': self.eat(); l = ('IMP', l, self.oor())
        return l

    def oor(self):
        l = self.aand()
        while self.peek() == 'OR':  self.eat(); l = ('OR', l, self.aand())
        return l

    def aand(self):
        l = self.neg()
        while self.peek() == 'AND': self.eat(); l = ('AND', l, self.neg())
        return l

    def neg(self):
        if self.peek() == 'NOT': self.eat(); return ('NOT', self.neg())
        return self.atom()

    def atom(self):
        k, v = self.eat()
        if k == 'VAR': return ('VAR', v)
        if k == 'LP':
            node = self.iff()
            if self.peek() != 'RP': raise ValueError("Missing ')'")
            self.eat()
            return node
        raise ValueError(f"Unexpected token: {k} {v!r}")


def parse_formula(s: str): return Parser(s).parse()


# AST to string

def ast_to_str(n, p=0) -> str:
    prec = {'IFF': 1, 'IMP': 2, 'OR': 3, 'AND': 4, 'NOT': 5, 'VAR': 6}
    k = n[0]
    if k == 'VAR': return n[1]
    if k == 'NOT': return '¬' + ast_to_str(n[1], prec['NOT'])
    if k == 'AND':
        s = f"{ast_to_str(n[1], prec['AND'])} ∧ {ast_to_str(n[2], prec['AND'])}"
        return f"({s})" if p > prec['AND'] else s
    if k == 'OR':
        s = f"{ast_to_str(n[1], prec['OR'])} ∨ {ast_to_str(n[2], prec['OR'])}"
        return f"({s})" if p > prec['OR'] else s
    if k == 'IMP': return f"({ast_to_str(n[1])} → {ast_to_str(n[2])})"
    if k == 'IFF': return f"({ast_to_str(n[1])} ↔ {ast_to_str(n[2])})"
    return None


# Normal form transformations

def eliminate_iff(n):
    k = n[0]
    if k == 'VAR': return n
    if k == 'NOT': return ('NOT', eliminate_iff(n[1]))
    if k in ('AND', 'OR', 'IMP'): return (k, eliminate_iff(n[1]), eliminate_iff(n[2]))
    if k == 'IFF':
        p, q = eliminate_iff(n[1]), eliminate_iff(n[2])
        return ('AND', ('IMP', p, q), ('IMP', q, p))


def eliminate_imp(n):
    k = n[0]
    if k == 'VAR': return n
    if k == 'NOT': return ('NOT', eliminate_imp(n[1]))
    if k in ('AND', 'OR'): return (k, eliminate_imp(n[1]), eliminate_imp(n[2]))
    if k == 'IMP':
        return ('OR', ('NOT', eliminate_imp(n[1])), eliminate_imp(n[2]))


def push_negation(n):
    k = n[0]
    if k == 'VAR': return n
    if k in ('AND', 'OR'): return (k, push_negation(n[1]), push_negation(n[2]))
    if k == 'NOT':
        inner = n[1]
        ik = inner[0]
        if ik == 'VAR': return n
        if ik == 'NOT': return push_negation(inner[1])  # ¬¬P → P
        if ik == 'AND': return ('OR', push_negation(('NOT', inner[1])), push_negation(('NOT', inner[2])))
        if ik == 'OR':  return ('AND', push_negation(('NOT', inner[1])), push_negation(('NOT', inner[2])))
        return ('NOT', push_negation(inner))


def to_nnf(n):
    return push_negation(eliminate_imp(eliminate_iff(n)))


def distribute_or(n):
    if n[0] in ('VAR', 'NOT'): return n
    if n[0] == 'AND': return ('AND', distribute_or(n[1]), distribute_or(n[2]))
    if n[0] == 'OR':
        l, r = distribute_or(n[1]), distribute_or(n[2])
        if l[0] == 'AND': return ('AND', distribute_or(('OR', l[1], r)), distribute_or(('OR', l[2], r)))
        if r[0] == 'AND': return ('AND', distribute_or(('OR', l, r[1])), distribute_or(('OR', l, r[2])))
        return ('OR', l, r)


def distribute_and(n):
    if n[0] in ('VAR', 'NOT'): return n
    if n[0] == 'OR':  return ('OR', distribute_and(n[1]), distribute_and(n[2]))
    if n[0] == 'AND':
        l, r = distribute_and(n[1]), distribute_and(n[2])
        if l[0] == 'OR': return ('OR', distribute_and(('AND', l[1], r)), distribute_and(('AND', l[2], r)))
        if r[0] == 'OR': return ('OR', distribute_and(('AND', l, r[1])), distribute_and(('AND', l, r[2])))
        return ('AND', l, r)


def to_cnf(n): return distribute_or(to_nnf(n))


def to_dnf(n): return distribute_and(to_nnf(n))


#clause extraction

def extract_clauses(cnf) -> List[FrozenSet[str]]:
    clauses = []

    def and_walk(n):
        if n[0] == 'AND':
            and_walk(n[1])
            and_walk(n[2])
        else:
            clauses.append(frozenset(or_walk(n)))

    def or_walk(n):
        if n[0] == 'OR':  return or_walk(n[1]) + or_walk(n[2])
        if n[0] == 'VAR': return [n[1]]
        if n[0] == 'NOT' and n[1][0] == 'VAR': return ['~' + n[1][1]]
        return [ast_to_str(n)]

    and_walk(cnf)
    return clauses


#resolution

def _neg(lit): return lit[1:] if lit.startswith('~') else '~' + lit


def _resolve(c1, c2):
    for lit in c1:
        if _neg(lit) in c2:
            return frozenset((c1 - {lit}) | (c2 - {_neg(lit)}))


def resolution_solver(clauses) -> Dict:
    working = list(clauses)
    known = set(clauses)
    labels = {c: f"C{i + 1}" for i, c in enumerate(clauses)}
    steps = [{"step": i + 1, "type": "given", "clause": sorted(c),
              "label": f"C{i + 1}", "from": None,
              "description": f"C{i + 1}: {{{', '.join(sorted(c)) if c else '□'}}}"}
             for i, c in enumerate(clauses)]
    n = len(clauses) + 1

    changed = True
    while changed:
        changed = False
        for c1, c2 in combinations(working, 2):
            res = _resolve(c1, c2)
            if res is None or res in known: continue
            lbl = f"C{n}"
            n += 1
            labels[res] = lbl
            known.add(res)
            working.append(res)
            changed = True
            steps.append({"step": int(lbl[1:]), "type": "resolved", "clause": sorted(res),
                          "label": lbl, "from": [labels[c1], labels[c2]],
                          "description": f"{lbl}: {{{', '.join(sorted(res)) if res else '□'}}} (from {labels[c1]}, {labels[c2]})"})
            if not res:
                return {"satisfiable": False, "steps": steps, "empty_clause_step": lbl,
                        "conclusion": "UNSATISFIABLE — empty clause derived, contradiction found"}

    return {"satisfiable": True, "steps": steps, "empty_clause_step": None,
            "conclusion": "SATISFIABLE — no empty clause derivable"}


#main
def solve_resolution(formula_str: str) -> Dict:
    try:
        ast = parse_formula(formula_str)
        nnf = to_nnf(ast)
        cnf = to_cnf(ast)
        clauses = extract_clauses(cnf)
        proof = resolution_solver(clauses)
        return {
            "success": True,
            "original": ast_to_str(ast),
            "nnf": ast_to_str(nnf),
            "cnf": ast_to_str(cnf),
            "clauses": [sorted(c) for c in clauses],
            "transformation_steps": [
                {"label": "Original", "formula": ast_to_str(ast)},
                {"label": "NNF", "formula": ast_to_str(nnf)},
                {"label": "CNF", "formula": ast_to_str(cnf)},
            ],
            "proof": proof
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

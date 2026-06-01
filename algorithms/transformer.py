from typing import Dict, List
from algorithms.resolution import (
    parse_formula, ast_to_str,
    eliminate_iff, eliminate_imp, push_negation,
    distribute_or, distribute_and,
    to_nnf, to_cnf, to_dnf,
    extract_clauses,
)


def get_all_transforms(formula_str: str) -> Dict:
    try:
        ast = parse_formula(formula_str)
        original = ast_to_str(ast)

        # NNF: show each sub-step separately
        after_iff = eliminate_iff(ast)
        after_imp = eliminate_imp(after_iff)
        after_neg = push_negation(after_imp)

        nnf_steps = [
            {"description": "Original formula",
             "formula": original, "rule": ""},
            {"description": "Remove biconditionals (↔)",
             "formula": ast_to_str(after_iff),
             "rule": "P ↔ Q  ≡  (P → Q) ∧ (Q → P)"},
            {"description": "Remove implications (→)",
             "formula": ast_to_str(after_imp),
             "rule": "P → Q  ≡  ¬P ∨ Q"},
            {"description": "Push negations inward",
             "formula": ast_to_str(after_neg),
             "rule": "¬(P ∧ Q) ≡ ¬P ∨ ¬Q  |  ¬(P ∨ Q) ≡ ¬P ∧ ¬Q  |  ¬¬P ≡ P"},
        ]

        # CNF: distribute ∨ over ∧
        nnf_for_cnf = to_nnf(ast)
        cnf_result  = distribute_or(nnf_for_cnf)

        clauses     = extract_clauses(cnf_result)
        clause_strs = [" ∨ ".join(sorted(c)) if c else "□" for c in clauses]

        cnf_steps = [
            {"description": "Start from NNF",
             "formula": ast_to_str(nnf_for_cnf),
             "rule": "computed above"},
            {"description": "Distribute ∨ over ∧",
             "formula": ast_to_str(cnf_result),
             "rule": "P ∨ (Q ∧ R)  ≡  (P ∨ Q) ∧ (P ∨ R)"},
        ]

        # DNF: distribute ∧ over ∨
        nnf_for_dnf = to_nnf(ast)
        dnf_result  = distribute_and(nnf_for_dnf)
        dnf_terms   = _collect_terms(dnf_result)

        dnf_steps = [
            {"description": "Start from NNF",
             "formula": ast_to_str(nnf_for_dnf),
             "rule": "computed above"},
            {"description": "Distribute ∧ over ∨",
             "formula": ast_to_str(dnf_result),
             "rule": "P ∧ (Q ∨ R)  ≡  (P ∧ Q) ∨ (P ∧ R)"},
        ]

        # Truth table
        variables = _get_vars(ast)
        tt = _truth_table(ast, variables)

        return {
            "success": True,
            "original": original,
            "variables": variables,
            "nnf": {"result": ast_to_str(after_neg), "steps": nnf_steps},
            "cnf": {"result": ast_to_str(cnf_result), "steps": cnf_steps, "clauses": clause_strs},
            "dnf": {"result": ast_to_str(dnf_result), "steps": dnf_steps, "terms": dnf_terms},
            "truth_table": tt,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# helpers

def _collect_terms(dnf) -> List[str]:
    terms = []

    def or_walk(node):
        if node[0] == 'OR':
            or_walk(node[1])
            or_walk(node[2])
        else:
            terms.append(" ∧ ".join(and_walk(node)))

    def and_walk(node) -> List[str]:
        if node[0] == 'AND':
            return and_walk(node[1]) + and_walk(node[2])
        if node[0] == 'VAR':
            return [node[1]]
        if node[0] == 'NOT' and node[1][0] == 'VAR':
            return [f"¬{node[1][1]}"]
        return [ast_to_str(node)]

    or_walk(dnf)
    return terms


def _get_vars(ast) -> List[str]:
    seen = set()

    def walk(node):
        if node[0] == 'VAR':
            seen.add(node[1])
        elif node[0] == 'NOT':
            walk(node[1])
        elif node[0] in ('AND', 'OR', 'IMP', 'IFF'):
            walk(node[1]); walk(node[2])

    walk(ast)
    return sorted(seen)


def _eval(ast, env: Dict[str, bool]) -> bool:
    k = ast[0]
    if k == 'VAR':  return env.get(ast[1], False)
    if k == 'NOT':  return not _eval(ast[1], env)
    if k == 'AND':  return _eval(ast[1], env) and _eval(ast[2], env)
    if k == 'OR':   return _eval(ast[1], env) or  _eval(ast[2], env)
    if k == 'IMP':  return (not _eval(ast[1], env)) or _eval(ast[2], env)
    if k == 'IFF':  return _eval(ast[1], env) == _eval(ast[2], env)
    return False


def _truth_table(ast, variables: List[str]) -> Dict:
    n = len(variables)
    rows = []

    for mask in range(2 ** n):
        env = {v: bool((mask >> (n - j - 1)) & 1) for j, v in enumerate(variables)}
        val = _eval(ast, env)
        rows.append({"values": [env[v] for v in variables], "result": val})

    return {
        "variables": variables,
        "rows": rows,
        "is_tautology":    all(r["result"] for r in rows),
        "is_contradiction": not any(r["result"] for r in rows),
        "is_satisfiable":   any(r["result"] for r in rows),
    }

from groq import Groq
from typing import Generator

client = Groq(api_key="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")
MODEL = "llama-3.3-70b-versatile"  # free on Groq — swap to "mixtral-8x7b-32768" if you prefer

SYSTEM = (
    "You are a formal methods tutor embedded in an interactive platform. "
    "Write clear, structured explanations using markdown formatting "
    "(bold headings, bullet points where helpful). "
    "Never skip steps. Always refer to the specific values from the computation."
)


# Prompt builders


def _build_resolution_prompt(data: dict) -> str:
    formula = data.get("original", "")
    nnf = data.get("nnf", "")
    cnf = data.get("cnf", "")
    clauses = data.get("clauses", [])
    proof = data.get("proof", {})
    steps = proof.get("steps", [])
    sat = proof.get("satisfiable", True)
    conclusion = proof.get("conclusion", "")

    clause_lines = []
    for i, c in enumerate(clauses):
        lits = " ∨ ".join(("¬" + l[1:]) if l.startswith("~") else l for l in c)
        clause_lines.append(f"  C{i + 1}: {{{lits or '□'}}}")

    step_lines = []
    for s in steps:
        lits = " ∨ ".join(
            ("¬" + l[1:]) if l.startswith("~") else l for l in s.get("clause", [])
        )
        from_str = (
            f"  (resolved from {', '.join(s['from'])})"
            if s.get("from")
            else "  (given)"
        )
        step_lines.append(f"  {s['label']}: {{{lits or '□'}}}{from_str}")

    return f"""You are an expert formal logic tutor. A student has just solved a propositional logic problem using the Resolution Method. Explain every part of what happened in clear, educational detail.

--- COMPUTATION RESULT ---

Original formula: {formula}
NNF: {nnf}
CNF: {cnf}

Clause Set:
{chr(10).join(clause_lines)}

Resolution Proof:
{chr(10).join(step_lines)}

Final conclusion: {conclusion}
Result: {"UNSATISFIABLE" if not sat else "SATISFIABLE"}

--- END OF COMPUTATION ---

Write a thorough explanation covering:
1. **What the formula means** in plain English.
2. **NNF conversion** — which rules fired (eliminate ↔ and →, De Morgan's, double negation).
3. **CNF conversion** — what a clause is, how distribution was applied.
4. **The clause set** — what each clause means.
5. **Each resolution step** — which parents, which literal was eliminated, why valid.
6. **The final conclusion** — why empty clause proves contradiction (UNSAT) or why saturation means SAT.
7. **The big picture** — resolution is refutation-based, works by contradiction, complete for propositional logic.

Write for a university student who understands logic symbols but has just seen resolution for the first time."""


def _build_transformer_prompt(data: dict) -> str:
    original = data.get("original", "")
    nnf_res = data.get("nnf", {})
    cnf_res = data.get("cnf", {})
    dnf_res = data.get("dnf", {})
    tt = data.get("truth_table", {})

    cls = (
        "a tautology (true under every assignment)"
        if tt.get("is_tautology")
        else (
            "a contradiction (false under every assignment)"
            if tt.get("is_contradiction")
            else "satisfiable (true under at least one assignment)"
        )
    )

    nnf_steps = "\n".join(
        f"  {s['description']}: {s['formula']}  [{s.get('rule', '')}]"
        for s in nnf_res.get("steps", [])
        if s.get("description")
    )

    return f"""You are an expert formal logic tutor. A student has transformed a propositional formula into NNF, CNF, and DNF.

--- COMPUTATION RESULT ---

Original formula: {original}
Classification: {cls}
NNF: {nnf_res.get("result", "")}
NNF steps:
{nnf_steps}
CNF: {cnf_res.get("result", "")}  |  Clauses: {", ".join(cnf_res.get("clauses", []))}
DNF: {dnf_res.get("result", "")}  |  Minterms: {", ".join(dnf_res.get("terms", []))}

--- END OF COMPUTATION ---

Explain:
1. **What the formula says** in plain English.
2. **NNF transformation** — each rule applied and why.
3. **CNF transformation** — what a clause is, how ∨ was distributed over ∧.
4. **DNF transformation** — what a minterm is, how ∧ was distributed over ∨.
5. **Classification** — why this formula is {cls}, relating to the truth table.
6. **Relationship between the forms** — same content, different structure; when each is useful."""


def _build_automata_prompt(data: dict) -> str:
    fa_type = data.get("fa_type", "DFA")
    states = data.get("states", "")
    alphabet = data.get("alphabet", data.get("input_alphabet", ""))
    start = data.get("start_state", "")
    accepts = data.get("accept_states", "")
    trans = data.get("transitions", "")
    inp = data.get("input_string", "")
    result = data.get("result", {})
    accepted = result.get("accepted", False)
    steps = result.get("steps", [])
    trace = "\n".join(f"  Step {s['step']}: {s['description']}" for s in steps)

    machine_notes = ""
    if fa_type == "NFA":
        machine_notes = "This is a Non-deterministic Finite Automaton — multiple states may be active simultaneously."
    elif fa_type == "PDA":
        machine_notes = f"This is a Pushdown Automaton. Initial stack symbol: {data.get('start_stack', 'Z')}. Accept mode: {data.get('accept_mode', 'final_state')}."

    return f"""You are an expert automata theory tutor. A student has just simulated a {fa_type}.

--- COMPUTATION RESULT ---

Machine type: {fa_type}
States: {states}  |  Alphabet: {alphabet}
Start: {start}  |  Accept states: {accepts}
Transitions: {trans}
{machine_notes}
Input: "{inp}"
Result: {"ACCEPTED" if accepted else "REJECTED"}

Trace:
{trace}

--- END OF COMPUTATION ---

Explain:
1. **What this machine recognises** — describe the language in plain English.
2. **How a {fa_type} works** — states, alphabet, transition function, accept condition{"" if fa_type != "PDA" else ", stack"}.
3. **Walk through each step** — state, symbol read, transition fired, new state.
4. **Why the string was {"accepted" if accepted else "rejected"}** — acceptance condition and whether it was met.
{"5. **NFA non-determinism** — ε-closures and multiple active states." if fa_type == "NFA" else ""}
{"5. **The stack** — what was pushed/popped and why PDAs can recognise CFLs that DFAs cannot." if fa_type == "PDA" else ""}"""


def _build_unification_prompt(data: dict) -> str:
    t1 = data.get("term1", "")
    t2 = data.get("term2", "")
    uni = data.get("unifiable", False)
    subst = data.get("substitution", [])
    steps = data.get("steps", [])
    unified = data.get("unified_term", "")

    step_lines = "\n".join(f"  {s['description']}" for s in steps)
    subst_str = ", ".join(subst) if subst else "{} (terms already identical)"

    return f"""You are an expert logic tutor. A student has run Robinson's Unification Algorithm.

--- COMPUTATION RESULT ---

Term 1: {t1}
Term 2: {t2}
Result: {"UNIFIABLE" if uni else "NOT UNIFIABLE"}
{"MGU: {" + subst_str + "}" if uni else ""}
{"Unified term: " + unified if uni else ""}

Trace:
{step_lines}

--- END OF COMPUTATION ---

Explain:
1. **What unification is** — find σ such that σ(t1) = σ(t2); why it matters in Prolog, theorem proving, type inference.
2. **Terms, variables, constants, function symbols** — identify them in {t1} and {t2}.
3. **Each algorithm step** — which case applied, what substitution was added and why.
4. **The occurs check** — what it is, why it prevents X = f(X), whether it was relevant here.
5. **{"Why the MGU is most general" if uni else "Why unification failed"}** — {"any other unifier is a composition of the MGU with another substitution." if uni else "which step failed and why no substitution could work."}"""


PROMPT_BUILDERS = {
    "resolution": _build_resolution_prompt,
    "transformer": _build_transformer_prompt,
    "automata": _build_automata_prompt,
    "unification": _build_unification_prompt,
}


# ── Streaming generator ───────────────────────────────────────────────────


def explain_stream(module: str, data: dict) -> Generator[str, None, None]:
    """
    Build the prompt, call Groq with streaming, yield text chunks.
    Raises ValueError for unknown modules.
    """
    builder = PROMPT_BUILDERS.get(module)
    if not builder:
        raise ValueError(f"No explainer for module '{module}'")

    prompt = builder(data)

    stream = client.chat.completions.create(
        model=MODEL,
        max_tokens=1500,
        stream=True,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": prompt},
        ],
    )

    for chunk in stream:
        text = chunk.choices[0].delta.content
        if text:
            yield text

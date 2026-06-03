from groq import Groq
from typing import Generator

client = Groq(api_key="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")
MODEL = "llama-3.3-70b-versatile"  # active Groq reasoning model with chain-of-thought; fallback: "llama-3.3-70b-versatile"

SYSTEM = (
    "You are a formal methods tutor embedded in an interactive platform. "
    "Write clear, structured explanations using markdown formatting "
    "(bold headings, bullet points where helpful). "
    "CRITICAL RULES: "
    "1. Only explain the computation steps provided — never invent, skip, or reorder them. "
    "2. Never re-derive clauses or steps not explicitly listed in the input. "
    "3. If a clause is a tautology (contains both x and ¬x), flag it as one that "
    "would normally be pruned in a clean proof. "
    "4. Always refer to specific values and labels from the computation. "
    "5. Never skip steps. Always refer to the specific values from the computation."
)


# ── Prompt builders ───────────────────────────────────────────────────────


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

    # SAT vs UNSAT conclusion instruction
    if not sat:
        conclusion_instruction = (
            "6. **The final conclusion** — an empty clause (□) was derived, proving contradiction. "
            "Explain why deriving □ means the original formula is UNSATISFIABLE by refutation."
        )
    else:
        conclusion_instruction = (
            "6. **The final conclusion** — no empty clause was derived and the clause set is saturated, "
            "proving SATISFIABLE. Construct an explicit satisfying assignment from the final clause set "
            "and verify it satisfies every original clause one by one."
        )

    return f"""You are an expert formal logic tutor. A student has just solved a propositional logic problem using the Resolution Method. Explain every part of what happened in clear, educational detail.

⚠️ STRICT RULES:
- Only explain the {len(steps)} resolution steps listed below, in order.
- Do not derive additional clauses or invent steps not in the list.
- If any clause is a tautology (e.g. {{q ∨ ¬q}}), explicitly note it would normally be pruned in a clean proof.
- The result is {"UNSATISFIABLE" if not sat else "SATISFIABLE"} — your entire explanation must clearly support this conclusion.

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
4. **The clause set** — what each clause means in plain English.
5. **Each resolution step** — go through ONLY the {len(steps)} steps listed above in order. For each: name the parent clauses by label, state which literal pair was resolved and eliminated, show the resulting clause. If a step produces a tautology, flag it. Do not add any steps not in the list.
{conclusion_instruction}
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

⚠️ STRICT RULES:
- Only explain the transformation steps listed below, in order.
- Do not invent additional steps or reorder them.
- Refer to specific formulas and rule names from the computation at every step.

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
2. **NNF transformation** — go through each step listed above in order, naming the rule applied and what changed.
3. **CNF transformation** — what a clause is, how ∨ was distributed over ∧, list each resulting clause.
4. **DNF transformation** — what a minterm is, how ∧ was distributed over ∨, list each resulting minterm.
5. **Classification** — why this formula is {cls}. If satisfiable, give an explicit satisfying assignment and verify it. If tautology or contradiction, explain why no assignment can change that.
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

⚠️ STRICT RULES:
- Only explain the {len(steps)} trace steps listed below, in order.
- Do not invent transitions or states not shown in the computation.
- Refer to specific state names, symbols, and step numbers from the trace.

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
3. **Walk through each step** — go through ONLY the {len(steps)} steps above in order: current state, symbol read, transition fired, new state.
4. **Why the string was {"accepted" if accepted else "rejected"}** — acceptance condition and whether it was met, referencing the final state by name.
{"5. **NFA non-determinism** — ε-closures and multiple active states, referencing specific steps from the trace." if fa_type == "NFA" else ""}
{"5. **The stack** — what was pushed/popped at each step and why PDAs can recognise CFLs that DFAs cannot." if fa_type == "PDA" else ""}"""


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

⚠️ STRICT RULES:
- Only explain the {len(steps)} algorithm steps listed below, in order.
- Do not invent substitution steps or occurs-check results not shown.
- Refer to specific variable names, terms, and substitutions from the computation.

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
2. **Terms, variables, constants, function symbols** — identify them specifically in {t1} and {t2}.
3. **Each algorithm step** — go through ONLY the {len(steps)} steps above in order: which case applied, what substitution was added and why.
4. **The occurs check** — what it is, why it prevents X = f(X), whether it was relevant in this specific computation.
5. **{"Why the MGU is most general" if uni else "Why unification failed"}** — {"any other unifier is a composition of the MGU with another substitution; verify the MGU works by applying it to both terms." if uni else "which specific step failed and why no substitution could work."}"""


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
        temperature=0.3,  # low temperature for consistent, factual explanations
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

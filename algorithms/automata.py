from collections import defaultdict
from typing import Dict, List, Set


class FiniteAutomaton:
    def __init__(self, states, alphabet, transitions, start_state, accept_states, fa_type="DFA"):
        self.states = set(states)
        self.alphabet = set(alphabet)
        self.transitions = transitions   # dict: state -> {symbol -> next_state(s)}
        self.start_state = start_state
        self.accept_states = set(accept_states)
        self.fa_type = fa_type.upper()

    def epsilon_closure(self, state_set: Set[str]) -> Set[str]:
        closure = set(state_set)
        stack = list(state_set)
        while stack:
            s = stack.pop()
            for t in self._get_targets(s, 'ε'):
                if t not in closure:
                    closure.add(t)
                    stack.append(t)
        return closure

    def _get_targets(self, state, symbol):
        raw = self.transitions.get(state, {}).get(symbol, [])
        if isinstance(raw, str):
            return [raw]
        return raw

    def simulate(self, input_string: str) -> Dict:
        if self.fa_type == "DFA":
            return self._run_dfa(input_string)
        return self._run_nfa(input_string)

    def _run_dfa(self, s: str) -> Dict:
        cur = self.start_state
        trace = [{
            "step": 0,
            "current_states": [cur],
            "remaining_input": s,
            "symbol_read": None,
            "description": f"Start in state {cur}"
        }]

        for i, sym in enumerate(s):
            if sym not in self.alphabet:
                return {"accepted": False, "steps": trace,
                        "final_states": [cur], "error": f"'{sym}' not in alphabet"}

            targets = self._get_targets(cur, sym)
            nxt = targets[0] if targets else None

            if nxt is None:
                trace.append({
                    "step": i + 1, "current_states": [cur],
                    "remaining_input": s[i+1:], "symbol_read": sym,
                    "description": f"No transition from {cur} on '{sym}' — reject"
                })
                return {"accepted": False, "steps": trace, "final_states": [cur], "error": None}

            trace.append({
                "step": i + 1, "current_states": [nxt],
                "remaining_input": s[i+1:], "symbol_read": sym,
                "description": f"δ({cur}, '{sym}') = {nxt}"
            })
            cur = nxt

        ok = cur in self.accept_states
        trace.append({
            "step": len(s) + 1, "current_states": [cur],
            "remaining_input": "", "symbol_read": None,
            "description": f"Finished in {cur} — {'ACCEPT ✓' if ok else 'REJECT ✗'}"
        })
        return {"accepted": ok, "steps": trace, "final_states": [cur], "error": None}

    def _run_nfa(self, s: str) -> Dict:
        # start with epsilon closure of the initial state
        cur_set = self.epsilon_closure({self.start_state})
        trace = [{
            "step": 0,
            "current_states": sorted(cur_set),
            "remaining_input": s,
            "symbol_read": None,
            "description": f"ε-closure({{{self.start_state}}}) = {{{', '.join(sorted(cur_set))}}}"
        }]

        for i, sym in enumerate(s):
            if sym not in self.alphabet:
                return {"accepted": False, "steps": trace,
                        "final_states": sorted(cur_set), "error": f"'{sym}' not in alphabet"}

            reached = set()
            for state in cur_set:
                reached.update(self._get_targets(state, sym))


            cur_set = self.epsilon_closure(reached)

            label = ', '.join(sorted(cur_set)) if cur_set else '∅'
            trace.append({
                "step": i + 1,
                "current_states": sorted(cur_set),
                "remaining_input": s[i+1:],
                "symbol_read": sym,
                "description": f"After '{sym}': {{{label}}}"
            })

            if not cur_set:
                return {"accepted": False, "steps": trace, "final_states": [], "error": None}

        ok = bool(cur_set & self.accept_states)
        note = '∩ F ≠ ∅ → ACCEPT ✓' if ok else '∩ F = ∅ → REJECT ✗'
        trace.append({
            "step": len(s) + 1,
            "current_states": sorted(cur_set),
            "remaining_input": "",
            "symbol_read": None,
            "description": f"{{{', '.join(sorted(cur_set))}}} {note}"
        })
        return {"accepted": ok, "steps": trace, "final_states": sorted(cur_set), "error": None}

    def get_graph_data(self) -> Dict:
        nodes = [{"id": st, "label": st,
                  "is_start": st == self.start_state,
                  "is_accept": st in self.accept_states}
                 for st in sorted(self.states)]


        edge_map = defaultdict(list)
        for state, sym_map in self.transitions.items():
            for sym, targets in sym_map.items():
                if isinstance(targets, str):
                    targets = [targets]
                for t in targets:
                    edge_map[(state, t)].append(sym)

        edges = [{"id": f"e{i}", "source": fr, "target": to,
                  "label": ", ".join(sorted(syms))}
                 for i, ((fr, to), syms) in enumerate(edge_map.items())]

        return {"nodes": nodes, "edges": edges}


# helpers used by app.py

def parse_automaton(data: Dict) -> FiniteAutomaton:
    states  = [s.strip() for s in data.get("states", "").split(",") if s.strip()]
    alpha   = [a.strip() for a in data.get("alphabet", "").split(",") if a.strip()]
    start   = data.get("start_state", "").strip()
    accepts = [s.strip() for s in data.get("accept_states", "").split(",") if s.strip()]
    fa_type = data.get("fa_type", "DFA")

    raw = data.get("transitions", "")
    trans = defaultdict(lambda: defaultdict(list))

    for chunk in raw.replace("\n", ";").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        parts = [p.strip() for p in chunk.split(",")]
        if len(parts) != 3:
            continue
        fr, sym, to = parts
        if fa_type == "DFA":
            trans[fr][sym] = to
        else:
            if to not in trans[fr][sym]:
                trans[fr][sym].append(to)

    flat = {s: dict(t) for s, t in trans.items()}
    return FiniteAutomaton(states, alpha, flat, start, accepts, fa_type)


def validate_automaton(data: Dict) -> List[str]:
    errors = []
    states  = [s.strip() for s in data.get("states", "").split(",") if s.strip()]
    start   = data.get("start_state", "").strip()
    accepts = [s.strip() for s in data.get("accept_states", "").split(",") if s.strip()]

    if not states:
        errors.append("states list is empty")
    if not start:
        errors.append("start state is required")
    elif start not in states:
        errors.append(f"start state '{start}' is not in the states list")
    for a in accepts:
        if a and a not in states:
            errors.append(f"accept state '{a}' is not in the states list")
    return errors


"""
Pushdown Automaton (PDA) Simulator
Supports non-deterministic PDA simulation via BFS over configurations.
A configuration is (state, remaining_input, stack).
Acceptance: by final state OR by empty stack (configurable).
"""

from collections import defaultdict, deque
from typing import Dict, List, Set, Tuple, Optional


class PushdownAutomaton:
    """
    PDA transition format:
        transitions[state][(input_symbol, stack_top)] = [(next_state, stack_push), ...]

    Conventions:
        - Use 'ε' for epsilon (no input consumed / no stack pop/push)
        - Stack bottom marker: 'Z' or 'Z0' (user-defined)
        - stack_push is a string of symbols pushed left-to-right
          e.g. 'AB' means push A then B, so B ends up on top
          'ε' means pop only (push nothing)
    """

    def __init__(self, states: List[str], input_alphabet: List[str],
                 stack_alphabet: List[str], transitions: Dict,
                 start_state: str, start_stack: str,
                 accept_states: List[str], accept_mode: str = "final_state"):
        self.states = set(states)
        self.input_alphabet = set(input_alphabet)
        self.stack_alphabet = set(stack_alphabet)
        self.transitions = transitions   # {state: {(in_sym, stack_sym): [(next, push_str)]}}
        self.start_state = start_state
        self.start_stack = start_stack  # initial stack symbol(s)
        self.accept_states = set(accept_states)
        self.accept_mode = accept_mode  # "final_state" or "empty_stack"

    # ── Simulation ────────────────────────────────────────────────────────

    def simulate(self, input_string: str) -> Dict:
        """
        BFS over PDA configurations.
        Config = (state, input_remaining, stack_tuple, path)
        Returns step trace of the accepting path (or rejection info).
        """
        initial_stack = tuple(reversed(self.start_stack))  # top of stack = index 0
        initial_config = (self.start_state, input_string, initial_stack)

        # BFS to find accepting path
        # Each node: (state, remaining, stack, steps_list)
        queue = deque()
        queue.append((self.start_state, input_string, initial_stack, []))
        visited = set()
        visited.add((self.start_state, input_string, initial_stack))

        all_steps = []   # collect steps from BFS for display
        reject_steps = []
        found_accept = False
        accept_path = None

        step_count = 0
        max_steps = 2000  # prevent infinite loops

        while queue and step_count < max_steps:
            state, remaining, stack, path = queue.popleft()
            step_count += 1

            stack_display = list(reversed(stack)) if stack else ['(empty)']
            step = {
                "state": state,
                "remaining": remaining,
                "stack": list(stack),
                "stack_top": stack[0] if stack else 'ε',
                "description": (
                    f"State: {state}  |  Input: \"{remaining}\"  |  "
                    f"Stack: [{', '.join(stack) if stack else '∅'}]"
                )
            }

            # Check acceptance
            if self._is_accepting(state, remaining, stack):
                found_accept = True
                accept_path = path + [step]
                break

            reject_steps = path + [step]

            # Generate successor configurations
            successors = self._get_successors(state, remaining, stack)
            for (next_state, next_remaining, next_stack, transition_desc) in successors:
                key = (next_state, next_remaining, next_stack)
                if key not in visited:
                    visited.add(key)
                    next_step = dict(step)
                    next_step["transition"] = transition_desc
                    queue.append((next_state, next_remaining, next_stack, path + [next_step]))

        if found_accept:
            return {
                "accepted": True,
                "steps": accept_path,
                "accept_mode": self.accept_mode,
                "error": None,
                "total_configs_explored": step_count
            }
        else:
            return {
                "accepted": False,
                "steps": reject_steps[:30],  # limit for display
                "accept_mode": self.accept_mode,
                "error": None if step_count < max_steps else "Search limit reached (possible infinite loop)",
                "total_configs_explored": step_count
            }

    def _is_accepting(self, state: str, remaining: str, stack: tuple) -> bool:
        if self.accept_mode == "final_state":
            return state in self.accept_states and remaining == ""
        elif self.accept_mode == "empty_stack":
            return remaining == "" and len(stack) == 0
        elif self.accept_mode == "both":
            return state in self.accept_states and remaining == "" and len(stack) == 0
        return False

    def _get_successors(self, state: str, remaining: str, stack: tuple) -> List[Tuple]:
        """Return list of (next_state, next_remaining, next_stack, desc)."""
        successors = []
        trans = self.transitions.get(state, {})
        stack_top = stack[0] if stack else 'ε'

        # Try consuming input symbol + stack top
        if remaining:
            in_sym = remaining[0]
            for (i_sym, s_sym), targets in trans.items():
                if i_sym == in_sym and (s_sym == stack_top or s_sym == 'ε'):
                    for (next_state, push_str) in targets:
                        next_remaining = remaining[1:]
                        next_stack = self._apply_stack(stack, s_sym, push_str)
                        desc = f"({state}, {in_sym}, {s_sym}) → ({next_state}, {push_str if push_str != 'ε' else 'ε'})"
                        successors.append((next_state, next_remaining, next_stack, desc))

        # Try epsilon transitions (no input consumed)
        for (i_sym, s_sym), targets in trans.items():
            if i_sym == 'ε':
                if s_sym == stack_top or s_sym == 'ε':
                    for (next_state, push_str) in targets:
                        next_remaining = remaining
                        next_stack = self._apply_stack(stack, s_sym, push_str)
                        desc = f"({state}, ε, {s_sym}) → ({next_state}, {push_str if push_str != 'ε' else 'ε'})"
                        successors.append((next_state, next_remaining, next_stack, desc))

        return successors

    def _apply_stack(self, stack: tuple, popped_sym: str, push_str: str) -> tuple:
        """Pop stack_top (if not ε-pop), then push push_str symbols."""
        # Pop
        if popped_sym != 'ε' and stack:
            stack = stack[1:]  # remove top

        # Push (push_str read left-to-right, leftmost ends on top)
        if push_str and push_str != 'ε':
            new_syms = tuple(push_str)  # each char is one symbol
            stack = new_syms + stack
        return stack

    def get_graph_data(self) -> Dict:
        """Return graph data for Cytoscape visualization."""
        nodes = []
        edges = []

        for state in sorted(self.states):
            nodes.append({
                "id": state,
                "label": state,
                "is_start": state == self.start_state,
                "is_accept": state in self.accept_states
            })

        edge_map = defaultdict(list)
        for state, trans in self.transitions.items():
            for (in_sym, stack_sym), targets in trans.items():
                for (next_state, push_str) in targets:
                    label = f"{in_sym},{stack_sym}/{push_str}"
                    edge_map[(state, next_state)].append(label)

        for eid, ((src, tgt), labels) in enumerate(edge_map.items()):
            edges.append({
                "id": f"e{eid}",
                "source": src,
                "target": tgt,
                "label": "\n".join(labels)
            })

        return {"nodes": nodes, "edges": edges}


# ── Parser ────────────────────────────────────────────────────────────────

def parse_pda(data: Dict) -> Tuple[Optional['PushdownAutomaton'], List[str]]:
    """
    Parse PDA from request data.
    Transition input format (one per line or semicolon-separated):
        q0,a,A,q1,BC   means: from q0, read 'a', pop 'A', go to q1, push 'BC'
        q0,ε,Z,q1,Z    means: epsilon input, pop Z, push Z (no change)
        q0,a,ε,q1,A    means: read 'a', don't pop, push A (ε-pop)
    """
    errors = []

    states = [s.strip() for s in data.get("states", "").split(",") if s.strip()]
    input_alpha = [a.strip() for a in data.get("input_alphabet", "").split(",") if a.strip()]
    stack_alpha = [a.strip() for a in data.get("stack_alphabet", "").split(",") if a.strip()]
    start_state = data.get("start_state", "").strip()
    start_stack = data.get("start_stack", "Z").strip()
    accept_states_raw = data.get("accept_states", "").strip()
    accept_states = [s.strip() for s in accept_states_raw.split(",") if s.strip()]
    accept_mode = data.get("accept_mode", "final_state")

    if not states:
        errors.append("States cannot be empty")
    if not start_state:
        errors.append("Start state is required")
    elif start_state not in states:
        errors.append(f"Start state '{start_state}' must be in states list")
    if not start_stack:
        errors.append("Initial stack symbol is required")
    if accept_mode not in ("final_state", "empty_stack", "both"):
        errors.append("Accept mode must be 'final_state', 'empty_stack', or 'both'")
    for acc in accept_states:
        if acc and acc not in states:
            errors.append(f"Accept state '{acc}' must be in states list")

    if errors:
        return None, errors

    # Parse transitions
    transitions = defaultdict(lambda: defaultdict(list))
    raw = data.get("transitions", "")

    lines = []
    for part in raw.replace(";", "\n").split("\n"):
        part = part.strip()
        if part:
            lines.append(part)

    for line in lines:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) != 5:
            errors.append(f"Invalid transition (need 5 fields: from,input,stack_pop,to,stack_push): '{line}'")
            continue
        from_s, in_sym, stack_sym, to_s, push_str = parts

        if from_s not in states:
            errors.append(f"Unknown state '{from_s}' in transition")
        if to_s not in states:
            errors.append(f"Unknown state '{to_s}' in transition")

        transitions[from_s][(in_sym, stack_sym)].append((to_s, push_str))

    if errors:
        return None, errors

    trans_dict = {s: dict(t) for s, t in transitions.items()}
    pda = PushdownAutomaton(
        states, input_alpha, stack_alpha, trans_dict,
        start_state, start_stack, accept_states, accept_mode
    )
    return pda, []
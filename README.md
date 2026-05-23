[README.md](https://github.com/user-attachments/files/28174373/README.md)
# FormalCS Platform

**A full-stack interactive formal methods toolkit** built with Python (Flask) backend and a modern dark-themed frontend. All computational logic runs server-side in Python; JavaScript handles only UI rendering and asynchronous requests.

---

## Project Overview

FormalCS Platform is a university-grade web application implementing five formal computer science modules in one cohesive interface:

| Module | Description |
|--------|-------------|
| **Automata Simulator** | DFA/NFA simulation with step-by-step trace and Cytoscape.js graph |
| **CFG Generator** | BFS-based string generation and recursive membership checking |
| **Resolution Solver** | Propositional resolution with CNF conversion and proof visualization |
| **Formula Transformer** | NNF, CNF, DNF transformations + truth table generation |
| **Unification Solver** | Robinson's algorithm with full MGU computation and occurs check |

---

## Architecture

```
formal_methods_platform/
├── app.py                   # Flask application + all REST API routes
├── requirements.txt
├── README.md
├── algorithms/              # Pure Python computation (NO JS here)
│   ├── __init__.py
│   ├── automata.py          # DFA/NFA: transitions, ε-closure, acceptance
│   ├── cfg.py               # CFG: BFS generation, membership, derivation
│   ├── resolution.py        # Parser, AST transforms, clause resolution
│   ├── transformer.py       # NNF/CNF/DNF transforms, truth table
│   └── unification.py       # Robinson's algorithm, term parser, MGU
├── templates/               # Jinja2 HTML (extend base.html)
│   ├── base.html            # Sidebar nav, toast system, shared layout
│   ├── index.html           # Dashboard
│   ├── automata.html        # DFA/NFA simulator page
│   ├── cfg.html             # CFG generator page
│   ├── resolution.html      # Resolution solver page
│   ├── transformer.html     # Formula transformer page
│   ├── unification.html     # Unification solver page
│   └── about.html           # Documentation
└── static/
    ├── css/main.css         # Complete design system (CSS variables, components)
    └── js/main.js           # UI helpers: sidebar, toasts, API calls, tabs
```

**Backend → Frontend flow:**
1. User fills form → JS collects data → `fetch()` POST to Flask endpoint
2. Flask calls Python algorithm module → returns JSON
3. JS renders result HTML inline (steps, formulas, graphs)

---

## Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Backend | Python 3.10+ | All algorithms and computation |
| Framework | Flask 3.x | HTTP server, routing, JSON API |
| Templating | Jinja2 | HTML template inheritance |
| Graph Viz | Cytoscape.js 3.28 | Automata state diagrams |
| Frontend | Vanilla JS | fetch API, DOM rendering, UI |
| Styling | CSS Custom Properties | Full design system, responsive |
| Fonts | Syne + JetBrains Mono | Display + monospace typography |

---

## Installation

### Requirements
- Python 3.10 or higher
- pip

### Steps

```bash
# 1. Navigate to the project directory
cd formal_methods_platform

# 2. Create a virtual environment
python -m venv venv

# 3. Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python app.py

# 6. Open in your browser
# http://localhost:5000
```

---

## API Reference

All endpoints accept and return JSON. Use `Content-Type: application/json`.

### POST `/api/automata/simulate`
Simulate a finite automaton on an input string.

**Request:**
```json
{
  "states": "q0, q1, q2",
  "alphabet": "a, b",
  "start_state": "q0",
  "accept_states": "q2",
  "transitions": "q0,a,q1;q1,b,q2",
  "input_string": "ab",
  "fa_type": "DFA"
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "accepted": true,
    "steps": [...],
    "final_states": ["q2"]
  },
  "graph": { "nodes": [...], "edges": [...] }
}
```

### POST `/api/automata/graph`
Get graph data only (no simulation). Same request body, returns `{ graph }`.

### POST `/api/cfg/generate`
Generate strings from a context-free grammar.

**Request:**
```json
{
  "variables": "S",
  "terminals": "a, b",
  "start": "S",
  "productions": "S -> a S b | ε",
  "max_length": 6,
  "count": 10
}
```

### POST `/api/cfg/check`
Check if a string is in L(G). Add `"test_string": "aabb"` to CFG request body.

### POST `/api/resolution/solve`
Apply resolution to a propositional formula.

**Request:** `{ "formula": "(p -> q) & (~q) & p" }`

**Response includes:** `original`, `nnf`, `cnf`, `clauses`, `proof` (steps, satisfiable, conclusion).

### POST `/api/transformer/transform`
Transform formula to NNF, CNF, DNF with truth table.

**Request:** `{ "formula": "p -> q" }`

**Response includes:** `nnf`, `cnf`, `dnf` (each with `result`, `steps`, clauses/terms), `truth_table`.

### POST `/api/unification/unify`
Unify two first-order logic terms.

**Request:** `{ "term1": "f(X, g(Y))", "term2": "f(a, g(b))" }`

**Response includes:** `unifiable`, `substitution`, `unified_term`, `steps`.

---

## Algorithm Explanations

### Finite Automata Simulation
- **DFA:** Deterministic transition function δ: Q × Σ → Q. At each step, exactly one next state. Dead state on missing transition.
- **NFA:** ε-closure via BFS. Each symbol maps current state *set* to new set. Accepts if intersection with F ≠ ∅.

### CFG String Generation
Uses BFS over sentential forms with leftmost variable expansion. Sentential forms pruned when terminal count exceeds max_length. Guarantees finding all strings up to the length limit.

### Resolution Method
1. Parse formula → AST
2. Eliminate biconditionals: `P ↔ Q ≡ (P → Q) ∧ (Q → P)`
3. Eliminate implications: `P → Q ≡ ¬P ∨ Q`
4. Push negations inward (De Morgan's laws)
5. Distribute ∨ over ∧ → CNF
6. Extract clause set
7. Resolution: pick two clauses with complementary literals, derive resolvent
8. Empty clause derivable → UNSATISFIABLE; saturation → SATISFIABLE

### NNF / CNF / DNF Transformations
- **NNF:** Steps 1–4 above (no implications, negations pushed to literals)
- **CNF:** NNF + distribute ∨ over ∧ recursively
- **DNF:** NNF + distribute ∧ over ∨ recursively

### Robinson's Unification (1965)
```
unify(t1, t2, σ):
  t1' = σ(t1), t2' = σ(t2)
  if t1' = t2': return σ
  if t1' is variable X not in vars(t2'): return σ ∘ {X ↦ t2'}
  if t2' is variable Y not in vars(t1'): return σ ∘ {Y ↦ t1'}
  if both functions f(s₁…sₙ) and f(t₁…tₙ):
    σ₀ = σ
    for i = 1..n: σᵢ = unify(sᵢ, tᵢ, σᵢ₋₁)
    return σₙ
  fail (clash or arity mismatch)
```

---

## Input Syntax

### Propositional Logic
| Symbol | Operator | Example |
|--------|----------|---------|
| `~` | Negation (¬) | `~p` |
| `&` | Conjunction (∧) | `p & q` |
| `\|` | Disjunction (∨) | `p \| q` |
| `->` | Implication (→) | `p -> q` |
| `<->` | Biconditional (↔) | `p <-> q` |

### Automata Transitions
Format: `from_state,symbol,to_state` separated by semicolons.
Example: `q0,a,q1;q0,b,q0;q1,a,q2`

### CFG Productions
One production per line. Alternatives separated by `|`. Use `ε` for empty.
```
S -> a S b | ε
A -> a A | a
```

### Unification Terms
- Variables: start with uppercase `X`, `Y`, `Var`
- Constants: lowercase `a`, `b`, `john`
- Functions: `f(X, a)`, `g(X, Y, Z)`

---

## Demo Walkthrough

1. **Dashboard** `/` — Module overview and quick-start links
2. **Automata** `/automata` — Load "Binary divisible 3" example, click Simulate, observe graph + trace
3. **CFG** `/cfg` — Load "Balanced ab" example, generate strings, click a string chip to see derivation
4. **Resolution** `/resolution` — Enter `(p -> q) & (~q) & p`, solve — proves UNSATISFIABLE via empty clause
5. **Transformer** `/transformer` — Enter `p | ~p`, transform — identified as Tautology, all normal forms shown
6. **Unification** `/unification` — Enter `f(X, g(Y))` and `f(a, g(b))`, unify — MGU = {X↦a, Y↦b}
7. **About** `/about` — Full documentation, API reference, installation guide

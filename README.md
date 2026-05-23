[README.md](https://github.com/user-attachments/files/28174373/README.md)
# | Theoretical Foundations of Computer Science | Platform By G1orga |

**A full-stack interactive formal methods toolkit** built with Python (Flask) backend and a modern dark-themed frontend. All computational logic runs server-side in Python; JavaScript handles only UI rendering and asynchronous requests.

---

## Project Overview

TFCS Platform is web application implementing three formal computer science modules in one cohesive interface:

| Module | Description |
|--------|-------------|
| **Automata Simulator** | DFA/NFA simulation with step-by-step trace and Cytoscape.js graph |
| **Resolution Solver** | Propositional resolution with CNF conversion and proof visualization |
| **Formula Transformer** | NNF, CNF, DNF transformations + truth table generation |

---

## Architecture

```
formal_methods_platform/
├── app.py                   # Flask application + all REST API routes
├── requirements.txt
├── README.md
├── algorithms/              # Pure Python computation 
│   ├── automata.py          # DFA/NFA: transitions, ε-closure, acceptance
│   ├── resolution.py        # Parser, AST transforms, clause resolution
│   └── transformer.py       # NNF/CNF/DNF transforms, truth table
├── templates/               # Jinja2 HTML (extend base.html)
│   ├── base.html            # Sidebar nav, toast system, shared layout
│   ├── index.html           # Dashboard
│   ├── automata.html        # DFA/NFA simulator page
│   ├── resolution.html      # Resolution solver page
│   ├── transformer.html     # Formula transformer page
│   ├── welcome.html         # Welcome / Presentation page
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
| Backend | Python 3.13+ | All algorithms and computation |
| Framework | Flask 3.1.3 | HTTP server, routing, JSON API |
| Templating | Jinja2 | HTML template inheritance |
| Graph Viz | Cytoscape.js 3.28 | Automata state diagrams |
| Frontend | Vanilla JS | fetch API, DOM rendering, UI |
| Styling | CSS Custom Properties | Full design system, responsive |
| Fonts | Syne + JetBrains Mono | Display + monospace typography |

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


---

## Demo Walkthrough
1. **Dashboard** `/` — Welcome / Presentation of the website in general
2. **Dashboard** `/index` — Module overview and quick-start links
3. **Automata** `/automata` — Load "Binary divisible 3" example, click Simulate, observe graph + trace
4. **Resolution** `/resolution` — Enter `(p -> q) & (~q) & p`, solve — proves UNSATISFIABLE via empty clause
5. **Transformer** `/transformer` — Enter `p | ~p`, transform — identified as Tautology, all normal forms shown
6. **About** `/about` — Full documentation, API reference, installation guide

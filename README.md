# ProofLab - Interactive TFCS Platform

**Course:** Theoretical Foundations of Computer Science & Python (TFCS)  
**Author:** Lasha Giorgadze (G1orga)  
**Version:** 3.13.0  
**Type:** Final course project - Python

---

## Abstract

ProofLab is a full-stack web application that implements core topics from **Theoretical Foundations of Computer Science** in an interactive, educational form. The platform lets users define formal objects (automata, logical formulas), run algorithms on them, and inspect every intermediate step of the computation.

All **algorithmic logic is implemented in Python** on the server. The browser is responsible only for presentation: forms, graphs, step-by-step traces, and optional AI-generated explanations. This separation keeps the implementation faithful to the course material while still providing a modern user interface.

The three main modules exposed in the UI are:

1. **Automata Simulator** - DFA and NFA simulation with animated state diagrams  
2. **Resolution Solver** - propositional resolution with CNF conversion and proof trace  
3. **Formula Transformer** - NNF, CNF, DNF conversion plus truth table generation  

---

## Table of Contents

1. [Project Motivation](#project-motivation)
2. [Learning Objectives](#learning-objectives)
3. [System Architecture](#system-architecture)
4. [Project Structure](#project-structure)
5. [How the Code Works - End-to-End Flow](#how-the-code-works--end-to-end-flow)
6. [Backend: Flask Application](#backend-flask-application)
7. [Algorithm Modules](#algorithm-modules)
   - [Automata (`algorithms/automata.py`)](#1-automata-simulator-algorithmsautomatapy)
   - [Resolution (`algorithms/resolution.py`)](#2-resolution-solver-algorithmsresolutionpy)
   - [Transformer (`algorithms/transformer.py`)](#3-formula-transformer-algorithmstransformerpy)
   - [AI Explainer (`algorithms/ai_explainer.py`)](#4-ai-explainer-algorithmsai_explainerpy)
8. [Frontend Architecture](#frontend-architecture)
9. [Input Syntax](#input-syntax)
10. [Installation and Running](#installation-and-running)
11. [Demo Guide for Evaluation](#demo-guide-for-evaluation)
12. [Screenshots](#screenshots)
13. [Dependencies](#dependencies)
14. [Future Work](#future-work)
15. [Conclusion](#conclusion)

---

## Project Motivation

Formal methods courses cover abstract concepts - automata, normal forms, resolution proofs - that are difficult to understand from notation alone. Textbook examples show final results but rarely let students **experiment** with their own machines and formulas.

ProofLab addresses this by:

- Letting the user **define** a problem (automaton configuration, logical formula)
- Running the **exact algorithm** taught in the course
- Showing a **complete trace** of every step (states visited, clauses derived, rewrite rules applied)
- Visualising results (state diagrams via Cytoscape.js, clause lists, truth tables)

The project demonstrates that course algorithms can be implemented cleanly in Python and exposed through a REST API without sacrificing correctness or pedagogical clarity.

---

## Learning Objectives

This project demonstrates understanding of:

| Topic | Implementation |
|-------|----------------|
| Deterministic and non-deterministic finite automata | `FiniteAutomaton` class with DFA and NFA simulation |
| ε-closure and set-based NFA transitions | BFS over epsilon transitions in `epsilon_closure()` |
| Propositional logic syntax | Recursive-descent parser producing an AST |
| Normal forms (NNF, CNF, DNF) | Structural AST rewrites with distributivity |
| Resolution refutation | Clause extraction + pairwise resolution until empty clause or saturation |
| Truth tables and formula classification | Exhaustive evaluation over \(2^n\) assignments |
| Web architecture | Flask routes, JSON API, separation of logic and presentation |

---

## System Architecture

The application follows a classic **three-layer architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER (Browser)                               │
│  templates/*.html  +  static/css  +  static/js              │
│  - forms, sidebar, graphs, step lists, toasts               │
└──────────────────────────┬──────────────────────────────────┘
                           │  HTTP (JSON POST / SSE)
┌──────────────────────────▼──────────────────────────────────┐
│  APPLICATION LAYER (Flask - app.py)                         │
│  - page routes (render HTML)                                │
│  - API routes (validate input, call algorithms, return JSON)│
└──────────────────────────┬──────────────────────────────────┘
                           │  Python function calls
┌──────────────────────────▼──────────────────────────────────┐
│  ALGORITHM LAYER (algorithms/*.py)                          │
│  - pure Python, no Flask dependency                         │
│  - automata, resolution, transformer, ai_explainer          │
└─────────────────────────────────────────────────────────────┘
```

### Request lifecycle (example: automata simulation)

```
User clicks "Simulate"
       │
       ▼
automata.html  -  JavaScript collects form fields
       │
       ▼
POST /api/automata/simulate  { states, alphabet, transitions, input_string, fa_type }
       │
       ▼
app.py  -  validate_automaton()  →  parse_automaton()  →  fa.simulate()
       │
       ▼
JSON response  { result: { steps, accepted }, graph: { nodes, edges } }
       │
       ▼
JavaScript  -  renders Cytoscape graph + playback controls + step trace
```

The same pattern applies to resolution and transformation: **the frontend never implements the algorithm**; it only sends input and renders the structured JSON response.

---

## Project Structure

```
ProofLab-TFCS-Platform-v3.13.0/
├── app.py                      # Flask server: page routes + REST API
├── requirements.txt            # Python dependencies
├── .env                        # GROQ_API_KEY (not committed; see Installation)
├── .gitignore
├── README.md
│
├── algorithms/                 # Core computation (framework-independent)
│   ├── automata.py             # DFA/NFA: parse, simulate, graph export
│   ├── pda.py                  # PDA simulation (backend; API ready)
│   ├── resolution.py           # Parser, AST, CNF, resolution prover
│   ├── transformer.py          # NNF/CNF/DNF + truth table
│   └── ai_explainer.py         # Groq LLM streaming explanations
│
├── templates/                    # Jinja2 HTML templates
│   ├── base.html               # Shared layout: sidebar, mobile nav, toasts
│   ├── welcome.html            # Landing / project presentation page
│   ├── index.html              # Platform dashboard
│   ├── automata.html           # Automata simulator UI
│   ├── resolution.html         # Resolution solver UI
│   ├── transformer.html        # Formula transformer UI
│   └── about.html              # In-app documentation
│
└── static/
    ├── css/
    │   ├── main.css            # Design system + responsive layout
    │   └── welcome.css         # Landing page styles
    └── js/
        ├── main.js             # Sidebar, API helper, toasts, UI utilities
        ├── welcome.js          # Landing page animations + mobile nav
        └── ai-explain.js       # Server-Sent Events streaming handler
```

**Design principle:** `algorithms/` contains no Flask imports. This makes each module testable in isolation and mirrors how algorithms are presented in the course - as self-contained procedures independent of any UI.

---

## How the Code Works - End-to-End Flow

### 1. Page routes (HTML)

`app.py` maps URLs to Jinja2 templates:

| URL | Template | Purpose |
|-----|----------|---------|
| `/` | `welcome.html` | Project presentation and module overview |
| `/index` | `index.html` | Dashboard with links to all modules |
| `/automata` | `automata.html` | Automata simulator |
| `/resolution` | `resolution.html` | Resolution solver |
| `/transformer` | `transformer.html` | Formula transformer |
| `/about` | `about.html` | Documentation |

All module pages **extend** `base.html`, which provides the sidebar navigation, mobile menu, toast notifications, and shared CSS/JS.

### 2. API routes (JSON computation)

| Method | Endpoint | Python entry point |
|--------|----------|-------------------|
| `POST` | `/api/automata/simulate` | `parse_automaton()` → `simulate()` |
| `POST` | `/api/automata/graph` | `parse_automaton()` → `get_graph_data()` |
| `POST` | `/api/resolution/solve` | `solve_resolution()` |
| `POST` | `/api/transformer/transform` | `get_all_transforms()` |
| `POST` | `/api/explain/<module>` | `explain_stream()` (SSE) |

Each API handler follows the same pattern:

1. Parse JSON body from the request
2. Validate input (return `400` with error message if invalid)
3. Call the algorithm module
4. Return JSON (or SSE stream for AI explanations)

### 3. Shared frontend utilities (`static/js/main.js`)

| Function | Role |
|----------|------|
| `apiCall(endpoint, data, btn)` | POST JSON, show loading state on button, handle errors |
| `showToast(message, type)` | User feedback for success/error |
| `highlightFormula(formula)` | Colour-code logical symbols in rendered output |
| Sidebar toggle | Responsive navigation on mobile/tablet |

---

## Backend: Flask Application

`app.py` is the single entry point. Key configuration:

```python
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False   # preserve ¬, ∧, ∨ in JSON responses
```

**Why Flask?** It is lightweight, maps naturally to a course project scope, and supports both server-rendered pages (Jinja2) and JSON APIs without a heavy framework. All TFCS logic stays in `algorithms/`, keeping `app.py` thin - it only routes requests and serialises results.

---

## Algorithm Modules

### 1. Automata Simulator (`algorithms/automata.py`)

#### Theory

A **finite automaton** is a tuple \(M = (Q, \Sigma, \delta, q_0, F)\):

- \(Q\) - finite set of states  
- \(\Sigma\) - input alphabet  
- \(\delta\) - transition function (DFA: one state; NFA: set of states)  
- \(q_0\) - start state  
- \(F\) - accept states  

A string is **accepted** if, after reading all symbols, the machine is in an accept state (DFA) or the active state set intersects \(F\) (NFA).

#### Code structure

| Component | Description |
|-----------|-------------|
| `FiniteAutomaton` | Data class holding states, alphabet, transitions, start, accepts |
| `epsilon_closure(state_set)` | BFS over ε-transitions; used by NFA before/after each symbol |
| `_run_dfa(input)` | Single current state; rejects on missing transition |
| `_run_nfa(input)` | Maintains a **set** of active states; applies ε-closure after each symbol |
| `simulate(input)` | Dispatches to DFA or NFA based on `fa_type` |
| `get_graph_data()` | Exports nodes/edges for Cytoscape.js rendering |
| `parse_automaton(data)` | Parses comma-separated form input into a `FiniteAutomaton` |
| `validate_automaton(data)` | Checks start/accept states belong to \(Q\) |

#### DFA simulation (simplified)

```python
cur = start_state
for sym in input_string:
    nxt = transitions[cur].get(sym)
    if nxt is None:
        return rejected
    cur = nxt
return cur in accept_states
```

Each transition appends a **trace step** with: current state, symbol read, remaining input, and a human-readable description (e.g. `δ(q0, 'a') = q1`).

#### NFA simulation

After each symbol, the algorithm:

1. Collects all targets reachable from every state in the current set  
2. Applies ε-closure to the result  
3. Accepts if `current_states ∩ accept_states ≠ ∅`

#### Frontend integration

`automata.html` sends the machine configuration to `/api/automata/simulate`, then:

- Builds a **Cytoscape.js** graph from `graph.nodes` and `graph.edges`
- Runs a **step-by-step playback** (scrubber, play/pause) over `result.steps`
- Highlights active/visited nodes and edges during animation

---

### 2. Resolution Solver (`algorithms/resolution.py`)

#### Theory

The **resolution method** is a refutation procedure for propositional logic:

1. Convert formula to **CNF** (conjunctive normal form)  
2. Extract a **clause set** (each conjunct is a disjunction of literals)  
3. Repeatedly resolve pairs of clauses containing complementary literals \(L\) and \(\neg L\)  
4. If the **empty clause** \(\square\) is derived → **UNSATISFIABLE**  
5. If no new clauses can be added → **SATISFIABLE** (saturation)

#### Code structure

| Component | Description |
|-----------|-------------|
| `tokenize(raw)` | Lexer: splits input into tokens (`VAR`, `NOT`, `AND`, `OR`, `IMP`, `IFF`, …) |
| `Parser` | Recursive-descent parser; builds AST with operator precedence |
| `eliminate_iff`, `eliminate_imp` | Remove ↔ and → using equivalences |
| `push_negation` | De Morgan's laws + double negation → **NNF** |
| `distribute_or` | \(P \lor (Q \land R) \equiv (P \lor Q) \land (P \lor R)\) → **CNF** |
| `extract_clauses(cnf)` | Walk CNF AST; each top-level ∧ becomes one clause |
| `_resolve(c1, c2)` | If \(L \in c_1\) and \(\neg L \in c_2\), return \((c_1 \setminus \{L\}) \cup (c_2 \setminus \{\neg L\})\) |
| `resolution_solver(clauses)` | Fixpoint loop over all clause pairs; records every step |
| `solve_resolution(formula_str)` | Orchestrates parse → NNF → CNF → clauses → resolution |

#### AST representation

Formulas are stored as nested tuples, e.g.:

```python
('AND', ('OR', ('VAR', 'p'), ('NOT', ('VAR', 'q'))), ('VAR', 'r'))
#  represents  (p ∨ ¬q) ∧ r
```

This tree structure makes structural rewrites (NNF, distribution) straightforward recursive functions.

#### Resolution loop

```python
while changed:
    for c1, c2 in combinations(working, 2):
        res = resolve(c1, c2)
        if res is new:
            add res to working set
            record step with parent clause labels
            if res is empty: return UNSATISFIABLE
return SATISFIABLE
```

The frontend displays each clause with a label (`C1`, `C2`, …) and shows which parent clauses produced each resolvent.

---

### 3. Formula Transformer (`algorithms/transformer.py`)

#### Theory

| Normal form | Property | Construction |
|-------------|----------|--------------|
| **NNF** | Negations only on atoms | Eliminate →, ↔; push ¬ inward |
| **CNF** | Conjunction of disjunctions | NNF + distribute ∨ over ∧ |
| **DNF** | Disjunction of conjunctions | NNF + distribute ∧ over ∨ |

The module reuses the parser and AST transforms from `resolution.py` via imports.

#### Code structure

| Function | Output |
|----------|--------|
| `get_all_transforms(formula_str)` | Main entry: returns NNF, CNF, DNF, and truth table |
| NNF steps | Four annotated steps: original → remove ↔ → remove → → push negations |
| CNF steps | NNF → distribute ∨ over ∧ → clause list |
| DNF steps | NNF → distribute ∧ over ∨ → minterm list |
| `_truth_table(ast, variables)` | Evaluates formula for all \(2^n\) assignments |
| Classification | `is_tautology`, `is_contradiction`, `is_satisfiable` |

#### Truth table generation

For \(n\) variables, the code iterates `mask` from `0` to `2^n - 1`, maps each bit to True/False, and evaluates the AST with `_eval()`. This provides independent verification of the formula's semantic properties alongside the syntactic normal forms.

---

### 4. AI Explainer (`algorithms/ai_explainer.py`)

Optional educational feature: after a computation, the user can request a **natural-language explanation** streamed from Groq (LLaMA 3.3 70B).

**How it works:**

1. Frontend POSTs computation results to `/api/explain/<module>`  
2. `explain_stream(module, data)` selects a prompt builder (`automata`, `resolution`, `transformer`)  
3. The prompt includes **only the actual steps from the computation** - the model is instructed not to invent steps  
4. Response is streamed via **Server-Sent Events (SSE)** and rendered as markdown in the UI  

This layer does not affect correctness of the algorithms; it is a tutoring aid built on top of the structured JSON output.

> **Note:** Requires a `GROQ_API_KEY` environment variable. See [Installation](#installation-and-running).

---

## Frontend Architecture

| File | Responsibility |
|------|----------------|
| `templates/base.html` | Sidebar navigation, mobile toggle, toast container, shared assets |
| `static/css/main.css` | CSS variables (colours, spacing), cards, forms, grids, **responsive breakpoints** (900px, 600px) |
| `static/js/main.js` | Sidebar/backdrop, `apiCall()`, toasts, tabs, accordions |
| `automata.html` | Cytoscape graph, playback bar, input tape, step pips |
| `resolution.html` | Clause chips, resolution step list, CNF transformation rows |
| `transformer.html` | NNF/CNF/DNF cards, truth table with horizontal scroll on small screens |
| `welcome.html` + `welcome.css` | Landing page with module showcase; mobile hamburger menu |

**Responsive design:** The UI adapts to phones and tablets - collapsible sidebar, stacked grids, scrollable tables, and full-width buttons on narrow viewports.

---

## Input Syntax

### Propositional logic

| Symbol | Operator | Example |
|--------|----------|---------|
| `~` | Negation (¬) | `~p` |
| `&` | Conjunction (∧) | `p & q` |
| `\|` | Disjunction (∨) | `p \| q` |
| `->` | Implication (→) | `p -> q` |
| `<->` | Biconditional (↔) | `p <-> q` |

Parentheses are supported: `(p | q) & (~p | r) & (~q | ~r)`

### Finite automaton transitions

Semicolon-separated triples: `from_state, symbol, to_state`

```
q0,a,q1;q0,b,q0;q1,a,q1;q1,b,q2;q2,a,q2;q2,b,q2
```

Use `ε` for epsilon transitions (NFA).

---

## Installation and Running

### Prerequisites

- Python **3.10+** (developed and tested on 3.13)
- pip
- Optional: [Groq API key](https://console.groq.com) for AI explanations

### Steps

```bash
# 1. Navigate to project folder
cd ProofLab-TFCS-Platform-v3.13.0

# 2. Create virtual environment
python -m venv venv

# 3. Activate (Windows)
venv\Scripts\activate

# 3. Activate (Linux / macOS)
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. (Optional) Create .env for AI explainer
# GROQ_API_KEY=your_key_here

# 6. Run the server
python app.py
```

Open **http://localhost:5000** in a browser.

---

## Demo Guide for Evaluation

Suggested walkthrough for demonstrating the project:

| Step | Route | Action | What to observe |
|------|-------|--------|-----------------|
| 1 | `/` | Browse landing page | Project overview, module descriptions |
| 2 | `/index` | Open dashboard | Three module cards |
| 3 | `/automata` | Load **"Binary divisible by 3"** example → **Simulate** | State diagram, step playback, ACCEPT/REJECT verdict |
| 4 | `/automata` | Switch to **NFA**, load **"NFA: ends in ab"** | ε-closure and multi-state trace |
| 5 | `/resolution` | Enter `(p -> q) & (~q) & p` → **Solve** | CNF conversion, clause list, resolution steps → UNSAT |
| 6 | `/transformer` | Enter `p \| ~p` → **Transform** | NNF/CNF/DNF steps, truth table → **Tautology** |
| 7 | Any module | Click **Explain with AI** (if API key configured) | Streaming natural-language explanation |

---

## Screenshots

### Welcome Page
![Welcome Page](static/img/welcome.gif)

### Automata Simulator - DFA / NFA
![Automata Simulator](static/img/automata1.gif)

### Formula Transformer - NNF / CNF / DNF
![Formula Transformer](static/img/transformation.gif)

### Resolution Solver
![Resolution Solver](static/img/Resolution.gif)

---

## Dependencies

| Package | Role |
|---------|------|
| Flask 3.1.3 | Web framework, routing, JSON responses |
| Jinja2 3.1.6 | HTML template engine |
| groq | AI explanation streaming (optional) |
| Werkzeug | WSGI utilities (Flask dependency) |

Full pinned list: see `requirements.txt`.

---

## Future Work

- [ ] Turing Machine simulator  
- [ ] CYK parser for context-free grammars  
- [ ] Regular expression engine  
- [ ] Unification algorithm UI (backend structure exists in `ai_explainer.py`)  
- [ ] PDA simulator page (algorithm in `algorithms/pda.py`, API routes in `app.py`)  

---

## Conclusion

ProofLab implements central TFCS algorithms - automata simulation, normal form transformation, and resolution - as a working web application with clear separation between **computation** (Python algorithms) and **presentation** (HTML/CSS/JS). Every module returns a structured step trace, making the tool suitable both as a course project deliverable and as a study aid for formal methods.

The codebase is organised so that each algorithm file can be read independently, matching the modular structure of the course itself: define a formal system, implement the procedure, verify on examples.

---

<div align="center">
  <strong>Lasha Giorgadze (G1orga)</strong><br>
  ProofLab v3.13.0 · Theoretical Foundations of Computer Science
</div>

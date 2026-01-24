# Modulus-of-One / Constructionist Arithmetic  
## Prototype Formalization & Vision  
Version: 0.1-proto  
Status: Internal design note

---

## 1. Purpose

This document links:

* the **conceptual foundation** (“Foundations of a Constructionist Mathematical System”), and
* the current **Python prototype** (`constructionist_math.py`)

into a single, clear description of what exists today and what it should grow into.

It’s meant to be a drop-in reference for future work on the “Modulus-of-One” / constructionist arithmetic stack.

---

## 2. Conceptual Core (Short Recap)

The system is based on a few strict ideas:

1. **1 is the only primitive certainty.**
   Everything else is constructed by acting on 1.

2. **Permitted actions are just `+`, `-`, `*`, `/`.**
   No sets, no real line, no pre-baked ℤ, ℚ, ℝ.

3. **Every constructed value is either:**

   * **Grounded (G):** actually constructed from grounded inputs.
   * **Speculative (S):** inferred/derived claims (including non-integer division, and integer claims from `*` and `/` until they align to an explicitly grounded `Ref(N)`).

4. **Identity is by normalization**, not by symbol:
   If multiple paths normalize to the same integer `N`, they converge on a single node `Ref(N)`.

5. **Zero, negatives, and fractions emerge**, they are not primitives:

   * `0` from `1 - 1`
   * negatives from `0 - n`
   * fractions from division that does *not* yield an integer (staying S)

The prototype is a first concrete realization of that picture.

---

## 3. Current Prototype: Data Model

File: `constructionist_math.py`

### 3.1 Node

```python
@dataclass
class Node:
    id: NodeId          # int for G, str like "S1" for S
    status: Status      # "G" or "S"
    metadata: Dict[str, object] = field(default_factory=dict)

    def label(self) -> str:
        prefix = "Ref" if self.status == "G" else "S"
        return f"{prefix}({self.id})"
```

* **Grounded nodes** (`status == "G"`) represent integers `Ref(N)` (`id` is an `int`).
* **Speculative nodes** (`status == "S"`) represent ungrounded results, `Sx` (`id` is a string).
* `metadata` records:

  * for all nodes:
    * `tier`:
      * `1` for the single primitive certainty `Ref(1)`
      * `2` for grounded (constructed) integers `Ref(N)` where `N != 1`
      * `3` for speculative / inferred nodes (e.g. non-integer division)
  * for S nodes:
    * a stable **value identity** when known: `{"value": {"p": ..., "q": ...}}` (a reduced rational `p/q`)
    * plus a “seed” provenance like `{"op": ..., "inputs": [...]}` from the first time that value was seen
    * integer-claims can carry `{"potential_val": N}` so they can snap to `Ref(N)` once `Ref(N)` exists
  * for special nodes: e.g. division by zero reason.

### 3.2 Edge

```python
@dataclass
class Edge:
    op: str             # "+", "-", "*", "/"
    inputs: List[Node]
    output: Node
    metadata: Dict[str, object] = field(default_factory=dict)
```

An edge is a **construction step**:

* which operation was used,
* which input nodes it consumed,
* which node it produced,
* any additional metadata (`result`, `rule`, etc.).

### 3.3 Graph

```python
class Graph:
    def __init__(self) -> None:
        self.nodes_by_int: Dict[int, Node] = {}
        self.speculative_nodes: Dict[str, Node] = {}
        self._speculative_by_value: Dict[Tuple[int, int], Node] = {}
        self.edges: List[Edge] = []
        self._snap_events: List[Dict[str, object]] = []
        self._spec_counter = itertools.count(1)
        self._div_by_zero_node: Optional[Node] = None
        # Seed with Ref(1)
        self._get_or_create_grounded_ref(1)
```

The `Graph` maintains:

* A unique map from `int → Ref(N)` for grounded integers (including 0 and negatives) that have been explicitly constructed.
* A map from speculative IDs (`"S1"`, `"S2"`, …) → speculative nodes.
* A **value-interning table** `p/q → Node` (reduced rationals) so speculative nodes are unique by value (e.g. `5/2`, `10/4`, and `2 + 1/2` converge on the same node).
* A list of all edges (construction history).
* A log of speculative → grounded snapping events.
* An internal counter for new speculative node IDs.
* A singleton node for division by zero.

---

## 4. Normalization & Identity

### 4.1 Integer-level normalization

```python
def _normalize(self, op: str, a: int, b: int) -> Tuple[str, Optional[int]]:
    if op == "+":
        return ("int", a + b)
    if op == "-":
        return ("int", a - b)
    if op == "*":
        if a == 1: return ("int", b)
        if b == 1: return ("int", a)
        if a == 0 or b == 0: return ("int", 0)
        return ("int", a * b)
    if op == "/":
        if b == 0:
            return ("undefined", None)
        if a % b == 0:
            return ("int", a // b)
        return ("non_integer", None)
```

* For grounded inputs `Ref(a)`, `Ref(b)`, normalization returns:

  * `("int", N)`
  * `("non_integer", None)`
  * or `("undefined", None)` (division by zero).

### 4.2 Node identity

```python
def get_or_create_ref(self, n: int) -> Node:
    n = int(n)
    grounded = self.nodes_by_int.get(n)
    if grounded is not None:
        self._snap_speculative_to_ref(n, grounded)
        return grounded
    if n == 1:
        return self._get_or_create_grounded_ref(1)
    return self.speculate_ref(n, reason="unconstructed_integer")
```

* There is exactly **one** `Ref(N)` node per integer.
* `Ref(1)` is the only first-class primitive; other integers become grounded only when constructed by explicit edges.
* When a new `Ref(N)` is created or reused, the graph **snaps** speculative nodes with `potential_val == N` into that grounded node.

---

## 5. Speculative Potential & Snapping

The prototype defines a consistent notion of “potential integer”:

```python
def _node_potential_int(self, node: Node) -> Optional[int]:
    if node.status == "G":
        return int(node.id)
    potential = node.metadata.get("potential_val")
    return int(potential) if isinstance(potential, int) else None
```

* For grounded nodes: potential integer = their `id`.
* For S nodes: potential integer = the `potential_val` in metadata, if any.

From that, it computes potential results of operations with speculative inputs:

```python
def _maybe_potential(self, op: str, a: Node, b: Node) -> Optional[int]:
    left = self._node_potential_int(a)
    right = self._node_potential_int(b)
    if left is None or right is None:
        return None
    kind, val = self._normalize(op, left, right)
    if kind == "int":
        return val
    return None
```

Similar for division:

```python
def _potential_division(self, a: Node, b: Node) -> Optional[int]:
    left = self._node_potential_int(a)
    right = self._node_potential_int(b)
    if right is None or right == 0 or left is None:
        return None
    kind, val = self._normalize("/", left, right)
    if kind == "int":
        return val
    return None
```

When a new `Ref(N)` is grounded, speculative nodes with `potential_val == N` are snapped:

```python
def _snap_speculative_to_ref(self, n: int, ref_node: Node) -> None:
    to_snap = [
        node for node in self.speculative_nodes.values()
        if node.metadata.get("potential_val") == n
    ]
    for node in to_snap:
        self._replace_node(node, ref_node)
        node.metadata["resolved_to"] = n
        self.speculative_nodes.pop(node.id, None)
```

This encodes the epistemic rule:

> If a speculative structure was “pointing at” N, and N becomes grounded, that speculation is resolved and folded into the grounded node.

---

## 6. Operational Semantics (Proto-Level)

### 6.1 Shared pattern

All operations follow a common pattern:

1. If both inputs are grounded (`G,G`):

   * `+` / `-`: use `_normalize` and **create** the resulting `Ref(N)` (grounded).
   * `*` / `/`: compute the exact rational result and **intern** it:
     * non-integer → a canonical speculative rational node keyed by reduced `p/q`
     * integer `N` → a speculative integer-claim unless `Ref(N)` already exists (then it snaps/converges to `Ref(N)`)
2. If any input is speculative:

   * when both inputs carry an exact rational value, compute the exact result and intern it by value;
     integer results remain speculative unless the corresponding `Ref(N)` is already grounded
   * otherwise attempt to compute `potential_val` using `_maybe_potential` / `_potential_division`
3. Create **or reuse** a speculative node via value interning.
4. Record an edge.
5. If a speculative node has `potential_val = N` and `Ref(N)` already exists, snap immediately.

### 6.2 Addition / Subtraction

```python
def add(self, a: Node, b: Node) -> Node:
    if a.status == "G" and b.status == "G":
        ...
    potential = self._maybe_potential("+", a, b)
    metadata = {"op": "+", "inputs": self._input_ids([a, b])}
    if potential is not None:
        metadata["potential_val"] = potential
    out = self._new_spec_node(metadata)
    self._record_edge("+", [a, b], out, {"result": "speculative", "potential_val": potential})
    return self._maybe_snap_new_spec_to_existing_ref(out)
```

Subtraction is analogous.

### 6.3 Multiplication with zero-annihilation

Key behavior:

* If one input is definitely `0` and the other input is unknown, multiply still yields a `0` **claim** (recorded with `"rule": "zero_annihilation"`).
* `*` does **not** create new grounded integers. Integer results are speculative claims until the corresponding `Ref(N)` is grounded by explicit iteration (`+` / `-`), at which point they snap.

### 6.4 Division

```python
def div(self, a: Node, b: Node) -> Node:
    if b.status == "G" and b.id == 0:
        node = self._div_by_zero()
        self._record_edge("/", [a, b], node, {"result": "div_by_zero"})
        return node

    # If both inputs carry an exact rational value (grounded ints always do),
    # compute the exact result and INTERN it so it is unique by value p/q.
    # If p/q is an integer, it becomes Ref(p).

    potential = self._potential_division(a, b)
    metadata = {"op": "/", "inputs": self._input_ids([a, b])}
    if potential is not None:
        metadata["potential_val"] = potential
    out = self._new_spec_node(metadata)
    self._record_edge("/", [a, b], out, {"result": "speculative", "potential_val": potential})
    return self._maybe_snap_new_spec_to_existing_ref(out)
```

* Division by zero: a dedicated, reusable speculative node (`S_div_by_zero`).
* Non-integer division: a **canonical** speculative rational node (interned by reduced `p/q`).
* Integer division: produces a speculative integer-claim unless `Ref(N)` already exists (then it snaps/converges to that grounded node).
* If exact rational values are known, the result is interned by value; otherwise fall back to speculative `potential_val`.

---

## 7. Demo Universe (Limit 3)

```python
def demo(limit: int = 3) -> Graph:
    g = Graph()
    one = g.get_or_create_ref(1)
    zero = g.sub(one, one)

    # Create a speculative integer-claim that will later snap to Ref(2).
    shadow_two = g.speculate_ref(2, reason="demo_shadow_ref")
    g.add(shadow_two, one)  # potential_val=3, will snap once Ref(3) is grounded

    limit = max(0, int(limit))

    positives = {1: one}
    for n in range(2, limit + 1):
        positives[n] = g.add(positives[n - 1], one)

    current = zero
    for _ in range(1, limit + 1):
        current = g.sub(current, one)

    # Apply a bounded set of multiplication/division steps within the integer backbone.
    ints = [g.nodes_by_int[n] for n in sorted(g.nodes_by_int.keys())]
    for i, a in enumerate(ints):
        ai = int(a.id)
        for j, b in enumerate(ints):
            bi = int(b.id)
            if j >= i and abs(ai) >= 2 and abs(bi) >= 2:
                prod = ai * bi
                if abs(prod) <= limit:
                    g.mul(a, b)
            if abs(bi) >= 2 and bi != 0 and ai % bi == 0:
                quotient = ai // bi
                if abs(quotient) <= limit:
                    g.div(a, b)

    if limit >= 2:
        half = g.div(one, positives[2])
        g.mul(half, zero)
    if limit >= 3:
        third = g.div(one, positives[3])
        g.add(half, third)

    return g
```

This builds:

* `Ref(1)` as seed.
* `Ref(0)` via `1 - 1`.
* Integers outward to `±limit` via repeated `+1` / `-1` construction steps.
* A speculative integer-claim that snaps when its `Ref(N)` is later grounded.
* A bounded set of integer multiplication/division facts within that backbone.
* Speculative fractions from non-integer division (e.g. `1/2`) and a zero-annihilation example.

Exports:

* `to_json()` → machine-readable introspection.
* `to_dot()` → Graphviz visualization.

---

## 8. Vision: Where This Should Go

This prototype is enough to support several future directions.

### 8.1 Near-term: Deepen the integer/S-structure

* **Larger demo universes**:

  * generate up to `limit = 10`, `20`, etc.
  * gather statistics on:

    * number of edges per node (path redundancy)
    * number of S nodes vs G nodes
    * distribution of `potential_val`
* **Stress-test snapping behavior**:

  * construct speculative nodes that carry `potential_val = 2` or `3` first (e.g. via operations on speculative inputs without exact values),
  * then ground `Ref(2)` or `Ref(3)` via pure `G,G` ops,
  * confirm that snapping rewires edges correctly.
* **Enrich metadata**:

  * track “depth” or “cost” of each edge,
  * track the first grounding path per `Ref(N)` vs later redundant paths.

### 8.2 Metrics & “Epistemic Geometry”

Define and compute:

* **Path redundancy**: how many distinct edges/paths lead into a node.
* **Centrality**: degree/betweenness of nodes like `Ref(0)`, `Ref(1)`, `Ref(2)`, `Ref(6)` in larger universes.
* **Speculation density**: number of S nodes “near” a given integer (in terms of one operation away).
* **Snapping events**: log every time an S node is resolved into a G node.

The prototype includes:

* `Graph.stats()` for basic counts/degree/redundancy.
* `Graph.snap_events()` for snapping telemetry.

These metrics can support an emergent “field” interpretation:

* integers as **attractors**,
* zero as a **singularity**,
* speculative halo around certain regions.

### 8.3 Visualization

Build minimal tooling on top of JSON / DOT:

* Interactive graph viewer:

  * color by status (G vs S),
  * size by degree / redundancy,
  * highlight speculative chains and snapping events over time.
* Layered views:

  * integer backbone only,
  * speculative halo only,
  * edges by operation type (+/−/×/÷).

The prototype can emit a few “map” views directly:

* `python3 constructionist_math.py --snap-dot --limit 6` — DOT augmented with “ghost” nodes/edges for S → G snapping.
* `python3 constructionist_math.py --field --field-ascii --limit 6` — per-integer number-line metrics (JSON + ASCII).
* `python3 constructionist_math.py --write-maps out/moo_demo --limit 6` — writes `out/moo_demo.*` files for DOT/CSV/JSON.

### 8.4 Extending the mathematical universe

Careful, staged steps:

1. **Structured rationals (optional future)**:

   * Instead of bare `S` nodes for `non_integer`, introduce `Rational(p, q)` structures *if* desired.
   * Still keep them S until grounded by some explicit rule.

2. **Constraints or rewrite rules**:

   * optionally add associativity/commutativity as structural rules in a future version,
   * or deliberately *do not*, to preserve construction history as primary.

3. **New status layers**:

   * In addition to G/S, later versions could differentiate:

     * *Proven speculative* vs *impossible speculative*,
     * or S → “refuted” when no consistent grounding is possible under extended rules.

---

## 9. Long-term Vision

The Python prototype is deliberately pragmatic. Longer-term, this could evolve into:

### 9.1 A formal foundation (Lean/Agda/Coq)

* Encode `Ref(N)`, S nodes, operations, and snapping in a dependently typed language.
* Prove structural theorems:

  * consistency of the construction rules,
  * properties of the grounded integer subgraph,
  * invariants under extension.

### 9.2 A “Modulus-of-One” language

* Treat `1` as the only primitive literal.
* Allow only `+`, `-`, `*`, `/` as primitive combinators.
* Execution builds the graph; evaluation reads off grounded results and speculative structures.

The prototype includes a minimal evaluator for this idea:

* `eval_moo(expr)` — parses an expression using only the literal `1` and `+ - * /`.
* `python3 constructionist_math.py '1/(1+1)'` — builds and prints the resulting graph.
* `python3 constructionist_math.py --stats '1/(1+1)'` — prints `Graph.stats()` and `Graph.snap_events()` as JSON.

### 9.3 A research object in epistemology / theory of computation

Use the system as:

* a model of **how knowledge structures grow** from a single primitive certainty,
* a testbed for:

  * construction vs abstraction,
  * speculative vs grounded inference,
  * how redundancy stabilizes concepts.

---

## 10. Summary

What exists now:

* A precise, working Python prototype of the constructionist arithmetic graph, starting from `Ref(1)` and building out small integer universes with speculative fringes.
* Fully explicit semantics for:

  * grounded vs speculative nodes,
  * integer normalization,
  * division behavior,
  * zero-annihilation,
  * speculative `potential_val`,
  * S → G snapping.

What this document does:

* It anchors that prototype to the original conceptual goals.
* It frames the code as the **first layer** of a larger Modulus-of-One project.
* It sketches clear paths for future work without locking in premature commitments.

You can drop this file into the repo as `VISION.md` or `SPEC_PROTO.md` and treat it as the reference for where to push next.

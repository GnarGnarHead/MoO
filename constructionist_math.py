from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union, Literal
import ast
from fractions import Fraction
import itertools
import json
from pathlib import Path
import sys

Status = Literal["G", "S"]
NodeId = Union[int, str]


@dataclass
class Node:
    id: NodeId
    status: Status
    metadata: Dict[str, object] = field(default_factory=dict)

    def label(self) -> str:
        prefix = "Ref" if self.status == "G" else "S"
        return f"{prefix}({self.id})"


@dataclass
class Edge:
    op: str
    inputs: List[Node]
    output: Node
    metadata: Dict[str, object] = field(default_factory=dict)


class Graph:
    """
    Constructionist arithmetic graph.

    Grounded nodes (status G) represent integers Ref(N).
    Speculative nodes (status S) capture non-integer results or operations that
    depend on speculative inputs.
    """

    def __init__(self) -> None:
        self.nodes_by_int: Dict[int, Node] = {}
        self.speculative_nodes: Dict[str, Node] = {}
        self._speculative_by_value: Dict[Tuple[int, int], Node] = {}
        self.edges: List[Edge] = []
        self._snap_events: List[Dict[str, object]] = []
        self._spec_counter = itertools.count(1)
        self._div_by_zero_node: Optional[Node] = None
        # Seed with the only first-class primitive: Ref(1)
        self._get_or_create_grounded_ref(1)

    # --- core helpers ---
    def _node_value(self, node: Node) -> Optional[Fraction]:
        """
        Return the exact rational value for a node when it is known.

        - Grounded ints always have a value.
        - Speculative nodes have a value when they were interned as a rational
          (or as an integer claim) and carry metadata["value"].
        """
        if node.status == "G":
            return Fraction(int(node.id), 1)
        value = node.metadata.get("value")
        if not isinstance(value, dict):
            return None
        p = value.get("p")
        q = value.get("q")
        if not isinstance(p, int) or not isinstance(q, int):
            return None
        if q == 0:
            return None
        return Fraction(p, q)

    def _intern_value(
        self,
        value: Fraction,
        *,
        seed_op: str,
        seed_inputs: List[NodeId],
        result_tag: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Node:
        """
        Return a canonical node for an exact rational value.

        Non-integer rationals always intern as speculative nodes.

        Integer values return a grounded Ref(N) only if that Ref(N) is already
        grounded (i.e., has been explicitly constructed). Otherwise they intern
        as a speculative integer-claim node with potential_val=N.
        """
        value = Fraction(value.numerator, value.denominator)
        if value.denominator == 1:
            n = int(value.numerator)
            grounded = self.nodes_by_int.get(n)
            if grounded is not None:
                return grounded
            key = (n, 1)
        else:
            key = (int(value.numerator), int(value.denominator))

        existing = self._speculative_by_value.get(key)
        if existing is not None:
            return existing

        metadata: Dict[str, object] = {"op": seed_op, "inputs": list(seed_inputs), "tier": 3}
        metadata["value"] = {"p": key[0], "q": key[1]}
        if key[1] == 1:
            metadata["potential_val"] = key[0]
        if result_tag is not None:
            metadata["result"] = result_tag
        if reason is not None:
            metadata["reason"] = reason
        node = self._new_spec_node(metadata)
        self._speculative_by_value[key] = node
        return node

    def _drop_interned_value(self, node: Node) -> None:
        value = node.metadata.get("value")
        if not isinstance(value, dict):
            return
        p = value.get("p")
        q = value.get("q")
        if not isinstance(p, int) or not isinstance(q, int):
            return
        self._speculative_by_value.pop((p, q), None)

    def _canonicalize_node(self, node: Node) -> Node:
        """
        Resolve stale speculative nodes that have already snapped/promoted to a
        grounded Ref(N), so callers holding old references don't reintroduce
        the speculative node into new edges.
        """
        if node.status != "S":
            return node
        resolved_to = node.metadata.get("resolved_to")
        if isinstance(resolved_to, int):
            ref = self.nodes_by_int.get(resolved_to)
            if ref is not None:
                return ref
        return node

    def _new_spec_node(self, metadata: Dict[str, object]) -> Node:
        metadata.setdefault("tier", 3)
        node_id = f"S{next(self._spec_counter)}"
        node = Node(id=node_id, status="S", metadata=metadata)
        self.speculative_nodes[node_id] = node
        return node

    def _input_ids(self, inputs: List[Node]) -> List[NodeId]:
        return [inp.id for inp in inputs]

    def _record_edge(
        self,
        op: str,
        inputs: List[Node],
        output: Node,
        metadata: Optional[Dict[str, object]] = None,
    ) -> Edge:
        edge_meta = metadata or {}
        edge = Edge(op=op, inputs=inputs, output=output, metadata=edge_meta)
        self.edges.append(edge)
        return edge

    def _count_usages(self, node: Node) -> int:
        usages = 0
        for edge in self.edges:
            if edge.output is node:
                usages += 1
            for inp in edge.inputs:
                if inp is node:
                    usages += 1
        return usages

    def _get_or_create_grounded_ref(self, n: int) -> Node:
        n = int(n)
        node = self.nodes_by_int.get(n)
        if node is not None:
            self._snap_speculative_to_ref(n, node)
            return node
        metadata: Dict[str, object] = {"tier": 1 if n == 1 else 2}
        if n == 1:
            metadata["primitive"] = True
        node = Node(id=n, status="G", metadata=metadata)
        self.nodes_by_int[n] = node
        self._snap_speculative_to_ref(n, node)
        return node

    def get_or_create_ref(self, n: int) -> Node:
        """
        Public helper for referring to Ref(N).

        - Ref(1) is the only first-class primitive and may be created directly.
        - Other integers are second-class: they must be explicitly constructed.
          If Ref(N) is not yet grounded, this returns a speculative integer-claim
          node instead.
        """
        n = int(n)
        grounded = self.nodes_by_int.get(n)
        if grounded is not None:
            self._snap_speculative_to_ref(n, grounded)
            return grounded
        if n == 1:
            return self._get_or_create_grounded_ref(1)
        return self.speculate_ref(n, reason="unconstructed_integer")

    def frontier(self) -> Dict[str, int]:
        if not self.nodes_by_int:
            return {"min": 0, "max": 0}
        keys = self.nodes_by_int.keys()
        return {"min": int(min(keys)), "max": int(max(keys))}

    def advance_frontier_max_to(self, n: int) -> None:
        """
        Extend the positive frontier by iterating +1 from the current maximum.
        """
        target = int(n)
        one = self.get_or_create_ref(1)
        while True:
            current_max = int(self.frontier()["max"])
            if current_max >= target:
                return
            current = self.get_or_create_ref(current_max)
            self.add(current, one)

    def advance_frontier_min_to(self, n: int) -> None:
        """
        Extend the negative frontier by iterating -1 from the current minimum.
        """
        target = int(n)
        one = self.get_or_create_ref(1)
        while True:
            current_min = int(self.frontier()["min"])
            if current_min <= target:
                return
            current = self.get_or_create_ref(current_min)
            self.sub(current, one)

    def speculate_ref(self, n: int, *, reason: Optional[str] = None) -> Node:
        """
        Create a speculative node that is believed to correspond to Ref(n),
        but is not yet grounded by an explicit construction path.
        """
        if n in self.nodes_by_int:
            return self.nodes_by_int[n]
        return self._intern_value(
            Fraction(int(n), 1),
            seed_op="speculate_ref",
            seed_inputs=[],
            reason=reason,
        )

    def snap_events(self) -> List[Dict[str, object]]:
        return list(self._snap_events)

    def stats(self, *, top_k: int = 5) -> Dict[str, object]:
        op_counts: Dict[str, int] = {}
        in_degree: Dict[NodeId, int] = {}
        out_degree: Dict[NodeId, int] = {}
        output_edge_counts: Dict[NodeId, int] = {}

        for edge in self.edges:
            op_counts[edge.op] = op_counts.get(edge.op, 0) + 1
            output_edge_counts[edge.output.id] = output_edge_counts.get(edge.output.id, 0) + 1
            for inp in edge.inputs:
                out_degree[inp.id] = out_degree.get(inp.id, 0) + 1
                in_degree[edge.output.id] = in_degree.get(edge.output.id, 0) + 1

        all_nodes = list(self.nodes_by_int.values()) + list(self.speculative_nodes.values())
        for node in all_nodes:
            in_degree.setdefault(node.id, 0)
            out_degree.setdefault(node.id, 0)
            output_edge_counts.setdefault(node.id, 0)

        def top(counter: Dict[NodeId, int]) -> List[Dict[str, object]]:
            items = sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))
            return [{"id": node_id, "count": count} for node_id, count in items[: max(0, top_k)]]

        grounded_ints = list(self.nodes_by_int.keys())
        grounded_range: Optional[Dict[str, int]] = None
        if grounded_ints:
            grounded_range = {"min": min(grounded_ints), "max": max(grounded_ints)}

        grounded_constructions: Dict[int, int] = {
            n: int(output_edge_counts.get(n, 0)) for n in grounded_ints
        }
        multi_constructed_grounded = {n: c for n, c in grounded_constructions.items() if c > 1}

        potential_val_hist: Dict[int, int] = {}
        speculative_with_potential_val = 0
        for node in self.speculative_nodes.values():
            potential_val = node.metadata.get("potential_val")
            if isinstance(potential_val, int):
                speculative_with_potential_val += 1
                potential_val_hist[potential_val] = potential_val_hist.get(potential_val, 0) + 1

        return {
            "counts": {
                "grounded_nodes": len(self.nodes_by_int),
                "speculative_nodes": len(self.speculative_nodes),
                "edges": len(self.edges),
                "snap_events": len(self._snap_events),
            },
            "grounded_range": grounded_range,
            "ops": op_counts,
            "degree": {
                "max_in": max(in_degree.values(), default=0),
                "max_out": max(out_degree.values(), default=0),
                "top_in": top(in_degree),
                "top_out": top(out_degree),
            },
            "constructions": {
                "grounded_with_multiple_constructions": len(multi_constructed_grounded),
                "max_constructions_into_grounded": max(grounded_constructions.values(), default=0),
                "top_grounded_by_constructions": top({n: c for n, c in grounded_constructions.items()}),
            },
            "speculation": {
                "speculative_with_potential_val": speculative_with_potential_val,
                "potential_val_histogram": potential_val_hist,
            },
        }

    def _replace_node(self, old: Node, new: Node) -> None:
        for edge in self.edges:
            if edge.output is old:
                edge.output = new
            for idx, inp in enumerate(edge.inputs):
                if inp is old:
                    edge.inputs[idx] = new

    def _maybe_snap_new_spec_to_existing_ref(self, node: Node) -> Node:
        if node.status != "S":
            return node
        potential_val = node.metadata.get("potential_val")
        if not isinstance(potential_val, int):
            return node
        ref_node = self.nodes_by_int.get(potential_val)
        if ref_node is None:
            return node
        self._snap_speculative_to_ref(potential_val, ref_node)
        return ref_node

    def _snap_speculative_to_ref(self, n: int, ref_node: Node) -> None:
        to_snap = [
            node for node in self.speculative_nodes.values()
            if node.metadata.get("potential_val") == n
        ]
        for node in to_snap:
            usages = 0
            for edge in self.edges:
                if edge.output is node:
                    usages += 1
                for inp in edge.inputs:
                    if inp is node:
                        usages += 1
            self._snap_events.append(
                {
                    "spec_id": node.id,
                    "resolved_to": n,
                    "usages": usages,
                    "spec_metadata": dict(node.metadata),
                }
            )
            self._replace_node(node, ref_node)
            # Preserve that this speculative node was resolved.
            node.metadata["resolved_to"] = n
            self._drop_interned_value(node)
            self.speculative_nodes.pop(node.id, None)

    def to_snap_dot(self) -> str:
        lines = ["digraph G {"]

        for node in self.nodes_by_int.values():
            lines.append(
                f'  "{node.id}" [label="{node.label()}", shape=box, style=filled, fillcolor=lightgray];'
            )
        for node in self.speculative_nodes.values():
            lines.append(
                f'  "{node.id}" [label="{node.label()}", shape=ellipse, style=filled, fillcolor=yellow];'
            )

        ghost_ids: Dict[str, str] = {}
        for event in self._snap_events:
            spec_id = str(event.get("spec_id"))
            ghost_id = f"ghost_{spec_id}"
            ghost_ids[spec_id] = ghost_id

        for event in self._snap_events:
            spec_id = str(event.get("spec_id"))
            resolved_to = event.get("resolved_to")
            spec_metadata = event.get("spec_metadata")

            ghost_id = ghost_ids[spec_id]
            op = ""
            if isinstance(spec_metadata, dict):
                op_val = spec_metadata.get("op")
                if isinstance(op_val, str):
                    op = op_val
            op_suffix = f" ({op})" if op else ""
            lines.append(
                f'  "{ghost_id}" [label="{spec_id}{op_suffix} -> Ref({resolved_to})", '
                'shape=ellipse, style="filled,dashed", fillcolor=lightblue, color=blue];'
            )
            lines.append(
                f'  "{ghost_id}" -> "{resolved_to}" [label="snap", style=dashed, color=blue];'
            )

            if isinstance(spec_metadata, dict):
                inputs = spec_metadata.get("inputs")
                if isinstance(inputs, list):
                    for inp in inputs:
                        src = ghost_ids.get(str(inp), str(inp))
                        edge_label = op if op else "spec"
                        lines.append(
                            f'  "{src}" -> "{ghost_id}" [label="{edge_label}", style=dotted, color=blue];'
                        )

        for edge in self.edges:
            for inp in edge.inputs:
                lines.append(f'  "{inp.id}" -> "{edge.output.id}" [label="{edge.op}"];')
        lines.append("}")
        return "\n".join(lines)

    def field_map(self) -> List[Dict[str, int]]:
        in_degree: Dict[NodeId, int] = {}
        out_degree: Dict[NodeId, int] = {}
        output_edge_counts: Dict[NodeId, int] = {}

        for edge in self.edges:
            output_edge_counts[edge.output.id] = output_edge_counts.get(edge.output.id, 0) + 1
            for inp in edge.inputs:
                out_degree[inp.id] = out_degree.get(inp.id, 0) + 1
                in_degree[edge.output.id] = in_degree.get(edge.output.id, 0) + 1

        snap_counts: Dict[int, int] = {}
        for event in self._snap_events:
            resolved_to = event.get("resolved_to")
            if isinstance(resolved_to, int):
                snap_counts[resolved_to] = snap_counts.get(resolved_to, 0) + 1

        rows: List[Dict[str, int]] = []
        for n in sorted(self.nodes_by_int.keys()):
            rows.append(
                {
                    "n": int(n),
                    "constructions": int(output_edge_counts.get(n, 0)),
                    "in_degree": int(in_degree.get(n, 0)),
                    "out_degree": int(out_degree.get(n, 0)),
                    "snap_resolutions": int(snap_counts.get(n, 0)),
                }
            )
        return rows

    def field_map_csv(self) -> str:
        rows = self.field_map()
        header = ["n", "constructions", "in_degree", "out_degree", "snap_resolutions"]
        lines = [",".join(header)]
        for row in rows:
            lines.append(",".join(str(row[col]) for col in header))
        return "\n".join(lines)

    def field_map_ascii(self, *, bar_width: int = 40) -> str:
        rows = self.field_map()
        if not rows:
            return "(no grounded nodes)"

        max_constructions = max(row["constructions"] for row in rows)
        if max_constructions <= 0:
            max_constructions = 1

        lines: List[str] = []
        for row in rows:
            n = row["n"]
            constructions = row["constructions"]
            in_degree = row["in_degree"]
            out_degree = row["out_degree"]
            snap_resolutions = row["snap_resolutions"]
            bar_len = int(round(constructions / max_constructions * bar_width))
            bar = "#" * bar_len
            lines.append(
                f"{n:>4} | c={constructions:>3} in={in_degree:>3} out={out_degree:>3} "
                f"snap={snap_resolutions:>3} | {bar}"
            )
        return "\n".join(lines)

    def _node_potential_int(self, node: Node) -> Optional[int]:
        if node.status == "G":
            return int(node.id)
        potential = node.metadata.get("potential_val")
        return int(potential) if isinstance(potential, int) else None

    def _normalize(self, op: str, a: int, b: int) -> Tuple[str, Optional[int]]:
        if op == "+":
            return ("int", a + b)
        if op == "-":
            return ("int", a - b)
        if op == "*":
            if a == 1:
                return ("int", b)
            if b == 1:
                return ("int", a)
            if a == 0 or b == 0:
                return ("int", 0)
            return ("int", a * b)
        if op == "/":
            if b == 0:
                return ("undefined", None)
            if a % b == 0:
                return ("int", a // b)
            return ("non_integer", None)
        raise ValueError(f"Unsupported op {op}")

    # --- operations ---
    def add(self, a: Node, b: Node) -> Node:
        a = self._canonicalize_node(a)
        b = self._canonicalize_node(b)
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("+", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            out = self._get_or_create_grounded_ref(val)
            self._record_edge("+", [a, b], out, {"result": val})
            return out
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val + right_val
            out = self._intern_value(value, seed_op="+", seed_inputs=self._input_ids([a, b]))
            if value.denominator == 1:
                n = int(value.numerator)
                if out.status == "G":
                    edge_meta: Dict[str, object] = {"result": n}
                else:
                    edge_meta = {"result": "speculative", "potential_val": n}
            else:
                edge_meta = {
                    "result": "speculative",
                    "value": {"p": int(value.numerator), "q": int(value.denominator)},
                }
            self._record_edge("+", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)
        potential = self._maybe_potential("+", a, b)
        metadata = {"op": "+", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._new_spec_node(metadata)
        self._record_edge("+", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    def sub(self, a: Node, b: Node) -> Node:
        a = self._canonicalize_node(a)
        b = self._canonicalize_node(b)
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("-", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            out = self._get_or_create_grounded_ref(val)
            self._record_edge("-", [a, b], out, {"result": val})
            return out
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val - right_val
            out = self._intern_value(value, seed_op="-", seed_inputs=self._input_ids([a, b]))
            if value.denominator == 1:
                n = int(value.numerator)
                if out.status == "G":
                    edge_meta: Dict[str, object] = {"result": n}
                else:
                    edge_meta = {"result": "speculative", "potential_val": n}
            else:
                edge_meta = {
                    "result": "speculative",
                    "value": {"p": int(value.numerator), "q": int(value.denominator)},
                }
            self._record_edge("-", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)
        potential = self._maybe_potential("-", a, b)
        metadata = {"op": "-", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._new_spec_node(metadata)
        self._record_edge("-", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    def mul(self, a: Node, b: Node) -> Node:
        a = self._canonicalize_node(a)
        b = self._canonicalize_node(b)
        # Zero annihilation with speculative partner.
        if (
            (a.status == "S" or b.status == "S")
            and ((a.status == "G" and a.id == 0) or (b.status == "G" and b.id == 0))
        ):
            zero = self._get_or_create_grounded_ref(0)
            self._record_edge("*", [a, b], zero, {"result": 0, "rule": "zero_annihilation"})
            return zero

        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("*", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            out = self._get_or_create_grounded_ref(val)
            self._record_edge("*", [a, b], out, {"result": val})
            return out

        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val * right_val
            out = self._intern_value(value, seed_op="*", seed_inputs=self._input_ids([a, b]))
            if value.denominator == 1:
                n = int(value.numerator)
                if out.status == "G":
                    edge_meta: Dict[str, object] = {"result": n}
                else:
                    edge_meta = {"result": "speculative", "potential_val": n}
            else:
                edge_meta = {
                    "result": "speculative",
                    "value": {"p": int(value.numerator), "q": int(value.denominator)},
                }
            self._record_edge("*", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)

        potential = self._maybe_potential("*", a, b)
        metadata = {"op": "*", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._new_spec_node(metadata)
        self._record_edge("*", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    def div(self, a: Node, b: Node) -> Node:
        a = self._canonicalize_node(a)
        b = self._canonicalize_node(b)
        if b.status == "G" and b.id == 0:
            node = self._div_by_zero()
            self._record_edge("/", [a, b], node, {"result": "div_by_zero"})
            return node
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("/", int(a.id), int(b.id))
            if kind == "int":
                assert val is not None
                out = self._get_or_create_grounded_ref(val)
                self._record_edge("/", [a, b], out, {"result": val})
                return out
            if kind == "non_integer":
                value = Fraction(int(a.id), int(b.id))
                out = self._intern_value(
                    value, seed_op="/", seed_inputs=self._input_ids([a, b]), result_tag="non_integer"
                )
                edge_meta = {
                    "result": "non_integer",
                    "value": {"p": int(value.numerator), "q": int(value.denominator)},
                }
                self._record_edge("/", [a, b], out, edge_meta)
                return out
            assert kind == "undefined"
            node = self._div_by_zero()
            self._record_edge("/", [a, b], node, {"result": "div_by_zero"})
            return node

        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            if right_val == 0:
                node = self._div_by_zero()
                self._record_edge("/", [a, b], node, {"result": "div_by_zero"})
                return node

            value = left_val / right_val
            result_tag = "non_integer" if value.denominator != 1 else None
            out = self._intern_value(
                value,
                seed_op="/",
                seed_inputs=self._input_ids([a, b]),
                result_tag=result_tag,
            )

            edge_meta: Dict[str, object]
            if value.denominator == 1:
                n = int(value.numerator)
                if out.status == "G":
                    edge_meta = {"result": n}
                else:
                    edge_meta = {"result": "speculative", "potential_val": n}
            else:
                edge_meta = {
                    "result": "non_integer",
                    "value": {"p": int(value.numerator), "q": int(value.denominator)},
                }
            self._record_edge("/", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)

        potential = self._potential_division(a, b)
        metadata = {"op": "/", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._new_spec_node(metadata)
        self._record_edge("/", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    # --- speculative potential helpers ---
    def _maybe_potential(self, op: str, a: Node, b: Node) -> Optional[int]:
        left = self._node_potential_int(a)
        right = self._node_potential_int(b)
        if left is None or right is None:
            return None
        kind, val = self._normalize(op, left, right)
        if kind == "int":
            return val
        return None

    def _potential_division(self, a: Node, b: Node) -> Optional[int]:
        left = self._node_potential_int(a)
        right = self._node_potential_int(b)
        if right is None or right == 0 or left is None:
            return None
        kind, val = self._normalize("/", left, right)
        if kind == "int":
            return val
        return None

    def _div_by_zero(self) -> Node:
        if self._div_by_zero_node:
            return self._div_by_zero_node
        self._div_by_zero_node = self._new_spec_node({"op": "/", "reason": "division_by_zero"})
        return self._div_by_zero_node

    # --- export utilities ---
    def to_jsonable(self) -> Dict[str, object]:
        def node_payload(node: Node) -> Dict[str, object]:
            return {"id": node.id, "status": node.status, "metadata": node.metadata}

        def edge_payload(edge: Edge) -> Dict[str, object]:
            return {
                "op": edge.op,
                "inputs": [inp.id for inp in edge.inputs],
                "output": edge.output.id,
                "metadata": edge.metadata,
            }

        return {
            "nodes": [node_payload(n) for n in self.nodes_by_int.values()] +
            [node_payload(n) for n in self.speculative_nodes.values()],
            "edges": [edge_payload(e) for e in self.edges],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_jsonable(), indent=indent, sort_keys=True)

    def to_dot(self) -> str:
        lines = ["digraph G {"]
        for node in self.nodes_by_int.values():
            lines.append(f'  "{node.id}" [label="{node.label()}", shape=box, style=filled, fillcolor=lightgray];')
        for node in self.speculative_nodes.values():
            lines.append(f'  "{node.id}" [label="{node.label()}", shape=ellipse, style=filled, fillcolor=yellow];')
        for edge in self.edges:
            inputs = " ".join([f'"{inp.id}"' for inp in edge.inputs])
            for inp in edge.inputs:
                lines.append(f'  "{inp.id}" -> "{edge.output.id}" [label="{edge.op}"];')
        lines.append("}")
        return "\n".join(lines)


class MooExpressionError(ValueError):
    pass


def eval_moo(expr: str, *, graph: Optional[Graph] = None) -> Tuple[Graph, Node]:
    """
    Evaluate a Modulus-of-One expression using only the literal `1` and the
    operators `+`, `-`, `*`, `/` (plus parentheses).

    Returns (graph, result_node).
    """
    g = graph or Graph()
    one = g.get_or_create_ref(1)
    zero: Optional[Node] = None

    def get_zero() -> Node:
        nonlocal zero
        if zero is None:
            zero = g.sub(one, one)
        return zero

    def eval_node(node: ast.AST) -> Node:
        if isinstance(node, ast.Expression):
            return eval_node(node.body)

        if isinstance(node, ast.Constant):
            value = node.value
            if isinstance(value, bool) or not isinstance(value, int) or value != 1:
                raise MooExpressionError("Only the literal `1` is allowed.")
            return one

        if isinstance(node, ast.UnaryOp):
            if isinstance(node.op, ast.UAdd):
                return eval_node(node.operand)
            if isinstance(node.op, ast.USub):
                return g.sub(get_zero(), eval_node(node.operand))
            raise MooExpressionError(f"Unsupported unary operator: {node.op.__class__.__name__}")

        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return g.add(left, right)
            if isinstance(node.op, ast.Sub):
                return g.sub(left, right)
            if isinstance(node.op, ast.Mult):
                return g.mul(left, right)
            if isinstance(node.op, ast.Div):
                return g.div(left, right)
            raise MooExpressionError(f"Unsupported binary operator: {node.op.__class__.__name__}")

        raise MooExpressionError(f"Unsupported syntax: {node.__class__.__name__}")

    try:
        parsed = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise MooExpressionError(str(exc)) from exc

    return g, eval_node(parsed)


def demo(limit: int = 3) -> Graph:
    """
    Build a small universe from Ref(1) by repeatedly applying the four
    fundamental operators across the grounded integer nodes discovered so far.

    `limit` is the number of synchronous closure rounds to run.

    Notes:
    - Negative integers are first-class nodes (grounded) and arise naturally via
      subtraction once 0 is constructed.
    - Non-integer division results are represented as speculative (second-class)
      nodes.
    """
    g = Graph()
    rounds = max(0, int(limit))
    for _ in range(rounds):
        ints = [g.nodes_by_int[n] for n in sorted(g.nodes_by_int.keys())]
        for i, a in enumerate(ints):
            for j, b in enumerate(ints):
                # Commutative ops: avoid duplicate work by only computing once
                # for each unordered pair.
                if j >= i:
                    g.add(a, b)
                    g.mul(a, b)
                # Non-commutative ops: compute on all ordered pairs.
                g.sub(a, b)
                g.div(a, b)

    # A tiny post-pass to ensure the demo includes a speculative fraction and a
    # zero-annihilation example without feeding second-class nodes back into the
    # closure loop.
    one = g.nodes_by_int.get(1)
    two = g.nodes_by_int.get(2)
    zero = g.nodes_by_int.get(0)
    if one is not None and two is not None and zero is not None:
        half = g.div(one, two)
        g.mul(half, zero)

    return g


if __name__ == "__main__":
    def parse_cli(argv: List[str]) -> Tuple[Optional[str], int, Dict[str, bool], Optional[str]]:
        flags = {
            "show_stats": False,
            "show_snap_dot": False,
            "show_field_json": False,
            "show_field_csv": False,
            "show_field_ascii": False,
        }
        limit = 3
        expr_tokens: List[str] = []
        write_maps_prefix: Optional[str] = None

        idx = 0
        while idx < len(argv):
            arg = argv[idx]
            if arg in {"-h", "--help"}:
                print(
                    "Usage:\n"
                    "  python3 constructionist_math.py [--limit N] [--maps] [--stats] [--snap-dot] [--field] [--field-csv] [--field-ascii]\n"
                    "  python3 constructionist_math.py [--maps] [--stats] [--snap-dot] [--field] [--field-csv] [--field-ascii] <expr>\n\n"
                    "  --write-maps PREFIX   Write dot/json/csv/txt map files to PREFIX.*\n\n"
                    "Expr syntax: only the literal `1`, operators `+ - * /`, and parentheses.\n"
                )
                raise SystemExit(0)

            if arg == "--maps":
                flags["show_stats"] = True
                flags["show_snap_dot"] = True
                flags["show_field_json"] = True
                flags["show_field_ascii"] = True
                idx += 1
                continue

            if arg == "--stats":
                flags["show_stats"] = True
                idx += 1
                continue

            if arg == "--snap-dot":
                flags["show_snap_dot"] = True
                idx += 1
                continue

            if arg == "--field":
                flags["show_field_json"] = True
                idx += 1
                continue

            if arg == "--field-csv":
                flags["show_field_csv"] = True
                idx += 1
                continue

            if arg == "--field-ascii":
                flags["show_field_ascii"] = True
                idx += 1
                continue

            if arg == "--write-maps":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --write-maps")
                write_maps_prefix = argv[idx + 1]
                idx += 2
                continue

            if arg == "--limit":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --limit")
                try:
                    limit = int(argv[idx + 1])
                except ValueError as exc:
                    raise SystemExit(f"Invalid --limit value: {argv[idx + 1]!r}") from exc
                idx += 2
                continue

            if arg.startswith("--"):
                raise SystemExit(f"Unknown option: {arg}")

            expr_tokens = argv[idx:]
            break

        expression = " ".join(expr_tokens).strip() if expr_tokens else None
        return expression, limit, flags, write_maps_prefix

    expression, limit, flags, write_maps_prefix = parse_cli(sys.argv[1:])
    if expression is not None:
        graph, result = eval_moo(expression)
        print("# EXPR")
        print(expression)
        print("\n# RESULT")
        print(result.label())
    else:
        graph = demo(limit=limit)

    if write_maps_prefix is not None:
        prefix = Path(write_maps_prefix)
        targets = {
            "dot": Path(str(prefix) + ".dot"),
            "snap_dot": Path(str(prefix) + ".snap.dot"),
            "field_json": Path(str(prefix) + ".field.json"),
            "field_csv": Path(str(prefix) + ".field.csv"),
            "field_ascii": Path(str(prefix) + ".field.txt"),
            "stats": Path(str(prefix) + ".stats.json"),
            "snap_events": Path(str(prefix) + ".snap_events.json"),
        }
        for path in targets.values():
            if path.exists():
                raise SystemExit(f"Refusing to overwrite existing file: {path}")
            if path.parent != Path(".") and not path.parent.exists():
                raise SystemExit(f"Directory does not exist: {path.parent}")

        targets["dot"].write_text(graph.to_dot() + "\n", encoding="utf-8")
        targets["snap_dot"].write_text(graph.to_snap_dot() + "\n", encoding="utf-8")
        targets["field_json"].write_text(
            json.dumps(graph.field_map(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["field_csv"].write_text(graph.field_map_csv() + "\n", encoding="utf-8")
        targets["field_ascii"].write_text(graph.field_map_ascii() + "\n", encoding="utf-8")
        targets["stats"].write_text(
            json.dumps(graph.stats(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["snap_events"].write_text(
            json.dumps(graph.snap_events(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("\n# WROTE_MAPS")
        for key, path in targets.items():
            print(f"{key}: {path}")

    if flags["show_stats"]:
        print("\n# STATS")
        print(json.dumps(graph.stats(), indent=2, sort_keys=True))
        print("\n# SNAP_EVENTS")
        print(json.dumps(graph.snap_events(), indent=2, sort_keys=True))
    if flags["show_field_json"]:
        print("\n# FIELD_JSON")
        print(json.dumps(graph.field_map(), indent=2, sort_keys=True))
    if flags["show_field_csv"]:
        print("\n# FIELD_CSV")
        print(graph.field_map_csv())
    if flags["show_field_ascii"]:
        print("\n# FIELD_ASCII")
        print(graph.field_map_ascii())
    if flags["show_snap_dot"]:
        print("\n# SNAP_DOT")
        print(graph.to_snap_dot())
    print("# JSON")
    print(graph.to_json(indent=2))
    print("\n# DOT")
    print(graph.to_dot())

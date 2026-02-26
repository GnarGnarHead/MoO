from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Union, Literal
import ast
from fractions import Fraction
import itertools
import json
from pathlib import Path
import sys

Status = Literal["G", "S"]
NodeId = Union[int, str]
NodeUid = int
ValueKey = Tuple[int, int]
InternPolicy = Literal["none", "by_provenance"]


@dataclass
class Node:
    id: NodeId
    status: Status
    node_uid: NodeUid
    value: Optional[ValueKey] = None
    eq_class: Optional[int] = None
    provenance: Dict[str, object] = field(default_factory=dict)
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
    Speculative nodes (status S) capture non-integer rationals and inferred
    integer claims.

    Identity is non-destructive and structure-preserving:
    derivations remain distinct while value-equivalence is tracked explicitly.
    """

    def __init__(
        self,
        *,
        intern_policy: Optional[InternPolicy] = None,
        max_nodes: Optional[int] = None,
        max_depth: Optional[int] = None,
        operation_budget: Optional[int] = None,
        dedupe_by_provenance: bool = False,
    ) -> None:
        resolved_intern_policy: InternPolicy
        if intern_policy is None:
            if dedupe_by_provenance:
                resolved_intern_policy = "by_provenance"
            else:
                resolved_intern_policy = "none"
        else:
            resolved_intern_policy = intern_policy

        if resolved_intern_policy not in {"none", "by_provenance"}:
            raise ValueError(f"Unsupported intern policy: {resolved_intern_policy}")
        if max_nodes is not None and max_nodes <= 0:
            raise ValueError("max_nodes must be > 0")
        if max_depth is not None and max_depth < 0:
            raise ValueError("max_depth must be >= 0")
        if operation_budget is not None and operation_budget < 0:
            raise ValueError("operation_budget must be >= 0")

        self.intern_policy: InternPolicy = resolved_intern_policy
        self.max_nodes = max_nodes
        self.max_depth = max_depth
        self.operation_budget = operation_budget

        self.nodes_by_int: Dict[int, Node] = {}
        self.speculative_nodes: Dict[str, Node] = {}
        self.nodes_by_uid: Dict[NodeUid, Node] = {}
        self.value_classes: Dict[ValueKey, Set[NodeUid]] = {}
        self._eq_class_ids: Dict[ValueKey, int] = {}
        self._speculative_by_provenance: Dict[Tuple[object, ...], Node] = {}
        self.edges: List[Edge] = []
        self._snap_events: List[Dict[str, object]] = []
        self._resolutions: List[Dict[str, object]] = []
        self._resolution_pairs: Set[Tuple[NodeUid, NodeUid]] = set()
        self._spec_counter = itertools.count(1)
        self._node_uid_counter = itertools.count(1)
        self._created_seq_counter = itertools.count(1)
        self._eq_class_counter = itertools.count(1)
        self._operation_count = 0
        self._div_by_zero_node: Optional[Node] = None

        # Seed with the only first-class primitive: Ref(1)
        self._get_or_create_grounded_ref(1)

    # --- core helpers ---
    def _next_node_uid(self) -> NodeUid:
        return int(next(self._node_uid_counter))

    def _next_created_seq(self) -> int:
        return int(next(self._created_seq_counter))

    def _normalize_value_key(self, value: Fraction) -> ValueKey:
        normalized = Fraction(value.numerator, value.denominator)
        return (int(normalized.numerator), int(normalized.denominator))

    def _value_key_from_metadata(self, metadata: Dict[str, object]) -> Optional[ValueKey]:
        value = metadata.get("value")
        if not isinstance(value, dict):
            return None
        p = value.get("p")
        q = value.get("q")
        if not isinstance(p, int) or not isinstance(q, int) or q == 0:
            return None
        normalized = Fraction(p, q)
        return self._normalize_value_key(normalized)

    def _ensure_node_limit(self) -> None:
        if self.max_nodes is None:
            return
        if len(self.nodes_by_uid) >= self.max_nodes:
            raise RuntimeError("max_nodes exceeded")

    def _register_value_class(self, node: Node, value_key: ValueKey) -> None:
        members = self.value_classes.setdefault(value_key, set())
        members.add(node.node_uid)
        if value_key not in self._eq_class_ids:
            self._eq_class_ids[value_key] = int(next(self._eq_class_counter))
        node.eq_class = self._eq_class_ids[value_key]

    def _unregister_value_class(self, node: Node) -> None:
        if node.value is None:
            node.eq_class = None
            return
        members = self.value_classes.get(node.value)
        if members is not None:
            members.discard(node.node_uid)
            if not members:
                self.value_classes.pop(node.value, None)
        node.eq_class = None

    def _register_node(self, node: Node) -> None:
        self._ensure_node_limit()
        self.nodes_by_uid[node.node_uid] = node
        if node.value is not None:
            self._register_value_class(node, node.value)

    def _unregister_node(self, node: Node) -> None:
        self.nodes_by_uid.pop(node.node_uid, None)
        self._unregister_value_class(node)

    def _freeze(self, obj: object) -> object:
        if isinstance(obj, dict):
            return tuple(sorted((str(k), self._freeze(v)) for k, v in obj.items()))
        if isinstance(obj, list):
            return tuple(self._freeze(item) for item in obj)
        if isinstance(obj, tuple):
            return tuple(self._freeze(item) for item in obj)
        if isinstance(obj, set):
            return tuple(sorted(self._freeze(item) for item in obj))
        return obj

    def _input_ids(self, inputs: List[Node]) -> List[NodeId]:
        return [inp.id for inp in inputs]

    def _input_uids(self, inputs: List[Node]) -> List[NodeUid]:
        return [inp.node_uid for inp in inputs]

    def _node_depth(self, node: Node) -> int:
        depth = node.provenance.get("depth")
        return int(depth) if isinstance(depth, int) else 0

    def _derive_depth(self, inputs: List[Node]) -> int:
        if not inputs:
            depth = 0
        else:
            depth = max(self._node_depth(node) for node in inputs) + 1
        if self.max_depth is not None and depth > self.max_depth:
            raise RuntimeError("max_depth exceeded")
        return depth

    def _consume_operation_budget(self) -> None:
        if self.operation_budget is None:
            return
        if self._operation_count >= self.operation_budget:
            raise RuntimeError("operation_budget exceeded")
        self._operation_count += 1

    def _make_provenance(self, *, op: str, inputs: List[Node], depth: int) -> Dict[str, object]:
        return {
            "op": op,
            "inputs": self._input_uids(inputs),
            "created_seq": self._next_created_seq(),
            "depth": depth,
        }

    def _provenance_key(
        self,
        *,
        op: str,
        inputs: List[Node],
        value_key: Optional[ValueKey],
        metadata: Dict[str, object],
    ) -> Tuple[object, ...]:
        stable_metadata = {k: v for k, v in metadata.items() if k != "tier"}
        return (
            op,
            tuple(self._input_uids(inputs)),
            value_key,
            self._freeze(stable_metadata),
        )

    def _node_value(self, node: Node) -> Optional[Fraction]:
        """
        Return the exact rational value for a node when it is known.

        - Grounded ints always have a value.
        - Speculative nodes have a value when they were interned as a rational
          (or as an integer claim) and carry metadata["value"].
        """
        if node.value is not None:
            return Fraction(int(node.value[0]), int(node.value[1]))
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
        seed_inputs: List[Node],
        result_tag: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Node:
        """
        Return a node for an exact rational value according to interning policy.

        Integer-valued derivations remain distinct nodes and can be linked to
        grounded anchors through non-destructive resolution relations.
        """
        key = self._normalize_value_key(value)

        metadata: Dict[str, object] = {"op": seed_op, "inputs": self._input_ids(seed_inputs), "tier": 3}
        metadata["value"] = {"p": key[0], "q": key[1]}
        if key[1] == 1:
            metadata["potential_val"] = key[0]
        if result_tag is not None:
            metadata["result"] = result_tag
        if reason is not None:
            metadata["reason"] = reason

        provenance_key: Optional[Tuple[object, ...]] = None
        if self.intern_policy == "by_provenance":
            provenance_key = self._provenance_key(
                op=seed_op,
                inputs=seed_inputs,
                value_key=key,
                metadata=metadata,
            )
            existing = self._speculative_by_provenance.get(provenance_key)
            if existing is not None:
                return existing

        depth = self._derive_depth(seed_inputs)
        provenance = self._make_provenance(op=seed_op, inputs=seed_inputs, depth=depth)
        node = self._new_spec_node(metadata, value_key=key, provenance=provenance)
        if self.intern_policy == "by_provenance" and provenance_key is not None:
            self._speculative_by_provenance[provenance_key] = node
        return node

    def _new_spec_node(
        self,
        metadata: Dict[str, object],
        *,
        value_key: Optional[ValueKey] = None,
        provenance: Optional[Dict[str, object]] = None,
    ) -> Node:
        metadata.setdefault("tier", 3)
        if value_key is None:
            value_key = self._value_key_from_metadata(metadata)
        if value_key is not None:
            metadata["value"] = {"p": int(value_key[0]), "q": int(value_key[1])}
            if value_key[1] == 1:
                metadata.setdefault("potential_val", int(value_key[0]))
        if provenance is None:
            op = metadata.get("op")
            provenance = {
                "op": op if isinstance(op, str) else "speculative",
                "inputs": [],
                "created_seq": self._next_created_seq(),
                "depth": 0,
            }

        node_id = f"S{next(self._spec_counter)}"
        node = Node(
            id=node_id,
            status="S",
            node_uid=self._next_node_uid(),
            value=value_key,
            provenance=provenance,
            metadata=metadata,
        )
        self.speculative_nodes[node_id] = node
        self._register_node(node)
        return node

    def _create_spec_node(
        self,
        *,
        op: str,
        inputs: List[Node],
        metadata: Dict[str, object],
        value_key: Optional[ValueKey] = None,
    ) -> Node:
        provenance_key: Optional[Tuple[object, ...]] = None
        if self.intern_policy == "by_provenance":
            provenance_key = self._provenance_key(
                op=op,
                inputs=inputs,
                value_key=value_key,
                metadata=metadata,
            )
            existing = self._speculative_by_provenance.get(provenance_key)
            if existing is not None:
                return existing

        depth = self._derive_depth(inputs)
        provenance = self._make_provenance(op=op, inputs=inputs, depth=depth)
        node = self._new_spec_node(metadata, value_key=value_key, provenance=provenance)
        if self.intern_policy == "by_provenance" and provenance_key is not None:
            self._speculative_by_provenance[provenance_key] = node
        return node

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
        metadata["value"] = {"p": n, "q": 1}
        node = Node(
            id=n,
            status="G",
            node_uid=self._next_node_uid(),
            value=(n, 1),
            provenance={
                "op": "anchor",
                "inputs": [],
                "created_seq": self._next_created_seq(),
                "depth": 0,
            },
            metadata=metadata,
        )
        self.nodes_by_int[n] = node
        self._register_node(node)
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

    def resolutions(self) -> List[Dict[str, object]]:
        return list(self._resolutions)

    def numeric_value(self, node: Node) -> Optional[ValueKey]:
        value = self._node_value(node)
        if value is None:
            return None
        return self._normalize_value_key(value)

    def value_equivalence_class(self, node: Node) -> Optional[ValueKey]:
        return self.numeric_value(node)

    def acceptance_report(self) -> Dict[str, object]:
        checks: Dict[str, Dict[str, object]] = {}

        # 1) Distinct same-value derivations can coexist.
        distinct_same_value_classes = 0
        for value_key, members in self.value_classes.items():
            active_members = [uid for uid in members if uid in self.nodes_by_uid]
            if len(active_members) < 2:
                continue
            if any(self.nodes_by_uid[uid].status == "S" for uid in active_members):
                distinct_same_value_classes += 1
        checks["distinct_same_value_nodes"] = {
            "status": "pass" if distinct_same_value_classes > 0 else "fail",
            "details": {"classes_with_multiplicity": distinct_same_value_classes},
        }

        # 2) Value class and eq_class consistency.
        consistency_issues: List[str] = []
        for value_key, members in self.value_classes.items():
            expected_eq = self._eq_class_ids.get(value_key)
            for uid in members:
                node = self.nodes_by_uid.get(uid)
                if node is None:
                    continue
                if node.value != value_key:
                    consistency_issues.append(
                        f"uid={uid} value={node.value} class={value_key}"
                    )
                if node.eq_class != expected_eq:
                    consistency_issues.append(
                        f"uid={uid} eq_class={node.eq_class} expected={expected_eq}"
                    )
        checks["value_equivalence_consistent"] = {
            "status": "pass" if not consistency_issues else "fail",
            "details": {"issues": consistency_issues[:10], "issue_count": len(consistency_issues)},
        }

        # 3) Non-destructive resolves_to for integer-valued speculative nodes.
        required_resolutions: Set[Tuple[NodeUid, NodeUid]] = set()
        for node in self.speculative_nodes.values():
            if node.value is None:
                continue
            numerator, denominator = node.value
            if int(denominator) != 1:
                continue
            anchor = self.nodes_by_int.get(int(numerator))
            if anchor is None:
                continue
            required_resolutions.add((node.node_uid, anchor.node_uid))

        actual_resolutions = {
            (int(event["from_uid"]), int(event["to_uid"]))
            for event in self._resolutions
            if isinstance(event.get("from_uid"), int) and isinstance(event.get("to_uid"), int)
        }
        missing_resolutions = sorted(required_resolutions - actual_resolutions)
        destroyed_sources = sorted(
            src_uid for src_uid, _ in required_resolutions if src_uid not in self.speculative_nodes_by_uid()
        )
        checks["non_destructive_resolution"] = {
            "status": "pass" if not missing_resolutions and not destroyed_sources else "fail",
            "details": {
                "required": len(required_resolutions),
                "actual": len(actual_resolutions),
                "missing_pairs": missing_resolutions[:10],
                "destroyed_sources": destroyed_sources[:10],
            },
        }

        statuses = [check["status"] for check in checks.values()]
        if any(status == "fail" for status in statuses):
            summary = "fail"
        elif any(status == "pass" for status in statuses):
            summary = "pass"
        else:
            summary = "na"

        return {"semantics": "preserve", "summary": summary, "checks": checks}

    def speculative_nodes_by_uid(self) -> Dict[NodeUid, Node]:
        return {node.node_uid: node for node in self.speculative_nodes.values()}

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
            "semantics": "preserve",
            "intern_policy": self.intern_policy,
            "counts": {
                "grounded_nodes": len(self.nodes_by_int),
                "speculative_nodes": len(self.speculative_nodes),
                "total_nodes": len(self.nodes_by_uid),
                "edges": len(self.edges),
                "snap_events": len(self._snap_events),
                "resolutions": len(self._resolutions),
                "value_classes": len(self.value_classes),
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

    def _record_resolution(self, source: Node, target: Node, *, reason: str) -> bool:
        key = (source.node_uid, target.node_uid)
        if key in self._resolution_pairs:
            return False
        self._resolution_pairs.add(key)
        self._resolutions.append(
            {
                "from_uid": source.node_uid,
                "to_uid": target.node_uid,
                "from_id": source.id,
                "to_id": target.id,
                "reason": reason,
            }
        )
        return True

    def _maybe_snap_new_spec_to_existing_ref(self, node: Node) -> Node:
        if node.status != "S":
            return node
        potential_val = node.metadata.get("potential_val")
        if not isinstance(potential_val, int):
            return node
        ref_node = self.nodes_by_int.get(potential_val)
        if ref_node is None:
            return node
        created = self._record_resolution(node, ref_node, reason="potential_val_match")
        if created:
            self._snap_events.append(
                {
                    "spec_id": node.id,
                    "spec_uid": node.node_uid,
                    "resolved_to": potential_val,
                    "resolved_to_uid": ref_node.node_uid,
                    "usages": self._count_usages(node),
                    "spec_metadata": dict(node.metadata),
                }
            )
        node.metadata["resolved_to"] = potential_val
        return node

    def _snap_speculative_to_ref(self, n: int, ref_node: Node) -> None:
        to_snap = [
            node for node in self.speculative_nodes.values()
            if node.metadata.get("potential_val") == n
        ]
        for node in to_snap:
            usages = self._count_usages(node)
            event = {
                "spec_id": node.id,
                "spec_uid": node.node_uid,
                "resolved_to": n,
                "resolved_to_uid": ref_node.node_uid,
                "usages": usages,
                "spec_metadata": dict(node.metadata),
            }
            created = self._record_resolution(node, ref_node, reason="anchor_grounded")
            if created:
                self._snap_events.append(event)
            node.metadata["resolved_to"] = n

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
        if node.value is not None and int(node.value[1]) == 1:
            return int(node.value[0])
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

    def _edge_meta_for_value(
        self,
        *,
        value: Fraction,
        out: Node,
        non_integer_result: str = "speculative",
    ) -> Dict[str, object]:
        if value.denominator == 1:
            n = int(value.numerator)
            if out.status == "G":
                return {"result": n}
            return {"result": "speculative", "potential_val": n}
        return {
            "result": non_integer_result,
            "value": {"p": int(value.numerator), "q": int(value.denominator)},
        }

    # --- operations ---
    def add(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("+", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            self._get_or_create_grounded_ref(val)
            value = Fraction(val, 1)
            out = self._intern_value(value, seed_op="+", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("+", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val + right_val
            if value.denominator == 1:
                self._get_or_create_grounded_ref(int(value.numerator))
            out = self._intern_value(value, seed_op="+", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("+", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)
        potential = self._maybe_potential("+", a, b)
        metadata = {"op": "+", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="+", inputs=[a, b], metadata=metadata)
        self._record_edge("+", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    def sub(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("-", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            self._get_or_create_grounded_ref(val)
            value = Fraction(val, 1)
            out = self._intern_value(value, seed_op="-", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("-", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val - right_val
            if value.denominator == 1:
                self._get_or_create_grounded_ref(int(value.numerator))
            out = self._intern_value(value, seed_op="-", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("-", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)
        potential = self._maybe_potential("-", a, b)
        metadata = {"op": "-", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="-", inputs=[a, b], metadata=metadata)
        self._record_edge("-", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    def mul(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if (left_val == 0 and right_val is None) or (right_val == 0 and left_val is None):
            value = Fraction(0, 1)
            out = self._intern_value(
                value,
                seed_op="*",
                seed_inputs=[a, b],
                reason="zero_annihilation",
            )
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            edge_meta["rule"] = "zero_annihilation"
            self._record_edge("*", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)

        if left_val is not None and right_val is not None:
            value = left_val * right_val
            out = self._intern_value(value, seed_op="*", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("*", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)

        potential = self._maybe_potential("*", a, b)
        metadata = {"op": "*", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="*", inputs=[a, b], metadata=metadata)
        self._record_edge("*", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_snap_new_spec_to_existing_ref(out)

    def div(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        if b.status == "G" and b.id == 0:
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
                seed_inputs=[a, b],
                result_tag=result_tag,
            )

            edge_meta = self._edge_meta_for_value(value=value, out=out, non_integer_result="non_integer")
            self._record_edge("/", [a, b], out, edge_meta)
            return self._maybe_snap_new_spec_to_existing_ref(out)

        potential = self._potential_division(a, b)
        metadata = {"op": "/", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="/", inputs=[a, b], metadata=metadata)
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
        self._div_by_zero_node = self._create_spec_node(
            op="/",
            inputs=[],
            metadata={"op": "/", "reason": "division_by_zero"},
        )
        return self._div_by_zero_node

    # --- export utilities ---
    def _active_nodes(self) -> List[Node]:
        return [self.nodes_by_uid[uid] for uid in sorted(self.nodes_by_uid.keys())]

    def _value_key_label(self, value_key: ValueKey) -> str:
        return f"{int(value_key[0])}/{int(value_key[1])}"

    def _value_projection_payload(self) -> Dict[str, object]:
        classes: Dict[str, Dict[str, object]] = {}
        node_to_class_label: Dict[NodeUid, str] = {}
        for value_key in sorted(self.value_classes.keys()):
            members = self.value_classes[value_key]
            active_members = sorted(uid for uid in members if uid in self.nodes_by_uid)
            if not active_members:
                continue
            label = self._value_key_label(value_key)
            classes[label] = {
                "value": {"p": int(value_key[0]), "q": int(value_key[1])},
                "eq_class": self._eq_class_ids.get(value_key),
                "node_uids": active_members,
            }
            for uid in active_members:
                node_to_class_label[uid] = label

        unknown_nodes = [node.node_uid for node in self._active_nodes() if node.value is None]

        edge_set: Set[Tuple[str, str, str]] = set()
        for edge in self.edges:
            out_label = node_to_class_label.get(edge.output.node_uid)
            if out_label is None:
                continue
            for inp in edge.inputs:
                in_label = node_to_class_label.get(inp.node_uid)
                if in_label is None:
                    continue
                edge_set.add((in_label, out_label, edge.op))

        return {
            "classes": classes,
            "unknown_node_uids": unknown_nodes,
            "edges": [
                {"src": src, "dst": dst, "op": op}
                for src, dst, op in sorted(edge_set, key=lambda item: (item[0], item[1], item[2]))
            ],
        }

    def to_jsonable(self) -> Dict[str, object]:
        def node_payload(node: Node) -> Dict[str, object]:
            value_payload: Optional[Dict[str, int]] = None
            if node.value is not None:
                value_payload = {"p": int(node.value[0]), "q": int(node.value[1])}
            return {
                "id": node.id,
                "node_uid": node.node_uid,
                "status": node.status,
                "value": value_payload,
                "eq_class": node.eq_class,
                "provenance": node.provenance,
                "metadata": node.metadata,
            }

        def edge_payload(edge: Edge) -> Dict[str, object]:
            return {
                "op": edge.op,
                "inputs": [inp.id for inp in edge.inputs],
                "input_uids": [inp.node_uid for inp in edge.inputs],
                "output": edge.output.id,
                "output_uid": edge.output.node_uid,
                "metadata": edge.metadata,
            }

        equivalence_classes = {
            self._value_key_label(value_key): sorted(
                uid for uid in members if uid in self.nodes_by_uid
            )
            for value_key, members in sorted(self.value_classes.items())
            if any(uid in self.nodes_by_uid for uid in members)
        }

        return {
            "semantics": "preserve",
            "intern_policy": self.intern_policy,
            "nodes": [node_payload(n) for n in self._active_nodes()],
            "edges": [edge_payload(e) for e in self.edges],
            "equivalence_classes": equivalence_classes,
            "resolutions": list(self._resolutions),
            "value_projection": self._value_projection_payload(),
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_jsonable(), indent=indent, sort_keys=True)

    def to_dot(self) -> str:
        return self.to_dot_view(view="structure")

    def to_dot_view(self, *, view: Literal["structure", "value"] = "structure") -> str:
        if view == "structure":
            return self._to_dot_structure()
        if view == "value":
            return self._to_dot_value_projection()
        raise ValueError(f"Unsupported view: {view}")

    def _to_dot_structure(self) -> str:
        lines = ["digraph G {"]
        for node in sorted(self.nodes_by_int.values(), key=lambda n: int(n.id)):
            lines.append(f'  "{node.id}" [label="{node.label()}", shape=box, style=filled, fillcolor=lightgray];')
        for node in sorted(self.speculative_nodes.values(), key=lambda n: n.node_uid):
            lines.append(f'  "{node.id}" [label="{node.label()}", shape=ellipse, style=filled, fillcolor=yellow];')
        for edge in self.edges:
            for inp in edge.inputs:
                lines.append(f'  "{inp.id}" -> "{edge.output.id}" [label="{edge.op}"];')
        for event in self._resolutions:
            src_uid = event.get("from_uid")
            dst_uid = event.get("to_uid")
            if not isinstance(src_uid, int) or not isinstance(dst_uid, int):
                continue
            src_node = self.nodes_by_uid.get(src_uid)
            dst_node = self.nodes_by_uid.get(dst_uid)
            if src_node is None or dst_node is None:
                continue
            lines.append(
                f'  "{src_node.id}" -> "{dst_node.id}" '
                '[label="resolves_to", style=dashed, color=blue];'
            )
        lines.append("}")
        return "\n".join(lines)

    def _to_dot_value_projection(self) -> str:
        lines = ["digraph G {"]
        node_to_class_node: Dict[NodeUid, str] = {}

        for value_key in sorted(self.value_classes.keys()):
            members = self.value_classes[value_key]
            active_members = sorted(uid for uid in members if uid in self.nodes_by_uid)
            if not active_members:
                continue
            eq_class = self._eq_class_ids.get(value_key)
            node_name = f'val_{int(value_key[0])}_{int(value_key[1])}'
            label = self._value_key_label(value_key)
            if isinstance(eq_class, int):
                label = f"{label}\\nEQ:{eq_class} n={len(active_members)}"
            else:
                label = f"{label}\\nn={len(active_members)}"
            for uid in active_members:
                node_to_class_node[uid] = node_name
            has_grounded = any(
                self.nodes_by_uid[uid].status == "G" for uid in active_members if uid in self.nodes_by_uid
            )
            shape = "box" if has_grounded else "ellipse"
            fill = "lightgray" if has_grounded else "khaki"
            lines.append(
                f'  "{node_name}" [label="{label}", shape={shape}, style=filled, fillcolor={fill}];'
            )

        for node in self._active_nodes():
            if node.value is not None:
                continue
            node_name = f"unknown_{node.node_uid}"
            node_to_class_node[node.node_uid] = node_name
            lines.append(
                f'  "{node_name}" [label="{node.label()}", shape=ellipse, style=filled, fillcolor=mistyrose];'
            )

        value_edges: Set[Tuple[str, str, str]] = set()
        for edge in self.edges:
            out_node_name = node_to_class_node.get(edge.output.node_uid)
            if out_node_name is None:
                continue
            for inp in edge.inputs:
                in_node_name = node_to_class_node.get(inp.node_uid)
                if in_node_name is None:
                    continue
                value_edges.add((in_node_name, out_node_name, edge.op))

        for src, dst, op in sorted(value_edges, key=lambda item: (item[0], item[1], item[2])):
            lines.append(f'  "{src}" -> "{dst}" [label="{op}"];')
        lines.append("}")
        return "\n".join(lines)


class MooExpressionError(ValueError):
    pass


def eval_moo(
    expr: str,
    *,
    graph: Optional[Graph] = None,
    intern_policy: Optional[InternPolicy] = None,
    max_nodes: Optional[int] = None,
    max_depth: Optional[int] = None,
    operation_budget: Optional[int] = None,
    dedupe_by_provenance: bool = False,
) -> Tuple[Graph, Node]:
    """
    Evaluate a Modulus-of-One expression using only the literal `1` and the
    operators `+`, `-`, `*`, `/` (plus parentheses).

    Returns (graph, result_node).
    """
    g = graph or Graph(
        intern_policy=intern_policy,
        max_nodes=max_nodes,
        max_depth=max_depth,
        operation_budget=operation_budget,
        dedupe_by_provenance=dedupe_by_provenance,
    )
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


def demo(
    limit: int = 3,
    *,
    intern_policy: Optional[InternPolicy] = None,
    max_nodes: Optional[int] = None,
    max_depth: Optional[int] = None,
    operation_budget: Optional[int] = None,
    dedupe_by_provenance: bool = False,
) -> Graph:
    """
    Build a small universe from the only primitive certainty: Ref(1).

    `limit` controls how far we iterate outward in the integer backbone
    (approximately grounding integers in [-limit, limit]).

    This demo deliberately:
    - treats integers as second-class (they must be explicitly constructed),
    - treats multiplication/division outputs as third-class claims until they align
      to an explicitly grounded integer,
    - includes a small S→G snapping example for an unconstructed integer claim.
    """
    g = Graph(
        intern_policy=intern_policy,
        max_nodes=max_nodes,
        max_depth=max_depth,
        operation_budget=operation_budget,
        dedupe_by_provenance=dedupe_by_provenance,
    )
    one = g.get_or_create_ref(1)
    zero = g.sub(one, one)

    # Create speculative "shadow refs" that will later snap to grounded Refs.
    shadow_two = g.speculate_ref(2, reason="demo_shadow_ref")
    g.add(shadow_two, one)  # potential_val=3, will snap once Ref(3) is grounded

    limit = max(0, int(limit))

    positives = {1: one}
    for n in range(2, limit + 1):
        positives[n] = g.add(positives[n - 1], one)

    current = zero
    for _ in range(1, limit + 1):
        current = g.sub(current, one)

    # Apply a bounded set of multiplication/division steps on the grounded integer
    # backbone so the demo exercises all operators without blowing up.
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

    # A couple of speculative fractions (third-class) + zero annihilation.
    half: Optional[Node] = None
    if limit >= 2:
        half = g.div(one, positives[2])
        g.mul(half, zero)  # triggers zero annihilation from speculative input
    if limit >= 3 and half is not None:
        third = g.div(one, positives[3])
        g.add(half, third)

    return g


if __name__ == "__main__":
    def parse_cli(
        argv: List[str],
    ) -> Tuple[
        Optional[str],
        int,
        Dict[str, bool],
        Optional[str],
        Dict[str, object],
    ]:
        flags = {
            "show_stats": False,
            "show_snap_dot": False,
            "show_field_json": False,
            "show_field_csv": False,
            "show_field_ascii": False,
        }
        graph_config: Dict[str, object] = {
            "view": "structure",
            "intern_policy": None,
            "max_nodes": None,
            "max_depth": None,
            "operation_budget": None,
            "dedupe_by_provenance": False,
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
                    "  python3 constructionist_math.py [--view structure|value] [--limit N]\n"
                    "      [--intern-policy none|by_provenance] [--max-nodes N] [--max-depth N]\n"
                    "      [--op-budget N] [--dedupe-by-provenance] [--maps] [--stats] [--snap-dot]\n"
                    "      [--field] [--field-csv] [--field-ascii] [--write-maps PREFIX] [<expr>]\n\n"
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

            if arg == "--view":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --view")
                view = argv[idx + 1]
                if view not in {"structure", "value"}:
                    raise SystemExit(f"Invalid --view value: {view!r}")
                graph_config["view"] = view
                idx += 2
                continue

            if arg == "--intern-policy":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --intern-policy")
                policy = argv[idx + 1]
                if policy not in {"none", "by_provenance"}:
                    raise SystemExit(f"Invalid --intern-policy value: {policy!r}")
                graph_config["intern_policy"] = policy
                idx += 2
                continue

            if arg == "--max-nodes":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --max-nodes")
                try:
                    graph_config["max_nodes"] = int(argv[idx + 1])
                except ValueError as exc:
                    raise SystemExit(f"Invalid --max-nodes value: {argv[idx + 1]!r}") from exc
                idx += 2
                continue

            if arg == "--max-depth":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --max-depth")
                try:
                    graph_config["max_depth"] = int(argv[idx + 1])
                except ValueError as exc:
                    raise SystemExit(f"Invalid --max-depth value: {argv[idx + 1]!r}") from exc
                idx += 2
                continue

            if arg == "--op-budget":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --op-budget")
                try:
                    graph_config["operation_budget"] = int(argv[idx + 1])
                except ValueError as exc:
                    raise SystemExit(f"Invalid --op-budget value: {argv[idx + 1]!r}") from exc
                idx += 2
                continue

            if arg == "--dedupe-by-provenance":
                graph_config["dedupe_by_provenance"] = True
                idx += 1
                continue

            if arg.startswith("--"):
                raise SystemExit(f"Unknown option: {arg}")

            expr_tokens = argv[idx:]
            break

        expression = " ".join(expr_tokens).strip() if expr_tokens else None
        return expression, limit, flags, write_maps_prefix, graph_config

    expression, limit, flags, write_maps_prefix, graph_config = parse_cli(sys.argv[1:])
    graph_kwargs = {
        "intern_policy": graph_config["intern_policy"],
        "max_nodes": graph_config["max_nodes"],
        "max_depth": graph_config["max_depth"],
        "operation_budget": graph_config["operation_budget"],
        "dedupe_by_provenance": graph_config["dedupe_by_provenance"],
    }
    view = str(graph_config["view"])

    if expression is not None:
        graph, result = eval_moo(expression, **graph_kwargs)
        print("# EXPR")
        print(expression)
        print("\n# RESULT")
        print(result.label())
    else:
        graph = demo(limit=limit, **graph_kwargs)

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
            "resolutions": Path(str(prefix) + ".resolutions.json"),
            "acceptance": Path(str(prefix) + ".acceptance.json"),
        }
        for path in targets.values():
            if path.exists():
                raise SystemExit(f"Refusing to overwrite existing file: {path}")
            if path.parent != Path(".") and not path.parent.exists():
                raise SystemExit(f"Directory does not exist: {path.parent}")

        targets["dot"].write_text(graph.to_dot_view(view=view) + "\n", encoding="utf-8")
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
        targets["resolutions"].write_text(
            json.dumps(graph.resolutions(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["acceptance"].write_text(
            json.dumps(graph.acceptance_report(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        print("\n# WROTE_MAPS")
        for key, path in targets.items():
            print(f"{key}: {path}")

    if flags["show_stats"]:
        print("\n# STATS")
        print(json.dumps(graph.stats(), indent=2, sort_keys=True))
        print("\n# SNAP_EVENTS")
        print(json.dumps(graph.snap_events(), indent=2, sort_keys=True))
        print("\n# RESOLUTIONS")
        print(json.dumps(graph.resolutions(), indent=2, sort_keys=True))
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
    print("\n# ACCEPTANCE")
    print(json.dumps(graph.acceptance_report(), indent=2, sort_keys=True))
    print("# JSON")
    print(graph.to_json(indent=2))
    print("\n# DOT")
    print(graph.to_dot_view(view=view))

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


class SpeculativeOperandError(ValueError):
    pass


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
    edge_uid: int = 0
    metadata: Dict[str, object] = field(default_factory=dict)


class Graph:
    """
    Constructionist arithmetic graph.

    Grounded nodes (status G) represent integers Ref(N).
    Speculative nodes (status S) represent non-grounded rationals and special
    undefined nodes (like division-by-zero).
    In the current positive-spine aligned mode, only confirmed positive-spine
    iterations are operands.
    Speculative nodes are real graph nodes for inspection, but they are not
    operated on until promotion by the selected field rule. In this runtime,
    that selected rule is the positive-spine confirmation path.

    Identity is value-centric:
    - Each reduced rational value p/q corresponds to exactly one node.
    - Emergence/spiderweb structure is represented by many provenance-carrying
      edges flowing into that node (distinct constructions are distinct edges).
    """

    def __init__(
        self,
        *,
        intern_policy: Optional[InternPolicy] = None,
        max_nodes: Optional[int] = None,
        max_depth: Optional[int] = None,
        operation_budget: Optional[int] = None,
        dedupe_by_provenance: bool = False,
        allow_speculative_operands: bool = False,
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
        self.allow_speculative_operands = bool(allow_speculative_operands)

        self.nodes_by_int: Dict[int, Node] = {}
        self.nodes_by_value: Dict[ValueKey, Node] = {}
        self.nodes_by_uid: Dict[NodeUid, Node] = {}
        self.value_classes: Dict[ValueKey, Set[NodeUid]] = {}
        self._eq_class_ids: Dict[ValueKey, int] = {}
        self._speculative_by_provenance: Dict[Tuple[object, ...], Node] = {}
        self.edges: List[Edge] = []
        self._resolve_events: List[Dict[str, object]] = []
        self._resolutions: List[Dict[str, object]] = []
        self._resolution_pairs: Set[Tuple[NodeUid, NodeUid]] = set()
        self._spec_counter = itertools.count(1)
        self._node_uid_counter = itertools.count(1)
        self._edge_uid_counter = itertools.count(1)
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

    def _id_for_value_key(self, value_key: ValueKey) -> NodeId:
        p, q = int(value_key[0]), int(value_key[1])
        if q == 1:
            return int(p)
        return f"{p}/{q}"

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

    def _integer_level(self, n: int) -> int:
        # Primitive-centered backbone:
        # Ref(1)=1, Ref(2)=2, ..., Ref(0)=2, Ref(-1)=3, ...
        return int(n) if n >= 1 else 2 - int(n)

    def _integer_tier(self, n: int) -> int:
        if int(n) == 1:
            return 1
        if int(n) > 1:
            return 2
        return 3

    def _node_level(self, node: Node, *, memo: Optional[Dict[NodeUid, int]] = None) -> int:
        """
        MoO semantic level anchored at Ref(1)=1.

        - Nodes with provenance inputs derive level recursively from inputs.
        - No-input integer anchors/claims use primitive-centered integer levels.
        - Falls back to depth+1 when no other signal is available.
        """
        if memo is None:
            memo = {}
        cached = memo.get(node.node_uid)
        if cached is not None:
            return cached

        inputs_obj = node.provenance.get("inputs")
        input_levels: List[int] = []
        if isinstance(inputs_obj, list):
            for parent_uid in inputs_obj:
                if not isinstance(parent_uid, int):
                    continue
                parent = self.nodes_by_uid.get(parent_uid)
                if parent is None:
                    continue
                input_levels.append(self._node_level(parent, memo=memo))

        if input_levels:
            level = max(input_levels) + 1
        elif node.value is not None and int(node.value[1]) == 1:
            level = self._integer_level(int(node.value[0]))
        else:
            level = self._node_depth(node) + 1

        memo[node.node_uid] = int(level)
        return int(level)

    def _epistemic_order(self, node: Node) -> int:
        """
        Epistemic hierarchy:
        - Order 1: Ref(1), the only certainty.
        - Order 2: confirmed positive-spine iterations of 1 in the current
          corpus/runtime.
        - Order 3: unconfirmed or relational constructions from iterations of 1.
        """
        if node.status == "G" and node.id == 1:
            return 1
        if node.status == "G" and node.value is not None:
            p, q = node.value
            if int(q) == 1 and int(p) > 1:
                return 2
            return 3
        return 3

    def _constructible_from_one(
        self,
        node: Node,
        *,
        memo: Optional[Dict[NodeUid, bool]] = None,
        visiting: Optional[Set[NodeUid]] = None,
        edges_by_output_uid: Optional[Dict[NodeUid, List[Edge]]] = None,
    ) -> bool:
        """
        Whether a node is constructible from the primitive Ref(1) under current graph evidence.

        Grounded refs are treated as constructible backbone nodes.
        Speculative nodes are constructible when there exists at least one recorded
        derivation edge into that node whose inputs are all constructible.
        """
        if memo is None:
            memo = {}
        if visiting is None:
            visiting = set()
        if edges_by_output_uid is None:
            edges_by_output_uid = {}
            for edge in self.edges:
                edges_by_output_uid.setdefault(edge.output.node_uid, []).append(edge)

        cached = memo.get(node.node_uid)
        if cached is not None:
            return cached

        if node.node_uid in visiting:
            return False
        visiting.add(node.node_uid)

        if node.status == "G":
            memo[node.node_uid] = True
            visiting.discard(node.node_uid)
            return True

        incoming = edges_by_output_uid.get(node.node_uid, [])
        result = False
        for edge in incoming:
            if not edge.inputs:
                continue
            if all(
                self._constructible_from_one(
                    inp,
                    memo=memo,
                    visiting=visiting,
                    edges_by_output_uid=edges_by_output_uid,
                )
                for inp in edge.inputs
            ):
                result = True
                break
        memo[node.node_uid] = result
        visiting.discard(node.node_uid)
        return result

    def _epistemic_summary(
        self,
        nodes: List[Node],
        *,
        constructible_cache: Optional[Dict[NodeUid, bool]] = None,
    ) -> Dict[str, object]:
        if constructible_cache is None:
            constructible_cache = {}

        edges_by_output_uid: Dict[NodeUid, List[Edge]] = {}
        for edge in self.edges:
            edges_by_output_uid.setdefault(edge.output.node_uid, []).append(edge)

        order_counts = {"1": 0, "2": 0, "3": 0}
        constructible_counts = {"true": 0, "false": 0}
        for node in nodes:
            order = self._epistemic_order(node)
            order_counts[str(order)] = order_counts.get(str(order), 0) + 1
            constructible = self._constructible_from_one(
                node,
                memo=constructible_cache,
                edges_by_output_uid=edges_by_output_uid,
            )
            key = "true" if constructible else "false"
            constructible_counts[key] = constructible_counts.get(key, 0) + 1

        return {
            "order_counts": order_counts,
            "constructible_from_one_counts": constructible_counts,
        }

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

    def _ensure_operands_allowed(self, op: str, inputs: List[Node]) -> None:
        if self.allow_speculative_operands:
            return
        speculative = [node for node in inputs if node.status == "S"]
        if not speculative:
            return
        labels = ", ".join(node.label() for node in speculative)
        raise SpeculativeOperandError(
            f"Cannot apply {op} to speculative operand(s): {labels}. "
            "MoO records speculative nodes but does not operate on them until promotion."
        )

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
        Return the canonical node for an exact reduced rational value.

        In value-centric semantics, each reduced rational p/q corresponds to exactly
        one node. Distinct derivations are represented as distinct edges into that
        node, not as duplicate nodes.
        """
        key = self._normalize_value_key(value)
        existing = self.nodes_by_value.get(key)
        if existing is not None:
            return existing

        metadata: Dict[str, object] = {"op": seed_op, "inputs": self._input_ids(seed_inputs), "tier": 3}
        metadata["value"] = {"p": int(key[0]), "q": int(key[1])}
        if int(key[1]) == 1:
            metadata["potential_val"] = int(key[0])
        if result_tag is not None:
            metadata["result"] = result_tag
        if reason is not None:
            metadata["reason"] = reason

        depth = self._derive_depth(seed_inputs)
        provenance = self._make_provenance(op=seed_op, inputs=seed_inputs, depth=depth)
        node = Node(
            id=self._id_for_value_key(key),
            status="S",
            node_uid=self._next_node_uid(),
            value=key,
            provenance=provenance,
            metadata=metadata,
        )
        self.nodes_by_value[key] = node
        self._register_node(node)
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
            # Value-bearing nodes are canonicalized via _intern_value (one node per p/q).
            op = metadata.get("op")
            seed_op = op if isinstance(op, str) else "speculative"
            return self._intern_value(
                Fraction(int(value_key[0]), int(value_key[1])),
                seed_op=seed_op,
                seed_inputs=[],
            )
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
            value=None,
            provenance=provenance,
            metadata=metadata,
        )
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
        edge = Edge(
            op=op,
            inputs=inputs,
            output=output,
            edge_uid=int(next(self._edge_uid_counter)),
            metadata=edge_meta,
        )
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
        grounded = self.nodes_by_int.get(n)
        if grounded is not None:
            self.nodes_by_value.setdefault((n, 1), grounded)
            return grounded

        key: ValueKey = (n, 1)
        node = self.nodes_by_value.get(key)
        if node is None:
            metadata: Dict[str, object] = {"tier": self._integer_tier(n)}
            if n == 1:
                metadata["primitive"] = True
            metadata["value"] = {"p": n, "q": 1}
            metadata.setdefault("potential_val", n)
            node = Node(
                id=n,
                status="G",
                node_uid=self._next_node_uid(),
                value=key,
                provenance={
                    "op": "anchor",
                    "inputs": [],
                    "created_seq": self._next_created_seq(),
                    "depth": 0,
                },
                metadata=metadata,
            )
            self.nodes_by_value[key] = node
            self._register_node(node)
        else:
            # Promote the canonical value-node to a grounded Ref(N) anchor.
            node.status = "G"
            node.metadata["tier"] = self._integer_tier(n)
            node.metadata.setdefault("value", {"p": n, "q": 1})
            node.metadata.setdefault("potential_val", n)
            if n == 1:
                node.metadata["primitive"] = True

        self.nodes_by_int[n] = node
        return node

    def promote_core_iteration(self, n: int) -> Node:
        """
        Promote a positive-spine whole-number iteration reached by the positive-spine
        runtime.

        This is the current positive-spine path from speculative construction
        to a stronger epistemic status. Ordinary arithmetic may construct an
        integer-valued speculative node, but arithmetic alone does not confirm
        it.
        """
        n = int(n)
        if n < 1:
            raise ValueError(
                "positive-spine promotion is only defined for positive integers"
            )
        return self._get_or_create_grounded_ref(n)

    def get_or_create_ref(self, n: int) -> Node:
        """
        Public helper for referring to Ref(N).

        - Ref(1) is the only first-class primitive and may be created directly.
        - Positive integers greater than 1 become second order in this runtime
          only when the positive-spine grounding path reaches them.
        - Zero and negative integers are runtime removal anchors when grounded.
          They are native to the operator fan concept, but this runtime does
          not yet implement a full signed-field confirmation rule.
        - If Ref(N) is not yet grounded, this returns a speculative
          integer-claim node instead.
        """
        n = int(n)
        grounded = self.nodes_by_int.get(n)
        if grounded is not None:
            self._resolve_speculative_to_ref(n, grounded)
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
        Extend the positive-spine frontier by iterating +1 from the current
        maximum, then explicitly promoting the newly reached iteration.
        """
        target = int(n)
        one = self.get_or_create_ref(1)
        while True:
            current_max = int(self.frontier()["max"])
            if current_max >= target:
                return
            current = self.promote_core_iteration(current_max)
            self.add(current, one)
            self.promote_core_iteration(current_max + 1)

    def advance_frontier_min_to(self, n: int) -> None:
        """
        Historical helper placeholder for the current positive-spine runtime.

        Zero and negative values are native to MoO's operator fan through
        cancellation/removal, but this runtime has not implemented the signed
        field confirmation rule. Do not read this placeholder as a claim that
        aligned MoO has no negative side.
        """
        raise ValueError("signed operator-fan frontier is not implemented here")

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

    def resolve_events(self) -> List[Dict[str, object]]:
        return list(self._resolve_events)

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

        # 1) Canonicalization: one active node per reduced value.
        value_cardinality_issues: List[str] = []
        for value_key, members in sorted(self.value_classes.items()):
            active_members = [uid for uid in members if uid in self.nodes_by_uid]
            if len(active_members) != 1:
                value_cardinality_issues.append(
                    f"value={value_key} active_members={len(active_members)} uids={sorted(active_members)[:5]}"
                )
        checks["one_node_per_value"] = {
            "status": "pass" if not value_cardinality_issues else "fail",
            "details": {
                "issue_count": len(value_cardinality_issues),
                "issues": value_cardinality_issues[:10],
            },
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

        # 3) Spiderweb preservation: multiple distinct derivations should survive as edges.
        incoming_signatures: Dict[NodeUid, Set[Tuple[str, Tuple[NodeUid, ...]]]] = {}
        for edge in self.edges:
            sig = (edge.op, tuple(int(inp.node_uid) for inp in edge.inputs))
            incoming_signatures.setdefault(edge.output.node_uid, set()).add(sig)
        nodes_with_multiple_derivations = sum(1 for sigs in incoming_signatures.values() if len(sigs) >= 2)
        checks["multiple_derivations_preserved"] = {
            "status": "pass" if nodes_with_multiple_derivations > 0 else "na",
            "details": {"nodes_with_multiple_derivations": nodes_with_multiple_derivations},
        }

        speculative_operand_edges: List[Dict[str, object]] = []
        for edge in self.edges:
            speculative_inputs = [inp for inp in edge.inputs if inp.status == "S"]
            if not speculative_inputs:
                continue
            speculative_operand_edges.append(
                {
                    "edge_uid": int(edge.edge_uid),
                    "op": edge.op,
                    "inputs": [inp.label() for inp in edge.inputs],
                    "output": edge.output.label(),
                }
            )
        if self.allow_speculative_operands:
            spec_operand_status = "na"
        else:
            spec_operand_status = "pass" if not speculative_operand_edges else "fail"
        checks["no_speculative_operands"] = {
            "status": spec_operand_status,
            "details": {
                "issue_count": len(speculative_operand_edges),
                "issues": speculative_operand_edges[:10],
                "allow_speculative_operands": bool(self.allow_speculative_operands),
            },
        }

        # 4) Grounding consistency for integer anchors.
        grounding_issues: List[str] = []
        for n, node in sorted(self.nodes_by_int.items()):
            if node.status != "G":
                grounding_issues.append(f"Ref({n}) status={node.status}")
            if node.value != (int(n), 1):
                grounding_issues.append(f"Ref({n}) value={node.value}")
            if self.nodes_by_value.get((int(n), 1)) is not node:
                grounding_issues.append(f"Ref({n}) nodes_by_value mismatch")
        checks["grounding_consistent"] = {
            "status": "pass" if not grounding_issues else "fail",
            "details": {"issues": grounding_issues[:10], "issue_count": len(grounding_issues)},
        }

        statuses = [check["status"] for check in checks.values()]
        if any(status == "fail" for status in statuses):
            summary = "fail"
        elif any(status == "pass" for status in statuses):
            summary = "pass"
        else:
            summary = "na"

        active_nodes = self._active_nodes()
        constructible_cache: Dict[NodeUid, bool] = {}
        return {
            "semantics": "value_nodes",
            "summary": summary,
            "checks": checks,
            "epistemic": self._epistemic_summary(
                active_nodes, constructible_cache=constructible_cache
            ),
        }

    def speculative_nodes_by_uid(self) -> Dict[NodeUid, Node]:
        return {node.node_uid: node for node in self.nodes_by_uid.values() if node.status == "S"}

    def structure_report(
        self,
        *,
        focus_node: Optional[Node] = None,
        top_k_classes: int = 8,
        max_focus_members: int = 20,
    ) -> Dict[str, object]:
        active_nodes = self._active_nodes()
        level_cache: Dict[NodeUid, int] = {}
        constructible_cache: Dict[NodeUid, bool] = {}
        level_hist: Dict[int, int] = {}
        depth_hist: Dict[int, int] = {}
        for node in active_nodes:
            level = self._node_level(node, memo=level_cache)
            level_hist[level] = level_hist.get(level, 0) + 1
            depth = int(node.provenance.get("depth", 0))
            depth_hist[depth] = depth_hist.get(depth, 0) + 1

        incoming_edge_counts: Dict[ValueKey, int] = {}
        for edge in self.edges:
            if edge.output.value is None:
                continue
            incoming_edge_counts[edge.output.value] = incoming_edge_counts.get(edge.output.value, 0) + 1

        class_rows: List[Dict[str, object]] = []
        uid_to_node = self.nodes_by_uid
        for value_key, members in self.value_classes.items():
            active_members = [uid for uid in members if uid in uid_to_node]
            if not active_members:
                continue
            grounded = [uid for uid in active_members if uid_to_node[uid].status == "G"]
            speculative = [uid for uid in active_members if uid_to_node[uid].status == "S"]
            class_rows.append(
                {
                    "value": {"p": int(value_key[0]), "q": int(value_key[1])},
                    "label": self._value_key_label(value_key),
                    "eq_class": self._eq_class_ids.get(value_key),
                    "derivations_in": int(incoming_edge_counts.get(value_key, 0)),
                    "grounded": bool(grounded),
                    "speculative": bool(speculative),
                }
            )

        class_rows.sort(
            key=lambda row: (
                -int(row["derivations_in"]),
                str(row["label"]),
            )
        )

        anchor_fanin: Dict[NodeUid, int] = {}
        for event in self._resolutions:
            to_uid = event.get("to_uid")
            if isinstance(to_uid, int):
                anchor_fanin[to_uid] = anchor_fanin.get(to_uid, 0) + 1
        anchor_rows: List[Dict[str, object]] = []
        for uid, count in sorted(anchor_fanin.items(), key=lambda item: (-item[1], item[0])):
            node = uid_to_node.get(uid)
            if node is None:
                continue
            anchor_rows.append({"uid": uid, "id": node.id, "count": count})

        focus_payload: Optional[Dict[str, object]] = None
        if focus_node is not None:
            focus_value = self.value_equivalence_class(focus_node)
            if focus_value is None:
                focus_payload = {
                    "node_uid": focus_node.node_uid,
                    "node_level": self._node_level(focus_node, memo=level_cache),
                    "node_epistemic_order": self._epistemic_order(focus_node),
                    "node_constructible_from_one": self._constructible_from_one(
                        focus_node, memo=constructible_cache
                    ),
                    "node_depth_debug": self._node_depth(focus_node),
                    "value_class": None,
                }
            else:
                member_uids = sorted(
                    uid for uid in self.value_classes.get(focus_value, set()) if uid in uid_to_node
                )
                member_rows: List[Dict[str, object]] = []
                for uid in member_uids[:max_focus_members]:
                    node = uid_to_node[uid]
                    depth = self._node_depth(node)
                    member_rows.append(
                        {
                            "uid": uid,
                            "id": node.id,
                            "status": node.status,
                            "op": node.provenance.get("op"),
                            "level": self._node_level(node, memo=level_cache),
                            "epistemic_order": self._epistemic_order(node),
                            "constructible_from_one": self._constructible_from_one(
                                node, memo=constructible_cache
                            ),
                            "depth_debug": depth,
                            "resolved_to": node.metadata.get("resolved_to"),
                        }
                    )
                focus_payload = {
                    "node_uid": focus_node.node_uid,
                    "node_id": focus_node.id,
                    "node_level": self._node_level(focus_node, memo=level_cache),
                    "node_epistemic_order": self._epistemic_order(focus_node),
                    "node_constructible_from_one": self._constructible_from_one(
                        focus_node, memo=constructible_cache
                    ),
                    "node_depth_debug": self._node_depth(focus_node),
                    "value_class": self._value_key_label(focus_value),
                    "class_size": len(member_uids),
                    "members": member_rows,
                    "truncated": len(member_uids) > max_focus_members,
                }

        return {
            "semantics": "value_nodes",
            "counts": {
                "nodes": len(active_nodes),
                "edges": len(self.edges),
                "grounded_nodes": len(self.nodes_by_int),
                "speculative_nodes": sum(1 for node in active_nodes if node.status == "S"),
                "value_classes": len(class_rows),
                "resolutions": len(self._resolutions),
            },
            "epistemic": self._epistemic_summary(
                active_nodes, constructible_cache=constructible_cache
            ),
            "level_histogram": dict(sorted(level_hist.items())),
            "depth_histogram": dict(sorted(depth_hist.items())),
            "depth_histogram_debug": dict(sorted(depth_hist.items())),
            "top_value_classes": class_rows[: max(0, top_k_classes)],
            "anchor_resolution_fanin": anchor_rows,
            "focus": focus_payload,
        }

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

        all_nodes = list(self.nodes_by_uid.values())
        constructible_cache: Dict[NodeUid, bool] = {}
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
        resolution_fanin: Dict[int, int] = {}
        for event in self._resolutions:
            to_id = event.get("to_id")
            if isinstance(to_id, int):
                resolution_fanin[to_id] = resolution_fanin.get(to_id, 0) + 1
        multi_resolved_grounded = {n: c for n, c in resolution_fanin.items() if c > 1}

        potential_val_hist: Dict[int, int] = {}
        speculative_with_potential_val = 0
        for node in all_nodes:
            if node.status != "S":
                continue
            potential_val = node.metadata.get("potential_val")
            if isinstance(potential_val, int):
                speculative_with_potential_val += 1
                potential_val_hist[potential_val] = potential_val_hist.get(potential_val, 0) + 1

        return {
            "semantics": "value_nodes",
            "intern_policy": self.intern_policy,
            "counts": {
                "grounded_nodes": len(self.nodes_by_int),
                "speculative_nodes": sum(1 for node in all_nodes if node.status == "S"),
                "total_nodes": len(self.nodes_by_uid),
                "edges": len(self.edges),
                "resolve_events": len(self._resolve_events),
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
            "resolution": {
                "grounded_with_multiple_resolutions": len(multi_resolved_grounded),
                "max_resolutions_into_grounded": max(resolution_fanin.values(), default=0),
                "top_grounded_by_resolution_fanin": top({n: c for n, c in resolution_fanin.items()}),
            },
            "speculation": {
                "speculative_with_potential_val": speculative_with_potential_val,
                "potential_val_histogram": potential_val_hist,
            },
            "epistemic": self._epistemic_summary(
                all_nodes, constructible_cache=constructible_cache
            ),
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

    def _maybe_resolve_new_spec_to_existing_ref(self, node: Node) -> Node:
        # Value-centric identity collapses integer claims and grounded refs into one node.
        # Resolution is therefore represented by grounding (promotion to status "G"),
        # not by speculative→grounded alias edges.
        return node

    def _resolve_speculative_to_ref(self, n: int, ref_node: Node) -> None:
        # See note in _maybe_resolve_new_spec_to_existing_ref().
        return

    def to_resolve_dot(self) -> str:
        lines = ["digraph G {"]

        for node in self.nodes_by_int.values():
            lines.append(
                f'  "{node.id}" [label="{node.label()}", shape=box, style=filled, fillcolor=lightgray];'
            )
        for node in sorted(
            [n for n in self.nodes_by_uid.values() if n.status == "S"],
            key=lambda n: (str(n.id), int(n.node_uid)),
        ):
            lines.append(
                f'  "{node.id}" [label="{node.label()}", shape=ellipse, style=filled, fillcolor=yellow];'
            )

        ghost_ids: Dict[str, str] = {}
        for event in self._resolve_events:
            spec_id = str(event.get("spec_id"))
            ghost_id = f"ghost_{spec_id}"
            ghost_ids[spec_id] = ghost_id

        for event in self._resolve_events:
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
                f'  "{ghost_id}" -> "{resolved_to}" [label="resolve", style=dashed, color=blue];'
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

        resolve_counts: Dict[int, int] = {}
        for event in self._resolve_events:
            resolved_to = event.get("resolved_to")
            if isinstance(resolved_to, int):
                resolve_counts[resolved_to] = resolve_counts.get(resolved_to, 0) + 1

        rows: List[Dict[str, int]] = []
        for n in sorted(self.nodes_by_int.keys()):
            rows.append(
                {
                    "n": int(n),
                    "constructions": int(output_edge_counts.get(n, 0)),
                    "in_degree": int(in_degree.get(n, 0)),
                    "out_degree": int(out_degree.get(n, 0)),
                    "resolve_links": int(resolve_counts.get(n, 0)),
                }
            )
        return rows

    def field_map_csv(self) -> str:
        rows = self.field_map()
        header = ["n", "constructions", "in_degree", "out_degree", "resolve_links"]
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
            resolve_links = row["resolve_links"]
            bar_len = int(round(constructions / max_constructions * bar_width))
            bar = "#" * bar_len
            lines.append(
                f"{n:>4} | c={constructions:>3} in={in_degree:>3} out={out_degree:>3} "
                f"resolve={resolve_links:>3} | {bar}"
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
        self._ensure_operands_allowed("+", [a, b])
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("+", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            value = Fraction(val, 1)
            out = self._intern_value(value, seed_op="+", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("+", [a, b], out, edge_meta)
            return self._maybe_resolve_new_spec_to_existing_ref(out)
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val + right_val
            out = self._intern_value(value, seed_op="+", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("+", [a, b], out, edge_meta)
            return self._maybe_resolve_new_spec_to_existing_ref(out)
        potential = self._maybe_potential("+", a, b)
        metadata = {"op": "+", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="+", inputs=[a, b], metadata=metadata)
        self._record_edge("+", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_resolve_new_spec_to_existing_ref(out)

    def sub(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        self._ensure_operands_allowed("-", [a, b])
        if a.status == "G" and b.status == "G":
            kind, val = self._normalize("-", int(a.id), int(b.id))
            assert kind == "int" and val is not None
            value = Fraction(val, 1)
            out = self._intern_value(value, seed_op="-", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("-", [a, b], out, edge_meta)
            return self._maybe_resolve_new_spec_to_existing_ref(out)
        left_val = self._node_value(a)
        right_val = self._node_value(b)
        if left_val is not None and right_val is not None:
            value = left_val - right_val
            out = self._intern_value(value, seed_op="-", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("-", [a, b], out, edge_meta)
            return self._maybe_resolve_new_spec_to_existing_ref(out)
        potential = self._maybe_potential("-", a, b)
        metadata = {"op": "-", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="-", inputs=[a, b], metadata=metadata)
        self._record_edge("-", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_resolve_new_spec_to_existing_ref(out)

    def mul(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        self._ensure_operands_allowed("*", [a, b])
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
            return self._maybe_resolve_new_spec_to_existing_ref(out)

        if left_val is not None and right_val is not None:
            value = left_val * right_val
            out = self._intern_value(value, seed_op="*", seed_inputs=[a, b])
            edge_meta = self._edge_meta_for_value(value=value, out=out)
            self._record_edge("*", [a, b], out, edge_meta)
            return self._maybe_resolve_new_spec_to_existing_ref(out)

        potential = self._maybe_potential("*", a, b)
        metadata = {"op": "*", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="*", inputs=[a, b], metadata=metadata)
        self._record_edge("*", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_resolve_new_spec_to_existing_ref(out)

    def div(self, a: Node, b: Node) -> Node:
        self._consume_operation_budget()
        self._ensure_operands_allowed("/", [a, b])
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
            return self._maybe_resolve_new_spec_to_existing_ref(out)

        potential = self._potential_division(a, b)
        metadata = {"op": "/", "inputs": self._input_ids([a, b])}
        if potential is not None:
            metadata["potential_val"] = potential
        out = self._create_spec_node(op="/", inputs=[a, b], metadata=metadata)
        self._record_edge("/", [a, b], out, {"result": "speculative", "potential_val": potential})
        return self._maybe_resolve_new_spec_to_existing_ref(out)

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
        incoming_edge_counts: Dict[ValueKey, int] = {}
        for edge in self.edges:
            if edge.output.value is None:
                continue
            incoming_edge_counts[edge.output.value] = incoming_edge_counts.get(edge.output.value, 0) + 1
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
                "derivations_in": int(incoming_edge_counts.get(value_key, 0)),
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
        level_cache: Dict[NodeUid, int] = {}
        constructible_cache: Dict[NodeUid, bool] = {}
        edges_by_output_uid: Dict[NodeUid, List[Edge]] = {}
        for edge in self.edges:
            edges_by_output_uid.setdefault(edge.output.node_uid, []).append(edge)

        def node_payload(node: Node) -> Dict[str, object]:
            value_payload: Optional[Dict[str, int]] = None
            if node.value is not None:
                value_payload = {"p": int(node.value[0]), "q": int(node.value[1])}
            depth = self._node_depth(node)
            return {
                "id": node.id,
                "node_uid": node.node_uid,
                "status": node.status,
                "level": self._node_level(node, memo=level_cache),
                "epistemic_order": self._epistemic_order(node),
                "constructible_from_one": self._constructible_from_one(
                    node,
                    memo=constructible_cache,
                    edges_by_output_uid=edges_by_output_uid,
                ),
                "depth_debug": depth,
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
                "edge_uid": int(edge.edge_uid),
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
            "semantics": "value_nodes",
            "intern_policy": self.intern_policy,
            "nodes": [node_payload(n) for n in self._active_nodes()],
            "edges": [edge_payload(e) for e in self.edges],
            "epistemic": self._epistemic_summary(
                self._active_nodes(), constructible_cache=constructible_cache
            ),
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
        for node in sorted(
            [n for n in self.nodes_by_uid.values() if n.status == "S"],
            key=lambda n: (str(n.id), int(n.node_uid)),
        ):
            lines.append(f'  "{node.id}" [label="{node.label()}", shape=ellipse, style=filled, fillcolor=yellow];')
        for edge in self.edges:
            for inp in edge.inputs:
                lines.append(f'  "{inp.id}" -> "{edge.output.id}" [label="{edge.op}"];')
        lines.append("}")
        return "\n".join(lines)

    def _to_dot_value_projection(self) -> str:
        lines = ["digraph G {"]
        node_to_class_node: Dict[NodeUid, str] = {}
        incoming_edge_counts: Dict[ValueKey, int] = {}
        for edge in self.edges:
            if edge.output.value is None:
                continue
            incoming_edge_counts[edge.output.value] = incoming_edge_counts.get(edge.output.value, 0) + 1

        for value_key in sorted(self.value_classes.keys()):
            members = self.value_classes[value_key]
            active_members = sorted(uid for uid in members if uid in self.nodes_by_uid)
            if not active_members:
                continue
            eq_class = self._eq_class_ids.get(value_key)
            node_name = f'val_{int(value_key[0])}_{int(value_key[1])}'
            label = self._value_key_label(value_key)
            derivations_in = int(incoming_edge_counts.get(value_key, 0))
            if isinstance(eq_class, int):
                label = f"{label}\\nEQ:{eq_class} in={derivations_in}"
            else:
                label = f"{label}\\nin={derivations_in}"
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
    allow_speculative_operands: bool = False,
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
        allow_speculative_operands=allow_speculative_operands,
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
                try:
                    return g.sub(get_zero(), eval_node(node.operand))
                except SpeculativeOperandError as exc:
                    raise MooExpressionError(
                        "Unary negation would operate on the speculative 0 node in aligned mode."
                    ) from exc
            raise MooExpressionError(f"Unsupported unary operator: {node.op.__class__.__name__}")

        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return promote_expression_integer(g.add(left, right))
            if isinstance(node.op, ast.Sub):
                return promote_expression_integer(g.sub(left, right))
            if isinstance(node.op, ast.Mult):
                return promote_expression_integer(g.mul(left, right))
            if isinstance(node.op, ast.Div):
                return promote_expression_integer(g.div(left, right))
            raise MooExpressionError(f"Unsupported binary operator: {node.op.__class__.__name__}")

        raise MooExpressionError(f"Unsupported syntax: {node.__class__.__name__}")

    def promote_expression_integer(node: Node) -> Node:
        value = g.numeric_value(node)
        if value is None:
            return node
        p, q = value
        if int(q) == 1 and int(p) >= 1:
            return g.promote_core_iteration(int(p))
        return node

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
    allow_speculative_operands: bool = False,
) -> Graph:
    """
    Build a small universe from the only primitive certainty: Ref(1).

    `limit` controls how far we iterate outward in the positive-spine demo
    backbone.

    This demo deliberately:
    - treats positive integers as positive-spine second-order confirmations,
    - treats multiplication/division outputs as speculative claims until the
      positive-spine runtime later promotes them,
    - includes a small shadow-ref example that is recorded and then promoted,
      without operating on the speculative shadow.
    """
    g = Graph(
        intern_policy=intern_policy,
        max_nodes=max_nodes,
        max_depth=max_depth,
        operation_budget=operation_budget,
        dedupe_by_provenance=dedupe_by_provenance,
        allow_speculative_operands=allow_speculative_operands,
    )
    one = g.get_or_create_ref(1)
    g.sub(one, one)

    # Create speculative "shadow refs" that will later be grounded by the integer backbone.
    g.speculate_ref(2, reason="demo_shadow_ref")

    limit = max(0, int(limit))

    positives = {1: one}
    for n in range(2, limit + 1):
        g.add(positives[n - 1], one)
        positives[n] = g.promote_core_iteration(n)

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

    # A speculative fraction. It is recorded but not used as an operand.
    if limit >= 2:
        g.div(one, positives[2])
    if limit >= 3:
        g.div(one, positives[3])

    return g


def fibonacci_demo(
    terms: int = 8,
    *,
    intern_policy: Optional[InternPolicy] = None,
    max_nodes: Optional[int] = None,
    max_depth: Optional[int] = None,
    operation_budget: Optional[int] = None,
    dedupe_by_provenance: bool = False,
    allow_speculative_operands: bool = False,
) -> Tuple[Graph, Dict[str, object], Optional[Node]]:
    """
    Build a Fibonacci-focused graph from Ref(1).

    The aligned construction deliberately layers:
    - recurrence terms F(n) = F(n-1) + F(n-2),
    - exact rational ratios F(n+1)/F(n),
    - subtraction back-links F(n) - F(n-1) = F(n-2).

    Cassini-style second-step identities are omitted by default because they
    operate on speculative product nodes. Pass allow_speculative_operands=True
    only for historical exploratory behavior.
    """
    terms = max(2, int(terms))
    g = Graph(
        intern_policy=intern_policy,
        max_nodes=max_nodes,
        max_depth=max_depth,
        operation_budget=operation_budget,
        dedupe_by_provenance=dedupe_by_provenance,
        allow_speculative_operands=allow_speculative_operands,
    )
    one = g.get_or_create_ref(1)

    fib_values = [1, 1]
    for _ in range(2, terms):
        fib_values.append(fib_values[-1] + fib_values[-2])

    backbone: Dict[int, Node] = {1: one}
    for n in range(2, max(fib_values) + 1):
        g.add(backbone[n - 1], one)
        backbone[n] = g.promote_core_iteration(n)

    fib_nodes: List[Node] = [backbone[value] for value in fib_values]
    for idx in range(2, len(fib_nodes)):
        g.add(fib_nodes[idx - 1], fib_nodes[idx - 2])

    ratio_nodes: List[Node] = []
    for idx in range(1, len(fib_nodes)):
        ratio_nodes.append(g.div(fib_nodes[idx], fib_nodes[idx - 1]))

    back_links: List[Tuple[int, int, int, Node]] = []
    focus_node: Optional[Node] = None
    for idx in range(2, len(fib_nodes)):
        back_link = g.sub(fib_nodes[idx], fib_nodes[idx - 1])
        back_links.append((idx + 1, idx, idx - 1, back_link))
        focus_node = back_link

    cassini_rows: List[Tuple[int, Node, Node, Node]] = []
    if allow_speculative_operands:
        for idx in range(1, len(fib_nodes) - 1):
            left = g.mul(fib_nodes[idx + 1], fib_nodes[idx - 1])
            right = g.mul(fib_nodes[idx], fib_nodes[idx])
            identity = g.sub(left, right)
            cassini_rows.append((idx + 1, left, right, identity))

    report = fibonacci_report(
        g,
        fib_nodes=fib_nodes,
        ratio_nodes=ratio_nodes,
        back_links=back_links,
        cassini_rows=cassini_rows,
        focus_node=focus_node,
    )
    return g, report, focus_node


def fibonacci_report(
    graph: Graph,
    *,
    fib_nodes: List[Node],
    ratio_nodes: List[Node],
    back_links: List[Tuple[int, int, int, Node]],
    cassini_rows: List[Tuple[int, Node, Node, Node]],
    focus_node: Optional[Node],
) -> Dict[str, object]:
    level_cache: Dict[NodeUid, int] = {}
    constructible_cache: Dict[NodeUid, bool] = {}

    def value_payload(node: Node) -> Optional[Dict[str, int]]:
        value = graph.numeric_value(node)
        if value is None:
            return None
        return {"p": int(value[0]), "q": int(value[1])}

    def node_payload(node: Node) -> Dict[str, object]:
        return {
            "id": node.id,
            "node_uid": node.node_uid,
            "status": node.status,
            "value": value_payload(node),
            "resolved_to": node.metadata.get("resolved_to"),
            "op": node.provenance.get("op"),
            "level": graph._node_level(node, memo=level_cache),
            "depth_debug": graph._node_depth(node),
            "constructible_from_one": graph._constructible_from_one(
                node, memo=constructible_cache
            ),
        }

    sequence = [
        {"index": idx, **node_payload(node)}
        for idx, node in enumerate(fib_nodes, start=1)
    ]
    ratios = [
        {"label": f"F{idx + 1}/F{idx}", **node_payload(node)}
        for idx, node in enumerate(ratio_nodes, start=1)
    ]
    subtraction_back_links = [
        {
            "label": f"F{source_idx} - F{subtract_idx} = F{result_idx}",
            **node_payload(node),
        }
        for source_idx, subtract_idx, result_idx, node in back_links
    ]
    cassini = [
        {
            "n": n,
            "label": f"F{n + 1}*F{n - 1} - F{n}^2",
            "expected": 1 if n % 2 == 0 else -1,
            "left": node_payload(left),
            "right": node_payload(right),
            "identity": node_payload(identity),
        }
        for n, left, right, identity in cassini_rows
    ]

    return {
        "terms": len(fib_nodes),
        "sequence": sequence,
        "ratios": ratios,
        "subtraction_back_links": subtraction_back_links,
        "cassini": cassini,
        "focus": graph.structure_report(
            focus_node=focus_node,
            top_k_classes=10,
            max_focus_members=10,
        )["focus"],
    }


if __name__ == "__main__":
    def parse_cli(
        argv: List[str],
    ) -> Tuple[
        Optional[str],
        int,
        Optional[int],
        Dict[str, bool],
        Optional[str],
        Dict[str, object],
    ]:
        flags = {
            "show_stats": False,
            "show_resolve_dot": False,
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
            "allow_speculative_operands": False,
        }
        limit = 3
        fibonacci_terms: Optional[int] = None
        expr_tokens: List[str] = []
        write_maps_prefix: Optional[str] = None

        idx = 0
        while idx < len(argv):
            arg = argv[idx]
            if arg in {"-h", "--help"}:
                print(
                    "Usage:\n"
                    "  python3 constructionist_math.py [--view structure|value] [--limit N]\n"
                    "      [--fibonacci N]\n"
                    "      [--intern-policy none|by_provenance] [--max-nodes N] [--max-depth N]\n"
                    "      [--op-budget N] [--dedupe-by-provenance] [--allow-speculative-operands]\n"
                    "      [--maps] [--stats] [--resolve-dot]\n"
                    "      [--field] [--field-csv] [--field-ascii] [--write-maps PREFIX] [<expr>]\n\n"
                    "Views:\n"
                    "  structure: canonical value nodes with all edge occurrences (construction lens)\n"
                    "  value:     deduped value-link projection (unique src/dst/op edges)\n\n"
                    "Expr syntax: only the literal `1`, operators `+ - * /`, and parentheses.\n"
                    "Aligned mode records speculative outputs but does not operate on them.\n"
                )
                raise SystemExit(0)

            if arg == "--maps":
                flags["show_stats"] = True
                flags["show_resolve_dot"] = True
                flags["show_field_json"] = True
                flags["show_field_ascii"] = True
                idx += 1
                continue

            if arg == "--stats":
                flags["show_stats"] = True
                idx += 1
                continue

            if arg == "--resolve-dot":
                flags["show_resolve_dot"] = True
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

            if arg == "--fibonacci":
                if idx + 1 >= len(argv):
                    raise SystemExit("Missing value for --fibonacci")
                try:
                    fibonacci_terms = int(argv[idx + 1])
                except ValueError as exc:
                    raise SystemExit(f"Invalid --fibonacci value: {argv[idx + 1]!r}") from exc
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

            if arg == "--allow-speculative-operands":
                graph_config["allow_speculative_operands"] = True
                idx += 1
                continue

            if arg.startswith("--"):
                raise SystemExit(f"Unknown option: {arg}")

            expr_tokens = argv[idx:]
            break

        expression = " ".join(expr_tokens).strip() if expr_tokens else None
        return expression, limit, fibonacci_terms, flags, write_maps_prefix, graph_config

    expression, limit, fibonacci_terms, flags, write_maps_prefix, graph_config = parse_cli(sys.argv[1:])
    if expression is not None and fibonacci_terms is not None:
        raise SystemExit("Cannot combine --fibonacci with an expression.")
    graph_kwargs = {
        "intern_policy": graph_config["intern_policy"],
        "max_nodes": graph_config["max_nodes"],
        "max_depth": graph_config["max_depth"],
        "operation_budget": graph_config["operation_budget"],
        "dedupe_by_provenance": graph_config["dedupe_by_provenance"],
        "allow_speculative_operands": graph_config["allow_speculative_operands"],
    }
    view = str(graph_config["view"])
    result: Optional[Node] = None
    fibonacci_payload: Optional[Dict[str, object]] = None

    if expression is not None:
        graph, result = eval_moo(expression, **graph_kwargs)
        print("# EXPR")
        print(expression)
        print("\n# RESULT")
        print(result.label())
    elif fibonacci_terms is not None:
        graph, fibonacci_payload, result = fibonacci_demo(terms=fibonacci_terms, **graph_kwargs)
        print("# DEMO")
        print(f"fibonacci:{fibonacci_terms}")
    else:
        graph = demo(limit=limit, **graph_kwargs)

    if write_maps_prefix is not None:
        prefix = Path(write_maps_prefix)
        targets = {
            "dot": Path(str(prefix) + ".dot"),
            "resolve_dot": Path(str(prefix) + ".resolve.dot"),
            "field_json": Path(str(prefix) + ".field.json"),
            "field_csv": Path(str(prefix) + ".field.csv"),
            "field_ascii": Path(str(prefix) + ".field.txt"),
            "stats": Path(str(prefix) + ".stats.json"),
            "resolve_events": Path(str(prefix) + ".resolve_events.json"),
            "resolutions": Path(str(prefix) + ".resolutions.json"),
            "acceptance": Path(str(prefix) + ".acceptance.json"),
            "structure": Path(str(prefix) + ".structure.json"),
        }
        if fibonacci_payload is not None:
            targets["fibonacci"] = Path(str(prefix) + ".fibonacci.json")
        for path in targets.values():
            if path.exists():
                raise SystemExit(f"Refusing to overwrite existing file: {path}")
            if path.parent != Path(".") and not path.parent.exists():
                raise SystemExit(f"Directory does not exist: {path.parent}")

        targets["dot"].write_text(graph.to_dot_view(view=view) + "\n", encoding="utf-8")
        targets["resolve_dot"].write_text(graph.to_resolve_dot() + "\n", encoding="utf-8")
        targets["field_json"].write_text(
            json.dumps(graph.field_map(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["field_csv"].write_text(graph.field_map_csv() + "\n", encoding="utf-8")
        targets["field_ascii"].write_text(graph.field_map_ascii() + "\n", encoding="utf-8")
        targets["stats"].write_text(
            json.dumps(graph.stats(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["resolve_events"].write_text(
            json.dumps(graph.resolve_events(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["resolutions"].write_text(
            json.dumps(graph.resolutions(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["acceptance"].write_text(
            json.dumps(graph.acceptance_report(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        targets["structure"].write_text(
            json.dumps(graph.structure_report(focus_node=result), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        if fibonacci_payload is not None:
            targets["fibonacci"].write_text(
                json.dumps(fibonacci_payload, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print("\n# WROTE_MAPS")
        for key, path in targets.items():
            print(f"{key}: {path}")

    if fibonacci_payload is not None:
        print("\n# FIBONACCI")
        print(json.dumps(fibonacci_payload, indent=2, sort_keys=True))
    if flags["show_stats"]:
        print("\n# STATS")
        print(json.dumps(graph.stats(), indent=2, sort_keys=True))
        print("\n# RESOLVE_EVENTS")
        print(json.dumps(graph.resolve_events(), indent=2, sort_keys=True))
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
    if flags["show_resolve_dot"]:
        print("\n# RESOLVE_DOT")
        print(graph.to_resolve_dot())
    print("\n# ACCEPTANCE")
    print(json.dumps(graph.acceptance_report(), indent=2, sort_keys=True))
    print("\n# STRUCTURE")
    print(json.dumps(graph.structure_report(focus_node=result), indent=2, sort_keys=True))
    print("# JSON")
    print(graph.to_json(indent=2))
    print("\n# DOT")
    print(graph.to_dot_view(view=view))

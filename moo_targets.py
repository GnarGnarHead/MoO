from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class Target:
    name: str
    value: float


KNOWN_TARGETS: Dict[str, Target] = {
    "pi": Target("pi", math.pi),
    "e": Target("e", math.e),
    "tau": Target("tau", math.tau),
    "sqrt2": Target("sqrt2", math.sqrt(2.0)),
    "sqrt3": Target("sqrt3", math.sqrt(3.0)),
    "phi": Target("phi", (1.0 + math.sqrt(5.0)) / 2.0),
    "ln2": Target("ln2", math.log(2.0)),
    "ln10": Target("ln10", math.log(10.0)),
}


def parse_targets(raw: str) -> Tuple[Target, ...]:
    names = [part.strip() for part in raw.split(",") if part.strip()]
    if not names:
        raise SystemExit("No targets specified.")

    expanded: List[str] = []
    for name in names:
        if name == "all":
            expanded.extend(sorted(KNOWN_TARGETS.keys()))
        else:
            expanded.append(name)

    targets: List[Target] = []
    for name in expanded:
        t = KNOWN_TARGETS.get(name)
        if t is not None:
            targets.append(t)
            continue
        try:
            val = float(name)
        except ValueError as exc:
            raise SystemExit(
                f"Unknown target: {name!r}. Known: {', '.join(sorted(KNOWN_TARGETS.keys()))} "
                "(or pass a numeric literal like 3.14159)."
            ) from exc
        targets.append(Target(name=name, value=float(val)))
    return tuple(targets)


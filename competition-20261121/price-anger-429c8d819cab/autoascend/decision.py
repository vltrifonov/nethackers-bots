"""Record and rerank the choices already admitted by AutoAscend."""

from math import isfinite

from . import learned_rules

_FLAGS = (
    "is_continue", "is_eat", "is_recover", "is_descend", "is_progress",
    "is_elbereth", "is_melee", "is_food", "is_ration",
)


def choice(choice_id, base, **features):
    base = float(base)
    if not isfinite(base):
        base = 0.0
    values = dict.fromkeys(_FLAGS, 0)
    values.update(features)
    values["base_score"] = base
    return {"id": choice_id, "score": base, "features": values}


def select(node, context, choices, hook, *, only=None, require_change=False, target_name=None):
    score = learned_rules.score
    if hook is not None:
        observed = [
            {**candidate, "features": candidate["features"].copy()} for candidate in choices
        ]
        record = {"node": node, "context": context.copy(), "choices": observed}
        if target_name is not None:
            record["target_name"] = target_name
        override = hook(record)
        if override is not None:
            score = override

    def priority(index):
        candidate = choices[index]
        base = candidate["score"]
        features = candidate["features"]
        if node == "combat" and target_name is None:
            return base
        if only is not None and not features.get(only):
            return base
        result = score(node, {**context, **features}, base)
        return result if isfinite(result) else base

    priorities = [priority(index) for index in range(len(choices))]
    if require_change and all(
        score == candidate["score"] for score, candidate in zip(priorities, choices)
    ):
        return None
    return max(range(len(choices)), key=priorities.__getitem__)

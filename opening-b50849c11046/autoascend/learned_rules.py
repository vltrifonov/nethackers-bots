"""Generated checkpoint scoring rules."""

from operator import ge, gt, le, lt

GENOMES = {'opening': [{'bias': 5.0, 'weights': {}, 'when': ['turn', '>=', 2500.0]}]}
ENABLED = True

_COMPARE = {"<": lt, "<=": le, ">": gt, ">=": ge}


def score(node, features, base):
    def value(name):
        return base if name == "base_score" else features.get(name, 0)

    for rule in GENOMES.get(node, ()):
        feature, operator, threshold = rule["when"]
        if _COMPARE[operator](value(feature), threshold):
            return base + rule["bias"] + sum(
                coefficient * value(name) for name, coefficient in rule["weights"].items()
            )
    return base

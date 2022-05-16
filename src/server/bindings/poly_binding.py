import math

from poly_classifier import (
    rooted_polynomial_classifier,
    unrooted_polynomial_classifier,
)
from problem import GenericProblem
from problem import each_constr_is_homogeneous
from response import GenericResponse
from .classify_context import ClassifyContext
from complexity import CONST, ITERATED_LOG, POLY, GLOBAL
from complexity import LOG, UNSOLVABLE
from .common import move_root_label_to_center


def classify(p: GenericProblem, context: ClassifyContext) -> GenericResponse:
    if not p.flags.is_tree:
        raise Exception("poly", "Cannot classify if the problem is not a tree")

    if not p.flags.is_regular:
        raise Exception("poly", "Cannot classify if the graph is not regular")

    if not p.root_allow_all or not p.leaf_allow_all:
        raise Exception("poly", "Leaves and roots must allow all configurations")

    active_degree = len(p.active_constraints[0]) if len(p.active_constraints) else 3
    passive_degree = len(p.passive_constraints[0]) if len(p.passive_constraints) else 2

    if active_degree != 3:
        raise Exception("poly", "Active configurations must be of size 3")

    if passive_degree != 2:
        raise Exception("poly", "Passive configurations must be of size 2")

    if p.flags.is_directed_or_rooted and not each_constr_is_homogeneous(
        p.passive_constraints
    ):
        raise Exception(
            "poly",
            "Passive constraints for rooted case must be simple pairs of the same labels.",
        )

    active_constraints = list(map(tuple, p.active_constraints))
    passive_constraints = list(map(tuple, p.passive_constraints))

    det_upper_bound = UNSOLVABLE
    det_lower_bound = CONST
    rand_upper_bound = UNSOLVABLE
    rand_lower_bound = CONST
    if p.flags.is_directed_or_rooted:
        k = rooted_polynomial_classifier(active_constraints)
    else:
        k = unrooted_polynomial_classifier(active_constraints, passive_constraints)
    if k == 0:
        det_lower_bound = UNSOLVABLE
        rand_lower_bound = UNSOLVABLE
    elif k == 1:
        det_lower_bound = GLOBAL
        rand_lower_bound = GLOBAL
        det_upper_bound = GLOBAL
        rand_upper_bound = GLOBAL
    elif k == math.inf:
        det_upper_bound = LOG
        rand_upper_bound = LOG
    else:
        det_lower_bound = f"(n^(1/{k}))"
        rand_lower_bound = f"(n^(1/{k}))"
        det_upper_bound = f"(n^(1/{k}))"
        rand_upper_bound = f"(n^(1/{k}))"

    return GenericResponse(
        p, rand_upper_bound, rand_lower_bound, det_upper_bound, det_lower_bound
    )

import math

CONST = "(1)"
ITERATED_LOG = "(log* n)"
LOGLOG = "(loglog n)"
LOG = "(log n)"
POLY = "(n^(1/k))"
GLOBAL = "(n)"
UNSOLVABLE = "unsolvable"
UNKNOWN = ""

complexities = [CONST, ITERATED_LOG, LOGLOG, LOG, POLY, GLOBAL, UNSOLVABLE]
from decimal import *


def extended_index(complexity):
    if complexity.startswith("(n^"):
        if complexity == "(n^(1/k))":
            a_index = math.nan
        else:
            a_index = complexities.index(POLY) + 1 / Decimal(complexity[6:-2])
    else:
        a_index = complexities.index(complexity)
    return a_index


# def complexity_from_idx(index):
#     if index

from problem import GenericProblem
from response import GenericResponse, Sources
from complexity import complexities, extended_index
from complexity import LOG, LOGLOG, CONST, UNSOLVABLE, UNKNOWN
from classifier_types import Classifier
from bindings import ClassifyContext
from typing import Dict, Tuple
from own_types import ComplexityType
from bindings import cp_classify
from bindings import rt_classify
from bindings import tlp_classify
from bindings import brt_classify
from bindings import re_classify
from bindings import poly_classify


def get_upper_bound(
    responses: Dict[Classifier, GenericResponse], attr_str: str
) -> Tuple[Classifier, ComplexityType]:
    classifier_to_complexity_idx = {
        k: (extended_index(getattr(res, attr_str)), getattr(res, attr_str))
        for k, res in responses.items()
    }
    min_classifier = min(
        classifier_to_complexity_idx, key=classifier_to_complexity_idx.get
    )
    return min_classifier, classifier_to_complexity_idx[min_classifier][1]


def get_lower_bound(
    responses: Dict[Classifier, GenericResponse], attr_str: str
) -> Tuple[Classifier, ComplexityType]:
    classifier_to_complexity_idx = {
        k: (extended_index(getattr(res, attr_str)), getattr(res, attr_str))
        for k, res in responses.items()
    }
    max_classifier = max(
        classifier_to_complexity_idx, key=classifier_to_complexity_idx.get
    )
    return max_classifier, classifier_to_complexity_idx[max_classifier][1]


def remove_unknowns(response: GenericResponse) -> GenericResponse:
    if response.rand_lower_bound == UNKNOWN:
        response.rand_lower_bound = CONST
    if response.det_lower_bound == UNKNOWN:
        response.det_lower_bound = CONST
    if response.rand_upper_bound == UNKNOWN:
        response.rand_upper_bound = UNSOLVABLE
    if response.det_upper_bound == UNKNOWN:
        response.det_upper_bound = UNSOLVABLE
    return response


def propagate_bounds(response: GenericResponse) -> GenericResponse:
    # propagate rand upper
    if extended_index(response.det_upper_bound) < extended_index(
        response.rand_upper_bound
    ):
        response.rand_upper_bound = response.det_upper_bound
        response.papers.rand_upper_bound_source = response.papers.det_upper_bound_source

    # propagate det lower
    if extended_index(response.rand_lower_bound) > extended_index(
        response.det_lower_bound
    ):
        response.det_lower_bound = response.rand_lower_bound
        response.papers.det_lower_bound_source = response.papers.rand_lower_bound_source

    # propagate det upper
    if response.rand_upper_bound != LOGLOG:
        response.det_upper_bound = response.rand_upper_bound
        response.papers.det_upper_bound_source = response.papers.rand_upper_bound_source
    elif extended_index(LOG) < extended_index(response.det_upper_bound):
        response.det_upper_bound = LOG
        # source of det_upper_bound is still in this case
        # dictated by rand_upper_bound
        response.papers.det_upper_bound_source = response.papers.rand_upper_bound_source

    # propagate rand lower
    if response.det_lower_bound != LOG:
        response.rand_lower_bound = response.det_lower_bound
        response.papers.rand_lower_bound_source = response.papers.det_lower_bound_source
    elif extended_index(LOGLOG) > extended_index(response.rand_lower_bound):
        response.rand_lower_bound = LOGLOG
        # source of rand_lower_bound_source is still in this case
        # dictated by det_lower_bound_source
        response.papers.rand_lower_bound_source = response.papers.det_lower_bound_source

    return response


def postprocess(response: GenericResponse) -> GenericResponse:
    response = remove_unknowns(response)
    response = propagate_bounds(response)
    return response


def check_for_contradictions(responses: Dict[Classifier, GenericResponse]) -> None:
    _, rand_upper_bound = get_upper_bound(responses, "rand_upper_bound")
    _, det_upper_bound = get_upper_bound(responses, "det_upper_bound")
    return
    _, rand_lower_bound = get_lower_bound(responses, "rand_lower_bound")
    _, det_lower_bound = get_lower_bound(responses, "det_lower_bound")
    for r in responses.values():
        if extended_index(r.rand_lower_bound) > extended_index(rand_upper_bound):
            raise Exception(
                "classification-contradiction",
                "rand_lower_bound in one of the respones is > rand_upper_bound in another response",
                responses,
                r.problem,
            )
        if extended_index(r.det_lower_bound) > extended_index(det_upper_bound):
            raise Exception(
                "classification-contradiction"
                "det_lower_bound in one of the respones is > det_upper_bound in another response",
                responses,
                r.problem,
            )
        if extended_index(r.rand_upper_bound) < extended_index(rand_lower_bound):
            raise Exception(
                "classification-contradiction"
                "rand_upper_bound in one of the respones is < rand_lower_bound in another response",
                responses,
                r.problem,
            )
        if extended_index(r.det_upper_bound) < extended_index(det_lower_bound):
            raise Exception(
                "classification-contradiction"
                "rand_upper_bound in one of the respones is < rand_lower_bound in another response",
                responses,
                r.problem,
            )


def classify(
    problem: GenericProblem,
    existing_classifications: Dict[Classifier, GenericResponse] = {},
    context: ClassifyContext = ClassifyContext(),
) -> GenericResponse:
    try:
        cp_result = cp_classify(problem, context)
    except Exception:
        cp_result = GenericResponse(problem)

    try:
        rt_result = rt_classify(problem, context)
    except Exception:
        rt_result = GenericResponse(problem)

    try:
        tlp_result = tlp_classify(problem, context)
    except Exception:
        tlp_result = GenericResponse(problem)

    try:
        brt_result = brt_classify(problem, context)
    except Exception:
        brt_result = GenericResponse(problem)

    try:
        re_result = re_classify(problem, context)
    except Exception:
        re_result = GenericResponse(problem)

    try:
        poly_result = poly_classify(problem, context)
    except Exception:
        poly_result = GenericResponse(problem)

    responses = {
        Classifier.CP: cp_result,
        Classifier.RT: rt_result,
        Classifier.TLP: tlp_result,
        Classifier.BRT: brt_result,
        Classifier.RE: re_result,
        Classifier.POLY: poly_result,
        **existing_classifications,
    }

    check_for_contradictions(responses)

    rub_source, rub = get_upper_bound(responses, "rand_upper_bound")
    rlb_source, rlb = get_lower_bound(responses, "rand_lower_bound")
    dub_source, dub = get_upper_bound(responses, "det_upper_bound")
    dlb_source, dlb = get_lower_bound(responses, "det_lower_bound")

    response = GenericResponse(
        problem,
        rub,
        rlb,
        dub,
        dlb,
        cp_result.solvable_count,
        cp_result.unsolvable_count,
        papers=Sources(
            context.sources[rub_source],
            context.sources[rlb_source],
            context.sources[dub_source],
            context.sources[dlb_source],
        ),
    )

    return postprocess(response)

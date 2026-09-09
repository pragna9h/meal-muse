from enum import Enum


class ResultState(str, Enum):
    SUCCESS = "success"
    CLARIFICATION_REQUIRED = "clarification_required"
    NO_RESULTS = "no_results"
    FAILURE = "failure"
"""SDK-visible native bootstrap; core validation also covers CLI callers."""
from typing import Annotated, Literal

from pydantic import Field
from typing_extensions import Required, TypedDict

from .advisors.native import _BASIS_ID


class AdvisorSelectionBasis(TypedDict, total=False):
    __pydantic_config__ = {"extra": "forbid"}
    source: Required[Literal["caller", "client_role", "evidence"]]
    reason_code: Required[Literal["bounded_ranking"]]
    evidence_refs: Annotated[list[Annotated[str, Field(pattern=_BASIS_ID.pattern)]], Field(max_length=16)]


class AdvisorRoute(TypedDict):
    __pydantic_config__ = {"extra": "forbid"}
    model: Annotated[str, Field(min_length=1)]
    effort: Annotated[str, Field(min_length=1)]
    selection_basis: AdvisorSelectionBasis

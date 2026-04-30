from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class EvidenceKind(str, Enum):
    source = "source"
    config = "config"
    infrastructure = "infrastructure"
    policy = "policy"
    runbook = "runbook"
    log = "log"
    data = "data"
    unknown = "unknown"


class ControlStatus(str, Enum):
    supported = "supported"
    partial = "partial"
    gap = "gap"
    unknown = "unknown"


class Confidence(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"


class Control(BaseModel):
    id: str
    title: str
    objective: str
    evidence_hints: list[str] = Field(default_factory=list)
    expected_evidence: list[str] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        value = value.strip().upper()
        if not value or " " in value:
            raise ValueError("control id must be non-empty and contain no spaces")
        return value


class Profile(BaseModel):
    id: str
    name: str
    description: str = ""
    controls: list[Control]

    @model_validator(mode="after")
    def unique_controls(self) -> "Profile":
        ids = [control.id for control in self.controls]
        if len(ids) != len(set(ids)):
            raise ValueError("profile contains duplicate control ids")
        return self


class EvidenceSource(BaseModel):
    id: str
    path: str
    kind: EvidenceKind = EvidenceKind.unknown
    sha256: str
    size_bytes: int


class EvidenceChunk(BaseModel):
    id: str
    source_id: str
    path: str
    line_start: int
    line_end: int
    sha256: str
    text: str
    kind: EvidenceKind = EvidenceKind.unknown

    @model_validator(mode="after")
    def valid_lines(self) -> "EvidenceChunk":
        if self.line_start < 1 or self.line_end < self.line_start:
            raise ValueError("invalid line range")
        return self


class AgentClaim(BaseModel):
    statement: str
    evidence_refs: list[str]
    confidence: Confidence = Confidence.medium


class AgentGap(BaseModel):
    statement: str
    reason: str = ""
    recommended_action: str = "Human input required."


class AgentControlResult(BaseModel):
    control_id: str
    status: ControlStatus
    claims: list[AgentClaim] = Field(default_factory=list)
    gaps: list[AgentGap] = Field(default_factory=list)
    reviewer_questions: list[str] = Field(default_factory=list)

    @field_validator("control_id")
    @classmethod
    def normalize_control_id(cls, value: str) -> str:
        return value.strip().upper()


class Claim(BaseModel):
    id: str
    control_id: str
    statement: str
    confidence: Confidence
    evidence_refs: list[str]


class Gap(BaseModel):
    id: str
    control_id: str
    statement: str
    reason: str = ""
    recommended_action: str = "Human input required."


class ReviewerQuestion(BaseModel):
    id: str
    control_id: str
    question: str


class GraphEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    type: Literal["supports", "partially_supports", "missing_for", "raises_question"]

    model_config = {"populate_by_name": True}


class GraphSummary(BaseModel):
    control_count: int = 0
    supported_controls: int = 0
    partial_controls: int = 0
    gap_controls: int = 0
    unknown_controls: int = 0
    claim_count: int = 0
    gap_count: int = 0
    evidence_count: int = 0


class ControlEvidenceGraph(BaseModel):
    schema_version: str = "0.1"
    profile_id: str
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    controls: list[Control]
    sources: list[EvidenceSource] = Field(default_factory=list)
    chunks: list[EvidenceChunk] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    gaps: list[Gap] = Field(default_factory=list)
    reviewer_questions: list[ReviewerQuestion] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    control_status: dict[str, ControlStatus] = Field(default_factory=dict)
    summary: GraphSummary = Field(default_factory=GraphSummary)

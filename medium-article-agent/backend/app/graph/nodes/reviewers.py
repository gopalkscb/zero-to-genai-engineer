"""Parallel reviewer nodes — write only to new_findings."""

from __future__ import annotations

import re
import uuid

from pydantic import BaseModel, Field, field_validator

from app.graph.nodes.supervisor import finding_fingerprint, sort_findings_by_severity
from app.graph.prompt_context import GROUNDING_SOURCE_BUDGET, REVIEW_SOURCE_BUDGET, skills_block, source_block
from app.graph.state import (
    AgentState,
    Finding,
    LogEntry,
    LogLevel,
    ReviewerRole,
    Severity,
)
from app.llm.client import LLMClient

MAX_NEW_FINDINGS_PER_REVIEWER = 2

# Discovery closes after the first review of the original draft. Iteration 0 may add
# issues; later passes only verify those IDs, otherwise the board grows forever.
LAST_DISCOVERY_ITERATION = 0

# The prompt has to stay readable for the model, so only the worst offenders are re-listed.
MAX_PREVIOUS_IN_PROMPT = 12

# A finding with no pass/fail condition can never be closed. "The intro could be more
# engaging" is true of every possible draft, so the reviewer re-reports it every pass and
# the loop burns its whole iteration budget without progress. Hedged phrasing is the tell.
# Only the problem statement is tested; a hedge inside suggested_fix is normal English.
_HEDGE_PATTERNS = (
    r"\b(could|would|might|may)\s+(be|benefit|use|help|need)\b",
    r"\bconsider\s+(adding|using|including|revising|rephrasing|expanding|breaking)\b",
    r"\bmore\s+(engaging|impactful|compelling|interesting|readable|approachable|polished|dynamic)\b",
    r"\b(somewhat|a bit|slightly|rather)\s+\w+",
)

# A hedge is only fatal when it is the whole complaint. Findings that quote the draft,
# name something absent, or cite a number are checkable even when the wording is soft,
# and those are the ones worth keeping.
_ANCHOR_PATTERNS = (
    r"['\"\u201c\u2018].{4,}['\"\u201d\u2019]",
    r"\b(no|not|never|missing|absent|omits?|lacks?|fails? to)\b",
    r"\b(incorrect|wrong|false|inaccurate|unsupported|unsourced|contradicts?|misstates?|mislabels?|undefined|unexplained)\b",
    r"\d",
)

_HEDGE_RE = tuple(re.compile(pattern, re.I) for pattern in _HEDGE_PATTERNS)
_ANCHOR_RE = tuple(re.compile(pattern, re.I) for pattern in _ANCHOR_PATTERNS)


def is_unfalsifiable(problem: str) -> bool:
    """True when a problem statement is pure taste with nothing checkable to point at."""
    text = (problem or "").strip()
    if not text:
        return True
    if not any(rx.search(text) for rx in _HEDGE_RE):
        return False
    return not any(rx.search(text) for rx in _ANCHOR_RE)


class ReviewerFinding(BaseModel):
    finding_id: str = ""
    severity: str = "minor"
    problem: str = ""
    suggested_fix: str = ""
    resolved: bool = False
    block_refs: list[str] = Field(default_factory=list)

    @field_validator("block_refs", mode="before")
    @classmethod
    def coerce_block_refs(cls, value):
        if value is None:
            return []
        if not isinstance(value, list):
            value = [value]
        return [str(item) for item in value if item is not None and str(item).strip() != ""]


class ReviewerOutput(BaseModel):
    findings: list[ReviewerFinding] = Field(default_factory=list)


def _run_reviewer(
    state: AgentState,
    role: ReviewerRole,
    stage: str,
    focus: str,
) -> dict:
    llm = LLMClient()
    draft = state.get("draft_markdown", "")
    research = state.get("web_research")
    web_text = research.as_text(1500) if research else ""
    extra = ""
    if role.value == "grounding" and web_text:
        extra = f"\n\nOptional web research (secondary; uploads are primary):\n{web_text}"
    skills = skills_block(state)
    src_budget = GROUNDING_SOURCE_BUDGET if role.value == "grounding" else REVIEW_SOURCE_BUDGET
    source = source_block(state, src_budget)
    iteration = state.get("iteration", 0)
    previous = [
        item
        for item in state.get("open_findings", []) or []
        if getattr(item, "reviewer", None) == role and not getattr(item, "resolved", False)
    ]
    previous = sort_findings_by_severity(previous)
    shown = previous[:MAX_PREVIOUS_IN_PROMPT]
    allow_new = MAX_NEW_FINDINGS_PER_REVIEWER if iteration <= LAST_DISCOVERY_ITERATION else 0

    previous_block = "None."
    if shown:
        previous_block = "\n".join(
            f"- ID {item.finding_id} [{item.severity.value}] {item.problem}"
            for item in shown
        )
        if len(previous) > len(shown):
            previous_block += f"\n(plus {len(previous) - len(shown)} lower-severity items, ignore for now)"

    new_rule = (
        f"Add at most {allow_new} genuinely NEW issues."
        if allow_new
        else "Do NOT raise any new issues. This pass verifies fixes only."
    )
    prompt = f"""Review this Medium article draft for {focus}.

House skill (backend/skills/medium.md) — treat as a gate, not flavor:
{skills}

You MUST re-check every previously open finding listed below.
If a previous finding is fixed, return it with the SAME finding_id and resolved=true.
If it is still present, return it with the SAME finding_id and resolved=false.
Do not invent a new ID for an old issue.
Be decisive: if the draft now satisfies the required fix, mark it resolved. Leaving a
finding open because it could still be better is not a valid verdict.

Every finding must be falsifiable. State a concrete defect that a reader can check as
fixed or not fixed, and name the exact claim, sentence, heading, or code line at fault.
Do not raise taste or polish opinions. Phrasing like "could be more engaging",
"could benefit from", or "would be smoother" is rejected automatically, because no
version of the draft ever makes it provably fixed.

Severity:
- critical: a wrong fact, a contradiction with the source, or a missing definition of the
  article's core term
- major: unexplained acronym on first use, no worked example, no citations for a factual
  claim, missing section the outline promised, or a figure that does not match the text
- minor: wording, heading polish, alt text. Still must be checkable.

Previously open findings for your role:
{previous_block}

Draft:
{draft[:14000]}

Primary source (coverage pack, not a first-N slice):
{source}
{extra}

Return JSON with a findings array. Each item:
{{"finding_id": "same id if this is a previous finding, else empty", "severity": "critical|major|minor", "problem": "...", "suggested_fix": "...", "resolved": false, "block_refs": []}}
{new_rule} Empty array if clean and all previous items are resolved."""

    messages = [
        {"role": "system", "content": f"You are a {role.value} reviewer."},
        {"role": "user", "content": prompt},
    ]
    try:
        result = llm.complete(stage, messages, structured_schema=ReviewerOutput, temperature=0.3)
        assert isinstance(result, ReviewerOutput)
        raw_findings = result.findings
    except Exception as exc:
        return {
            "new_findings": [],
            "logs": [
                LogEntry(
                    node=f"reviewer_{role.value}",
                    level=LogLevel.WARNING,
                    message=f"Reviewer failed: {exc}",
                    iteration=state.get("iteration", 0),
                )
            ],
        }

    findings, skip_logs = normalize_reviewer_findings(
        role=role,
        raw_findings=raw_findings,
        previous=previous,
        iteration=iteration,
        max_new=allow_new,
    )

    resolved_count = sum(1 for item in findings if item.resolved)
    new_count = sum(
        1
        for item in findings
        if not item.resolved and item.finding_id not in {p.finding_id for p in previous}
    )
    return {
        "new_findings": findings,
        "logs": skip_logs
        + [
            LogEntry(
                node=f"reviewer_{role.value}",
                level=LogLevel.INFO,
                message=(
                    f"{len(findings)} finding(s): {resolved_count} resolved, "
                    f"{len(findings) - resolved_count - new_count} still open, {new_count} new"
                ),
                iteration=state.get("iteration", 0),
            )
        ],
    }


def normalize_reviewer_findings(
    role: ReviewerRole,
    raw_findings: list,
    previous: list[Finding],
    iteration: int,
    max_new: int = MAX_NEW_FINDINGS_PER_REVIEWER,
) -> tuple[list[Finding], list[LogEntry]]:
    """Reuse previous IDs when a reviewer is re-checking an old issue."""
    previous_by_id = {item.finding_id: item for item in previous}
    previous_by_fp = {finding_fingerprint(item): item for item in previous}
    findings: list[Finding] = []
    skip_logs: list[LogEntry] = []
    new_count = 0

    for item in raw_findings:
        if isinstance(item, ReviewerFinding):
            incoming_id = (item.finding_id or "").strip()
            sev = item.severity
            problem = item.problem
            suggested_fix = item.suggested_fix
            block_refs = item.block_refs
            resolved = bool(item.resolved)
        elif isinstance(item, dict):
            incoming_id = str(item.get("finding_id") or "").strip()
            sev = item.get("severity", "minor")
            problem = str(item.get("problem", ""))
            suggested_fix = str(item.get("suggested_fix", ""))
            block_refs = item.get("block_refs") or []
            resolved = bool(item.get("resolved", False))
        else:
            continue
        if sev not in ("critical", "major", "minor"):
            sev = "minor"

        candidate = Finding(
            finding_id=incoming_id or "pending",
            reviewer=role,
            severity=Severity(sev),
            problem=problem,
            suggested_fix=suggested_fix,
            block_refs=block_refs,
            resolved=resolved,
            review_iteration=iteration,
        )
        matched = previous_by_id.get(incoming_id) or previous_by_fp.get(finding_fingerprint(candidate))
        if matched:
            candidate.finding_id = matched.finding_id
        elif is_unfalsifiable(problem):
            skip_logs.append(
                LogEntry(
                    node=f"reviewer_{role.value}",
                    level=LogLevel.INFO,
                    message=f"Dropped unfalsifiable finding (no pass/fail condition): {problem[:80]}",
                    iteration=iteration,
                )
            )
            continue
        elif new_count >= max_new:
            skip_logs.append(
                LogEntry(
                    node=f"reviewer_{role.value}",
                    level=LogLevel.INFO,
                    message=(
                        f"Dropped new finding (discovery closed after iteration "
                        f"{LAST_DISCOVERY_ITERATION}): {problem[:80]}"
                        if max_new == 0
                        else f"Dropped extra new finding (cap {max_new}): {problem[:80]}"
                    ),
                    iteration=iteration,
                )
            )
            continue
        else:
            candidate.finding_id = incoming_id if incoming_id and incoming_id not in previous_by_id else str(uuid.uuid4())[:8]
            candidate.resolved = False
            new_count += 1

        try:
            findings.append(candidate)
        except Exception as exc:
            skip_logs.append(
                LogEntry(
                    node=f"reviewer_{role.value}",
                    level=LogLevel.WARNING,
                    message=f"Skipped malformed finding: {exc}",
                    iteration=iteration,
                )
            )

    return findings, skip_logs


def reviewer_technical_node(state: AgentState) -> dict:
    return _run_reviewer(state, ReviewerRole.TECHNICAL, "reviewer_technical", "technical accuracy")


def reviewer_style_node(state: AgentState) -> dict:
    return _run_reviewer(
        state,
        ReviewerRole.STYLE,
        "reviewer_style",
        (
            "writing style and Medium house skill: banned AI-isms, max 3-sentence "
            "paragraphs, golden sentences, no 'Thanks for reading', conversational voice"
        ),
    )


def reviewer_structure_node(state: AgentState) -> dict:
    return _run_reviewer(state, ReviewerRole.STRUCTURE, "reviewer_structure", "structure and flow")


def reviewer_grounding_node(state: AgentState) -> dict:
    return _run_reviewer(state, ReviewerRole.GROUNDING, "reviewer_grounding", "factual grounding vs source material")


def reviewer_reader_node(state: AgentState) -> dict:
    return _run_reviewer(
        state,
        ReviewerRole.READER,
        "reviewer_reader",
        (
            "reader experience for a Medium subscriber: the hook in the first three "
            "sentences, whether a skimmer can follow the H2s, whether the core term "
            "is defined before jargon, and whether the ending gives a usable takeaway. "
            "Findings must still be falsifiable (name the missing sentence, heading, "
            "or example). Do not write 'could be more engaging'"
        ),
    )

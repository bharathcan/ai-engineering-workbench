from app.ai.base import AIProvider
from app.ai.prompts import TASK_DECOMPOSITION_SYSTEM_PROMPT, build_task_decomposition_user_prompt
from app.core.exceptions import InvalidAIResponseError
from app.schemas.requirement_analysis import RequirementAnalysisResult
from app.schemas.task_decomposition import TaskDecompositionResult


class TaskDecomposer:
    """Converts an already-analyzed requirement into a structured, reviewable
    engineering plan. Does not generate implementation code and does not
    execute tasks — see docs/ENGINEERING_WORKFLOW.md for where those
    responsibilities live instead.

    Schema validation (field types, patterns) happens inside AIProvider.
    Referential integrity — duplicate/self/missing/circular dependencies,
    unknown requirement references, sequence-vs-dependency ordering — is
    this codebase's own responsibility, since a Pydantic field schema alone
    cannot express "this id must point to another item in this same list."
    """

    def __init__(self, ai_provider: AIProvider):
        self._ai_provider = ai_provider

    def decompose(
        self, requirement_text: str, analysis: RequirementAnalysisResult
    ) -> TaskDecompositionResult:
        result = self._ai_provider.complete_structured(
            system_prompt=TASK_DECOMPOSITION_SYSTEM_PROMPT,
            user_prompt=build_task_decomposition_user_prompt(
                requirement_text, _format_analysis_context(analysis)
            ),
            response_model=TaskDecompositionResult,
        )
        _validate_task_plan(result, valid_requirement_ref_ids=_analysis_ref_ids(analysis))
        return result


def _format_analysis_context(analysis: RequirementAnalysisResult) -> str:
    lines = [f"Summary: {analysis.summary}", ""]

    lines.append("Functional requirements:")
    lines += [f"- {i.id}: {i.description}" for i in analysis.functional_requirements]

    lines.append("Non-functional requirements:")
    lines += [f"- {i.id}: {i.description}" for i in analysis.non_functional_requirements]

    lines.append("Constraints:")
    lines += [f"- {i.id}: {i.description}" for i in analysis.constraints]

    lines.append("Success criteria:")
    lines += [f"- {i.id}: {i.description}" for i in analysis.success_criteria]

    lines.append("Engineering concerns:")
    lines += [f"- {i.id}: {i.description}" for i in analysis.engineering_concerns]

    if analysis.ambiguities:
        lines.append(
            "Unresolved ambiguities (non-blocking — do not resolve these; "
            "note them as task risks where relevant):"
        )
        lines += [f"- {i.id} ({i.impact}): {i.description}" for i in analysis.ambiguities]

    if analysis.assumptions:
        lines.append("Assumptions already made during analysis (treat as given):")
        lines += [f"- {i.id}: {i.description}" for i in analysis.assumptions]

    return "\n".join(lines)


def _analysis_ref_ids(analysis: RequirementAnalysisResult) -> set[str]:
    return {
        item.id
        for group in (
            analysis.functional_requirements,
            analysis.non_functional_requirements,
            analysis.constraints,
            analysis.success_criteria,
            analysis.engineering_concerns,
        )
        for item in group
    }


def _validate_task_plan(
    result: TaskDecompositionResult, *, valid_requirement_ref_ids: set[str]
) -> None:
    if not result.tasks:
        raise InvalidAIResponseError("The AI returned an empty task list.")

    seen_ids: set[str] = set()
    for task in result.tasks:
        if task.id in seen_ids:
            raise InvalidAIResponseError(f"Duplicate task id in AI output: {task.id}.")
        seen_ids.add(task.id)

    task_ids = seen_ids

    for task in result.tasks:
        if task.id in task.dependencies:
            raise InvalidAIResponseError(f"Task {task.id} depends on itself.")

        for dep_id in task.dependencies:
            if dep_id not in task_ids:
                raise InvalidAIResponseError(
                    f"Task {task.id} depends on unknown task id: {dep_id}."
                )

        unknown_refs = [
            ref for ref in task.requirement_refs if ref not in valid_requirement_ref_ids
        ]
        if unknown_refs:
            raise InvalidAIResponseError(
                f"Task {task.id} references requirement id(s) not present in the "
                f"requirement analysis: {unknown_refs}."
            )

    _check_no_circular_dependencies(result.tasks)
    _check_sequence_consistent_with_dependencies(result.tasks)


def _check_no_circular_dependencies(tasks: list) -> None:
    """DFS cycle detection over the task dependency graph."""
    dependencies_by_id = {task.id: task.dependencies for task in tasks}
    WHITE, GRAY, BLACK = 0, 1, 2
    color = dict.fromkeys(dependencies_by_id, WHITE)

    def visit(task_id: str, path: list[str]) -> None:
        color[task_id] = GRAY
        for dep_id in dependencies_by_id[task_id]:
            if color[dep_id] == GRAY:
                cycle = " -> ".join([*path, dep_id])
                raise InvalidAIResponseError(f"Circular dependency detected: {cycle}.")
            if color[dep_id] == WHITE:
                visit(dep_id, [*path, dep_id])
        color[task_id] = BLACK

    for task_id in dependencies_by_id:
        if color[task_id] == WHITE:
            visit(task_id, [task_id])


def _check_sequence_consistent_with_dependencies(tasks: list) -> None:
    sequence_by_id = {task.id: task.sequence for task in tasks}
    for task in tasks:
        for dep_id in task.dependencies:
            if sequence_by_id[task.id] <= sequence_by_id[dep_id]:
                raise InvalidAIResponseError(
                    f"Task {task.id} (sequence {sequence_by_id[task.id]}) does not come "
                    f"after its dependency {dep_id} (sequence {sequence_by_id[dep_id]})."
                )

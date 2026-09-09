"""Read-only summaries of existing observations, not a timing or telemetry collector."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from .kernel import Kernel, STAGES, TransitionError
from .ledger import AtomicLedger, LedgerError

DURATION_SOURCE = 'history.leaf-result-recorded.details.wall_time'
RETRY_SOURCE = 'history quality-failed/final-tree-quality-stage-failed; failures < configured maximum'
FAILURE_EVENTS = {'quality-failed', 'final-tree-quality-stage-failed'}
CHECK_STATUSES = ('succeeded', 'failed', 'errored', 'skipped', 'not-run', 'unavailable')


def _number(value: object) -> bool:
    return (type(value) is int and value >= 0) or (
        type(value) is float and math.isfinite(value) and value >= 0
    )


def _measurement(value: int | float | None, unit: str, source: str) -> dict[str, Any]:
    return {'value': value, 'unit': unit, 'source': source,
            'availability': 'unavailable' if value is None else 'recorded'}


def _duration(values: list[object], unit: str) -> dict[str, Any]:
    observed = [value for value in values if _number(value)]
    missing = len(values) - len(observed)
    result = _measurement(sum(observed) if observed else None, unit, DURATION_SOURCE)
    result.update(observations=len(observed), missing=missing)
    if observed and missing:
        result['availability'] = 'partial'
    return result


def _context(value: dict[str, str] | None) -> dict[str, str] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {'workload', 'environment', 'protocol', 'wall_time_unit'}:
        raise ValueError('invalid comparison context')
    if not all(isinstance(item, str) and item.strip() and len(item) <= 1000 for item in value.values()):
        raise ValueError('invalid comparison context')
    if value['wall_time_unit'] not in {'seconds', 'milliseconds', 'unspecified'}:
        raise ValueError('invalid wall-time unit')
    return dict(value)


def _checks(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, dict) or value.get('schema') != 1 or not isinstance(value.get('records'), list):
        raise ValueError('expected existing test-local schema-1 report')
    counts = dict.fromkeys(CHECK_STATUSES, 0)
    for row in value['records']:
        state = row.get('status') if isinstance(row, dict) else None
        counts[state if isinstance(state, str) and state in counts else 'unavailable'] += 1
    # Never read or export argv, diagnostics, prompts, stdout/stderr or log paths.
    return {'source': 'test-local schema-1 records', 'count_unit': 'check invocations',
            'counts': counts, 'duration': _measurement(None, 'seconds', 'test-local schema 1 records no duration'),
            'environment': {key: value.get(key) if isinstance(value.get(key), str) else None
                            for key in ('mode', 'platform', 'node_version', 'python_version', 'git_version')}}


def build_report(status: dict[str, Any], history: list[dict[str, Any]] | None, *,
                 context: dict[str, str] | None = None,
                 checks: dict[str, Any] | None = None) -> dict[str, Any]:
    """Project normalized Kernel.report/history inputs without changing either input.

    A duration belongs to a reported leaf invocation at its stage, not to individual
    leaf progress milestones. Partial sums are explicitly not complete stage totals.
    """
    context = _context(context)
    unit = context['wall_time_unit'] if context else 'unspecified'
    tickets = {}
    slowest = []
    maximum = status.get('budget_config', {}).get('max_quality_failures')
    for ticket_id, ticket in sorted(status['tickets'].items()):
        events = [event for event in (history or []) if event.get('ticket_id') == ticket_id]
        phases = []
        for stage in STAGES:
            leaf = [event['details'] for event in events
                    if event.get('event') == 'leaf-result-recorded' and event.get('details', {}).get('stage') == stage]
            failures = [event['details'].get('failures') for event in events
                        if event.get('event') in FAILURE_EVENTS and event.get('details', {}).get('stage') == stage]
            retry_count = None
            if history is not None and (not failures or (
                type(maximum) is int and maximum > 0 and all(type(n) is int and n > 0 for n in failures)
            )):
                retry_count = sum(count < maximum for count in failures)
            duration = _duration([event.get('wall_time') for event in leaf], unit)
            phases.append({'stage': stage, 'duration': duration, 'leaf_observations': len(leaf),
                           'retry_requests': _measurement(retry_count, 'requests', RETRY_SOURCE)})
            if duration['value'] is not None and unit != 'unspecified':
                slowest.append({'ticket_id': ticket_id, 'stage': stage, 'unit': unit,
                                'recorded_wall_time': duration['value'], 'availability': duration['availability']})
        count = ticket.get('quality_failures')
        tickets[ticket_id] = {'phases': phases, 'quality_failures': _measurement(
            count if type(count) is int and count >= 0 else None, 'failures', 'Kernel.report tickets.quality_failures (current counter)')}
    return {'schema': 1, 'run_id': status['run_id'], 'tickets': tickets,
            'slowest_observed': sorted(slowest, key=lambda row: (-row['recorded_wall_time'], row['ticket_id'], row['stage'])),
            'comparison_context': context, 'checks': _checks(checks),
            'session_time': _measurement(None, 'seconds', 'not recorded by leaf resource accounting'),
            'model_tokens': _measurement(None, 'tokens', 'owned by autopilot-token-economics-wayfinder live-token investigation'),
            'limitations': [
                'The ledger does not persist wall-time units; a context declaration is not historical unit evidence.',
                'Leaf-reported time is not session time; recorded zero may be the caller default.',
                'Absent leaf observations remain unavailable rather than zero; partial sums are not complete durations.',
                'History sums include all candidate generations; current quality_failures may have been reset.',
                'Retry requests count nonterminal quality failures, not confirmed reruns or leaf continuations.',
                'Comparison context is operator-declared, not discovered historical environment evidence.',
                'No command timing is inferred from timeouts/logs; static bytes are not model tokens.',
            ]}


def compare_reports(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Compare declared-equivalent samples; never infer a general speedup."""
    if any(report['comparison_context'] is None or report['comparison_context']['wall_time_unit'] == 'unspecified'
           for report in (left, right)):
        return {'status': 'unavailable', 'reason': 'Both samples require explicit context and known time units', 'phase_deltas': []}
    left_environment = left['checks']['environment'] if left['checks'] else None
    right_environment = right['checks']['environment'] if right['checks'] else None
    if (left['comparison_context'] != right['comparison_context'] or left_environment != right_environment
            or set(left['tickets']) != set(right['tickets'])):
        return {'status': 'incomparable', 'reason': 'Declared context, observed check environment or ticket set differs', 'phase_deltas': []}
    deltas = []
    for ticket_id in sorted(left['tickets']):
        other = {row['stage']: row for row in right['tickets'][ticket_id]['phases']}
        for row in left['tickets'][ticket_id]['phases']:
            target = other[row['stage']]
            complete = all(item['duration']['availability'] == 'recorded' for item in (row, target))
            retries = [item['retry_requests']['value'] for item in (row, target)]
            deltas.append({'ticket_id': ticket_id, 'stage': row['stage'], 'unit': row['duration']['unit'],
                           'recorded_wall_time_delta': target['duration']['value'] - row['duration']['value'] if complete else None,
                           'retry_requests_delta': retries[1] - retries[0] if None not in retries else None})
    return {'status': 'declared-comparable', 'direction': 'right minus left',
            'limitation': 'Declared-equivalent observations only; no general performance conclusion.', 'phase_deltas': deltas}


def _read_optional(path: Path | None) -> Any:
    return json.loads(path.read_text(encoding='utf-8')) if path else None


def _load(path: Path, context: Path | None, checks: Path | None) -> dict[str, Any]:
    ledger = AtomicLedger(path).load()
    report = build_report(Kernel(ledger).report(), ledger['history'],
                          context=_read_optional(context), checks=_read_optional(checks))
    report['source'] = {'ledger': str(path.resolve()), 'context': str(context.resolve()) if context else None,
                        'checks': str(checks.resolve()) if checks else None}
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ledger', type=Path)
    parser.add_argument('--context', type=Path)
    parser.add_argument('--checks', type=Path)
    parser.add_argument('--compare-ledger', type=Path)
    parser.add_argument('--compare-context', type=Path)
    parser.add_argument('--compare-checks', type=Path)
    args = parser.parse_args(argv)
    if not args.compare_ledger and (args.compare_context or args.compare_checks):
        parser.error('comparison inputs require --compare-ledger')
    try:
        report = _load(args.ledger, args.context, args.checks)
        comparison = None
        if args.compare_ledger:
            other = _load(args.compare_ledger, args.compare_context, args.compare_checks)
            comparison = compare_reports(report, other)
            comparison['sources'] = [report['source'], other['source']]
        print(json.dumps({'report': report, 'comparison': comparison}, sort_keys=True, allow_nan=False))
        return 0
    except (OSError, ValueError, LedgerError, TransitionError):
        # Do not echo input contents, exception messages or paths containing secrets.
        print(json.dumps({'error': 'input-unavailable-or-invalid'}))
        return 2

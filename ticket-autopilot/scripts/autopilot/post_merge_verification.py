"""Read-only merged-source quality, owned by a technical gate rather than delivery.

Git observation is confined to binding/reentry. Session replay is deterministic and uses
existing ticket, leaf-budget and verification contracts; it never drives a provider.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .candidate_contract import semantic_candidate
from .leaf_protocol import (
    new_leaf_budget, normalize_resource_usage, record_leaf_result,
    validate_handoff_progression, validate_leaf_result,
)
from .ticket_contract import acceptance_criteria
from .verification_checkpoint import load_verification_adapters

CATEGORY = 'post-merge-verification'
SESSION_KEY = 'verification_session'
# The first two are read-only source assessments, not ticket implementation actions.
STAGES = ('implement', 'simplify', 'review', 'qa-plan', 'qa-execute', 'verify')
REQUIRED_STAGES = ['candidate-invalidation-or-rebind', 'review', 'qa-plan', 'qa-execute', 'verify']
BINDING_FIELDS = {
    'schema', 'gate_id', 'ticket_id', 'source_worktree', 'source_head', 'source_tree',
    'candidate_ref', 'ticket_envelope_ref', 'normalized_ticket', 'criteria', 'files_expected',
}
SESSION_FIELDS = BINDING_FIELDS | {'entries', 'audit'}


class PostMergeVerificationError(ValueError):
    pass


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
        ensure_ascii=False, allow_nan=False).encode('utf-8')).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise PostMergeVerificationError(message)


def gate_scope(ledger: Mapping[str, Any], gate_id: str, *, active: bool = True):
    gate = ledger['gates'].get(gate_id)
    _require(isinstance(gate, dict) and gate.get('category') == CATEGORY
        and gate.get('scope') == 'ticket' and gate.get('kind') == 'dynamic',
        'post-merge verification requires its exact technical gate')
    details = gate.get('details')
    _require(isinstance(details, dict) and type(details.get('schema')) is int
        and details['schema'] == 1 and details.get('required_stages') == REQUIRED_STAGES
        and details.get('human_canary_approval') is False,
        'post-merge gate has unsupported source/quality requirements')
    historical = semantic_candidate(details.get('historical_candidate_ref')).as_dict()
    _require(all(isinstance(value, str) and re.fullmatch(r'(?:[0-9a-f]{40}|[0-9a-f]{64})', value)
        for value in (historical['base_tree_oid'], historical['candidate_tree_oid'],
                      details.get('source_head'), details.get('source_tree'))),
        'post-merge source identities must be full Git object IDs')
    _require(details['source_tree'] != historical['candidate_tree_oid'],
        'post-merge source verification requires a changed semantic tree')
    owner = ledger['tickets'][gate['ticket_id']]
    parents = [ident for ident in owner['blocked_by']
        if ledger['tickets'][ident].get('candidate_ref') == historical]
    _require(len(parents) == 1, 'post-merge predecessor is missing or ambiguous')
    parent_id = parents[0]
    if active:
        _require(gate['state'] == 'open', 'post-merge gate is not open')
        _require(ledger.get('pause') is None and ledger.get('run_state') not in {'aborted', 'failed'},
            'post-merge verification cannot run in a paused or stopped run')
        _require(owner.get('disposition') == 'open' and owner.get('status_barrier') is None
            and owner['state'] == 'gated' and owner.get('stage') is None
            and owner.get('candidate_ref') is None and gate.get('resume_state') == 'pending'
            and gate.get('resume_stage') is None,
            'post-merge verification requires an open, unstarted gated successor')
        _require(ledger['tickets'][parent_id]['state'] == 'integrated',
            'post-merge predecessor must remain integrated')
        _require(not any(g['state'] == 'open' and
            (g.get('scope') == 'run' or (g.get('ticket_id') == gate['ticket_id'] and g.get('kind') == 'start'))
            for g in ledger['gates'].values()), 'post-merge verification has another prerequisite gate')
    return gate, parent_id, historical


def _git(root: Path, *args: str) -> str:
    env = os.environ.copy()
    for name in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR',
                 'GIT_OBJECT_DIRECTORY', 'GIT_ALTERNATE_OBJECT_DIRECTORIES'):
        env.pop(name, None)
    env['GIT_NO_REPLACE_OBJECTS'] = '1'
    try:
        result = subprocess.run(['git', '--no-optional-locks', '-c', 'core.fsmonitor=false',
            '-C', str(root), *args], env=env, capture_output=True, timeout=60)
        _require(result.returncode == 0, 'post-merge Git source observation failed')
        return result.stdout.decode('utf-8', errors='strict').strip('\r\n')
    except (OSError, subprocess.TimeoutExpired, UnicodeError) as error:
        raise PostMergeVerificationError('post-merge Git source observation is unavailable') from error


def normalized_input(ledger: Mapping[str, Any], parent_id: str):
    # Git's adapter imports Kernel; defer it until the source boundary is invoked.
    from .git_ops import GitError
    from .ticket_source import load_ticket_snapshot

    path = Path(ledger['snapshot_manifest_path'])
    try:
        source = load_ticket_snapshot(path, Path(ledger['repo']))
    except (GitError, OSError) as error:
        raise PostMergeVerificationError('post-merge normalized snapshot is unavailable or invalid') from error
    _require(source.manifest_digest == ledger['snapshot_manifest_digest'],
        'post-merge normalized snapshot differs from the runner')
    items = [item for item in source.manifest['tickets'] if item['envelope']['ticket_id'] == parent_id]
    _require(len(items) == 1, 'post-merge normalized predecessor is missing')
    item = items[0]
    reference = path.as_posix() + '#ticket=' + parent_id + '&sha256=' + item['content_digest']
    return item, reference


def bind_source(ledger: Mapping[str, Any], gate_id: str, source_worktree: Path) -> dict[str, Any]:
    gate, parent_id, historical = gate_scope(ledger, gate_id, active=False)
    if gate['state'] == 'open':
        gate_scope(ledger, gate_id)
    else:
        _require(gate['state'] == 'passed' and gate['details'].get(SESSION_KEY, {}).get('audit') is not None,
            'post-merge binding requires an open gate or exact completed replay')
    details = gate['details']
    root = Path(source_worktree).resolve(strict=True)
    repo = Path(ledger['repo']).resolve(strict=True)
    _require(root.is_dir(), 'post-merge source is not a directory')
    common = Path(_git(repo, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve()
    _require(Path(_git(root, 'rev-parse', '--path-format=absolute', '--git-common-dir')).resolve() == common,
        'post-merge source is from a different repository')
    registered = [Path(row[len('worktree '):]).resolve() for row in
        _git(repo, 'worktree', 'list', '--porcelain', '-z').split('\0') if row.startswith('worktree ')]
    _require(root in registered and Path(_git(root, 'rev-parse', '--show-toplevel')).resolve() == root,
        'post-merge source must be an exact registered worktree root')
    _require(not _git(root, 'for-each-ref', '--format=%(refname)', 'refs/replace/'),
        'post-merge source contains replacement refs')
    _require(not _git(root, 'status', '--porcelain=v1', '--untracked-files=all'),
        'post-merge source worktree must be clean')
    head = _git(root, 'rev-parse', '--verify', 'HEAD^{commit}')
    tree = _git(root, 'rev-parse', '--verify', 'HEAD^{tree}')
    _require(head == details.get('source_head') and tree == details.get('source_tree'),
        'post-merge source head/tree differs from the recorded gate')
    integration = ledger['tickets'][parent_id].get('delivery', {}).get('terminal-integration', {})
    witness = integration.get('reachable_sha')
    _require(isinstance(witness, str) and bool(witness),
        'post-merge predecessor has no terminal integration witness')
    _git(root, 'merge-base', '--is-ancestor', witness, head)
    _require(_git(root, 'cat-file', '-t', historical['base_tree_oid']) == 'tree',
        'post-merge historical base is not a Git tree')
    item, envelope_ref = normalized_input(ledger, parent_id)
    _require(item['content_digest'] == historical['ticket_digest'],
        'post-merge normalized predecessor identity differs')
    candidate = {**historical, 'candidate_tree_oid': tree}
    files = _git(root, 'diff', '--name-only', '--no-renames', '-z', historical['base_tree_oid'], tree).split('\0')
    binding = {
        'schema': 1, 'gate_id': gate_id, 'ticket_id': parent_id, 'source_worktree': str(root),
        'source_head': head, 'source_tree': tree, 'candidate_ref': candidate,
        'ticket_envelope_ref': envelope_ref,
        'normalized_ticket': {'envelope': item['envelope'], 'body': item['body']},
        'criteria': acceptance_criteria(item['body']), 'files_expected': sorted(filter(None, files)),
    }
    existing = details.get(SESSION_KEY)
    if existing is not None:
        _require({key: existing[key] for key in BINDING_FIELDS} == binding,
            'post-merge session cannot be retargeted or reset')
        validate_session(ledger, gate_id, existing)
        return copy.deepcopy(existing)
    return {**binding, 'entries': [], 'audit': None}


def stage_artifact(session: Mapping[str, Any], stage: str) -> str:
    binding = {key: session[key] for key in BINDING_FIELDS}
    prefix = 'post-merge://' + digest(binding) + '/' + stage
    # The verification bundle cannot contain the hash of its own enclosing leaf.
    if stage == 'verify':
        return prefix
    records = [entry['leaf_result'] for entry in session['entries']
        if entry['leaf_result']['stage'] == stage and entry['leaf_result']['complete']]
    _require(len(records) == 1, 'post-merge stage is not complete')
    return prefix + '#sha256=' + digest(records[0])


def replay_entries(ledger: Mapping[str, Any], session: Mapping[str, Any]):
    budget = new_leaf_budget(ledger)
    results: dict[str, Any] = {}
    phase = 0
    prior = None
    for entry in session['entries']:
        _require(isinstance(entry, dict) and set(entry) == {'leaf_result', 'tool_calls', 'wall_time'},
            'post-merge entry shape is invalid')
        _require(phase < len(STAGES), 'post-merge has entries after its final leaf')
        leaf = validate_leaf_result(entry['leaf_result'],
            expected_candidate_ref=session['candidate_ref'], expected_stage=STAGES[phase])
        _require(leaf['scope']['files_expected'] == session['files_expected'],
            'post-merge leaf scope differs from its Git manifest')
        if prior is not None:
            _require(validate_handoff_progression(prior, leaf) != 'duplicate',
                'post-merge history contains a duplicate charged interaction')
        budget, normalized, _ = record_leaf_result(ledger, budget, leaf,
            expected_candidate_ref=session['candidate_ref'], expected_stage=STAGES[phase],
            tool_calls=entry['tool_calls'], wall_time=entry['wall_time'])
        _require(normalized == entry['leaf_result'], 'post-merge leaf is not normalized')
        results[STAGES[phase]] = normalized
        prior = normalized
        if normalized['complete']:
            phase += 1
            prior = None
    return budget, results, STAGES[phase] if phase < len(STAGES) else None


def validate_session(ledger: Mapping[str, Any], gate_id: str, session: Mapping[str, Any]) -> None:
    gate, parent_id, historical = gate_scope(ledger, gate_id, active=False)
    _require(isinstance(session, dict) and set(session) == SESSION_FIELDS
        and type(session.get('schema')) is int and session['schema'] == 1,
        'post-merge session shape is invalid')
    _require(session['gate_id'] == gate_id and session['ticket_id'] == parent_id
        and session['source_head'] == gate['details']['source_head']
        and session['source_tree'] == gate['details']['source_tree']
        and session['candidate_ref'] == {**historical, 'candidate_tree_oid': session['source_tree']},
        'post-merge session identity differs from its gate')
    item, reference = normalized_input(ledger, parent_id)
    _require(item['content_digest'] == historical['ticket_digest']
        and session['ticket_envelope_ref'] == reference
        and session['normalized_ticket'] == {'envelope': item['envelope'], 'body': item['body']}
        and session['criteria'] == acceptance_criteria(item['body']),
        'post-merge normalized input or criteria differ from the runner snapshot')
    _require(isinstance(session['files_expected'], list)
        and all(isinstance(p, str) and p for p in session['files_expected'])
        and session['files_expected'] == sorted(set(session['files_expected'])),
        'post-merge file manifest is invalid')
    _require(isinstance(session['entries'], list), 'post-merge entries must be a list')
    replay_entries(ledger, session)
    if session['audit'] is not None:
        audit = session['audit']
        _require(isinstance(audit, dict) and set(audit) == {'bundle', 'digest', 'reduction'}
            and audit['digest'] == digest(audit['bundle']), 'post-merge audit receipt is invalid')
        _require(validate_audit(ledger, session, audit['bundle']) == audit['reduction'],
            'post-merge audit reduction differs')


def append_leaf(ledger: Mapping[str, Any], session: Mapping[str, Any], result: Mapping[str, Any],
                *, tool_calls: int = 0, wall_time: int = 0) -> dict[str, Any]:
    validate_session(ledger, session['gate_id'], session)
    normalized = validate_leaf_result(result, expected_candidate_ref=session['candidate_ref'])
    tool_calls, wall_time = normalize_resource_usage(tool_calls, wall_time)
    entry = {'leaf_result': normalized, 'tool_calls': tool_calls, 'wall_time': wall_time}
    if entry in session['entries']:
        return copy.deepcopy(session)
    _require(session['audit'] is None, 'post-merge audit is already complete')
    updated = copy.deepcopy(session)
    updated['entries'].append(entry)
    validate_session(ledger, session['gate_id'], updated)
    return updated


def validate_audit(ledger: Mapping[str, Any], session: Mapping[str, Any], bundle: Mapping[str, Any]):
    _, results, stage = replay_entries(ledger, session)
    _require(stage is None, 'post-merge audit requires all fresh source quality leaves')
    validate, reduce_claims = load_verification_adapters(
        Path(__file__).resolve().parents[3] / 'verification-audit', current_candidate=session['candidate_ref'])
    normalized = validate(bundle)
    _require(normalized['ticket_id'] == session['ticket_id']
        and normalized['ticket_envelope_ref'] == session['ticket_envelope_ref'],
        'post-merge audit normalized ticket differs')
    stages = {item['stage']: item for item in normalized['stage_results']}
    _require(set(stages) == set(STAGES) and all(stages[name]['result'] == 'pass'
        and stages[name]['artifact'] == stage_artifact(session, name) for name in STAGES),
        'post-merge audit does not bind every accepted fresh stage')
    _require(all('post-merge isolation: ' + results[name]['execution']['isolation']
        in stages[name]['limitations'] for name in STAGES),
        'post-merge audit omitted accepted leaf isolation limitations')
    claims = {item['id']: item for item in normalized['claims']}
    _require(set(claims) == {item['id'] for item in session['criteria']}
        and all(claims[item['id']]['text'] == item['text'] for item in session['criteria']),
        'post-merge audit does not cover the normalized acceptance criteria')
    _require(all(item['status'] == 'supported' and item['kind'] in {'implementation', 'behavior'}
        and item['environment_scope'] in {'local', 'test'}
        and item['boundary_scope'] in {'internal', 'simulated-external'}
        and item['requested_claim'] != 'production-ready' for item in claims.values()),
        'post-merge audit cannot authorize an unsupported, live or release claim')
    _require('merge_authorization' not in normalized
        and normalized['verification']['requested_operation'] == 'report',
        'post-merge audit is report-only, not delivery authority')
    reduction = reduce_claims(normalized)
    gate_states = {gate['id']: gate['status'] for gate in normalized['gates']}
    _require(reduction['implementation_status'] == 'complete'
        and reduction['max_claim'] in {'deployable-for-test', 'behavior-verified'}
        and all(gate_states[ident] in {'passed', 'waived'}
                for claim in claims.values() for ident in claim['gate_ids']),
        'post-merge audit does not establish offline source readiness')
    bound = [e for e in results['verify']['quality']['evidence'] if e['id'] == 'post-merge:bundle']
    _require(len(bound) == 1 and bound[0]['result'] == 'pass'
        and bound[0]['artifact'] == 'post-merge-bundle://' + digest(normalized)
        and bound[0]['sha256'] == digest(normalized), 'post-merge verify leaf does not bind this audit bundle')
    return reduction


def check_artifacts(ledger: Mapping[str, Any], session: Mapping[str, Any]) -> None:
    """Re-observe local leaf content addresses; never fetch artifact URLs."""
    allowed = [Path(ledger['snapshot_manifest_path']).resolve().parent.parent,
               Path(session['source_worktree']).resolve()]
    for entry in session['entries']:
        leaf = entry['leaf_result']
        for evidence in leaf.get('quality', {}).get('evidence', []):
            if leaf['stage'] == 'verify' and evidence['id'] == 'post-merge:bundle':
                # This semantic address is checked against the canonical bundle at completion.
                continue
            path = Path(evidence['artifact'])
            _require(path.is_absolute() and not path.is_symlink() and path.is_file(),
                'post-merge quality artifact must be an existing absolute regular file')
            actual = path.resolve(strict=True)
            _require(any(actual.is_relative_to(root) for root in allowed),
                'post-merge quality artifact is outside its source/run scope')
            _require(hashlib.sha256(actual.read_bytes()).hexdigest() == evidence['sha256'],
                'post-merge quality artifact content hash differs')


def attach_audit(ledger, session, bundle):
    validate_session(ledger, session['gate_id'], session)
    reduction = validate_audit(ledger, session, bundle)
    updated = copy.deepcopy(session)
    receipt = {'bundle': copy.deepcopy(bundle), 'digest': digest(bundle), 'reduction': reduction}
    _require(session['audit'] in (None, receipt), 'post-merge audit replay is contradictory')
    updated['audit'] = receipt
    return updated


def validate_transition(previous: Mapping[str, Any], gate_id: str, updated: Mapping[str, Any]) -> None:
    gate_scope(previous, gate_id)
    before = previous['gates'][gate_id]['details'].get(SESSION_KEY)
    validate_session(previous, gate_id, updated)
    if before is None:
        _require(not updated['entries'] and updated['audit'] is None,
            'post-merge binding cannot import quality results')
        return
    _require(all(before[key] == updated[key] for key in BINDING_FIELDS),
        'post-merge transition changed its frozen binding')
    if before == updated:
        return
    if updated['entries'] != before['entries']:
        _require(before['audit'] is None and updated['audit'] is None
            and len(updated['entries']) == len(before['entries']) + 1
            and updated['entries'][:-1] == before['entries'],
            'post-merge transition rewrote quality history')
    else:
        _require(before['audit'] is None and updated['audit'] is not None,
            'post-merge transition changed its audit history')


def approval_evidence(ledger: Mapping[str, Any], gate_id: str) -> str:
    gate, _, _ = gate_scope(ledger, gate_id, active=False)
    session = gate['details'].get(SESSION_KEY)
    _require(isinstance(session, dict) and session.get('audit') is not None,
        'post-merge gate requires complete fresh canonical verification')
    validate_session(ledger, gate_id, session)
    return 'post-merge-audit://' + session['audit']['digest']


def session_context(ledger: Mapping[str, Any], gate_id: str) -> dict[str, Any]:
    gate, _, _ = gate_scope(ledger, gate_id, active=False)
    session = gate['details'].get(SESSION_KEY)
    if session is None:
        return {'schema': 1, 'gate_id': gate_id, 'state': 'unbound', 'candidate_ref': None}
    validate_session(ledger, gate_id, session)
    budget, results, stage = replay_entries(ledger, session)
    return {**{key: copy.deepcopy(session[key]) for key in BINDING_FIELDS},
        'stage': stage, 'state': 'verified' if session['audit'] else 'verifying',
        'gate_state': gate['state'], 'budget': budget,
        'stage_artifacts': {name: stage_artifact(session, name) for name, leaf in results.items() if leaf['complete']},
        'verify_artifact': stage_artifact(session, 'verify'),
        'stage_isolation_limitations': {name: 'post-merge isolation: ' + leaf['execution']['isolation']
            for name, leaf in results.items()},
        'scope': 'read-only assessment of merged predecessor; no ticket implementation or live authority'}

"""Bounded native command/receipt port; no model/provider/process selection here."""
from __future__ import annotations

import hashlib
import json

from chain_controller import ChainGate, digest


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


class ChainJudge:
    """Trusted caller grants a separately reserved judge call; DecisionEngine owns parsing."""
    def __init__(self, session, contract, *, model, grant):
        self.session, self.contract, self.model, self.grant = session, dict(contract), dict(model), grant
        if set(self.model) != {'provider', 'id'} or not all(
                isinstance(v, str) and v for v in self.model.values()):
            raise ChainGate('exact configured judge provider/id required')

    def __call__(self, request):
        binding = request['binding']
        if any(binding.get(field + '_digest') != digest(value) for field, value in
               [('question', request['question']), ('state', request['state']), ('contract', self.contract)]):
            raise ChainGate('judge input binding mismatch')
        authority = self.grant(dict(binding))
        if (not isinstance(authority, dict) or authority.get('authorized') is not True
                or type(authority.get('budget_calls')) is not int or authority['budget_calls'] <= 0
                or type(authority.get('max_tokens')) is not int or not 0 < authority['max_tokens'] <= 16384):
            raise ChainGate('judge recipient permission and reserved budget required')
        payload = {**request, 'contract': self.contract, 'model': self.model, **authority,
                   'canonical': {field: canonical(value) for field, value in
                       [('question', request['question']), ('state', request['state']), ('contract', self.contract)]}}
        # Authority fields cannot replace inputs/model/bindings.
        payload.update(binding=binding, question=request['question'], state=request['state'],
                       contract=self.contract, model=self.model)
        raw = canonical(payload)
        if len(raw.encode()) > 65536:
            raise ChainGate('judge command input bound')
        observed = self.session.prompt('/chain-judge ' + raw)
        entries = observed.get('entries', [])
        matches = [e for e in entries if e.get('type') == 'custom'
                   and e.get('customType') == 'chain-judge-result'
                   and e.get('data', {}).get('call_id') == binding['call_id']]
        if observed.get('disposition') != 'handled' or len(matches) != 1:
            raise ChainGate('native handled command with one attributable receipt required')
        data = matches[0]['data']
        expected = {**binding, 'model': self.model,
                    'request_digest': hashlib.sha256(raw.encode()).hexdigest()}
        if payload.get('reasoning') is not None:
            expected['reasoning'] = payload['reasoning']
        if any(data.get(k) != v for k, v in expected.items()):
            raise ChainGate('judge receipt binding mismatch')
        # Preserve returned usage even for invalid/unknown answers. Do not execute a tool
        # or parse a permissive result; the controller's canonical Answer parser decides.
        return {**expected, 'usage': data.get('usage'), 'text': data.get('text'),
                'stopReason': data.get('stopReason') if data.get('valid') is True else 'invalid',
                'error': data.get('error'), 'entry_id': matches[0]['id']}

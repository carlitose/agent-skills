"""Native-shaped RPC fixture. Never imports Pi or contacts a provider."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--mode', required=True)
parser.add_argument('--session-dir', required=True)
parser.add_argument('--session')
args = parser.parse_args()
store = Path(args.session_dir)
store.mkdir(parents=True, exist_ok=True)
path = Path(args.session) if args.session else store / 'fake-main.jsonl'
if not path.exists():
    path.write_bytes(b'{"type":"session","version":3,"id":"fake-main"}\n')
entries = [json.loads(line) for line in path.read_bytes().split(b'\n') if line][1:]


def emit(data):
    sys.stdout.buffer.write((json.dumps(data, ensure_ascii=False) + '\r\n').encode())
    sys.stdout.buffer.flush()


def append(entry_type, **fields):
    entry = {'type': entry_type, 'id': str(len(entries) + 1),
             'parentId': entries[-1]['id'] if entries else None, **fields}
    entries.append(entry)
    with path.open('ab') as stream:
        stream.write((json.dumps(entry, ensure_ascii=False) + '\n').encode())
        stream.flush()
    return entry


usage = {'input': 3, 'output': 2, 'cacheRead': 0, 'cacheWrite': 0,
         'totalTokens': 5, 'cost': {'input': 0, 'output': 0, 'cacheRead': 0, 'cacheWrite': 0, 'total': 0}}
for raw in sys.stdin.buffer:
    command = json.loads(raw)
    kind = command['type']
    data = {}
    if kind == 'get_state':
        changed = bool(entries and entries[-1].get('message', {}).get('content') == [{'type': 'text', 'text': 'replace-session'}])
        data = {'sessionId': 'unexpected' if changed else 'fake-main', 'sessionFile': str(path), 'isStreaming': False,
                'isCompacting': False, 'pendingMessageCount': 0,
                'model': {'provider': 'fake', 'id': 'frontier-fixture'}}
    elif kind == 'get_entries':
        since = command.get('since')
        offset = next((i + 1 for i, e in enumerate(entries) if e['id'] == since), None) if since else 0
        if offset is None:
            emit({'id': command['id'], 'type': 'response', 'command': kind, 'success': False})
            continue
        data = {'entries': entries[offset:], 'leafId': entries[-1]['id'] if entries else None}
        if entries and entries[-1].get('message', {}).get('content') == [{'type': 'text', 'text': 'unterminated'}]:
            sys.stdout.buffer.write(json.dumps({'id': command['id'], 'type': 'response',
                'command': kind, 'success': True, 'data': data}).encode())
            sys.stdout.buffer.flush()
            os._exit(0)
    elif kind == 'prompt':
        message = command['message']
        if message == 'crash':
            os._exit(17)
        if message == 'bad-response':
            emit({'id': command['id'], 'type': 'response', 'command': kind, 'success': True, 'data': []})
            continue
        if message == 'malformed':
            sys.stdout.buffer.write(b'not-json\n')
            sys.stdout.buffer.flush()
            continue
        if message == 'slow':
            time.sleep(4)
        if message == 'queued':
            data = {'disposition': 'queued'}
        elif message in ('handled', 'handled-empty'):
            if message == 'handled':
                append('custom', customType='fixture-receipt', data={'output': 'not agent text'})
            data = {'disposition': 'handled'}
        else:
            text = ('secret=' + str('TYPESAFE_API_KEY' in os.environ)) if message == 'sentinel' else message
            final = {'role': 'assistant', 'content': [{'type': 'text', 'text': text}],
                     'usage': usage, 'stopReason': message if message in ('length', 'error', 'aborted') else 'stop'}
            if message == 'stderr':
                sys.stderr.buffer.write(b'x' * 131072)
                sys.stderr.buffer.flush()
            append('message', message=final)
            if message == 'compaction':
                append('compaction', usage=usage, firstKeptEntryId='1', summary='fixture')
                append('usage', kind='new-unknown-kind', usage=usage)
                append('message', message={'role': 'toolResult', 'usage': usage})
            emit({'type': 'message_end', 'message': final})
            emit({'type': 'agent_end', 'willRetry': False})
            emit({'type': 'agent_settled'})
            data = {'disposition': 'started'}
    else:
        raise ValueError('unknown fixture command')
    emit({'id': command['id'], 'type': 'response', 'command': kind, 'success': True, 'data': data})

import test from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { installJudge, canonicalDigest } from '../extensions/chain-judge-core.ts';

const candidate = { contract_version: 2, base_tree_oid: 'a'.repeat(40), candidate_tree_oid: 'b'.repeat(40), ticket_digest: 'c'.repeat(64) };
function fixture(options = {}) {
  const entries = [];
  let handler, count = 0, observed;
  const api = { registerCommand(name, config) { assert.equal(name, 'chain-judge'); handler = config.handler; },
    appendEntry(customType, data) { entries.push({type:'custom',id:String(entries.length+1),customType,data}); } };
  const model = { provider: 'fixture', id: 'exact', api: 'fake' };
  const backend = { getModel(provider,id) { return provider === 'fixture' && id === 'exact' ? model : undefined; },
    async completeSimple(m, context, config) { count++; observed = {m, context, config};
      if (options.throw) throw Error('PRIVATE CREDENTIAL DO NOT LEAK');
      return {role:'assistant',content:Object.hasOwn(options,'content') ? options.content : [{type:'text',text:'Answer: yes'}],
        stopReason:options.stop ?? 'stop',usage:Object.hasOwn(options,'usage') ? options.usage : {totalTokens:5}}; } };
  installJudge(api, async () => backend);
  const ctx = { isIdle: () => options.idle !== false, hasPendingMessages: () => false,
    sessionManager: {getEntries: () => entries}, signal: undefined };
  const question = {type:'noul',instructions:'Decide only these facts',criteria:{true:'covered',false:'not covered'}};
  const state = {proof:'stub evidence'}, contract = {scope:'fixture'};
  const binding = {call_id:'call-1',candidate_ref:candidate,question_id:'q',question_digest:canonicalDigest(question),
    state_digest:canonicalDigest(state),contract_digest:canonicalDigest(contract)};
  const payload = {binding,question,state,contract,model:{provider:'fixture',id:'exact'},authorized:true,
    budget_calls:1,max_tokens:128};
  return {entries,ctx,payload,invoke: () => handler(JSON.stringify(payload),ctx),
    reload: () => installJudge(api, async () => backend),
    calls: () => count, observed: () => observed};
}

test('only a command; one fresh tool-less completion and custom receipt', async () => {
  const f = fixture(); await f.invoke();
  assert.equal(f.calls(),1);
  const {context,config,m} = f.observed();
  assert.equal(context.messages.length,1);
  assert.equal(context.messages[0].role,'user');
  assert.equal(context.tools,undefined);
  assert.equal(m.id,'exact'); assert.equal(config.maxTokens,128);
  assert(!JSON.stringify(context).includes('builder history'));
  const receipt = f.entries.at(-1);
  assert.equal(receipt.customType,'chain-judge-result');
  assert.equal(receipt.data.call_id,'call-1');
  assert.equal(receipt.data.usage.totalTokens,5);
  assert.equal(receipt.data.text,'Answer: yes');
  await assert.rejects(f.invoke()); assert.equal(f.calls(),1);
});

test('idle, binding, recipient permission and budget fail before completion', async () => {
  for (const [key,value] of [['authorized',false],['budget_calls',0],['max_tokens',0]]) {
    const f=fixture(); f.payload[key]=value; await assert.rejects(f.invoke()); assert.equal(f.calls(),0);
  }
  const busy=fixture({idle:false}); await assert.rejects(busy.invoke()); assert.equal(busy.calls(),0);
  const changed=fixture(); changed.payload.state={proof:'different'}; await assert.rejects(changed.invoke());
  const missing=fixture(); missing.payload.model.id='fuzzy'; await missing.invoke();
  assert.equal(missing.entries.at(-1).data.valid,false); assert.equal(missing.calls(),0);
});

test('failed/aborted/length/tool-call replies preserve usage but cannot decide', async () => {
  for (const stop of ['error','aborted','length']) {
    const f=fixture({stop}); await f.invoke();
    assert.equal(f.entries.at(-1).data.stopReason,stop);
    assert.equal(f.entries.at(-1).data.usage.totalTokens,5);
    assert.equal(f.entries.at(-1).data.valid,false);
  }
  const tools=fixture({content:[{type:'toolCall',name:'not-allowed',arguments:{}}]});
  await tools.invoke(); assert.equal(tools.entries.at(-1).data.valid,false);
});

test('durable reservation blocks overlapping calls and altered replay ids', async () => {
  const f=fixture();
  const results=await Promise.allSettled([f.invoke(),f.invoke()]);
  assert.equal(results.filter(r=>r.status==='fulfilled').length,1);
  assert.equal(f.calls(),1);
  f.payload.binding.call_id='altered-id';
  await assert.rejects(f.invoke()); assert.equal(f.calls(),1);
});

test('malformed content and missing usage are unknown, never invented zero', async () => {
  for (const content of [null,{bad:true},[]]) {
    const malformed=fixture({content}); await malformed.invoke();
    assert.equal(malformed.entries.at(-1).data.valid,false);
  }
  const unknown=fixture({usage:null}); await unknown.invoke();
  assert.equal(unknown.entries.at(-1).data.usage,null);
});

test('explicit reasoning is used and retained, never silently downgraded', async () => {
  const f=fixture(); f.payload.reasoning='medium'; await f.invoke();
  assert.equal(f.observed().config.reasoning,'medium');
  assert.equal(f.entries.at(-1).data.reasoning,'medium');
  const bad=fixture(); bad.payload.reasoning='invented';
  await assert.rejects(bad.invoke()); assert.equal(bad.calls(),0);
});

test('canonical Python evidence beyond JS integer precision reaches the model unchanged', async () => {
  const f=fixture();
  const raw='{"integer":9007199254740993,"decimal":1.0}';
  f.payload.state=JSON.parse(raw);
  f.payload.canonical={state:raw};
  f.payload.binding.state_digest=createHash('sha256').update(raw).digest('hex');
  await f.invoke();
  assert(f.observed().context.messages[0].content.includes('9007199254740993'));
  assert(f.observed().context.messages[0].content.includes('1.0'));
});

test('exception is sanitized, reservation remains durable across handler reconstruction', async () => {
  const f=fixture({throw:true}); await f.invoke();
  assert.equal(f.entries.at(-1).data.valid,false);
  assert(!JSON.stringify(f.entries).includes('PRIVATE'));
  assert.equal(f.entries.at(-1).data.usage,null);
  f.reload();
  await assert.rejects(f.invoke()); assert.equal(f.calls(),1);
});

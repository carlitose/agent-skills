// Controlled Node RPC peer exercises the real bridge with a completion stub. Never Pi/auth.
import { appendFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { installJudge } from '../extensions/chain-judge-core.ts';

const store = process.argv[process.argv.indexOf('--session-dir') + 1];
mkdirSync(store, {recursive:true});
const path = join(store, 'fake-judge.jsonl');
if (!existsSync(path)) appendFileSync(path, JSON.stringify({type:'session',id:'fake-judge'}) + '\n');
const entries = readFileSync(path,'utf8').trim().split('\n').slice(1).map(JSON.parse);
const emit = value => process.stdout.write(JSON.stringify(value) + '\n');
let handler;
installJudge({
  registerCommand(name, config) { handler = config.handler; },
  appendEntry(customType, data) {
    const entry = {type:'custom',id:String(entries.length+1),customType,data,
      parentId:entries.at(-1)?.id ?? null};
    entries.push(entry); appendFileSync(path,JSON.stringify(entry)+'\n');
    emit({type:'entry_appended',entry});
  },
}, async () => ({
  getModel(provider,id) { return provider === 'fixture' && id === 'exact' ? {provider,id} : undefined; },
  async completeSimple(model, context) {
    const state=JSON.parse(context.messages[0].content).state;
    if (state.exception) throw Error('FIXTURE SECRET');
    return {role:'assistant',content:state.tool ? [{type:'toolCall',name:'bad'}]
      : [{type:'text',text:state.answer ?? 'Answer: yes'}], stopReason:state.stop ?? 'stop',
      usage:state.no_usage ? undefined : {totalTokens:5}};
  },
}));
const ctx = {isIdle:()=>true, hasPendingMessages:()=>false, signal:undefined,
  sessionManager:{getEntries:()=>entries}};
async function* records() {
  let buffer = Buffer.alloc(0);
  for await (const chunk of process.stdin) {
    buffer = Buffer.concat([buffer, chunk]);
    let end;
    while ((end = buffer.indexOf(10)) >= 0) {
      yield buffer.subarray(0, end).toString('utf8');
      buffer = buffer.subarray(end + 1);
    }
  }
}
for await (const line of records()) {
  const command=JSON.parse(line);
  let data={};
  try {
    if (command.type === 'get_state') data={sessionId:'fake-judge',sessionFile:path,
      isStreaming:false,isCompacting:false,pendingMessageCount:0};
    else if (command.type === 'get_entries') {
      const start=command.since ? entries.findIndex(e=>e.id===command.since)+1 : 0;
      if (command.since && !start) throw Error('unknown cursor');
      data={entries:entries.slice(start),leafId:entries.at(-1)?.id ?? null};
    } else if (command.type === 'prompt') {
      if (!command.message.startsWith('/chain-judge ')) throw Error('only judge fixture');
      await handler(command.message.slice('/chain-judge '.length),ctx);
      data={disposition:'handled'};
    } else throw Error('unknown command');
    emit({type:'response',id:command.id,command:command.type,success:true,data});
  } catch {
    emit({type:'response',id:command.id,command:command.type,success:false,error:'fixture-command-rejected'});
  }
}

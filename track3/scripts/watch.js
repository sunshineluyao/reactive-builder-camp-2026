// SPDX-License-Identifier: MIT
// Read-only worker for one submitted quote. Accepts the six signed transaction hashes from the console.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const {parseArgs} = require('node:util');
const proof = require('../review/receipts.js');
const {planStep, confirmTransaction, steps} = require('../site/console.js');
const contracts = require('../site/contracts.json').contracts;
const model = require('../model/runtime.js');
const hex = n => '0x' + BigInt(n).toString(16);
const pause = ms => new Promise(resolve => setTimeout(resolve, ms));

async function rpc(role, method, params) {
  const id = 1, network = proof.networks[role];
  const url = process.env[role.toUpperCase() + '_RPC'] || network.rpc;
  const reply = await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({jsonrpc:'2.0',id,method,params}),signal:AbortSignal.timeout(20000)});
  if (!reply.ok) throw Error(network.name+' HTTP '+reply.status);
  const body = await reply.json();
  if (body.id !== id || body.error || !Object.hasOwn(body,'result')) throw Error(network.name+' '+method+' '+(body.error?.message || 'invalid reply'));
  return body.result;
}

async function deployments(backup, read) {
  if (backup.version !== 1 || !/^0x[0-9a-f]{40}$/i.test(backup.account) || backup.hashes?.length !== steps.length)
    throw Error('Export the deployment record after all six signed steps.');
  const records = [];
  for (const [i,[role]] of steps.entries()) {
    const h = backup.hashes[i];
    if (!/^0x[0-9a-f]{64}$/i.test(h)) throw Error('Missing transaction hash at step '+(i+1));
    const [id,tx,receipt] = await Promise.all([read(role,'eth_chainId',[]),read(role,'eth_getTransactionByHash',[h]),read(role,'eth_getTransactionReceipt',[h])]);
    if (Number(BigInt(id)) !== proof.networks[role].id) throw Error('RPC chain ID mismatch for '+role);
    const result = confirmTransaction(planStep(i,contracts,records),receipt,tx,backup.account,h);
    if (result.state !== 'confirmed') throw Error('Step '+(i+1)+' was not successful.');
    proof.verifyBlock(receipt,await read(role,'eth_getBlockByNumber',[receipt.blockNumber,false]),role);
    records.push(result);
  }
  return records;
}

async function findLeg(role, deployed, sourceHash, cursor, read) {
  const tip = Number(BigInt(await read(role,'eth_blockNumber',[])));
  for (let start=cursor[role]; start<=tip; start+=750) {
    const end=Math.min(start+749,tip);
    const logs=await read(role,'eth_getLogs',[{address:deployed.address,fromBlock:hex(start),toBlock:hex(end),
      topics:[proof.topics[role],null,sourceHash]}]);
    const event=logs.find(l => !l.removed && String(l.address).toLowerCase()===deployed.address.toLowerCase() &&
      String(l.topics?.[2]).toLowerCase()===sourceHash.toLowerCase());
    if (event) return event.transactionHash;
    cursor[role]=Math.max(deployed.block,end-10);
  }
  return '';
}
async function collect(records, read, {timeout=900, interval=8000, onWaiting=()=>{}}={}) {
  const deadline=Date.now()+timeout*1000, [a,b,c]=records, originHash=records[5].hash;
  const cursor={reactive:b.block,destination:c.block};
  const hashes={origin:originHash};
  for (;;) {
    let lastError;
    try {
      for (const [role,deploy] of [['reactive',b],['destination',c]]) {
        if (!hashes[role]) hashes[role]=await findLeg(role,deploy,originHash,cursor,read);
      }
      if (hashes.reactive && hashes.destination) {
        const run={version:1,mode:'public-testnet'};
        for (const [i,role] of proof.roles.entries()) run[role]={chainId:proof.networks[role].id,address:[a,b,c][i].address,txHash:hashes[role]};
        const {result,receipts}=await proof.fetchPublic(run,read);
        return {run:{...run,receipts},result};
      }
    } catch(error) {
      lastError=error;
      if (hashes.reactive && hashes.destination) {
        // A mined replacement may have a different hash if a block was reorganized.
        delete hashes.reactive; delete hashes.destination;
        cursor.reactive=b.block; cursor.destination=c.block;
      }
    }
    if (Date.now()>=deadline) throw Error('No three-leg canonical proof yet. Resume with the same progress file. '+(lastError?.message || ''));
    onWaiting(lastError?.message || 'Awaiting correlated Lasna and Base receipts.'); await pause(interval);
  }
}
function evaluate(alert, context) {return model.assess(alert,context || null);}
async function main() {
  const {values,positionals}=parseArgs({allowPositionals:true,options:{
    out:{type:'string'},context:{type:'string'},timeout:{type:'string',default:'900'},help:{type:'boolean'}}});
  if (values.help || positionals.length!==1 || !values.out) {
    console.log('node scripts/watch.js deployment-progress.json --out public-run.json [--context evidence.json] [--timeout 900]');
    return values.help ? 0 : 2;
  }
  const timeout=Number(values.timeout);
  if (!Number.isFinite(timeout)||timeout<0) throw Error('The timeout must be a nonnegative number of seconds.');
  const readJSON=p=>JSON.parse(fs.readFileSync(p,'utf8'));
  const records=await deployments(readJSON(positionals[0]),rpc);
  const {run,result}=await collect(records,rpc,{timeout,onWaiting:msg=>console.error(msg)});
  const decision=evaluate(result.alert,values.context ? readJSON(values.context) : null);
  const artifact={...run,alert:result.alert,triage:decision};
  const target=path.resolve(values.out),tmp=target+'.'+crypto.randomUUID()+'.tmp';
  try {fs.writeFileSync(tmp,JSON.stringify(artifact,null,2)+'\n',{flag:'wx'});fs.renameSync(tmp,target);}
  finally {if (fs.existsSync(tmp)) fs.unlinkSync(tmp);}
  console.log(decision.label+' · '+result.alert.evidenceId);
  for (const role of proof.roles) console.log(proof.networks[role].name+'  '+proof.networks[role].explorer+'/tx/'+run[role].txHash);
  return 0;
}
module.exports={deployments,collect,evaluate};
if (require.main===module) main().then(code=>{process.exitCode=code;}).catch(e=>{console.error(e.message);process.exitCode=1;});

// SPDX-License-Identifier: MIT
const test = require('node:test');
const assert = require('node:assert/strict');
const {planStep,confirmTransaction,parseHash} = require('../site/console');
const {collect,evaluate} = require('../scripts/watch');
const contracts = require('../site/contracts.json').contracts;
const run = require('../evidence/local-run.json');
const proof = require('../review/receipts');
const records = Object.values({a:run.origin,b:run.reactive,c:run.destination}).map(v=>({address:v.address,block:0}));
const h=run.origin.txHash;
test('six transaction plans encode source, proxy and both prices',()=>{
  const plans=Array.from({length:6},(_,i)=>planStep(i,contracts,records));
  assert.equal(plans[0].data,contracts.QuoteSource.bytecode);
  assert.ok(plans[1].data.endsWith(run.origin.address.slice(2).toLowerCase())); assert.equal(BigInt(plans[1].value),150000000000000000n);
  assert.equal(BigInt(plans[2].value),1000000000000000n); assert.ok(plans[2].data.includes('476f44b11f5c942c58f4c8e3d0300e5710743585'));
  assert.equal(plans[3].to,run.reactive.address); assert.ok(plans[3].data.endsWith(run.destination.address.slice(2).toLowerCase()));
  assert.equal(BigInt('0x'+plans[4].data.slice(10)),9990n); assert.equal(BigInt('0x'+plans[5].data.slice(10)),9930n);
  assert.throws(()=>planStep(2,contracts,[]));
});
test('import rechecks signer, bytecode, amount, target and successful deployment',()=>{
  const plan=planStep(0,contracts,[]), from=run.origin.address;
  const tx={from,to:null,input:plan.data,value:'0x0',hash:h};
  const receipt={contractAddress:run.destination.address,transactionHash:h,blockNumber:'0x2',status:'0x1'};
  assert.equal(confirmTransaction(plan,receipt,tx,from,h).address,run.destination.address);
  for(const changed of [{hash:run.reactive.txHash},{input:'0x'},{from:run.reactive.address},{value:'0x01'},{to:run.origin.address}])
    assert.throws(()=>confirmTransaction(plan,receipt,{...tx,...changed},from,h));
  assert.equal(confirmTransaction(plan,{...receipt,status:'0x0'},tx,from,h).state,'failed');
  assert.throws(()=>confirmTransaction(plan,{...receipt,contractAddress:null},tx,from,h));
});
test('receipt links accept the expected explorers and reject unrelated URLs',()=>{
  assert.equal(parseHash(h),h);assert.equal(parseHash('https://sepolia.etherscan.io/tx/'+h),h);
  assert.equal(parseHash('https://example.org/tx/'+h),'');assert.equal(parseHash('0x123'),'');
});
test('an arriving callback is verified against all three canonical receipts then automatically triaged', async()=>{
  const rec=[...records,null,null,{hash:h}];
  const calls=[];
  const read=async(role,m,params)=>{
    calls.push([role,m]);
    const receipt=run.receipts[role];
    switch(m){
      case 'eth_blockNumber':return receipt.blockNumber;
      case 'eth_getLogs':return receipt.logs.filter(l=>l.topics[0]===params[0].topics[0]);
      case 'eth_getTransactionReceipt':return receipt;
      case 'eth_chainId':return '0x'+run[role].chainId.toString(16);
      case 'eth_getBlockByNumber':return {hash:receipt.blockHash,number:receipt.blockNumber,timestamp:'0x'+run.alert.observedAt.toString(16),transactions:[receipt.transactionHash]};
      default:throw Error(m);
    }
  };
  const got=await collect(rec,read,{timeout:0});
  assert.equal(got.result.alert.evidenceId,run.alert.evidenceId);
  assert.equal(evaluate(got.result.alert,null).decision,'insufficient');
  assert.equal(evaluate(got.result.alert,require('../model/context-example.json')).decision,'escalate');
  assert.equal(calls.filter(v=>v[1]==='eth_getBlockByNumber').length,3);
  assert.equal(proof.verify(run,run.receipts).alert.priceBps,9930);
});

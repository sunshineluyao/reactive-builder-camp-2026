// SPDX-License-Identifier: MIT
const test = require('node:test');
const assert = require('node:assert/strict');
const {planStep,confirmTransaction,confirmStepTransaction,readQuoteReceipt,parseHash,steps} = require('../site/console');
const {deployments,collect,evaluate} = require('../scripts/watch');
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

function delegatedQuote(step, sponsored = false) {
  const plan = planStep(step, contracts, records);
  const account = run.receipts.origin.from;
  const manager = '0xdb9b1e94b5b69df7e401ddbede43491141047db3';
  const from = sponsored ? run.destination.address : account;
  const uint = n => BigInt(n).toString(16).padStart(64,'0');
  // ABI fixture with one byte of permission data and an 88-byte target/value/publish call.
  const input = '0xcef6d209' + [96,224,288,1,32,1].map(uint).join('') + 'ab'.padEnd(64,'0') +
    [1,0,1,32,88].map(uint).join('') + plan.to.slice(2) + uint(0) + plan.data.slice(2) + '0'.repeat(16);
  const tx = {hash:h, from, to:manager, value:'0x0', input, chainId:'0xaa36a7'};
  const receipt = structuredClone(run.receipts.origin);
  Object.assign(receipt,{from, to:manager});
  receipt.logs[0].data = '0x' + plan.data.slice(10) + uint(run.alert.observedAt);
  const block = {hash:receipt.blockHash, number:receipt.blockNumber, timestamp:run.alert.observedAt, transactions:[h]};
  const request = async (method, params) => {
    if (method === 'eth_getBlockByNumber') {
      assert.deepEqual(params,[receipt.blockNumber,false]);
      return block;
    }
    assert.equal(method,'eth_call');
    assert.deepEqual(params,[{to:plan.to,data:'0x8c72c54e'},receipt.blockNumber]);
    return '0x' + uint(account);
  };
  const verify = (changes = {}) => confirmStepTransaction(step, contracts, changes.plan ?? plan, receipt,
    changes.tx ?? tx, changes.account ?? account, changes.hash ?? h, request);
  return {verify, receipt, tx, block, request, account, plan};
}

test('both delegated quotes confirm using their original hash and the effective publisher', async () => {
  for (const [step,sponsored] of [[4,false],[5,true]]) {
    const {verify} = delegatedQuote(step,sponsored);
    assert.deepEqual(await verify(),{hash:h, state:'confirmed', block:Number(BigInt(run.receipts.origin.blockNumber))});
  }
});

test('delegated quote verification rejects mismatched calls, publishers and chain evidence', async () => {
  const {verify, tx, receipt, block} = delegatedQuote(4);
  await assert.rejects(verify({plan:planStep(5,contracts,records)}));
  await assert.rejects(verify({account:run.destination.address}));
  await assert.rejects(verify({hash:run.reactive.txHash}));
  for (const change of [{value:'0x1'},{to:run.destination.address},{chainId:'0x1'},
    {input:tx.input+'00'.repeat(32)}, {input:tx.input.replace(run.origin.address.slice(2),run.destination.address.slice(2))}]) {
    await assert.rejects(verify({tx:{...tx,...change}}));
  }
  block.transactions[0] = run.reactive.txHash;
  await assert.rejects(verify());
  block.transactions[0] = h;
  receipt.logs[0].data = run.receipts.origin.logs[0].data; // 0.9930 instead of the requested 0.9990
  await assert.rejects(verify());
  receipt.logs.length = 0;
  await assert.rejects(verify());
  receipt.status = '0x0';
  assert.deepEqual(await verify(),{hash:h,state:'failed'});
});

test('a saved quote uses public chain data and falls back only after an RPC read fails', async () => {
  const {receipt, tx, block, request, account, plan} = delegatedQuote(4);
  const read = async (method, params) => {
    if (method === 'eth_chainId') return '0xaa36a7';
    if (method === 'eth_getTransactionReceipt') return receipt;
    if (method === 'eth_getTransactionByHash') return tx;
    return request(method, params);
  };
  const walletReads = [];
  const wallet = (method, params) => { walletReads.push(method); return read(method, params); };
  const check = primary => readQuoteReceipt(4, contracts, plan, account, h, primary, wallet);
  assert.equal((await check(read)).state, 'confirmed');
  assert.equal(await check((m,p) => m === 'eth_getTransactionReceipt' ? null : read(m,p)), null);
  await assert.rejects(check((m,p) => m === 'eth_chainId' ? '0x1' : read(m,p)), /Sepolia/);
  block.transactions[0] = run.reactive.txHash;
  await assert.rejects(check(read), /canonical block/);
  assert.deepEqual(walletReads, []);
  block.transactions[0] = h;
  assert.equal((await check((m,p) => {
    if (m === 'eth_getBlockByNumber') throw Error('RPC unavailable');
    return read(m,p);
  })).state, 'confirmed');
  assert.ok(walletReads.includes('eth_getTransactionReceipt'));
  assert.ok(walletReads.includes('eth_call'));
});

test('a direct quote still requires a matching canonical event and publisher', async () => {
  const {verify, receipt, tx, plan, account} = delegatedQuote(5);
  const direct = {...tx, from:account, to:plan.to, input:plan.data};
  Object.assign(receipt, {from:account, to:plan.to});
  assert.equal((await verify({tx:direct})).state, 'confirmed');
  receipt.logs.length = 0;
  await assert.rejects(verify({tx:direct}), /matching event/);
});
test('the watcher resumes all six signatures with a delegated control quote and a direct trigger', async () => {
  const delegated = delegatedQuote(4);
  const account = delegated.account;
  const byHash = new Map(), byBlock = new Map();
  const hashes = steps.map(([role], i) => {
    const plan = planStep(i,contracts,records);
    const hash = '0x' + (i+1).toString(16).padStart(64,'0');
    const blockNumber = '0x' + (i+1).toString(16);
    const tx = i === 4 ? {...delegated.tx,hash} : {hash,from:account,to:plan.to ?? null,input:plan.data,value:plan.value};
    const receipt = {...run.receipts.origin,transactionHash:hash,blockNumber,from:tx.from,to:tx.to,
      contractAddress:records[i]?.address ?? null,logs:[]};
    if (i >= 4) {
      const log = (i === 4 ? delegated.receipt : run.receipts.origin).logs[0];
      receipt.logs.push({...log,transactionHash:hash,blockNumber});
    }
    byHash.set(hash,{role,tx,receipt});
    byBlock.set(blockNumber,{number:blockNumber,hash:receipt.blockHash,transactions:[hash],timestamp:run.alert.observedAt});
    return hash;
  });
  let publisher = account;
  const read = async (role, method, [key, atBlock]) => {
    if (method === 'eth_chainId') return '0x' + proof.networks[role].id.toString(16);
    if (method === 'eth_getBlockByNumber') return byBlock.get(key);
    if (method === 'eth_call') {
      assert.equal(role,'origin');
      assert.deepEqual(key,{to:run.origin.address,data:'0x8c72c54e'});
      assert.ok(byBlock.has(atBlock));
      return '0x' + publisher.slice(2).padStart(64,'0');
    }
    const entry = byHash.get(key);
    assert.equal(entry.role,role);
    if (method === 'eth_getTransactionByHash') return entry.tx;
    assert.equal(method,'eth_getTransactionReceipt');
    return entry.receipt;
  };
  const backup = {version:1,account,hashes};
  assert.deepEqual((await deployments(backup,read)).map(record=>record.hash),hashes);
  publisher = run.destination.address;
  await assert.rejects(deployments(backup,read),/发布账户/);
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

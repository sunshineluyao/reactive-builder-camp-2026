// SPDX-License-Identifier: MIT
// Shared by the read-only browser console and the command-line verifier.
(function (root) {
  'use strict';
  const roles = ['origin', 'reactive', 'destination'];
  const networks = {
    origin: {id:11155111, name:'Ethereum Sepolia', rpc:'https://ethereum-sepolia-rpc.publicnode.com', explorer:'https://sepolia.etherscan.io'},
    reactive: {id:5318007, name:'Reactive Lasna', rpc:'https://lasna-rpc.rnk.dev/', explorer:'https://lasna.reactscan.net'},
    destination: {id:84532, name:'Base Sepolia', rpc:'https://sepolia.base.org', explorer:'https://sepolia.basescan.org'}
  };
  const mask = (1n << 64n) - 1n;
  const rotations = [0,1,62,28,27,36,44,6,55,20,3,10,43,25,39,41,45,15,21,8,18,2,61,56,14];
  const roundConstants = [
    '1','8082','800000000000808a','8000000080008000','808b','80000001','8000000080008081','8000000000008009',
    '8a','88','80008009','8000000a','8000808b','800000000000008b','8000000000008089','8000000000008003',
    '8000000000008002','8000000000000080','800a','800000008000000a','8000000080008081','8000000000008080',
    '80000001','8000000080008008'
  ].map(value => BigInt('0x'+value));
  function rotate(value, shift) {
    const n = BigInt(shift);
    return ((value << n) | (value >> (64n - n))) & mask;
  }
  // Ethereum Keccak-256 (legacy 0x01 padding, not NIST SHA3-256).
  function keccak(bytes) {
    const rate = 136;
    const padded = new Uint8Array((Math.floor(bytes.length / rate) + 1) * rate);
    padded.set(bytes);
    padded[bytes.length] = 1;
    padded[padded.length-1] |= 128;
    const state = Array(25).fill(0n);
    for (let block = 0; block < padded.length; block += rate) {
      for (let j = 0; j < rate; j++) {
        state[j >> 3] ^= BigInt(padded[block+j]) << BigInt(8 * (j % 8));
      }
      for (const rc of roundConstants) {
        const parity = Array(5).fill(0n);
        for (let x=0; x<5; x++) {
          for (let y=0; y<5; y++) parity[x] ^= state[x+5*y];
        }
        const rotated = Array(25);
        for (let x=0; x<5; x++) {
          const delta = parity[(x+4)%5] ^ rotate(parity[(x+1)%5],1);
          for (let y=0; y<5; y++) {
            const i=x+5*y;
            rotated[y+5*((2*x+3*y)%5)] = rotate(state[i]^delta,rotations[i]);
          }
        }
        for (let x=0; x<5; x++) {
          for (let y=0; y<5; y++) {
            const i=x+5*y;
            state[i]=rotated[i] ^ ((~rotated[(x+1)%5+5*y]) & rotated[(x+2)%5+5*y]);
          }
        }
        state[0] ^= rc;
      }
    }
    let result='0x';
    for (let j=0; j<32; j++) {
      result += Number((state[j >> 3] >> BigInt(8*(j%8))) & 255n).toString(16).padStart(2,'0');
    }
    return result;
  }
  function requireThat(condition, message) { if (!condition) throw Error(message); }
  function hash32(value, label) {
    requireThat(typeof value === 'string' && /^0x[0-9a-f]{64}$/i.test(value) && !/^0x0{64}$/i.test(value), label+' must be a nonzero 32-byte hash.');
    return value.toLowerCase();
  }
  function address(value, label) {
    requireThat(typeof value === 'string' && /^0x[0-9a-f]{40}$/i.test(value) && !/^0x0{40}$/i.test(value),label+' must be a nonzero EVM address.');
    return value.toLowerCase();
  }
  function quantity(value, label) {
    const valid = typeof value === 'number' ? Number.isSafeInteger(value) && value>=0 :
      typeof value === 'string' && (/^0x[0-9a-f]+$/i.test(value) || /^(0|[1-9][0-9]*)$/.test(value));
    requireThat(valid,label+' must be a nonnegative quantity.');
    const n=BigInt(value);
    requireThat(n<=BigInt(Number.MAX_SAFE_INTEGER),label+' is too large.');
    return Number(n);
  }
  function uintWord(n) { return BigInt(n).toString(16).padStart(64,'0'); }
  function eventId(chainId,txHash,logIndex) {
    const encoded = uintWord(chainId)+hash32(txHash,'origin tx').slice(2)+uintWord(logIndex);
    return keccak(Uint8Array.from(encoded.match(/../g), pair=>parseInt(pair,16)));
  }
  const signatures = {
    origin:'PriceObserved(uint256,uint256)',
    reactive:'QuoteRouted(bytes32,bytes32,uint256,uint256,uint256)',
    destination:'PriceDeviation(bytes32,bytes32,uint256,uint256,uint256)'
  };
  const topics=Object.fromEntries(roles.map(role=>[role,keccak(new TextEncoder().encode(signatures[role]))]));
  function manifest(input) {
    requireThat(input && input.version===1,'Expected a version 1 evidence manifest.');
    requireThat(input.mode==='local-evm' || input.mode==='public-testnet','Unknown evidence mode.');
    const normalized={version:1,mode:input.mode};
    for (const role of roles) {
      const leg=input[role];
      requireThat(leg && typeof leg==='object','Missing '+role+' coordinates.');
      const chainId=quantity(leg.chainId,role+' chain ID');
      requireThat(chainId===networks[role].id,role+' chain ID does not match the expected network.');
      normalized[role]={chainId,address:address(leg.address,role+' contract'),txHash:hash32(leg.txHash,role+' transaction')};
      if (leg.logIndex!==undefined) normalized[role].logIndex=quantity(leg.logIndex,role+' log index');
    }
    return normalized;
  }
  function words(log,count,role) {
    requireThat(typeof log.data==='string' && new RegExp('^0x[0-9a-f]{'+(64*count)+'}$','i').test(log.data),role+' event payload is malformed.');
    return log.data.slice(2).match(/.{64}/g).map(x=>quantity('0x'+x,role+' event value'));
  }
  function selectLog(role,coordinates,receipt,originHash) {
    requireThat(receipt && typeof receipt==='object',role+' receipt is missing.');
    requireThat(quantity(receipt.status,role+' receipt status')===1,role+' transaction reverted.');
    requireThat(hash32(receipt.transactionHash,role+' receipt hash')===coordinates.txHash,role+' transaction hash mismatch.');
    const blockHash=hash32(receipt.blockHash,role+' block hash');
    const blockNumber=quantity(receipt.blockNumber,role+' block number');
    requireThat(Array.isArray(receipt.logs),role+' receipt has no logs array.');
    const matches=receipt.logs.filter(log=>log && String(log.address).toLowerCase()===coordinates.address &&
      Array.isArray(log.topics) && String(log.topics[0]).toLowerCase()===topics[role] &&
      (role==='origin' || String(log.topics[2]).toLowerCase()===originHash) &&
      (coordinates.logIndex===undefined || quantity(log.logIndex,role+' log index')===coordinates.logIndex));
    requireThat(matches.length===1,role+' must contain exactly one matching event. If needed, supply its logIndex.');
    const log=matches[0];
    requireThat(log.removed===undefined || log.removed===false,role+' log has been removed.');
    requireThat(hash32(log.transactionHash,role+' log transaction hash')===coordinates.txHash,role+' log transaction mismatch.');
    requireThat(hash32(log.blockHash,role+' log block hash')===blockHash && quantity(log.blockNumber,role+' log block number')===blockNumber,role+' log is in a different block.');
    if (log.transactionIndex!==undefined || receipt.transactionIndex!==undefined) {
      requireThat(quantity(log.transactionIndex,role+' log transaction position')===quantity(receipt.transactionIndex,role+' receipt transaction position'),role+' log transaction position mismatch.');
    }
    requireThat(log.topics.length===(role==='origin'?1:3),role+' event has the wrong indexed parameters.');
    return {log,blockHash,blockNumber,logIndex:quantity(log.logIndex,role+' log index')};
  }
  function verify(input,receipts) {
    const run=manifest(input);
    requireThat(receipts && typeof receipts==='object','Receipt bodies are required.');
    const source=selectLog('origin',run.origin,receipts.origin);
    const [priceBps,observedAt]=words(source.log,2,'origin');
    requireThat(priceBps>0 && priceBps<=20000 && Math.abs(priceBps-10000)>50,'Origin quote does not cross the strict 0.5% alert threshold.');
    requireThat(observedAt>0 && observedAt<253402300800,'Invalid observation timestamp.');
    for (const stamp of [source.log.blockTimestamp,receipts.origin.blockTimestamp]) {
      if (stamp!==undefined) requireThat(quantity(stamp,'origin block timestamp')===observedAt,'Origin quote time differs from its block timestamp.');
    }
    const evidenceId=eventId(run.origin.chainId,run.origin.txHash,source.logIndex);
    const legs={};
    for (const role of roles) {
      const leg=role==='origin'?source:selectLog(role,run[role],receipts[role],run.origin.txHash);
      if (role!=='origin') {
        requireThat(hash32(leg.log.topics[1],role+' event ID')===evidenceId,role+' event ID differs from the source event.');
        const [sourceIndex,price,time]=words(leg.log,3,role);
        requireThat(sourceIndex===source.logIndex && price===priceBps && time===observedAt,role+' source index, price, or observation time mismatch.');
      }
      legs[role]={...run[role],logIndex:leg.logIndex,blockNumber:leg.blockNumber,blockHash:leg.blockHash};
    }
    return {version:1,mode:run.mode,alert:{evidenceId,priceBps,observedAt},legs};
  }
  function verifyBlock(receipt,block,role) {
    requireThat(block && hash32(block.hash,role+' canonical block hash')===hash32(receipt.blockHash,role+' receipt block hash') &&
      quantity(block.number,role+' canonical block number')===quantity(receipt.blockNumber,role+' receipt block number'),role+' receipt block is no longer canonical.');
    const transaction=hash32(receipt.transactionHash,role+' receipt hash');
    requireThat(Array.isArray(block.transactions),role+' canonical block omits the transaction list.');
    const position=quantity(receipt.transactionIndex,role+' receipt transaction position');
    requireThat(typeof block.transactions[position]==='string' && block.transactions[position].toLowerCase()===transaction,role+' transaction position does not match the canonical block.');
  }
  async function fetchPublic(input, rpc) {
    const run=manifest(input);
    requireThat(run.mode==='public-testnet','Choose a public-testnet manifest for live verification.');
    const receipts={};
    let sourceBlockTime;
    await Promise.all(roles.map(async role=>{
      const chainId=await rpc(role,'eth_chainId',[]);
      requireThat(quantity(chainId,role+' RPC chain ID')===run[role].chainId,role+' RPC belongs to another network.');
      const receipt=await rpc(role,'eth_getTransactionReceipt',[run[role].txHash]);
      requireThat(receipt,'No confirmed '+role+' receipt yet.');
      const n=quantity(receipt.blockNumber,role+' receipt block number');
      const block=await rpc(role,'eth_getBlockByNumber',['0x'+n.toString(16),false]);
      verifyBlock(receipt,block,role);
      if (role==='origin') sourceBlockTime=quantity(block.timestamp,'canonical origin block timestamp');
      receipts[role]=receipt;
    }));
    const result=verify(run,receipts);
    requireThat(result.alert.observedAt===sourceBlockTime,'Origin quote time differs from its canonical block timestamp.');
    return {result,receipts};
  }
  const api={roles,networks,signatures,topics,keccak,eventId,manifest,verify,verifyBlock,fetchPublic};
  if (typeof module==='object' && module.exports) module.exports=api;
  else root.ReceiptProof=api;
})(globalThis);

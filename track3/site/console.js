'use strict';

const networks = {
  origin: {id: 11155111, name: 'Ethereum Sepolia', symbol: 'ETH', rpc: 'https://ethereum-sepolia-rpc.publicnode.com', explorer: 'https://sepolia.etherscan.io'},
  reactive: {id: 5318007, name: 'Reactive Lasna', symbol: 'lREACT', rpc: 'https://lasna-rpc.rnk.dev', explorer: 'https://lasna.reactscan.net'},
  destination: {id: 84532, name: 'Base Sepolia', symbol: 'ETH', rpc: 'https://sepolia.base.org', explorer: 'https://sepolia.basescan.org'}
};
const proxy = '0x476F44b11F5C942c58f4c8E3d0300E5710743585';
const delegationManager = '0xdb9b1e94b5b69df7e401ddbede43491141047db3';
const receiptProof = typeof module !== 'undefined' && module.exports ? require('../review/receipts') : window.ReceiptProof;
const steps = [
  ['origin', '部署报价合约 QuoteSource', '0 ETH'],
  ['reactive', '部署并订阅 ReactiveAlert', '0.15 lREACT · 合约服务费储备'],
  ['destination', '部署接收合约 AlertSink', '0.001 ETH · 合约回调费储备'],
  ['reactive', '绑定接收合约', '0 lREACT'],
  ['origin', '发布对照报价 0.9990', '0 ETH · 偏离 10 个基点'],
  ['origin', '发布触发报价 0.9930', '0 ETH · 偏离 70 个基点']
];
const eventTopics = {
  reactive: '0x4802f94df321e645ac06b4994188191718fcc0f00c3f7c45ed87a4c9fe62acfa',
  destination: '0x7b4c0f772a3a1cc70aa03b4dd13c6156ef567f06ea5e47e33ba92ef5ce5f9f4c'
};
const validAddress = x => typeof x === 'string' && /^0x[0-9a-f]{40}$/i.test(x);
const validHash = x => typeof x === 'string' && /^0x[0-9a-f]{64}$/i.test(x);
const lower = x => String(x || '').toLowerCase();
const hex = n => '0x' + BigInt(n).toString(16);
const word = v => BigInt(v).toString(16).padStart(64, '0');
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

function planStep(i, contracts, records) {
  const address = j => {
    const addr = records[j]?.address;
    if (!validAddress(addr)) throw new Error('请先核对前面的部署交易。');
    return addr;
  };
  const call = (contract, fn, value) => '0x' + contracts[contract].methodIdentifiers[fn] + word(value);
  switch (i) {
    case 0: return {data: contracts.QuoteSource.bytecode, value: '0x0'};
    case 1: return {data: contracts.ReactiveAlert.bytecode + word(address(0)), value: hex(150000000000000000n)};
    case 2: return {data: contracts.AlertSink.bytecode + word(proxy) + word(address(1)), value: hex(1000000000000000n)};
    case 3: return {to: address(1), data: call('ReactiveAlert', 'bindDestination(address)', address(2)), value: '0x0'};
    case 4: return {to: address(0), data: call('QuoteSource', 'publish(uint256)', 9990), value: '0x0'};
    case 5: return {to: address(0), data: call('QuoteSource', 'publish(uint256)', 9930), value: '0x0'};
    default: throw new Error('未知步骤。');
  }
}

function confirmTransaction(plan, receipt, tx, account, expectedHash) {
  if (!receipt || !tx || !validHash(expectedHash) || lower(receipt.transactionHash) !== lower(expectedHash) ||
      lower(tx.hash) !== lower(expectedHash) || lower(tx.from) !== lower(account) ||
      lower(tx.to) !== lower(plan.to) || lower(tx.input) !== lower(plan.data) ||
      BigInt(tx.value) !== BigInt(plan.value)) throw new Error('交易与当前步骤的签名地址、接收地址、金额或 calldata 不匹配。');
  if (BigInt(receipt.status) === 0n) return {hash: expectedHash, state: 'failed'};
  if (BigInt(receipt.status) !== 1n || !/^0x[0-9a-f]+$/i.test(receipt.blockNumber) ||
      (!plan.to && !validAddress(receipt.contractAddress))) throw new Error('回执缺少成功状态、区块或合约地址。');
  return {hash: expectedHash, state: 'confirmed', block: Number(BigInt(receipt.blockNumber)), ...(plan.to ? {} : {address: receipt.contractAddress})};
}

function matchesSingleRedemption(input, plan) {
  // redeemDelegations(bytes[],bytes32[],bytes[]) with one default-mode ERC-7579 call.
  const data = lower(input);
  const args = data.slice(10);
  if (!data.startsWith('0xcef6d209') || args.length < 6 * 64 ||
      args.length % 64 !== 0 || !/^[0-9a-f]+$/.test(args)) return false;

  // The three offsets, permission count, element offset and byte length occupy six words.
  // The manager validates the permission bytes. Rebuild the canonical ABI envelope so
  // extra executions, different modes, or bytes outside the actual call cannot match.
  const permissionLength = BigInt('0x' + args.slice(5 * 64, 6 * 64));
  if (permissionLength > BigInt(args.length / 2 - 192)) return false;
  const length = Number(permissionLength);
  const permissions = args.slice(6 * 64, 6 * 64 + 2 * length);
  const paddedLength = Math.ceil(length / 32) * 32;
  const modesOffset = 192 + paddedLength;
  const header = [96, modesOffset, modesOffset + 64, 1, 32, length].map(word).join('');
  const call = lower(plan.to).slice(2) + word(plan.value) + lower(plan.data).slice(2);
  const modesAndCallHeader = [1, 0, 1, 32, call.length / 2].map(word).join('');
  return args === header + permissions.padEnd(paddedLength * 2, '0') +
    modesAndCallHeader + call.padEnd(Math.ceil(call.length / 64) * 64, '0');
}

async function confirmStepTransaction(i, contracts, plan, receipt, tx, account, hash, request) {
  if ((i !== 4 && i !== 5) || lower(tx?.to) !== delegationManager) {
    return confirmTransaction(plan, receipt, tx, account, hash);
  }
  if (!validHash(hash) || !validAddress(account) || !validAddress(tx.from) ||
      lower(tx.hash) !== lower(hash) || lower(receipt?.transactionHash) !== lower(hash) ||
      lower(receipt.to) !== delegationManager || lower(receipt.from) !== lower(tx.from) ||
      (tx.chainId != null && BigInt(tx.chainId) !== BigInt(networks.origin.id)) ||
      tx.value == null || BigInt(tx.value) !== 0n || !matchesSingleRedemption(tx.input, plan)) {
    throw new Error('委托交易的哈希、网络、目标合约、金额或报价调用与本步骤不匹配。');
  }

  const [block, publisher] = await Promise.all([
    request('eth_getBlockByNumber', [receipt.blockNumber, false]),
    request('eth_call', [{to:plan.to, data:'0x' + contracts.QuoteSource.methodIdentifiers['publisher()']}, receipt.blockNumber])
  ]);
  receiptProof.verifyBlock(receipt, block, 'origin');
  // QuoteSource only lets its immutable publisher emit PriceObserved, even if a relayer pays gas.
  if (lower(publisher) !== '0x' + word(account)) throw new Error('报价合约的发布账户与当前钱包不匹配。');
  if (BigInt(receipt.status) === 0n) return {hash, state:'failed'};
  const quote = receiptProof.readQuote({address:lower(plan.to), txHash:lower(hash)}, receipt);
  if (BigInt(quote.priceBps) !== BigInt('0x' + plan.data.slice(10)) || BigInt(quote.observedAt) !== BigInt(block.timestamp)) {
    throw new Error('报价合约的链上事件与本步价格或区块时间不匹配。');
  }
  return {hash, state:'confirmed', block:quote.blockNumber};
}

function parseHash(raw) {
  if (validHash(raw.trim())) return raw.trim();
  try {
    const u = new URL(raw.trim());
    const parts = u.pathname.split('/').filter(Boolean);
    const end = parts[parts.length - 1];
    return validHash(end) && Object.values(networks).some(n => u.origin === n.explorer) ? end : '';
  } catch { return ''; }
}

if (typeof module !== 'undefined') module.exports = {planStep, confirmTransaction, confirmStepTransaction, parseHash, networks, steps};
if (typeof window !== 'undefined') window.addEventListener('DOMContentLoaded', startConsole);

async function startConsole() {
  const $ = id => document.getElementById(id);
  let contracts, provider, account = '', records = [], running = false, scanGeneration = 0;
  let found = {reactive: '', destination: ''}, verifiedProof = null;
  const status = (msg, bad = false) => { $('status').textContent = msg; $('status').classList.toggle('bad', bad); };
  const key = () => 'reactive-camp-console-v1/' + lower(account);
  const known = new Map();
  window.addEventListener('eip6963:announceProvider', ev => {
    if (ev.detail?.provider && ev.detail.info) known.set(ev.detail.info.rdns, ev.detail.provider);
  });
  window.dispatchEvent(new Event('eip6963:requestProvider'));

  function save() { if (account) localStorage.setItem(key(), JSON.stringify({records, found})); }
  function showAccount(next, refresh = false) {
    if (lower(account) === lower(next) && account && !refresh) return;
    ++scanGeneration;
    account = validAddress(next) ? next : '';
    records = []; found = {reactive: '', destination: ''}; verifiedProof = null;
    if (account) {
      try { const old = JSON.parse(localStorage.getItem(key()) || '{}'); records = old.records || []; found = {...found, ...old.found}; }
      catch { status('未能读取上次进度。可以从下载的部署记录恢复。', true); }
    }
    $('reactiveHash').value = found.reactive; $('destHash').value = found.destination;
    render();
  }
  function render() {
    $('accountText').textContent = account || '尚未连接';
    $('connect').disabled = running || !contracts;
    $('connect').textContent = account ? '检查钱包连接' : '连接 MetaMask';
    $('steps').replaceChildren();
    steps.forEach(([chain, title, cost], i) => {
      const net = networks[chain], r = records[i];
      const row = document.createElement('li'), info = document.createElement('div'), name = document.createElement('b');
      name.textContent = title; info.append(name);
      const desc = document.createElement('small'); desc.textContent = net.name + ' · ' + cost; info.append(desc);
      if (r?.hash) {
        const link = document.createElement('a'); link.href = net.explorer + '/tx/' + r.hash;
        link.target = '_blank'; link.rel = 'noopener'; link.textContent = '查看交易 ↗'; info.append(link);
      }
      const btn = document.createElement('button');
      const done = r?.state === 'confirmed';
      btn.textContent = done ? '已确认' : r?.state === 'pending' ? '检查回执' : r?.state === 'failed' ? '重新签名' : '签名';
      btn.disabled = !contracts || !account || running || done || (i > 0 && records[i - 1]?.state !== 'confirmed');
      btn.addEventListener('click', () => guardedStep(i)); row.append(info, btn); $('steps').append(row);
    });
    const ready = records[5]?.state === 'confirmed';
    $('sourceHash').value = ready ? records[5].hash : '';
    const complete = ready && validHash(parseHash($('reactiveHash').value)) && validHash(parseHash($('destHash').value));
    $('locate').disabled = running || !ready; $('download').disabled = !complete; $('review').disabled = !complete;
    $('backup').disabled = !account || !records.some(r => r?.hash); $('restore').disabled = !account || running;
  }
  async function rpc(net, method, params) {
    const resp = await fetch(net.rpc, {method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({jsonrpc:'2.0',id:1,method,params}),signal:AbortSignal.timeout(12000)});
    if (!resp.ok) throw new Error(net.name + ' RPC HTTP ' + resp.status);
    const data = await resp.json(); if (data.error) throw new Error(data.error.message); return data.result;
  }
  async function pickNetwork(net) {
    try { await provider.request({method:'wallet_switchEthereumChain',params:[{chainId:hex(net.id)}]}); }
    catch (err) {
      if (Number(err.code) !== 4902 && Number(err.data?.originalError?.code) !== 4902) throw err;
      await provider.request({method:'wallet_addEthereumChain',params:[{
        chainId:hex(net.id),chainName:net.name,nativeCurrency:{name:net.symbol,symbol:net.symbol,decimals:18},
        rpcUrls:[net.rpc],blockExplorerUrls:[net.explorer]}]});
      await provider.request({method:'wallet_switchEthereumChain',params:[{chainId:hex(net.id)}]});
    }
  }
  async function assertWallet(a, net) {
    const [chain, accounts] = await Promise.all([provider.request({method:'eth_chainId'}),provider.request({method:'eth_accounts'})]);
    if (Number(BigInt(chain)) !== net.id || lower(accounts[0]) !== lower(a) || lower(account) !== lower(a))
      throw new Error('钱包账户或网络已切换。回到相同账户后可继续。');
  }
  window.addEventListener('storage',ev => {
    if (!running && account && ev.key === key()) showAccount(account,true);
  });
  async function guardedStep(i) {
    if (!navigator.locks) return runStep(i);
    const signer=account;
    await navigator.locks.request('stablecoin-sign/'+lower(signer),{ifAvailable:true},async lock => {
      if (!lock) return status('另一个标签页正在处理此钱包。请在该页完成当前步骤。',true);
      if (lower(signer)!==lower(account)) return;
      showAccount(signer,true);
      if (records[i]?.state==='confirmed' || (i>0 && records[i-1]?.state!=='confirmed')) return;
      await runStep(i);
    });
  }
  async function runStep(i) {
    if (running || !account) return;
    const a = account, net = networks[steps[i][0]];
    running = true; render();
    try {
      const plan = planStep(i, contracts, records);
      await pickNetwork(net); await assertWallet(a, net);
      let hash = records[i]?.state === 'pending' ? records[i].hash : '';
      if (!hash) {
        status('请在 MetaMask 核对 ' + net.name + '、' + steps[i][1] + ' 和金额 ' + steps[i][2] + '。');
        hash = await provider.request({method:'eth_sendTransaction',params:[{from:a,...plan}]});
        if (!validHash(hash)) throw new Error('钱包未返回有效的交易哈希。');
        if (lower(account) !== lower(a)) {
          const oldKey = 'reactive-camp-console-v1/' + lower(a), old = JSON.parse(localStorage.getItem(oldKey) || '{}');
          old.records ||= []; old.records[i] = {hash, state:'pending'}; localStorage.setItem(oldKey, JSON.stringify(old));
          throw new Error('交易已保存在原签名账户下。切回该账户即可检查回执。');
        }
        records[i] = {hash,state:'pending'}; save(); render();
      }
      status(net.name + ' 已返回交易哈希。等待交易入块…');
      for (let k = 0; k < 32; k++) {
        await assertWallet(a, net);
        const receipt = await provider.request({method:'eth_getTransactionReceipt',params:[hash]});
        if (receipt) {
          const tx = await provider.request({method:'eth_getTransactionByHash',params:[hash]});
          const verified = await confirmStepTransaction(i, contracts, plan, receipt, tx, a, hash,
            (method,params) => provider.request({method,params}));
          await assertWallet(a, net);
          records[i] = verified; save();
          if (verified.state === 'failed') throw new Error('交易已回滚。请检查该网测试币余额和浏览器回执，再决定是否重试。');
          status('第 ' + (i + 1) + ' 步已在 ' + net.name + ' 确认。' + (i < 5 ? '可以继续下一步。' : '正在查找跨链回执。'));
          return;
        }
        await sleep(3500);
      }
      status('交易仍在等待入块。稍后点「检查回执」继续追踪同一笔交易。');
    } catch (e) { status(e.code === 4001 ? '已取消钱包请求。可从本步继续。' : e.message || String(e), true); }
    finally { running = false; render(); if (i === 5 && records[5]?.state === 'confirmed') autoLocate(); }
  }
  async function readEvent(chain, index, sourceHash) {
    const net = networks[chain];
    const id = await rpc(net, 'eth_chainId', []); if (Number(BigInt(id)) !== net.id) throw new Error(net.name + ' RPC chainId 异常。');
    const tip = Number(BigInt(await rpc(net, 'eth_blockNumber', [])));
    // Most public RPCs cap the number of blocks per query. Recently deployed contracts are cheap to scan.
    const first = Math.max(records[index].block, tip - 6000);
    for (let end = tip; end >= first; end -= 750) {
      const logs = await rpc(net, 'eth_getLogs', [{address:records[index].address,topics:[eventTopics[chain],null,sourceHash],
        fromBlock:hex(Math.max(first,end-749)),toBlock:hex(end)}]);
      const match = logs.find(l => !l.removed && lower(l.address) === lower(records[index].address) &&
        lower(l.topics?.[2]) === lower(sourceHash) && validHash(l.transactionHash));
      if (match) return match.transactionHash;
    }
    return '';
  }
  async function locate(silent = false) {
    if (records[5]?.state !== 'confirmed') return false;
    const generation = scanGeneration, sourceHash = records[5].hash;
    if (!silent) status('用同一笔源交易哈希查找 Lasna 和 Base 事件…');
    const results = await Promise.allSettled(['reactive','destination'].map((n,i) => found[n] ? Promise.resolve(found[n]) : readEvent(n,i+1,sourceHash)));
    if (generation !== scanGeneration) return false;
    const errors = [];
    results.forEach((r,i) => {
      const n = ['reactive','destination'][i], input = $(i ? 'destHash' : 'reactiveHash');
      if (r.status === 'fulfilled' && r.value && !parseHash(input.value)) { found[n] = r.value; input.value = r.value; }
      if (r.status === 'rejected') errors.push(networks[n].name);
    });
    save(); render();
    if (validHash(found.reactive) && validHash(found.destination)) {
      const run = manifest();
      try {
        const evidence = await window.ReceiptProof.fetchPublic(run,(role,method,params)=>rpc(networks[role],method,params));
        if (generation!==scanGeneration || found.reactive!==run.reactive.txHash || found.destination!==run.destination.txHash) return false;
        const triage = window.StablecoinAI.assess(evidence.result.alert,null);
        verifiedProof = {receipts:evidence.receipts,alert:evidence.result.alert,triage};
        status('三笔交易已通过链上核验。AI 初步分流为「'+triage.labelZh+'」。可打开复核页补充美元报价，或下载公开回执。');
        return true;
      } catch (e) {status('已取得三笔哈希，链上核验仍待完成。'+(e.message || e),true);return false;}
    }
    if (!silent || errors.length) status(errors.length ? errors.join('、') + ' 的公开 RPC 暂未能完成查询。稍后再查，或从浏览器粘贴哈希。' : '等待中继或回调入块。页面会继续读取，也可稍后手动查找。', !!errors.length);
    return false;
  }
  async function autoLocate() {
    const gen = ++scanGeneration;
    for (let tries=0; tries<12 && gen===scanGeneration; tries++) { if (await locate(tries>0)) return; await sleep(10000); }
  }
  function manifest() {
    const v = (chain,i,h) => ({chainId:networks[chain].id,address:records[i].address,txHash:h});
    const rh = parseHash($('reactiveHash').value), dh = parseHash($('destHash').value);
    if (!records[5]?.hash || !rh || !dh) throw new Error('需要三笔有效交易。');
    return {version:1,mode:'public-testnet',origin:v('origin',0,records[5].hash),reactive:v('reactive',1,rh),destination:v('destination',2,dh),...(verifiedProof || {})};
  }
  function download(name, data) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(data,null,2)+'\n'],{type:'application/json'}));
    const anchor = document.createElement('a'); anchor.href=url; anchor.download=name; anchor.click(); setTimeout(()=>URL.revokeObjectURL(url),2000);
  }
  $('connect').onclick = async () => {
    try {
      const picked = known.get('io.metamask') || window.ethereum?.providers?.find(p=>p.isMetaMask) ||
        (window.ethereum?.isMetaMask ? window.ethereum : null);
      if (!picked) throw new Error('请在启用 MetaMask 的浏览器或 MetaMask 自带浏览器打开本页。');
      if (picked !== provider) { provider = picked; provider.on?.('accountsChanged', arr=>showAccount(arr?.[0])); }
      const accounts = await provider.request({method:'eth_requestAccounts'}); showAccount(accounts?.[0]);
      if (account) status('已连接。请从第一个未完成的步骤继续。');
    } catch(e) { status(e.message || String(e),true); }
  };
  $('backup').onclick = () => download('deployment-progress.json',{version:1,account,hashes:records.map(r=>r?.hash || null),found});
  $('restore').onchange = async ev => {
    try {
      const file = ev.target.files[0]; if (!file || !account || running) return;
      const data = JSON.parse(await file.text());
      if (data.version !== 1 || lower(data.account) !== lower(account) || !Array.isArray(data.hashes) || data.hashes.length > steps.length || data.hashes.some(h=>h!==null && !validHash(h)))
        throw new Error('备份的账户、哈希或版本不匹配。');
      const merged = records.slice();
      data.hashes.forEach((h,i) => {
        if (!h) return;
        if (merged[i]?.hash && lower(merged[i].hash)!==lower(h)) throw new Error('此账户已有不同的交易记录。');
        if (!merged[i]) merged[i] = {hash:h,state:'pending'};
      });
      records = merged; save(); render(); status('已导入。逐步点「检查回执」核对原始交易，无须重复发送。');
    } catch(e) { status(e.message || String(e),true); } finally { ev.target.value=''; }
  };
  for (const [id,name] of [['reactiveHash','reactive'],['destHash','destination']]) $(id).oninput = () => {verifiedProof=null;found[name]=parseHash($(id).value);save();render();};
  $('locate').onclick = () => locate();
  $('download').onclick = () => download('public-run.json',manifest());
  $('review').onclick = () => {localStorage.setItem('reactive-track3-review',JSON.stringify(manifest()));location.href='../review/?source=wallet';};
  try {
    const resp = await fetch('contracts.json'); if (!resp.ok) throw new Error('无法读取 contracts.json。');
    contracts = (await resp.json()).contracts; render(); status('合约字节码已加载。连接 MetaMask 即可开始。');
  } catch (e) {render();status(e.message || String(e),true);}
}

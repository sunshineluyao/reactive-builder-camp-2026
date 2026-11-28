// SPDX-License-Identifier: MIT
'use strict';
(() => {
  const {text, lang} = window.PegPulseLocale;
  const proof = window.ReceiptProof;
  const ai = window.StablecoinAI;
  const $ = id => document.getElementById(id);
  const scenarios = Array.from(document.querySelectorAll('[data-kind]'));
  const names = {origin:'Origin quote', reactive:'Reactive evaluation', destination:'Destination callback'};
  const events = {origin:'PriceObserved', reactive:'QuoteRouted', destination:'PriceDeviation'};
  const contracts = {origin:'QuoteSource', reactive:'ReactiveAlert', destination:'AlertSink'};
  const modes = {
    local:['Local EVM rehearsal','Three saved receipts from private Anvil chains. Local contracts emulate cross-chain delivery.'],
    live:['Public testnet · RPC verified','Three RPCs returned matching receipts in canonical blocks on Ethereum Sepolia, Reactive Lasna and Base Sepolia.'],
    offline:['Offline public snapshot · unconfirmed','Saved event data match across three receipts. Public-chain inclusion has not been verified in this session.']
  };
  let active = null;
  let epoch = 0;
  let fallback = null;
  let currentMode = null;
  let importedPacket = null;

  function element(tag, cls, value) {
    const node = document.createElement(tag);
    if (cls) node.className = cls;
    if (value !== undefined) node.textContent = text(value);
    return node;
  }
  function status(title, detail, state) {
    $('mode').textContent = text(title);
    $('verification').textContent = text(detail);
    document.querySelector('.run-notice').dataset.state = state;
  }
  function reset() {
    active = null;
    fallback = null;
    currentMode = null;
    importedPacket = null;
    $('return-context').hidden = true;
    $('result-type').textContent = text('Queue decision');
    $('snapshot').hidden = true;
    $('legs').replaceChildren(element('li','empty','Awaiting matched receipts.'));
    for (const id of ['price','distance','count']) $(id).textContent = '—';
    $('queue').textContent = text('Awaiting evidence');
    $('evidence-id').textContent = text('Awaiting matched receipts');
    $('decision-label').textContent = text('Awaiting receipts');
    $('reason').textContent = '';
    $('score').textContent = '';
    $('features').replaceChildren();
    $('source-kind').textContent = text('References load after receipt validation.');
    $('context-data').textContent = text('Awaiting model inputs');
    $('context-error').textContent = '';
    $('context-input').disabled = true;
    delete $('result-box').dataset.decision;
    for (const btn of scenarios) btn.disabled = true;
  }
  function shortHash(value) { return value.slice(0,12) + '…' + value.slice(-8); }
  function explorer(role, path, value, text) {
    const a = element('a', 'hash', text);
    a.href = proof.networks[role].explorer + '/' + path + '/' + value;
    a.rel = 'noopener noreferrer';
    a.target = '_blank';
    return a;
  }
  function legNode(role, index, mode, leg) {
    const row = element('li','leg');
    row.dataset.role = role;
    const marker = element('span','leg-marker',index + 1);
    marker.setAttribute('aria-hidden','true');
    const body = element('div','leg-body');
    const chain = mode === 'local' ? 'Local EVM · chain ' + leg.chainId : proof.networks[role].name;
    body.append(element('h3','',names[role]),element('p','chain',chain + ' · ' + events[role]));
    const tx = mode === 'local' ? element('span','hash',shortHash(leg.txHash)) : explorer(role,'tx',leg.txHash,shortHash(leg.txHash));
    tx.title = leg.txHash;
    const ids = element('div','leg-ids');
    ids.append(tx,element('span','caption','Log ' + leg.logIndex));
    const details = element('details','leg-detail');
    details.append(element('summary','','Receipt details'));
    const full = element('div','full-coordinates');
    full.append(element('code','','Transaction ' + leg.txHash),element('code','',contracts[role] + ' · emitter'));
    const emitter = mode === 'local' ? element('code','',leg.address) : explorer(role,'address',leg.address,leg.address);
    full.append(emitter,element('code','','Block ' + leg.blockNumber + ' · ' + leg.blockHash));
    details.append(full);
    body.append(ids,details);
    row.append(marker,body);
    return row;
  }
  function row(label, value) {
    const r = element('div','');
    r.append(element('dt','',label),element('dd','',value));
    return r;
  }
  function usd(quote) {
    if (!quote || !Number.isSafeInteger(quote.usdMicros) || quote.usdMicros <= 0) return 'Missing or invalid';
    return '$' + (quote.usdMicros / 1000000).toFixed(6);
  }
  function assess(kind, context) {
    if (!active) return;
    for (const btn of scenarios) btn.setAttribute('aria-pressed',String(btn.dataset.kind === kind));
    const alert = active.alert;
    const evidence = kind === 'absent' ? null : kind === 'import' ? context : ai.demoContext(alert,kind);
    const output = ai.assess(alert,evidence);
    const syntheticReplay = ['corroborated','pool-only','missing'].includes(kind);
    $('return-context').hidden = !(syntheticReplay && (currentMode !== 'local' || importedPacket));
    $('return-context').textContent = text(importedPacket ? 'Return to imported context' : 'Return to alert evidence');
    $('result-type').textContent = text(syntheticReplay && currentMode !== 'local' ? 'Replay decision · synthetic context' : 'Queue decision');
    $('source-kind').textContent = text(kind === 'absent'
      ? 'No external reference packet supplied. Import one to assess the observed alert or select a synthetic replay.'
      : kind === 'import' ? 'Imported packet · author declares ' + output.provenance + ' inputs.'
      : 'Synthetic reference packet · illustrative USD quotes and pair history.');
    $('context-error').textContent = '';
    $('result-box').dataset.decision = output.decision;
    $('decision-label').textContent = lang === 'zh' ? output.labelZh : output.label;
    $('reason').textContent = lang === 'zh' ? output.reasonZh : output.reason;
    $('score').textContent = text(Number.isFinite(output.score) ? 'Model score ' + output.score.toFixed(3) : 'Score withheld');
    const history = Array.isArray(evidence?.history) ? evidence.history : [];
    $('features').replaceChildren(
      row('Receipt quote', (alert.priceBps / 10000).toFixed(4) + ' USDT'),
      row('USDC / USD reference', usd(evidence?.references?.['USDC/USD'])),
      row('USDT / USD reference', usd(evidence?.references?.['USDT/USD'])),
      row('Prior pair quotes', String(history.length)),
      row('Observation time (UTC)', new Date(alert.observedAt * 1000).toISOString().replace('T',' ').replace('.000Z',''))
    );
    $('context-data').textContent = JSON.stringify({alert,context:evidence,output},null,2);
  }
  function accept(result, mode) {
    active = result;
    currentMode = mode;
    const a = result.alert;
    status(...modes[mode],mode);
    $('snapshot').hidden = true;
    $('price').textContent = (a.priceBps / 10000).toFixed(4);
    $('distance').textContent = (Math.abs(a.priceBps - 10000) / 100).toFixed(2) + '%';
    $('count').textContent = '3 / 3';
    $('queue').textContent = text('1 unique alert');
    $('evidence-id').textContent = a.evidenceId;
    $('legs').replaceChildren(...proof.roles.map((role,i) => legNode(role,i,mode,result.legs[role])));
    if (!ai || typeof ai.assess !== 'function' || typeof ai.demoContext !== 'function') {
      $('decision-label').textContent = text('Model unavailable');
      $('reason').textContent = text('The model weights or runtime could not be loaded.');
      return;
    }
    for (const btn of scenarios) btn.disabled = false;
    $('context-input').disabled = false;
    assess(mode === 'local' ? 'corroborated' : 'absent');
  }
  async function rpc(role, method, params) {
    const response = await fetch(proof.networks[role].rpc,{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({jsonrpc:'2.0',id:1,method,params}),
      signal:AbortSignal.timeout(18000)
    });
    if (!response.ok) throw Error(proof.networks[role].name + ' RPC returned HTTP ' + response.status + '.');
    const answer = await response.json();
    if (answer?.jsonrpc !== '2.0' || answer.id !== 1 || answer.error || !Object.hasOwn(answer,'result')) {
      throw Error(proof.networks[role].name + ' RPC could not complete ' + method + '.');
    }
    return answer.result;
  }
  async function readFile(file) {
    if (!file) throw Error('Choose a JSON file.');
    if (file.size > 4 * 1024 * 1024) throw Error('Choose a JSON file smaller than 4 MiB.');
    return JSON.parse(await file.text());
  }
  async function load(getManifest) {
    const current = ++epoch;
    reset();
    status('Checking evidence','Validating the coordinates and transaction receipts.','waiting');
    try {
      const raw = await getManifest();
      if (current !== epoch) return;
      const run = proof.manifest(raw);
      if (run.mode === 'local-evm') {
        accept(proof.verify(run,raw.receipts),'local');
      } else {
        status('Checking public testnets','Requesting chain IDs, transaction receipts and block inclusion from three RPCs.','waiting');
        try {
          const {result} = await proof.fetchPublic(run,rpc);
          if (current === epoch) accept(result,'live');
        } catch (error) {
          if (current !== epoch) return;
          if (raw.receipts) { fallback = raw; $('snapshot').hidden = false; }
          throw error;
        }
      }
    } catch (error) {
      if (current === epoch) status('Evidence unverified',error.message || 'Receipt validation failed.','error');
    }
  }
  $('snapshot').addEventListener('click',() => {
    if (!fallback) return;
    try { accept(proof.verify(fallback,fallback.receipts),'offline'); }
    catch (error) { status('Snapshot failed validation',error.message,'error'); }
  });
  $('manifest-input').addEventListener('change',e => {
    const file = e.target.files[0];
    e.target.value = '';
    if (file) load(() => readFile(file));
  });
  $('context-input').addEventListener('change',async e => {
    const file = e.target.files[0];
    e.target.value = '';
    if (!file || !active) return;
    const current = epoch;
    try {
      const packet = await readFile(file);
      if (epoch === current) {
        importedPacket = packet;
        assess('import',packet);
      }
    } catch (error) {
      if (epoch === current) $('context-error').textContent = text('Context import failed. ' + error.message);
    }
  });
  for (const btn of scenarios) btn.addEventListener('click',() => assess(btn.dataset.kind));
  $('return-context').addEventListener('click',() => assess(importedPacket ? 'import' : 'absent',importedPacket));
  $('print').addEventListener('click',() => window.print());
  let expandedForPrint = [];
  window.addEventListener('beforeprint',() => {
    if (expandedForPrint.length) return;
    expandedForPrint = [...document.querySelectorAll('#trace details:not([open])')];
    expandedForPrint.forEach(node => { node.open = true; });
  });
  window.addEventListener('afterprint',() => {
    expandedForPrint.forEach(node => { node.open = false; });
    expandedForPrint = [];
  });
  async function initial() {
    const source = new URLSearchParams(location.search).get('source') || 'local';
    if (source === 'wallet') {
      const session = localStorage.getItem('reactive-track3-review');
      if (!session) throw Error('The deployment console has not exported a run in this browser. Load an evidence manifest or complete the wallet run.');
      return JSON.parse(session);
    }
    if (!['local','public'].includes(source)) throw Error('Unknown evidence source. Choose local, public or wallet.');
    const path = source === 'public' ? '../evidence/public-run.json' : '../evidence/local-run.json';
    const response = await fetch(path,{cache:'no-store'});
    if (!response.ok || response.headers.get('content-type')?.includes('text/html')) {
      throw Error(source === 'public' ? 'No public deployment manifest is available here yet. Load a signed run from the deployment console or import its evidence JSON.' : 'The local rehearsal file could not be loaded. Serve the project over HTTP or import the saved evidence JSON.');
    }
    return response.json();
  }
  load(initial);
})();

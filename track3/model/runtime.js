/* SPDX-License-Identifier: MIT. Load weights.js before this script in a browser. */
(function (root) {
  "use strict";
  const model = typeof module === "object" && module.exports
    ? require("./weights.js")
    : root.StablecoinRiskWeights;
  if (!model) throw new Error("Load model/weights.js before model/runtime.js");

  const SCHEMA = "stablecoin-evidence/v1";
  const LABELS = {
    escalate: ["Escalate review", "升级复核"],
    observe: ["Continue observation", "继续观察"],
    insufficient: ["Insufficient evidence", "证据不足"]
  };
  const MAX_REFERENCE_AGE = 300;
  const HISTORY_WINDOW = 900;
  const isInteger = Number.isSafeInteger;
  const eventPrice = value => isInteger(value) && value > 0 && value <= 20000;
  const fresh = (value, asOf, window) =>
    isInteger(value) && value > 0 && value <= asOf && asOf - value <= window;

  function validSource(value, provenance) {
    if (typeof value !== "string" || value.length === 0 || value.length > 1000 ||
        value.trim() !== value) return false;
    if (provenance === "synthetic" && /^fixture:[a-z0-9/_:.+-]+$/i.test(value)) return true;
    // Public, credential-free HTTPS URLs. The scorer records the citation; no URL is fetched.
    const match = /^https:\/\/([a-zA-Z0-9.-]+)(?::([0-9]{1,5}))?(?:[/?#][^\s\\]*)?$/.exec(value);
    return Boolean(match && (!match[2] || Number(match[2]) <= 65535) &&
      match[1].split(".").every(label => /^[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?$/.test(label)));
  }

  function modelScore(features) {
    const x = model.featureOrder.map((key, i) =>
      Math.min(1, Math.max(0, features[key] / model.normalizationScales[i])));
    const hidden = model.hiddenWeights.map((row, j) => Math.tanh(
      row.reduce((sum, w, k) => sum + w * x[k], model.hiddenBias[j])
    ));
    const logit = hidden.reduce((sum, value, j) =>
      sum + model.outputWeights[j] * value, model.outputBias);
    return 1 / (1 + Math.exp(-logit));
  }

  function assess(alert, context) {
    const provenance = context?.provenance;
    const evidence = [];
    function result(decision, code, reason, reasonZh, score = null, features = null) {
      const [label, labelZh] = LABELS[decision];
      return {decision, label, labelZh, code, reason, reasonZh, score, features,
        inferenceRan: score !== null, modelVersion: model.version, evidence,
        provenance: ["observed", "synthetic"].includes(provenance) ? provenance : "unknown"};
    }
    const fail = (code, en, zh) => result("insufficient", code, en, zh);
    if (!eventPrice(alert?.priceBps) || !isInteger(alert?.observedAt) || alert.observedAt <= 0 ||
        typeof alert.evidenceId !== "string" || !alert.evidenceId.trim() || alert.evidenceId.length > 512)
      return fail("invalid_event", "A valid price event, timestamp and event ID are required.",
        "需要有效的报价事件、时间戳和事件标识。");
    const {priceBps, observedAt} = alert;
    evidence.push({role: "alert event", source: alert.evidenceId, observedAt});
    const pairDeviationBps = Math.abs(priceBps - 10000);
    if (pairDeviationBps <= 50)
      return result("observe", "no_threshold_crossing", "The quote is within the 50 bp trigger band. No triage is needed.",
        "报价位于 50 个基点的触发区间内，无需启动复核。");
    if (!context || context.schema !== SCHEMA || context.pair !== "USDC/USDT" ||
        !["observed", "synthetic"].includes(provenance) || context.alertId !== alert.evidenceId)
      return fail("context_mismatch", "A versioned evidence packet must match this alert ID and pair.",
        "需要与本条告警及币对匹配的版本化证据。");
    const refs = [];
    for (const asset of ["USDC/USD", "USDT/USD"]) {
      const q = context.references?.[asset];
      if (!q || !isInteger(q.usdMicros) || q.usdMicros <= 0 || q.usdMicros > 10000000 ||
          !validSource(q.source, provenance))
        return fail("missing_reference", "Missing or invalid independent " + asset + " reference.",
          "缺少有效且可追溯的 " + asset + " 独立报价。");
      if (!fresh(q.observedAt, observedAt, MAX_REFERENCE_AGE))
        return fail("stale_reference", asset + " falls outside the five minutes preceding the event.",
          asset + " 的采样时间超出事件发生前五分钟的允许范围。");
      evidence.push({role: asset, source: q.source, observedAt: q.observedAt, usdMicros: q.usdMicros});
      refs.push(q.usdMicros);
    }
    const history = context.history;
    if (!Array.isArray(history) || history.length < 2 || history.length > 24)
      return fail("missing_history", "Provide two to 24 earlier observations of the same pair.",
        "需要 2 至 24 条该币对的先前报价。");
    let previous = 0;
    let persistent = 0;
    const direction = Math.sign(priceBps - 10000);
    for (const q of history) {
      if (!q || !eventPrice(q.priceBps) || !validSource(q.source, provenance) ||
          !fresh(q.observedAt, observedAt, HISTORY_WINDOW) || q.observedAt >= observedAt ||
          q.observedAt <= previous)
        return fail("invalid_history", "Pair history must be recent, ordered, distinct and sourced.",
          "币对历史报价需处于最近 15 分钟内、按时间递增且附来源。");
      previous = q.observedAt;
      if (direction * (q.priceBps - 10000) > 50) persistent++;
      evidence.push({role: "USDC/USDT history", source: q.source, observedAt: q.observedAt, priceBps: q.priceBps});
    }
    if (!fresh(previous, observedAt, MAX_REFERENCE_AGE))
      return fail("stale_history", "The latest pair-history sample is older than five minutes.",
        "最近一条币对历史报价距事件已超过五分钟。");
    const [usdc, usdt] = refs;
    const usdDeviationBps = Math.max(Math.abs(usdc - 1000000), Math.abs(usdt - 1000000)) / 100;
    const independentPairBps = (usdc / usdt - 1) * 10000;
    const features = {pairDeviationBps, usdDeviationBps,
      alignedUsdPairBps: Math.max(0, direction * independentPairBps), persistence: persistent / history.length};
    const score = modelScore(features);
    const action = score >= 0.5 ? "escalate" : "observe";
    const summary = "The pair moved " + pairDeviationBps + " bp from parity. The largest USD-reference deviation was " +
      usdDeviationBps.toFixed(1) + " bp. " + persistent + " of " + history.length +
      " earlier quotes exceeded the threshold in the same direction.";
    const summaryZh = "币对报价偏离 " + pairDeviationBps + " 个基点，美元参考价最大偏离 " +
      usdDeviationBps.toFixed(1) + " 个基点，先前 " + history.length + " 条报价中有 " + persistent +
      " 条同向超过门槛。";
    return result(action, "model_decision", summary, summaryZh, score, features);
  }

  // Purpose-built demonstrator. It never claims to query the quoted assets in a market.
  function demoContext(alert, mode = "corroborated") {
    if (!["corroborated", "pool-only", "missing", "stale"].includes(mode))
      throw new Error("Unknown synthetic evidence scenario");
    const direction = alert.priceBps < 10000 ? -1 : 1;
    const poolOnly = mode === "pool-only";
    const deltas = poolOnly ? [3, 0, 2] : [55, 61, 66];
    const history = deltas.map((d, i) => ({
      priceBps: 10000 + direction * d, observedAt: alert.observedAt - 180 + i * 60,
      source: "fixture:pair/" + (i + 1)
    }));
    const context = {schema: SCHEMA, alertId: alert.evidenceId, pair: "USDC/USDT", provenance: "synthetic", history,
      references: {
        "USDC/USD": {usdMicros: poolOnly ? 999900 : 1000000 + direction * 9600,
          observedAt: alert.observedAt - 15, source: "fixture:usd-reference/usdc"},
        "USDT/USD": {usdMicros: 1000100, observedAt: alert.observedAt - 10, source: "fixture:usd-reference/usdt"}
      }};
    if (mode === "missing") delete context.references["USDT/USD"];
    if (mode === "stale") context.references["USDT/USD"].observedAt = alert.observedAt - 1200;
    return context;
  }

  const api = Object.freeze({assess, demoContext, modelVersion: model.version, schema: SCHEMA});
  root.StablecoinAI = api;
  if (typeof module === "object" && module.exports) module.exports = api;
})(globalThis);

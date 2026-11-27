"use strict";

const query = new URLSearchParams(location.search);
const stage = document.querySelector("#stage");
const canvas = document.querySelector("#wanim-canvas");
const playButton = document.querySelector("#play-film");
const slider = document.querySelector("#quote-slider");
const presets = Array.from(document.querySelectorAll("[data-sample]"));
const loading = document.querySelector("#loading");
const examples = [9990, 9950, 9930];
const filmMode = query.get("mode") === "film";
if (filmMode) document.body.classList.add("film");
let scene;
let selected = 0;
let animation = 0;

function formatQuote(units) {
  return (units / 10000).toFixed(4);
}

function onQuote({key, value}) {
  if (key !== "quote") return;
  const [sample, units, deviation, trigger] = value;
  const boundary = deviation === 50;
  const quote = formatQuote(units);
  const decision = trigger ? "Request callback" : "Observe";
  const reason = trigger ? "The quote has crossed the 0.5% threshold."
    : boundary ? "Exactly 0.50% is still inside the band." : "The quote is inside the band.";
  document.querySelector("#reason-zh").textContent = trigger ? "偏差超过 0.5%，请求回调。"
    : boundary ? "恰好 0.5%，继续观察。" : "报价在观察区间内。";
  selected = sample;
  document.querySelector("#sample-index").textContent = String(sample + 1);
  document.querySelector("#quote-value").textContent = quote;
  document.querySelector("#deviation").replaceChildren(
    document.createTextNode(deviation + " bp "),
    Object.assign(document.createElement("span"), {textContent: "/ " + (deviation / 100).toFixed(2) + "%"})
  );
  document.querySelector("#action").textContent = decision;
  document.querySelector("#reason").textContent = reason;
  document.querySelector("#slider-output").textContent = quote;
  slider.value = String(units);
  slider.setAttribute("aria-valuetext", quote + " USDT per USDC");
  for (let i = 0; i < presets.length; i += 1) {
    presets[i].setAttribute("aria-pressed", String(i === sample && units === examples[i]));
  }
  stage.dataset.signal = trigger ? "trigger" : boundary ? "boundary" : "observe";
  stage.dataset.units = String(units);
  if (stage.dataset.ready === "false") {
    loading.hidden = true;
    stage.dataset.ready = "true";
    playButton.disabled = false;
    slider.disabled = false;
    if (filmMode) requestAnimationFrame(playSequence);
  }
}

function selectQuote(sample, units, progress = 1) {
  if (!scene || stage.dataset.ready !== "true") return;
  scene.set_sample(sample, units, progress);
  scene.mark_input();
}

function announce() {
  const value = document.querySelector("#quote-value").textContent;
  const action = document.querySelector("#action").textContent;
  document.querySelector("#announcement").textContent = value + " USDT per USDC. " + action + ".";
}

function stopSequence() {
  cancelAnimationFrame(animation);
  animation = 0;
  stage.dataset.playing = "false";
}

function playSequence() {
  stopSequence();
  stage.dataset.playing = "true";
  selectQuote(0, examples[0]);
  let start;
  let lastSample = 0;
  let lastProgress = 1;

  function frame(now) {
    if (start === undefined) start = now;
    const elapsed = now - start;
    const sample = elapsed < 3600 ? 0 : elapsed < 7900 ? 1 : 2;
    if (sample > 0) {
      const transitionStart = sample === 1 ? 3600 : 7900;
      const amount = Math.max(0, Math.min(1, (elapsed - transitionStart) / 650));
      const progress = amount * amount * (3 - 2 * amount);
      if (lastSample !== sample || lastProgress !== progress) {
        const units = Math.round(examples[sample - 1] + (examples[sample] - examples[sample - 1]) * progress);
        selectQuote(sample, units, progress);
        lastSample = sample;
        lastProgress = progress;
      }
    }
    if (elapsed < 12500) animation = requestAnimationFrame(frame);
    else {
      stopSequence();
      announce();
    }
  }
  animation = requestAnimationFrame(frame);
}

for (const button of presets) {
  button.addEventListener("click", () => {
    const sample = Number(button.dataset.sample);
    stopSequence();
    selectQuote(sample, examples[sample]);
    announce();
  });
}
slider.addEventListener("input", () => {
  stopSequence();
  selectQuote(selected, Number(slider.value));
});
slider.addEventListener("change", announce);
playButton.addEventListener("click", playSequence);

function loadClassic(url) {
  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = url;
    script.onload = resolve;
    script.onerror = () => reject(new Error("Could not load the Wanim compiler."));
    document.head.append(script);
  });
}

async function run() {
  const runtime = query.has("offline") ? "./_runtime/wanim/browser/"
    : "https://cdn.jsdelivr.net/npm/@wanimjs/wanim@0.1.3/browser/";
  const [bridge, response] = await Promise.all([
    import(runtime + "bridge.browser.js"),
    fetch("./threshold.py"),
    loadClassic(runtime + "rapydscript.js")
  ]);
  if (!response.ok) throw new Error("Could not load threshold.py.");
  const source = (await response.text()).replace("HOST_CONTROLS = False", "HOST_CONTROLS = True");
  await bridge.runPythonOnCanvas(source, canvas, {
    sceneName: "QuoteThreshold", quality: "-qm", fps: 30, mode: "normal",
    background: "#142125", theme: "dark", preload: "none",
    onSceneReady: (active) => { scene = active; },
    onMessage: onQuote
  });
}

run().catch((error) => {
  stopSequence();
  stage.dataset.ready = "error";
  loading.textContent = "Wanim could not load. Retry the page or use the local player in visual/README.md.";
  loading.hidden = false;
  playButton.disabled = true;
  slider.disabled = true;
  console.error("Wanim threshold player", error);
});

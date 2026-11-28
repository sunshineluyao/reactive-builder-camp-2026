# Reactive PegPulse · Host script

**English** · [简体中文](script.md)

One quote. Three chains. Anyone can verify.

Sunshine · Sunshine Swarm Superintelligence (3S) Lab

Reactive Builder Camp Demo Day · November 29, 2026

Play from 00:00. The simulated Q&A starts at 02:50 and the recording ends at 04:40. Sunshine is presenting in person at another conference at the same time. The host can collect audience questions for a written follow-up.

## Presentation

### 00:00 · One quote, three chains

Hello, I’m Sunshine from 3S Lab. Our project is Reactive PegPulse. One quote. Three chains. Anyone can verify. Imagine volunteering for a community treasury. One USDC buys only 0.9930 USDT. Would you ask others to review it? First, check that the alert reached the chain. Then ask whether market evidence is sufficient. Anyone with a mobile browser can follow the receipts.

### 00:28 · Which quotes trigger a callback?

The center line is parity. The green band extends half a percent on either side. The control quote, 0.9990, is ten basis points below parity. The animation’s 0.9950 sits exactly on the boundary. Both stay quiet. At 0.9930, the gap reaches seventy basis points. Crossing the threshold makes the contract request a callback.

### 00:54 · Three receipts for one source event

These are real testnet transactions. I published a simulated quote on Ethereum Sepolia. The Lasna contract subscribes to that publisher’s quote events. Reactive calls react() on Lasna. The contract checks the source, threshold and duplicates, then requests a callback. Base Sepolia records the alert automatically. To match the event, compare the source transaction hash and log index two. The three UTC block times are 13:38:12, 13:38:12 and 13:38:14. The first and last block timestamps differ by two seconds in this run. Each receipt has its own explorer link.

### 01:29 · When should a treasury escalate review?

An off-chain model prioritizes review. It needs earlier pair history and contemporaneous independent dollar references for both coins. The public run had no dollar references. The alert was retained and the score withheld. That is the observed outcome. For the two alternatives I keep the on-chain alert fixed and switch labeled synthetic evidence. Corroborating dollar weakness escalates review. Near-par references support observation.

### 02:00 · Duplicate events and fee limits

The tool records alerts and moves zero stablecoin principal. Repeating a source log sends one callback. Redelivering it records one alert. The newer contracts cap both individual and lifetime service payments. An empty balance or budget stops new work. Top-ups do not reset the lifetime cap. All fifteen local tests passed, including valid runs, rejection, replay and recovery. The public receipts shown earlier predate the added fee caps.

### 02:28 · Who can verify the result?

Community volunteers can read all three receipts without connecting a wallet or paying a fee. Bilingual captions and a transcript let people check at their own pace. Our design goals are wider participation and transparent accountability, aligned with SDGs 10 and 16. Next we will test how many community members can verify an alert unaided.

## Prerecorded simulated Q&A

### 02:50 · Execution · How can we verify the callback?

This is a prerecorded simulated Q&A. First question: how can a judge verify that the destination executed? Open the Base Sepolia receipt and find the recipient’s PriceDeviation event. Match its source transaction hash and log index two to the event ID on Lasna. This verifies that the alert was recorded. Two seconds is the difference between the endpoint block timestamps in this run.

### 03:15 · Integration · What does Reactive add to an oracle?

Second question: if we have price oracles, what does Reactive add? Price oracles can supply dollar references. Our contract subscribes to a specific quote event and requests a cross-chain callback when the threshold is crossed. Anyone can match the three receipts. The simulated quote triggered a real callback. Live oracle feeds are a next step. Without dollar references, the review tool retained the alert and withheld a score.

### 03:42 · Usefulness · Does one quote establish a depeg?

Third question: when volunteers see one pool quote fall, can they conclude that a stablecoin lost its peg? One pool quote warrants investigation. The model also needs history and independent dollar prices for both coins. The public run kept the alert and identified the missing inputs. Volunteers can flag the missing prices and use the same alert with two synthetic inputs to check when the model escalates review.

### 04:12 · Craft · What happens on replay, failure or exhaustion?

Final question: what if a callback fails or an event arrives twice? A failed call leaves the destination count unchanged. Inspect the proxy, target event, balance, debt and remaining budget. Authorized redelivery can record that event once. You can rerun all fifteen tests from the repository. Please collect additional questions for my written follow-up.

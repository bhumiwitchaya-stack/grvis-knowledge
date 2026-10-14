// Source-owned static analysis fixture; no external calls or target execution.
export const supportedTimeframes = ["1m", "5m"];
export function selectTimeframe(state, timeframe) {
  if (!supportedTimeframes.includes(timeframe)) throw new RangeError("Unsupported timeframe");
  return { ...state, timeframe };
}

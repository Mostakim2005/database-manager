// Hardware Planner — PSU transient & rail load analyzer
export const TRANSIENT_EXCURSION_MULTIPLIER = {
  highTdpThresholdW: 250,
  midTdpThresholdW: 180,
  high: 2.0,
  mid: 1.65,
  low: 1.35,
} as const;

export interface PsuAnalysis {
  continuousWatts: number;
  peakWatts: number;
  status: "pass" | "warn" | "fail";
  badgeText: string;
  explanation: string;
}

export function analyzePsuLoad(gpuTdpWatts: number, psuWattage = 550, systemBaseWatts = 85): PsuAnalysis {
  const safeTdp = Math.max(0, Number(gpuTdpWatts) || 0);
  const safePsu = Math.max(100, Number(psuWattage) || 550);
  const safeBase = Math.max(0, Number(systemBaseWatts) || 85);
  const continuousWatts = safeTdp + safeBase;
  const transientMult =
    safeTdp >= TRANSIENT_EXCURSION_MULTIPLIER.highTdpThresholdW
      ? TRANSIENT_EXCURSION_MULTIPLIER.high
      : safeTdp >= TRANSIENT_EXCURSION_MULTIPLIER.midTdpThresholdW
        ? TRANSIENT_EXCURSION_MULTIPLIER.mid
        : TRANSIENT_EXCURSION_MULTIPLIER.low;
  const peakWatts = Math.round(safeTdp * transientMult + safeBase);
  let status: PsuAnalysis["status"] = "pass";
  let badgeText = "Headroom Safe";
  let explanation = "";
  if (peakWatts > safePsu) {
    status = "fail";
    badgeText = "OCP Trip Risk";
    explanation = `Microsecond transient power bursts can spike to ~${peakWatts}W, which exceeds your ${safePsu}W rated PSU capacity. This risks triggering Over-Current Protection (OCP) shutdowns during demanding games.`;
  } else if (continuousWatts > 0.75 * safePsu) {
    status = "warn";
    badgeText = "Heavy PSU Load";
    explanation = `Continuous consumption is ${continuousWatts}W with peak spikes around ~${peakWatts}W. The ${safePsu}W PSU will handle it, but the internal fan will run hot and loud under continuous gaming sessions.`;
  } else {
    status = "pass";
    badgeText = "Headroom Safe";
    explanation = `Continuous load is an easy ${continuousWatts}W with transient peaks at ~${peakWatts}W. The ${safePsu}W PSU operates inside its quietest and most energy-efficient curve.`;
  }
  return { continuousWatts, peakWatts, status, badgeText, explanation };
}

export const evaluatePsuThresholds = analyzePsuLoad;

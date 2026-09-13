export interface GaugeScaleConfig {
  min: number;
  max: number;
}

export const GAUGE_CONFIG = {
  cx: 100,
  cy: 100,
  radius: 72,
  needleRadius: 62,
  startAngle: -120, // 0% at -120 deg (8 o'clock)
  sweepAngle: 240, // 100% at +120 deg (4 o'clock)
  download: { min: 0, max: 300 } as GaugeScaleConfig,
  upload: { min: 0, max: 100 } as GaugeScaleConfig,
};

export interface Point {
  x: number;
  y: number;
}

/**
 * Converts polar coordinates to Cartesian coordinates where 0 deg is 12 o'clock, clockwise.
 */
export function polarToCartesian(
  cx: number,
  cy: number,
  r: number,
  angleDeg: number
): Point {
  const rad = (angleDeg * Math.PI) / 180;
  return {
    x: cx + r * Math.sin(rad),
    y: cy - r * Math.cos(rad),
  };
}

/**
 * Computes exact SVG arc path string given center, radius, start and end angles.
 */
export function computeArcD(
  cx: number,
  cy: number,
  r: number,
  startAngle: number,
  endAngle: number
): string {
  const start = polarToCartesian(cx, cy, r, startAngle);
  const end = polarToCartesian(cx, cy, r, endAngle);
  const diff = endAngle - startAngle;
  const largeArc = diff > 180 ? 1 : 0;
  return `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${r} ${r} 0 ${largeArc} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`;
}

export interface GaugeGeometry {
  normalized: number;
  angle: number;
  arcPath: string;
  needleTransform: string;
}

/**
 * Pure mathematical gauge geometry derivation.
 * Guarantees that arc endpoint and needle angle share 100% identical normalized angle.
 */
export function calculateGaugeGeometry(
  value: number,
  type: 'download' | 'upload'
): GaugeGeometry {
  const cfg = GAUGE_CONFIG[type];
  const normalized = Math.max(
    0,
    Math.min(1, (value - cfg.min) / (cfg.max - cfg.min))
  );
  const angle = GAUGE_CONFIG.startAngle + normalized * GAUGE_CONFIG.sweepAngle;

  const arcPath =
    normalized <= 0.002
      ? ''
      : computeArcD(
          GAUGE_CONFIG.cx,
          GAUGE_CONFIG.cy,
          GAUGE_CONFIG.radius,
          GAUGE_CONFIG.startAngle,
          angle
        );

  const needleTransform = `rotate(${angle.toFixed(2)} ${GAUGE_CONFIG.cx} ${GAUGE_CONFIG.cy})`;

  return {
    normalized,
    angle,
    arcPath,
    needleTransform,
  };
}

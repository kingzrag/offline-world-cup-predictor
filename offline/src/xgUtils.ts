export function formatXG(xg: number): string {
  if (xg === 0) {
    return '0.00';
  }

  if (xg > 0 && xg < 0.05) {
    return '< 0.05';
  }

  return xg.toFixed(2);
}

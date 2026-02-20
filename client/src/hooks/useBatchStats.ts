export type BatchResult = {
  assetValue: number;
  frequency: number;
  severity: number;
  premium: number | null;
  netProfit: number | null;
  loss: number | null;
  margin: number | null;
};

export const computeBatchStats = (batch: BatchResult[]) => {
  const stat = (arr: number[]) => ({
    min: Math.min(...arr),
    max: Math.max(...arr),
    mean: arr.reduce((a, b) => a + b, 0) / arr.length,
    std:
      arr.length > 1
        ? Math.sqrt(
            arr
              .map((x) => Math.pow(x - arr.reduce((a, b) => a + b, 0) / arr.length, 2))
              .reduce((a, b) => a + b, 0) /
              (arr.length - 1)
          )
        : 0,
  });

  const boxplot = (arr: number[]) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const q1 = sorted[Math.floor(sorted.length * 0.25)];
    const q2 = sorted[Math.floor(sorted.length * 0.5)];
    const q3 = sorted[Math.floor(sorted.length * 0.75)];
    return { min: sorted[0], q1, median: q2, q3, max: sorted[sorted.length - 1] };
  };

  const percentile = (arr: number[], p: number) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const idx = Math.floor(p * (sorted.length - 1));
    return sorted[idx];
  };

  const pearson = (a: number[], b: number[]) => {
    const n = a.length;
    const ma = a.reduce((x, y) => x + y, 0) / n;
    const mb = b.reduce((x, y) => x + y, 0) / n;
    const cov = a.map((x, i) => (x - ma) * (b[i] - mb)).reduce((x, y) => x + y, 0) / n;
    const sa = Math.sqrt(a.map((x) => Math.pow(x - ma, 2)).reduce((x, y) => x + y, 0) / n);
    const sb = Math.sqrt(b.map((x) => Math.pow(x - mb, 2)).reduce((x, y) => x + y, 0) / n);
    return cov / (sa * sb);
  };

  const outliers = (arr: number[]) => {
    const sorted = [...arr].sort((a, b) => a - b);
    const q1 = sorted[Math.floor(sorted.length * 0.25)];
    const q3 = sorted[Math.floor(sorted.length * 0.75)];
    const iqr = q3 - q1;
    const lower = q1 - 1.5 * iqr;
    const upper = q3 + 1.5 * iqr;
    return arr.filter((x) => x < lower || x > upper);
  };

  const premiumStats = stat(batch.map((b) => b.premium ?? 0));
  const lossStats = stat(batch.map((b) => b.loss ?? 0));
  const profitStats = stat(batch.map((b) => b.netProfit ?? 0));
  const marginStats = stat(batch.map((b) => b.margin ?? 0));

  const premiumBox = boxplot(batch.map((b) => b.premium ?? 0));
  const profitBox = boxplot(batch.map((b) => b.netProfit ?? 0));

  const corrPremioLucro = pearson(
    batch.map((b) => b.premium ?? 0),
    batch.map((b) => b.netProfit ?? 0)
  );

  const p10 = percentile(batch.map((b) => b.netProfit ?? 0), 0.1);
  const p90 = percentile(batch.map((b) => b.netProfit ?? 0), 0.9);

  const outPremio = outliers(batch.map((b) => b.premium ?? 0));
  const outLucro = outliers(batch.map((b) => b.netProfit ?? 0));

  return {
    premiumStats,
    lossStats,
    profitStats,
    marginStats,
    premiumBox,
    profitBox,
    corrPremioLucro,
    p10,
    p90,
    outPremio,
    outLucro,
  };
};

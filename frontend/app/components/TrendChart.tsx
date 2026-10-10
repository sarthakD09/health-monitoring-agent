type TrendChartProps = {
  values: (number | null | undefined)[];
  color: string;
  label: string;
  unit: string;
};

export default function TrendChart({
  values,
  color,
  label,
  unit,
}: TrendChartProps) {
  const validValues = values.filter(
    (value): value is number =>
      typeof value === "number" && Number.isFinite(value),
  );

  if (validValues.length < 2) {
    return (
      <div className="trend-empty">
        Need at least two valid observations to show a trend.
      </div>
    );
  }

  const width = 320;
  const height = 76;
  const padding = 8;

  const minValue = Math.min(...validValues);
  const maxValue = Math.max(...validValues);
  const range = maxValue - minValue || 1;

  // Preserve gaps where observations are missing.
  const points = values.map((value, index) => {
    if (
      typeof value !== "number" ||
      !Number.isFinite(value)
    ) {
      return null;
    }

    const x =
      padding +
      (index / Math.max(values.length - 1, 1)) *
        (width - padding * 2);

    const y =
      height -
      padding -
      ((value - minValue) / range) *
        (height - padding * 2);

    return { x, y, value };
  });

  const segments: string[] = [];
  let currentSegment = "";

  points.forEach((point) => {
    if (!point) {
      if (currentSegment) segments.push(currentSegment);
      currentSegment = "";
      return;
    }

    currentSegment +=
      `${currentSegment ? " L" : "M"}${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
  });

  if (currentSegment) segments.push(currentSegment);

  return (
    <div className="trend-chart">
      <div className="trend-summary">
        <span>{label}</span>
        <span>
          {minValue === maxValue
            ? `${minValue} ${unit}`
            : `${minValue}–${maxValue} ${unit}`}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`${label} trend across ${validValues.length} valid observations`}
        preserveAspectRatio="none"
      >
        {[16, 34, 52, 70].map((y) => (
          <line
            key={y}
            x1={padding}
            y1={y}
            x2={width - padding}
            y2={y}
            stroke="currentColor"
            strokeOpacity="0.12"
            strokeDasharray="3 4"
          />
        ))}

        {segments.map((segment, index) => (
          <path
            key={index}
            d={segment}
            fill="none"
            stroke={color}
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            vectorEffect="non-scaling-stroke"
          />
        ))}
      </svg>

      <div className="trend-foot">
        {validValues.length} valid observations · session history
      </div>
    </div>
  );
}

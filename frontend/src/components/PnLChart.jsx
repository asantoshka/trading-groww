import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from 'recharts'

export default function PnLChart({ trades }) {
  const monthly = trades.reduce((acc, trade) => {
    const month = trade.date?.substring(0, 7) || 'Unknown'
    if (!acc[month]) acc[month] = 0
    acc[month] += trade.pnl || 0
    return acc
  }, {})

  const data = Object.entries(monthly)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([month, pnl]) => ({
      month:
        month === 'Unknown'
          ? 'Unknown'
          : new Date(`${month}-01`).toLocaleDateString('en-IN', {
              month: 'short',
              year: '2-digit'
            }),
      pnl: parseFloat(pnl.toFixed(2)),
      positive: pnl >= 0
    }))

  if (data.length === 0) {
    return (
      <div className="py-8 text-center font-mono text-sm text-muted">
        No trade data yet
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart
        data={data}
        margin={{ top: 5, right: 10, left: 10, bottom: 5 }}
      >
        <CartesianGrid
          strokeDasharray="3 3"
          stroke="#1e2832"
          vertical={false}
        />
        <XAxis
          dataKey="month"
          tick={{
            fill: '#4a5568',
            fontSize: 10,
            fontFamily: 'JetBrains Mono'
          }}
          axisLine={{ stroke: '#1e2832' }}
          tickLine={false}
        />
        <YAxis
          tick={{
            fill: '#4a5568',
            fontSize: 10,
            fontFamily: 'JetBrains Mono'
          }}
          axisLine={false}
          tickLine={false}
          tickFormatter={(value) => `₹${value}`}
        />
        <Tooltip
          contentStyle={{
            background: '#0d1117',
            border: '1px solid #1e2832',
            borderRadius: '8px',
            fontFamily: 'JetBrains Mono',
            fontSize: '11px',
            color: '#e2e8f0'
          }}
          formatter={(value) => [
            `${value >= 0 ? '+' : ''}₹${value}`,
            'P&L'
          ]}
          cursor={{ fill: 'rgba(255,255,255,0.03)' }}
        />
        <Bar dataKey="pnl" radius={[4, 4, 0, 0]}>
          {data.map((entry, index) => (
            <Cell
              key={index}
              fill={
                entry.positive
                  ? 'rgba(0,255,136,0.7)'
                  : 'rgba(255,69,96,0.7)'
              }
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

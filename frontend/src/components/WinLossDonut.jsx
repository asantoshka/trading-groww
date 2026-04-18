import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip
} from 'recharts'

export default function WinLossDonut({ wins, losses, total }) {
  if (total === 0) {
    return (
      <div className="py-8 text-center font-mono text-sm text-muted">
        No trades yet
      </div>
    )
  }

  const data = [
    { name: 'Wins', value: wins, color: 'rgba(0,255,136,0.8)' },
    { name: 'Losses', value: losses, color: 'rgba(255,69,96,0.8)' }
  ].filter((item) => item.value > 0)

  const winRate = total > 0 ? ((wins / total) * 100).toFixed(0) : '0'

  return (
    <div className="relative">
      <ResponsiveContainer width="100%" height={160}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={45}
            outerRadius={65}
            paddingAngle={3}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: '#0d1117',
              border: '1px solid #1e2832',
              borderRadius: '8px',
              fontFamily: 'JetBrains Mono',
              fontSize: '11px'
            }}
            formatter={(value, name) => [value, name]}
          />
        </PieChart>
      </ResponsiveContainer>

      <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
        <div className="font-display text-xl font-bold text-green">{winRate}%</div>
        <div className="font-mono text-[10px] text-muted">win rate</div>
      </div>

      <div className="mt-2 flex justify-center gap-6 font-mono text-[11px] text-muted">
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-green" />
          <span>{wins} wins</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-red" />
          <span>{losses} losses</span>
        </div>
      </div>
    </div>
  )
}

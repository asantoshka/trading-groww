import { useEffect, useMemo, useState } from 'react'

const INPUT_CLASS =
  'w-full rounded border border-border bg-bg px-3 py-2 font-mono text-sm text-text transition-colors focus:border-border-hover focus:outline-none'
const LABEL_CLASS =
  'mb-1 block font-mono text-[10px] uppercase tracking-wider text-muted'

function Section({ title, open, onToggle, children }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <button
        type="button"
        onClick={onToggle}
        className="mb-4 flex w-full items-center justify-between text-left"
      >
        <span className="font-mono text-[10px] uppercase tracking-[3px] text-muted">
          {title}
        </span>
        <span className="text-xs text-muted">{open ? '▲' : '▼'}</span>
      </button>
      {open ? children : null}
    </div>
  )
}

export default function ConfigPanel({ config, onSave, saving }) {
  const [local, setLocal] = useState(config)
  const [dirty, setDirty] = useState(false)
  const [scanTimeInput, setScanTimeInput] = useState('')
  const [symbolInput, setSymbolInput] = useState('')
  const [openSections, setOpenSections] = useState({
    capital: true,
    scanner: true,
    watchlist: true,
    order: true
  })

  useEffect(() => {
    setLocal(config)
    setDirty(false)
  }, [config])

  const serializedConfig = useMemo(() => JSON.stringify(config), [config])
  const serializedLocal = useMemo(() => JSON.stringify(local), [local])

  useEffect(() => {
    if (!config || !local) return
    setDirty(serializedConfig !== serializedLocal)
  }, [config, local, serializedConfig, serializedLocal])

  if (!local) return null

  const updateField = (field, value) => {
    setLocal((prev) => ({ ...prev, [field]: value }))
    setDirty(true)
  }

  const toggleSection = (key) => {
    setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }))
  }

  const addScanTime = () => {
    if (!scanTimeInput || local.scan_times.includes(scanTimeInput)) return
    updateField('scan_times', [...local.scan_times, scanTimeInput])
    setScanTimeInput('')
  }

  const removeScanTime = (time) => {
    updateField(
      'scan_times',
      local.scan_times.filter((item) => item !== time)
    )
  }

  const addSymbol = () => {
    const symbol = symbolInput.trim().toUpperCase()
    if (!symbol || local.watchlist.includes(symbol)) return
    updateField('watchlist', [...local.watchlist, symbol])
    setSymbolInput('')
  }

  const removeSymbol = (symbol) => {
    updateField(
      'watchlist',
      local.watchlist.filter((item) => item !== symbol)
    )
  }

  const discardChanges = () => {
    setLocal(config)
    setDirty(false)
    setScanTimeInput('')
    setSymbolInput('')
  }

  const handleSave = async () => {
    await onSave(local)
  }

  const maxTradePct =
    local.capital_limit > 0
      ? ((local.max_trade_value / local.capital_limit) * 100).toFixed(0)
      : '0'

  return (
    <>
      <div className="space-y-4">
        <Section
          title="CAPITAL & RISK LIMITS"
          open={openSections.capital}
          onToggle={() => toggleSection('capital')}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className={LABEL_CLASS}>Capital Limit (₹)</label>
              <input
                type="number"
                min="1000"
                step="500"
                className={INPUT_CLASS}
                value={local.capital_limit}
                onChange={(e) => updateField('capital_limit', Number(e.target.value))}
              />
            </div>

            <div>
              <label className={LABEL_CLASS}>Max Trade Value (₹)</label>
              <input
                type="number"
                min="500"
                step="100"
                className={INPUT_CLASS}
                value={local.max_trade_value}
                onChange={(e) =>
                  updateField('max_trade_value', Number(e.target.value))
                }
              />
              <div className="mt-1 font-mono text-[10px] text-muted">
                {maxTradePct}% of capital
              </div>
            </div>

            <div>
              <label className={LABEL_CLASS}>Max Loss Per Trade (₹)</label>
              <input
                type="number"
                min="100"
                step="50"
                className={INPUT_CLASS}
                value={local.max_loss_per_trade}
                onChange={(e) =>
                  updateField('max_loss_per_trade', Number(e.target.value))
                }
              />
            </div>

            <div>
              <label className={LABEL_CLASS}>Min Risk:Reward</label>
              <input
                type="number"
                step="0.1"
                min="1.0"
                className={INPUT_CLASS}
                value={local.min_rr_ratio}
                onChange={(e) => updateField('min_rr_ratio', Number(e.target.value))}
              />
            </div>
          </div>
        </Section>

        <Section
          title="SCANNER SETTINGS"
          open={openSections.scanner}
          onToggle={() => toggleSection('scanner')}
        >
          <div className="space-y-5">
            <div>
              <div className="mb-1 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <label className={LABEL_CLASS}>RSI Oversold (BUY signal)</label>
                <span className="font-mono text-[11px] text-amber">
                  RSI &lt; {local.rsi_oversold}
                </span>
              </div>
              <input
                type="range"
                min="20"
                max="50"
                step="1"
                value={local.rsi_oversold}
                onChange={(e) => updateField('rsi_oversold', Number(e.target.value))}
                className="w-full accent-amber"
              />
              <div className="mt-1 font-mono text-[9px] text-muted">
                20 (strict) → 50 (loose)
              </div>
            </div>

            <div>
              <div className="mb-1 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
                <label className={LABEL_CLASS}>Min Confidence Score</label>
                <span className="font-mono text-[11px] text-green">
                  {local.confidence_threshold}%
                </span>
              </div>
              <input
                type="range"
                min="50"
                max="95"
                step="5"
                value={local.confidence_threshold}
                onChange={(e) =>
                  updateField('confidence_threshold', Number(e.target.value))
                }
                className="w-full accent-green"
              />
              <div className="mt-1 font-mono text-[9px] text-muted">
                50% (loose) → 95% (strict)
              </div>
            </div>

            <div>
              <label className={LABEL_CLASS}>Scan Times (IST)</label>
              <div className="mb-3 flex flex-wrap gap-2">
                {local.scan_times.map((time) => (
                  <div
                    key={time}
                    className="flex items-center gap-1 rounded border border-border bg-surface2 px-2 py-1 font-mono text-[10px] text-text"
                  >
                    <span>{time}</span>
                    <button
                      type="button"
                      onClick={() => removeScanTime(time)}
                      className="text-muted transition-colors hover:text-red"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  type="time"
                  value={scanTimeInput}
                  onChange={(e) => setScanTimeInput(e.target.value)}
                  className={INPUT_CLASS}
                />
                <button
                  type="button"
                  onClick={addScanTime}
                  className="rounded border border-blue/30 bg-blue-dim px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-blue transition-colors hover:bg-blue/20"
                >
                  Add
                </button>
              </div>
            </div>
          </div>
        </Section>

        <Section
          title="WATCHLIST"
          open={openSections.watchlist}
          onToggle={() => toggleSection('watchlist')}
        >
          <div className="flex flex-wrap gap-2">
            {local.watchlist.map((symbol) => (
              <div
                key={symbol}
                className="flex items-center gap-1 rounded border border-blue/30 bg-blue-dim px-2 py-1 font-mono text-[10px] text-blue"
              >
                <span>{symbol}</span>
                <button
                  type="button"
                  onClick={() => removeSymbol(symbol)}
                  className="transition-colors hover:text-red"
                >
                  ×
                </button>
              </div>
            ))}
          </div>

          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <input
              type="text"
              value={symbolInput}
              placeholder="Add symbol..."
              onChange={(e) => setSymbolInput(e.target.value.toUpperCase())}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  addSymbol()
                }
              }}
              className={`${INPUT_CLASS} uppercase`}
            />
            <button
              type="button"
              onClick={addSymbol}
              className="rounded border border-blue/30 bg-blue-dim px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-blue transition-colors hover:bg-blue/20"
            >
              Add
            </button>
          </div>

          <div className="mt-2 font-mono text-[10px] text-muted">
            {local.watchlist.length} symbols
          </div>
        </Section>

        <Section
          title="ORDER SETTINGS"
          open={openSections.order}
          onToggle={() => toggleSection('order')}
        >
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className={LABEL_CLASS}>Product Type</label>
              <select
                className={INPUT_CLASS}
                value={local.default_product_type}
                onChange={(e) => updateField('default_product_type', e.target.value)}
              >
                <option value="MIS">MIS</option>
                <option value="CNC">CNC</option>
                <option value="NRML">NRML</option>
              </select>
            </div>

            <div>
              <label className={LABEL_CLASS}>Auto Square-off (IST)</label>
              <input
                type="time"
                className={INPUT_CLASS}
                value={local.auto_squareoff_time}
                onChange={(e) => updateField('auto_squareoff_time', e.target.value)}
              />
              <div className="mt-1 font-mono text-[10px] text-red">
                All MIS positions close at this time
              </div>
            </div>
          </div>
        </Section>
      </div>

      {dirty ? (
        <div className="fixed bottom-0 left-0 right-0 z-30 flex flex-col gap-3 border-t border-amber/30 bg-surface px-4 py-4 sm:px-5 xl:left-[220px] lg:flex-row lg:items-center lg:justify-between lg:px-6">
          <div className="font-mono text-[11px] text-amber">
            You have unsaved changes
          </div>
          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <button
              type="button"
              onClick={discardChanges}
              className="rounded border border-border px-4 py-2 font-mono text-[11px] text-muted hover:border-border-hover"
            >
              Discard
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="rounded border border-green/30 bg-green-dim px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-green transition-colors hover:bg-green/20 disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      ) : null}
    </>
  )
}

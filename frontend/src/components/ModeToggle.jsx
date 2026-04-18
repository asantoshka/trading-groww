import { useState } from 'react'

export default function ModeToggle({ mode, onModeChange, disabled }) {
  const [showConfirmModal, setShowConfirmModal] = useState(false)
  const [confirmText, setConfirmText] = useState('')
  const [switching, setSwitching] = useState(false)

  const handleSwitchToPaper = async () => {
    try {
      await onModeChange('paper')
    } catch (error) {
      console.error(error)
    }
  }

  const handleConfirmLive = async () => {
    if (confirmText !== 'CONFIRM' || switching) return

    setSwitching(true)
    try {
      await onModeChange('live')
      setShowConfirmModal(false)
      setConfirmText('')
    } catch (error) {
      console.error(error)
    } finally {
      setSwitching(false)
    }
  }

  const closeModal = () => {
    setShowConfirmModal(false)
    setConfirmText('')
  }

  const isPaper = mode === 'paper'

  return (
    <>
      <div
        className={`flex flex-col items-stretch gap-3 sm:flex-row sm:items-center ${
          disabled ? 'pointer-events-none opacity-50' : ''
        }`}
      >
        <div
          className={`rounded-full border px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-widest ${
            isPaper
              ? 'border-amber/30 bg-amber-dim text-amber'
              : 'border-green/30 bg-green-dim text-green'
          }`}
        >
          ● {isPaper ? 'PAPER MODE' : 'LIVE MODE'}
        </div>

        {isPaper ? (
          <button
            type="button"
            onClick={() => setShowConfirmModal(true)}
            className="rounded border border-green/30 bg-green-dim px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-green transition-colors hover:bg-green/20"
          >
            Switch to LIVE
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSwitchToPaper}
            className="rounded border border-amber/30 bg-amber-dim px-4 py-2 font-mono text-[11px] font-bold uppercase tracking-wider text-amber transition-colors hover:bg-amber/20"
          >
            Switch to PAPER
          </button>
        )}
      </div>

      {showConfirmModal ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="mx-4 w-full max-w-md rounded-xl border border-red/40 bg-surface p-8 shadow-2xl">
            <div className="mb-4 text-center text-4xl">⚠️</div>
            <h2 className="mb-2 text-center font-display text-xl font-bold text-red">
              Switch to LIVE Trading
            </h2>
            <p className="mb-6 text-center font-mono text-sm text-muted">
              Real money will be used. Orders will be placed on NSE. Losses are
              real.
            </p>

            <label className="mb-2 block font-mono text-[11px] text-muted">
              Type &quot;CONFIRM&quot; to proceed:
            </label>
            <input
              value={confirmText}
              onChange={(event) => setConfirmText(event.target.value)}
              placeholder="Type CONFIRM"
              className="mb-4 w-full rounded border border-border bg-bg px-3 py-2 font-mono text-sm text-text placeholder:text-muted focus:border-red/50 focus:outline-none"
            />

            <div className="flex flex-col gap-3 sm:flex-row">
              <button
                type="button"
                onClick={closeModal}
                className="flex-1 rounded border border-border py-2 font-mono text-[11px] uppercase text-muted hover:border-border-hover"
              >
                Cancel
              </button>

              <button
                type="button"
                disabled={confirmText !== 'CONFIRM' || switching}
                onClick={handleConfirmLive}
                className={`flex-1 rounded border py-2 font-mono text-[11px] font-bold uppercase tracking-wider transition-colors ${
                  confirmText !== 'CONFIRM' || switching
                    ? 'cursor-not-allowed opacity-40'
                    : 'border-red/30 bg-red-dim text-red hover:bg-red/20'
                }`}
              >
                {switching ? 'Switching...' : 'CONFIRM'}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </>
  )
}

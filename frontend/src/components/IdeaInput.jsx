export default function IdeaInput({ idea, onChange, onSubmit }) {
  function handleKey(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') onSubmit()
  }

  return (
    <div className="idea-stage">
      <div className="idea-card">
        <label className="idea-label">Describe your idea</label>
        <textarea
          className="idea-textarea"
          placeholder="e.g. A task manager for remote teams with real-time updates and role-based access..."
          value={idea}
          onChange={e => onChange(e.target.value)}
          onKeyDown={handleKey}
          rows={5}
          autoFocus
        />
        <p className="idea-hint">Tip: Ctrl+Enter to submit</p>
        <button
          className="btn-primary"
          onClick={onSubmit}
          disabled={!idea.trim()}
        >
          Understand My Idea →
        </button>
      </div>
    </div>
  )
}

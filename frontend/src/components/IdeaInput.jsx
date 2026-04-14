import { Button, Card, TextArea } from '@heroui/react'

export default function IdeaInput({ idea, onChange, onSubmit }) {
  function handleKey(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') onSubmit()
  }

  return (
    <div className="flex justify-center">
      <Card className="w-full">
        <Card.Content className="flex flex-col gap-3 p-6">
          <TextArea
            aria-label="Describe your idea"
            placeholder="e.g. A task manager for remote teams with real-time updates and role-based access..."
            value={idea}
            rows={5}
            onChange={e => onChange(e.target.value)}
            onKeyDown={handleKey}
            autoFocus
          />
          <p className="text-muted text-xs">Tip: Ctrl+Enter to submit</p>
          <Button
            variant="primary"
            className="w-full"
            onPress={onSubmit}
            isDisabled={!(typeof idea === 'string' ? idea : JSON.stringify(idea)).trim()}
          >
            Understand My Idea →
          </Button>
        </Card.Content>
      </Card>
    </div>
  )
}

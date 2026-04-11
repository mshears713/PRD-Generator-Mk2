import { useState } from 'react'
import { Button, Card, Disclosure } from '@heroui/react'
import ReactMarkdown from 'react-markdown'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)

  function copy() {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <Button variant="outline" size="sm" onPress={copy}>
      {copied ? 'Copied!' : 'Copy'}
    </Button>
  )
}

const GROWTH_SECTIONS = [
  { key: 'good',     label: 'Good Choices',  topColor: 'border-t-2 border-t-success' },
  { key: 'warnings', label: 'Warnings',       topColor: 'border-t-2 border-t-warning' },
  { key: 'missing',  label: 'Still Missing',  topColor: 'border-t-2 border-t-danger' },
]

function GrowthCheckCards({ data }) {
  if (!data || typeof data !== 'object') return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {GROWTH_SECTIONS.map(({ key, label, topColor }) => (
        <Card key={key} className={topColor}>
          <Card.Content className="p-4">
            <p className="text-xs font-bold uppercase tracking-wide text-muted mb-3">{label}</p>
            <div className="flex flex-col gap-1">
              {(data[key] || []).map((item, i) => (
                <Disclosure key={i}>
                  <Disclosure.Heading>
                    <Disclosure.Trigger className="w-full flex justify-between items-center py-1.5 text-left text-sm font-medium text-foreground hover:text-accent transition-colors">
                      {item.title}
                      <Disclosure.Indicator className="text-muted text-xs flex-shrink-0" />
                    </Disclosure.Trigger>
                  </Disclosure.Heading>
                  <Disclosure.Content>
                    <Disclosure.Body className="text-xs text-muted leading-relaxed pt-1.5 pb-1 border-t border-border mt-0.5">
                      {item.detail}
                    </Disclosure.Body>
                  </Disclosure.Content>
                </Disclosure>
              ))}
            </div>
          </Card.Content>
        </Card>
      ))}
    </div>
  )
}

export default function OutputPanel({ output, onReset }) {
  return (
    <div className="flex flex-col gap-8">

      <Card>
        <Card.Content className="p-6">
          <h2 className="text-base font-semibold mb-4">Growth Check</h2>
          <GrowthCheckCards data={output.growth_check} />
        </Card.Content>
      </Card>

      <Card>
        <Card.Content className="p-6">
          <h2 className="text-base font-semibold mb-4">PRD</h2>
          <div className="markdown-body">
            <ReactMarkdown>{output.prd}</ReactMarkdown>
          </div>
        </Card.Content>
      </Card>

      <Card>
        <Card.Content className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold">.env</h2>
            <CopyButton text={output.env} />
          </div>
          <pre className="bg-background border border-border rounded-lg p-4 font-mono text-sm whitespace-pre-wrap overflow-x-auto text-foreground">
            {output.env}
          </pre>
        </Card.Content>
      </Card>

      <div className="flex justify-center">
        <Button variant="outline" onPress={onReset}>← Start Over</Button>
      </div>
    </div>
  )
}

import React, { useEffect, useMemo, useState } from 'react'
import { Button, Card, Disclosure, ToggleButton, ToggleButtonGroup } from '@heroui/react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

function CopyButton({ text, label = 'Copy', copiedLabel = 'Copied!', variant = 'outline' }) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      setCopied(false)
    }
  }

  return (
    <Button variant={variant} size="sm" onPress={copy}>
      {copied ? copiedLabel : label}
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
  const docs = useMemo(() => {
    const main = output?.main_prd || output?.prd || ''
    const items = [
      { key: 'main', label: 'Main PRD', markdown: main },
    ]
    if (output?.backend_prd) items.push({ key: 'backend', label: 'Backend PRD', markdown: output.backend_prd })
    if (output?.frontend_prd) items.push({ key: 'frontend', label: 'Frontend PRD', markdown: output.frontend_prd })
    return items
  }, [output])

  const [activeDocKey, setActiveDocKey] = useState('main')

  useEffect(() => {
    if (!docs.some(d => d.key === activeDocKey)) setActiveDocKey('main')
  }, [docs, activeDocKey])

  const activeDoc = docs.find(d => d.key === activeDocKey) || docs[0]

  function inferFilename(markdown) {
    const firstLine = String(markdown || '').split('\n')[0] || ''
    const name = firstLine.replace(/^#\s+/, '').replace(/\s+PRD\s*$/i, '').trim()
    const safe = (name || 'StackLens_PRD').replace(/[^a-z0-9-_ ]/gi, '').trim().replace(/\s+/g, '_')
    return `${safe || 'StackLens_PRD'}.md`
  }

  function downloadMarkdown(markdown) {
    const blob = new Blob([markdown || ''], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = inferFilename(markdown)
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex flex-col gap-8">

      <Card>
        <Card.Content className="p-6">
          <h2 className="text-base font-semibold mb-4">System Review</h2>
          <GrowthCheckCards data={output.growth_check} />
        </Card.Content>
      </Card>

      <Card>
        <Card.Content className="p-6">
          <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-base font-semibold">PRDs</h2>
              {docs.length > 1 && (
                <ToggleButtonGroup
                  selectionMode="single"
                  selectedKeys={new Set([activeDocKey])}
                  onSelectionChange={keys => {
                    const v = [...keys][0]
                    if (v) setActiveDocKey(v)
                  }}
                  size="sm"
                >
                  {docs.map((d, idx) => (
                    <React.Fragment key={d.key}>
                      {idx > 0 && <ToggleButtonGroup.Separator />}
                      <ToggleButton id={d.key}>{d.label}</ToggleButton>
                    </React.Fragment>
                  ))}
                </ToggleButtonGroup>
              )}
            </div>
            <div className="flex items-center gap-2">
              {docs.map(d => (
                <Button
                  key={d.key}
                  size="sm"
                  variant="outline"
                  onPress={() => downloadMarkdown(d.markdown)}
                >
                  Download {d.label}
                </Button>
              ))}
              <CopyButton
                text={activeDoc?.markdown}
                label={`Use ${activeDoc?.label || 'PRD'} with Codex`}
                copiedLabel="Copied for Codex!"
                variant="secondary"
              />
            </div>
          </div>
          <div className="markdown-body">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{activeDoc?.markdown}</ReactMarkdown>
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

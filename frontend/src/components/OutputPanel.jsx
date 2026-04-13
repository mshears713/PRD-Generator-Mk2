import React, { useEffect, useMemo, useState } from 'react'
import { Alert, Button, Card, Disclosure, Input, Link, ToggleButton, ToggleButtonGroup } from '@heroui/react'
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

export default function OutputPanel({ output, idea, onReset }) {
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
  const [repoName, setRepoName] = useState('')
  const [isPrivate, setIsPrivate] = useState(true)
  const [creatingRepo, setCreatingRepo] = useState(false)
  const [createRepoError, setCreateRepoError] = useState('')
  const [createRepoResult, setCreateRepoResult] = useState(null)

  useEffect(() => {
    if (!docs.some(d => d.key === activeDocKey)) setActiveDocKey('main')
  }, [docs, activeDocKey])

  const activeDoc = docs.find(d => d.key === activeDocKey) || docs[0]

  async function handleCreateRepo() {
    setCreateRepoError('')
    setCreateRepoResult(null)
    setCreatingRepo(true)
    try {
      const payload = {
        idea: idea || null,
        main_prd: output?.main_prd || output?.prd || '',
        backend_prd: output?.backend_prd || null,
        frontend_prd: output?.frontend_prd || null,
        env: output?.env || null,
        repo_name: repoName.trim() ? repoName.trim() : null,
        private: isPrivate,
      }
      const res = await fetch('/create-repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await res.json().catch(() => ({}))
      if (!res.ok) throw new Error(data.detail || 'Failed to create repo')
      setCreateRepoResult(data)
    } catch (e) {
      setCreateRepoError(e.message)
    } finally {
      setCreatingRepo(false)
    }
  }

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

      <Card>
        <Card.Content className="p-6">
          <div className="flex items-center justify-between gap-3 mb-4 flex-wrap">
            <h2 className="text-base font-semibold">GitHub Repo</h2>
          </div>

          {createRepoError && (
            <div className="mb-4">
              <Alert status="danger">
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Description>{createRepoError}</Alert.Description>
                </Alert.Content>
              </Alert>
            </div>
          )}

          <div className="flex flex-col gap-3">
            <div className="flex flex-col md:flex-row gap-3 items-start md:items-end">
              <Input
                label="Repo name (optional)"
                placeholder="e.g. ai-journaling-assistant"
                value={repoName}
                onChange={e => setRepoName(e.target.value)}
                disabled={creatingRepo}
                className="w-full"
              />
              <ToggleButtonGroup
                selectionMode="single"
                selectedKeys={new Set([isPrivate ? 'private' : 'public'])}
                onSelectionChange={keys => {
                  if (creatingRepo) return
                  const v = [...keys][0]
                  if (v === 'public') setIsPrivate(false)
                  if (v === 'private') setIsPrivate(true)
                }}
                size="sm"
                className={creatingRepo ? 'pointer-events-none opacity-60' : ''}
              >
                <ToggleButton id="private">Private</ToggleButton>
                <ToggleButtonGroup.Separator />
                <ToggleButton id="public">Public</ToggleButton>
              </ToggleButtonGroup>
            </div>

            <Button variant="primary" onPress={handleCreateRepo} isLoading={creatingRepo}>
              Create GitHub Repo
            </Button>

            {createRepoResult?.repo_url && (
              <div className="mt-2 flex flex-col gap-3">
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm text-muted">Repo:</span>
                    <Link href={createRepoResult.repo_url} target="_blank" rel="noreferrer">
                      {createRepoResult.repo_url}
                    </Link>
                  </div>
                  <CopyButton
                    text={createRepoResult.kickoff_prompt || ''}
                    label="Copy kickoff prompt"
                    copiedLabel="Copied!"
                    variant="secondary"
                  />
                </div>
                <pre className="bg-background border border-border rounded-lg p-4 font-mono text-sm whitespace-pre-wrap overflow-x-auto text-foreground">
                  {createRepoResult.kickoff_prompt}
                </pre>
              </div>
            )}
          </div>
        </Card.Content>
      </Card>

      <div className="flex justify-center">
        <Button variant="outline" onPress={onReset}>← Start Over</Button>
      </div>
    </div>
  )
}

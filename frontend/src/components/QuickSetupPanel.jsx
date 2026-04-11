import { useState } from 'react'
import { Button, ToggleButton, ToggleButtonGroup } from '@heroui/react'

const DEFAULT_CONSTRAINTS = {
  user_scale: 'small',
  auth: 'none',
  data: { types: [], persistence: 'temporary' },
  execution: 'short',
  app_shape: 'simple',
}

export default function QuickSetupPanel({ onContinue }) {
  const [c, setC] = useState(DEFAULT_CONSTRAINTS)

  function set(key, value) {
    setC(prev => ({ ...prev, [key]: value }))
  }

  function setData(key, value) {
    setC(prev => ({ ...prev, data: { ...prev.data, [key]: value } }))
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="text-center">
        <p className="font-semibold text-foreground">Quick Setup</p>
        <p className="text-muted text-sm mt-1">5 questions · ~15 seconds</p>
      </div>

      <div className="flex flex-col">

        {/* 1. Users & Scale */}
        <div className="bg-surface border border-border rounded-t-lg border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">Who's using this?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.user_scale])}
            onSelectionChange={keys => { const v = [...keys][0]; if (v) set('user_scale', v) }}
            size="sm"
          >
            <ToggleButton id="single">Just me</ToggleButton>
            <ToggleButton id="small"><ToggleButtonGroup.Separator />Small group</ToggleButton>
            <ToggleButton id="large"><ToggleButtonGroup.Separator />Larger audience</ToggleButton>
          </ToggleButtonGroup>
        </div>

        {/* 2. Accounts / Identity */}
        <div className="bg-surface border border-border border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">Accounts / login?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.auth])}
            onSelectionChange={keys => { const v = [...keys][0]; if (v) set('auth', v) }}
            size="sm"
          >
            <ToggleButton id="none">No accounts</ToggleButton>
            <ToggleButton id="simple"><ToggleButtonGroup.Separator />Email / magic link</ToggleButton>
            <ToggleButton id="oauth"><ToggleButtonGroup.Separator />Social login</ToggleButton>
          </ToggleButtonGroup>
        </div>

        {/* 3. Data & Storage */}
        <div className="bg-surface border border-border border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">What data does it handle?</p>
          <ToggleButtonGroup
            selectionMode="multiple"
            selectedKeys={new Set(c.data.types)}
            onSelectionChange={keys => setData('types', [...keys])}
            size="sm"
            className="flex-wrap"
          >
            <ToggleButton id="none">No storage</ToggleButton>
            <ToggleButton id="text"><ToggleButtonGroup.Separator />Text / data</ToggleButton>
            <ToggleButton id="files"><ToggleButtonGroup.Separator />Files (PDFs, images)</ToggleButton>
            <ToggleButton id="results"><ToggleButtonGroup.Separator />Saved history</ToggleButton>
          </ToggleButtonGroup>
          <div className="flex items-center gap-3 mt-3 flex-wrap">
            <span className="text-muted text-sm whitespace-nowrap">Save long-term?</span>
            <ToggleButtonGroup
              selectionMode="single"
              selectedKeys={new Set([c.data.persistence])}
              onSelectionChange={keys => { const v = [...keys][0]; if (v) setData('persistence', v) }}
              size="sm"
            >
              <ToggleButton id="temporary">Temporary</ToggleButton>
              <ToggleButton id="permanent"><ToggleButtonGroup.Separator />Persistent</ToggleButton>
            </ToggleButtonGroup>
          </div>
        </div>

        {/* 4. Speed / Execution */}
        <div className="bg-surface border border-border border-b-0 p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">How fast does it need to respond?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.execution])}
            onSelectionChange={keys => { const v = [...keys][0]; if (v) set('execution', v) }}
            size="sm"
          >
            <ToggleButton id="realtime">Instant</ToggleButton>
            <ToggleButton id="short"><ToggleButtonGroup.Separator />Few seconds</ToggleButton>
            <ToggleButton id="async"><ToggleButtonGroup.Separator />Background</ToggleButton>
          </ToggleButtonGroup>
        </div>

        {/* 5. App Shape */}
        <div className="bg-surface border border-border rounded-b-lg p-4">
          <p className="text-muted text-xs font-bold uppercase tracking-widest mb-3">What shape is this app?</p>
          <ToggleButtonGroup
            selectionMode="single"
            selectedKeys={new Set([c.app_shape])}
            onSelectionChange={keys => { const v = [...keys][0]; if (v) set('app_shape', v) }}
            size="sm"
          >
            <ToggleButton id="simple">Simple tool</ToggleButton>
            <ToggleButton id="ai_core"><ToggleButtonGroup.Separator />AI-powered tool</ToggleButton>
            <ToggleButton id="workflow"><ToggleButtonGroup.Separator />Multi-step workflow</ToggleButton>
          </ToggleButtonGroup>
        </div>

      </div>

      <Button variant="primary" className="w-full" onPress={() => onContinue(c)}>
        Continue →
      </Button>
    </div>
  )
}

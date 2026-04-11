export const DEFAULT_FIXED_ANSWERS = {
  for_whom: 'small',
  accounts: 'none',
  remember_over_time: 'temporary',
  reliability_vs_speed: 'balanced',
}

export const FIXED_QUESTIONS = [
  {
    id: 'for_whom',
    question: 'Who is this for?',
    options: [
      {
        label: 'Just me',
        value: 'single',
        technical_effect: {
          explanation: 'Keeps the architecture lightweight and avoids multi-user complexity.',
          constraint_impacts: [
            'Sets user_scale = single',
            'Optimizes for minimal infrastructure and simplest deployment',
          ],
        },
      },
      {
        label: 'Small group',
        value: 'small',
        technical_effect: {
          explanation: 'Supports a handful of users without overbuilding for massive scale.',
          constraint_impacts: [
            'Sets user_scale = small',
            'Allows simple auth/storage patterns without heavy scaling work',
          ],
        },
      },
      {
        label: 'Public',
        value: 'large',
        technical_effect: {
          explanation: 'Shifts decisions toward reliability, concurrency, and predictable performance.',
          constraint_impacts: [
            'Sets user_scale = large',
            'Biases toward caching, rate limiting, and scalable deployment choices',
          ],
        },
      },
    ],
  },
  {
    id: 'accounts',
    question: 'Do users need accounts?',
    options: [
      {
        label: 'No',
        value: 'none',
        technical_effect: {
          explanation: 'Avoids login flows and account data; the product is usable immediately.',
          constraint_impacts: [
            'Sets auth = none',
            'Removes the need for sessions, account tables, and auth middleware',
          ],
        },
      },
      {
        label: 'Simple login',
        value: 'simple',
        technical_effect: {
          explanation: 'Adds basic identity while keeping the auth surface area small.',
          constraint_impacts: [
            'Sets auth = simple',
            'Adds a minimal login/session layer (no social providers)',
          ],
        },
      },
      {
        label: 'Social login',
        value: 'oauth',
        technical_effect: {
          explanation: 'Adds third-party identity providers and OAuth callback handling.',
          constraint_impacts: [
            'Sets auth = oauth',
            'Adds OAuth provider setup, callback routes, and token/session management',
          ],
        },
      },
    ],
  },
  {
    id: 'remember_over_time',
    question: 'Should this remember things over time?',
    options: [
      {
        label: 'No',
        value: 'temporary',
        technical_effect: {
          explanation: 'Keeps the system more stateless and reduces database requirements.',
          constraint_impacts: [
            'Sets data.persistence = temporary',
            'Optimizes for in-session data and simpler storage needs',
          ],
        },
      },
      {
        label: 'Yes',
        value: 'permanent',
        technical_effect: {
          explanation: 'Requires durable storage and data modeling so information persists between sessions.',
          constraint_impacts: [
            'Sets data.persistence = permanent',
            'Biases toward a real database and a stable data model',
          ],
        },
      },
    ],
  },
  {
    id: 'reliability_vs_speed',
    question: 'How important is reliability vs speed?',
    options: [
      {
        label: 'Fast/simple',
        value: 'fast',
        technical_effect: {
          explanation: 'Optimizes for fewer moving parts and a straightforward request/response flow.',
          constraint_impacts: [
            'Sets execution = short',
            'Avoids background workers and job orchestration',
          ],
        },
      },
      {
        label: 'Balanced',
        value: 'balanced',
        technical_effect: {
          explanation: 'Keeps the system simple while leaving room for reliability improvements later.',
          constraint_impacts: [
            'Sets execution = short (default)',
            'Optimizes for shipping quickly without adding background infra up front',
          ],
        },
      },
      {
        label: 'Reliable/robust',
        value: 'reliable',
        technical_effect: {
          explanation: 'Adds background execution patterns to handle retries, long tasks, and reliability.',
          constraint_impacts: [
            'Sets execution = async',
            'Biases toward workers/queues and idempotent job design',
          ],
        },
      },
    ],
  },
]


// Static option metadata: names, subtitles, benefits, drawbacks, sponsorship.
// Add new options or providers here — nothing else needs to change.

export const STACK_DETAILS = {
  scope: {
    fullstack: {
      name: 'Fullstack',
      subtitle: 'Frontend + Backend',
      learnMoreUrl: null,
      benefits: [
        'Complete product end-to-end',
        'Full control of the data flow',
        'Single team owns everything',
      ],
      drawbacks: [
        'More surface area to build and maintain',
        'Two environments to configure',
        'Higher initial complexity',
      ],
    },
    frontend: {
      name: 'Frontend only',
      subtitle: 'UI — no custom server',
      learnMoreUrl: null,
      benefits: [
        'Fast to ship',
        'Simple static deployment',
        'No server costs',
      ],
      drawbacks: [
        'Logic is exposed in the browser',
        'Data must come from third-party APIs',
        'No custom backend compute',
      ],
    },
    backend: {
      name: 'Backend only',
      subtitle: 'API / service — no UI',
      learnMoreUrl: null,
      benefits: [
        'Clean API contract from day one',
        'Reusable across any client or team',
        'Easy to scale independently',
      ],
      drawbacks: [
        'No user interface included',
        'Needs a client to access it',
        'More coordination overhead',
      ],
    },
  },

  backend: {
    fastapi: {
      name: 'FastAPI',
      subtitle: 'Python async API framework',
      learnMoreUrl: 'https://fastapi.tiangolo.com/',
      benefits: [
        'Fast to prototype with minimal boilerplate',
        'Native async support',
        'Auto-generates Swagger/OpenAPI docs',
        'Ideal for AI/ML pipelines',
      ],
      drawbacks: [
        'Python GIL limits raw concurrency',
        'Smaller ecosystem than Node',
        'Less suited for pure real-time apps',
      ],
    },
    node: {
      name: 'Node.js',
      subtitle: 'JavaScript runtime server',
      learnMoreUrl: 'https://nodejs.org/en/docs',
      benefits: [
        'Massive npm ecosystem',
        'Native WebSocket support',
        'Same language as the frontend',
      ],
      drawbacks: [
        'Async complexity can grow fast',
        'Less structure out of the box',
        'Not ideal for CPU-heavy tasks',
      ],
    },
    none: {
      name: 'No backend',
      subtitle: 'Fully client-side',
      learnMoreUrl: null,
      benefits: [
        'Zero server infrastructure',
        'Deploy as static files anywhere',
        'Near-zero cost to run',
      ],
      drawbacks: [
        'No server-side logic',
        'All state lives in the browser',
        'Limited to public APIs only',
      ],
    },
  },

  frontend: {
    react: {
      name: 'React',
      subtitle: 'Component-based UI library',
      learnMoreUrl: 'https://react.dev/',
      benefits: [
        'Rich component and library ecosystem',
        'Excellent for complex, interactive UIs',
        'Strong community and tooling',
      ],
      drawbacks: [
        'Bundle size overhead vs plain HTML',
        'Requires a build step',
        'More setup than a static page',
      ],
    },
    static: {
      name: 'Static HTML',
      subtitle: 'Plain HTML / CSS / JS',
      learnMoreUrl: null,
      benefits: [
        'Zero dependencies',
        'Instant load time',
        'Trivially easy to deploy anywhere',
      ],
      drawbacks: [
        'No reactive state management',
        'Manual DOM manipulation',
        'Harder to scale UI complexity',
      ],
    },
    none: {
      name: 'No frontend',
      subtitle: 'Headless service',
      learnMoreUrl: null,
      benefits: [
        'Pure API or background service',
        'No UI complexity to manage',
        'Faster to ship core logic',
      ],
      drawbacks: [
        'No user-facing interface',
        'Developer-only access',
        'Requires a separate client to consume',
      ],
    },
  },

  database: {
    postgres: {
      name: 'PostgreSQL',
      subtitle: 'Relational SQL database',
      learnMoreUrl: 'https://www.postgresql.org/docs/',
      benefits: [
        'Rock-solid data consistency',
        'Powerful queries with joins and indexes',
        'Battle-tested at production scale',
      ],
      drawbacks: [
        'Schema migrations required as you iterate',
        'More setup than Firebase',
        'Needs managed hosting',
      ],
    },
    firebase: {
      name: 'Firebase',
      subtitle: 'Google real-time database',
      learnMoreUrl: 'https://firebase.google.com/docs',
      benefits: [
        'Real-time sync built in out of the box',
        'No rigid schema — flexible structure',
        'Easy auth integration',
      ],
      drawbacks: [
        'Google vendor lock-in',
        'Gets expensive at scale',
        'Weak for complex relational queries',
      ],
    },
    none: {
      name: 'No database',
      subtitle: 'Stateless / ephemeral',
      learnMoreUrl: null,
      benefits: [
        'Zero DB complexity',
        'Fully stateless and fast',
        'No infrastructure to manage',
      ],
      drawbacks: [
        'Data lost on restart or between sessions',
        'No user history or saved state',
        'Limited to in-session data only',
      ],
    },
  },
}

export const DEPLOYMENT_OPTIONS = [
  {
    value: 'render',
    name: 'Render',
    subtitle: 'Managed cloud platform',
    learnMoreUrl: 'https://render.com/docs',
    sponsored: true,
    sponsorOffer: 'Free tier available — push to Git and deploy in minutes. Zero DevOps required.',
    benefits: [
      'Auto-deploy from GitHub on every push',
      'Free tier for prototypes and side projects',
      'Managed SSL, databases, cron, and workers',
    ],
    drawbacks: [
      'Cold starts on the free tier (50s spin-up)',
      'Less granular control than AWS',
      'Vendor dependency',
    ],
  },
  {
    value: 'aws',
    name: 'AWS',
    subtitle: 'Amazon Web Services',
    learnMoreUrl: 'https://docs.aws.amazon.com/',
    sponsored: false,
    benefits: [
      'Unmatched service breadth and global reach',
      'Enterprise-grade reliability and SLAs',
      'Fine-grained control of every resource',
    ],
    drawbacks: [
      'Significant learning curve to configure correctly',
      'Easy to accumulate unexpected costs',
      'Requires real DevOps expertise',
    ],
  },
  {
    value: 'self',
    name: 'Self-hosted',
    subtitle: 'Your own server or VPS',
    learnMoreUrl: null,
    sponsored: false,
    benefits: [
      'Full infrastructure control',
      'No vendor dependency',
      'Cheapest option at sustained scale',
    ],
    drawbacks: [
      'You handle all ops, patching, and security',
      'No managed failover or backups by default',
      'Higher long-term maintenance burden',
    ],
  },
]

/**
 * MathModelingAgent — Frontend Application
 * Pure vanilla JS, hash-based routing, state management.
 */

/* ============================================
   SVG Icon Library (inline SVGs)
   ============================================ */
const icons = {
  menu: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>',
  plus: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="5" y2="19"/><line x1="5" x2="19" y1="12" y2="12"/></svg>',
  send: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 3 9-3 9 19-9Z"/><path d="M6 12h16"/></svg>',
  paperclip: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg>',
  search: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
  settings: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
  zap: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>',
  messageSquare: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
  user: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
  logOut: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16,17 21,12 16,7"/><line x1="21" x2="9" y1="12" y2="12"/></svg>',
  brain: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/></svg>',
  terminal: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4,17 10,11 4,5"/><line x1="12" x2="20" y1="19" y2="19"/></svg>',
  monitor: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="3" rx="2"/><line x1="8" x2="16" y1="21" y2="21"/><line x1="12" x2="12" y1="17" y2="21"/></svg>',
  cpu: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="16" height="16" x="4" y="4" rx="2"/><rect width="6" height="6" x="9" y="9" rx="1"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>',
  bell: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>',
  creditCard: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>',
  shield: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/></svg>',
  layoutGrid: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/></svg>',
  fileText: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
  x: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
  stop: '<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><rect x="6" y="6" width="12" height="12" rx="2"/></svg>',
};

/* ============================================
   i18n Translations
   ============================================ */
const translations = {
  English: {
    'login.title': 'Welcome back',
    'login.subtitle': 'Sign in to continue to MathModeler',
    'login.email': 'Email',
    'login.password': 'Password',
    'login.signIn': 'Sign In',
    'login.or': 'or continue with',
    'login.google': 'Continue with Google',
    'login.terms': 'By continuing, you agree to our Terms of Service and Privacy Policy.',
    'sidebar.newProject': 'New Project',
    'sidebar.settings': 'Settings',
    'sidebar.user': 'User',
    'sidebar.logout': 'Logout',
    'chat.greeting': 'What can I do for you?',
    'chat.subtitle': 'Upload a math modeling problem and I\'ll help you analyze, strategize, code, and write.',
    'chat.placeholder': 'Describe your math modeling task...',
    'chat.disclaimer': 'MathModeler can make mistakes. Please verify important information.',
    'chat.chip1': 'Solve MCM 2025 Problem B',
    'chat.chip2': 'Analyze this PDF',
    'chat.chip3': 'Plan modeling strategy',
    'chat.connected': 'Connected',
    'chat.connecting': 'Connecting...',
    'chat.thinking': 'Thinking...',
    'chat.executing': 'Executing tools...',
    'chat.attach': 'Attach file',
    'chat.search': 'Search',
    'chat.stop': 'Stop',
    'chat.replyPlaceholder': 'Type your response...',
    'chat.replySend': 'Send',
    'chat.loginLoading': 'Signing in...',
    'chat.loginFailed': 'Login failed',
    'chat.toggleSandbox': 'Toggle Sandbox',
    'chat.memory': 'Memory Layers',
    'chat.toolSteps': 'thinking & tool steps',
    'chat.thoughtSteps': 'thinking steps',
    'sidebar.plan': 'Free Plan',
    'sandbox.timeline': 'Timeline',
    'sandbox.code': 'Code',
    'sandbox.document': 'Document',
    'sandbox.files': 'Files',
    'sandbox.timelineEmptyTitle': 'No activity yet',
    'sandbox.timelineEmptySubtitle': 'Send a task to see the execution timeline',
    'sandbox.codeEmptyTitle': 'No code generated yet',
    'sandbox.codeEmptySubtitle': 'Code will appear here during the Coding phase',
    'sandbox.documentEmptyTitle': 'No document generated yet',
    'sandbox.documentEmptySubtitle': 'Reports and papers will be rendered here',
    'sandbox.filesEmptyTitle': 'No files yet',
    'sandbox.filesEmptySubtitle': 'Generated artifacts will appear here',
    'artifact.report': 'Inception Report',
    'artifact.blueprint': 'Blueprint',
    'artifact.code': 'Source Code',
    'artifact.paper': 'Paper',
    'artifact.frozen': 'Frozen',
    'artifact.draft': 'Draft',
    'settings.title': 'Settings',
    'settings.account': 'Account',
    'settings.general': 'General',
    'settings.aiConfig': 'AI Configuration',
    'settings.notifications': 'Notifications',
    'settings.billing': 'Billing & Usage',
    'settings.danger': 'Danger Zone',
    'settings.theme': 'Theme',
    'settings.language': 'Language',
    'settings.model': 'Model',
    'settings.temperature': 'Temperature',
    'settings.systemPrompt': 'System Prompt',
    'settings.marketing': 'Marketing Emails',
    'settings.security': 'Security Alerts',
    'settings.changeAvatar': 'Change Avatar',
    'settings.name': 'Name',
    'settings.email': 'Email',
    'settings.deleteAccount': 'Delete Account',
    'settings.deleteWarning': 'Once you delete your account, there is no going back.',
    'settings.backToChat': 'Back to Chat',
    'artifacts.title': 'Artifacts',
    'artifacts.empty': 'No artifacts yet. Start a conversation to generate reports, blueprints, code, and papers.',
  },
  Chinese: {
    'login.title': '欢迎回来',
    'login.subtitle': '登录以继续使用 MathModeler',
    'login.email': '邮箱',
    'login.password': '密码',
    'login.signIn': '登录',
    'login.or': '或者使用以下方式登录',
    'login.google': '使用 Google 登录',
    'login.terms': '继续即表示您同意我们的服务条款和隐私政策。',
    'sidebar.newProject': '新建项目',
    'sidebar.settings': '设置',
    'sidebar.user': '用户',
    'sidebar.logout': '退出登录',
    'chat.greeting': '我能为您做什么？',
    'chat.subtitle': '上传数学建模题目，我将帮你分析、策划、编码和撰写论文。',
    'chat.placeholder': '描述你的数学建模任务....',
    'chat.disclaimer': 'MathModeler 可能会出错，请验证重要信息。',
    'chat.chip1': '解决 MCM 2025 Problem B',
    'chat.chip2': '分析这个 PDF',
    'chat.chip3': '规划建模策略',
    'chat.connected': '已连接',
    'chat.connecting': '连接中...',
    'chat.thinking': '思考中...',
    'chat.executing': '执行工具中...',
    'chat.attach': '上传文件',
    'chat.search': '搜索',
    'chat.stop': '停止',
    'chat.replyPlaceholder': '输入你的回复...',
    'chat.replySend': '发送',
    'chat.loginLoading': '登录中...',
    'chat.loginFailed': '登录失败',
    'chat.toggleSandbox': '切换工作台',
    'chat.memory': '记忆层状态',
    'chat.toolSteps': '个思考与工具步骤',
    'chat.thoughtSteps': '个思考步骤',
    'sidebar.plan': '免费版',
    'sandbox.timeline': '时间线',
    'sandbox.code': '代码',
    'sandbox.document': '文档',
    'sandbox.files': '文件',
    'sandbox.timelineEmptyTitle': '还没有活动',
    'sandbox.timelineEmptySubtitle': '发送任务后，这里会显示执行时间线',
    'sandbox.codeEmptyTitle': '还没有生成代码',
    'sandbox.codeEmptySubtitle': '进入编码阶段后，代码会显示在这里',
    'sandbox.documentEmptyTitle': '还没有生成文档',
    'sandbox.documentEmptySubtitle': '报告和论文会渲染在这里',
    'sandbox.filesEmptyTitle': '还没有文件',
    'sandbox.filesEmptySubtitle': '生成的制品会显示在这里',
    'artifact.report': '破题报告',
    'artifact.blueprint': '建模方案',
    'artifact.code': '源代码',
    'artifact.paper': '论文',
    'artifact.frozen': '已冻结',
    'artifact.draft': '草稿',
    'settings.title': '设置',
    'settings.account': '账户',
    'settings.general': '通用',
    'settings.aiConfig': 'AI 配置',
    'settings.notifications': '通知',
    'settings.billing': '账单与用量',
    'settings.danger': '危险区域',
    'settings.theme': '主题',
    'settings.language': '语言',
    'settings.model': '模型',
    'settings.temperature': '温度',
    'settings.systemPrompt': '系统提示词',
    'settings.marketing': '营销邮件',
    'settings.security': '安全提醒',
    'settings.changeAvatar': '更换头像',
    'settings.name': '姓名',
    'settings.email': '邮箱',
    'settings.deleteAccount': '删除账户',
    'settings.deleteWarning': '一旦删除账户，将无法恢复。',
    'settings.backToChat': '返回对话',
    'artifacts.title': '制品',
    'artifacts.empty': '暂无制品。开始对话以生成报告、蓝图、代码和论文。',
  },
};

/* ============================================
   Application State
   ============================================ */
const state = {
  currentView: 'login', // 'login' | 'chat' | 'settings'
  sidebarOpen: window.innerWidth >= 768,
  isConnected: false,
  agentStatus: 'idle', // 'idle' | 'thinking' | 'executing' | 'error'
  messages: [],
  projects: [],
  currentProjectId: null,
  artifacts: [],
  // File upload state
  pendingFiles: [],        // [{file_id, filename, file_type, content, size, parsed}]
  uploadingFile: false,    // true while upload is in progress
  settings: {
    name: 'Demo User',
    email: 'demo@example.com',
    theme: 'dark',
    language: 'Chinese',
    model: 'gpt-4o',
    temperature: 0.0,
    systemPrompt: '',
    marketingEmails: false,
    securityAlerts: true,
  },
  // Sandbox panel state
  sandbox: {
    activeTab: 'timeline',  // 'timeline' | 'code' | 'document' | 'files'
    phases: [],              // [{name, status, steps: [{title, status, result}]}]
    currentPhase: null,
    codeFiles: [],           // [{name, content, language}]
    selectedFileIndex: 0,
    documentContent: '',     // Latest report/paper markdown
    sandboxOpen: false,      // Mobile toggle
    problemUnderstanding: null, // {type, variables, constraints, tools, confidence}
    probPanelExpanded: true,    // Problem Understanding panel expand state
    evalLoops: {},              // {stepKey: [{tag, text, status}]} for Obs→Eval→Fix
  },
  memoryPanelOpen: false,
  memoryLayers: null,          // {working, session, project, longterm} from memory_update WS event
  phaseConfirmPending: false,  // Waiting for user to confirm next phase
  phaseConfirmData: null,      // {phase, summary}
  _userScrolledUp: false,      // Track if user has scrolled up from bottom
};

/* ============================================
   Helpers
   ============================================ */
function t(key) {
  return translations[state.settings.language]?.[key] || translations['English'][key] || key;
}

function $(selector) { return document.querySelector(selector); }
function $$(selector) { return document.querySelectorAll(selector); }

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/** Render markdown string to HTML via marked.js (with breaks for chat) */
function renderMarkdown(content) {
  if (typeof marked !== 'undefined') {
    try { return marked.parse(content, { breaks: true, gfm: true }); } catch (e) { /* fallback */ }
  }
  return escapeHtml(content);
}

/** Post-process a rendered message element: Prism highlight + KaTeX math */
function postProcessMessage(el) {
  // Syntax highlighting
  if (typeof Prism !== 'undefined') {
    el.querySelectorAll('pre code[class*="language-"]').forEach(block => {
      try { Prism.highlightElement(block); } catch (e) { /* skip */ }
    });
  }
  // KaTeX math rendering
  if (typeof renderMathInElement !== 'undefined') {
    try {
      renderMathInElement(el, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true },
        ],
        throwOnError: false,
      });
    } catch (e) { /* skip */ }
  }
}

/** Toast notification system */
function showToast(message, type = 'info', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  // Trigger enter animation
  requestAnimationFrame(() => toast.classList.add('show'));
  setTimeout(() => {
    toast.classList.remove('show');
    toast.addEventListener('transitionend', () => toast.remove());
  }, duration);
}

/* ============================================
   Theme Management
   ============================================ */
const SETTINGS_STORAGE_KEY = 'mathmodeler-settings';

function loadStoredSettings() {
  try {
    const raw = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object') return;
    state.settings = {
      ...state.settings,
      ...parsed,
    };
  } catch (e) {
    console.warn('Failed to load stored settings:', e);
  }
}

function persistSettings() {
  try {
    localStorage.setItem(SETTINGS_STORAGE_KEY, JSON.stringify(state.settings));
  } catch (e) {
    console.warn('Failed to persist settings:', e);
  }
}

function resolveIsDarkTheme(theme) {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return theme === 'dark';
}

function applyTheme(theme) {
  const html = document.documentElement;
  const isDark = resolveIsDarkTheme(theme);
  html.classList.toggle('dark', isDark);
  html.dataset.theme = isDark ? 'dark' : 'light';

  const metaTheme = document.querySelector('meta[name="theme-color"]');
  if (metaTheme) {
    metaTheme.setAttribute('content', isDark ? '#000000' : '#ffffff');
  }

  const prismTheme = document.getElementById('prism-theme');
  if (prismTheme) {
    prismTheme.href = isDark
      ? 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism-okaidia.min.css'
      : 'https://cdn.jsdelivr.net/npm/prismjs@1.29.0/themes/prism.min.css';
  }
}

// Listen for system theme changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
  if (state.settings.theme === 'system') applyTheme('system');
});

/* ============================================
   Routing
   ============================================ */
function navigate(view) {
  state.currentView = view;
  if (window.innerWidth < 768) state.sidebarOpen = false;
  render();
}

/* ============================================
   WebSocket Integration
   ============================================ */
function initWebSocket(projectId) {
  agentWS.off(); // Remove old callbacks

  agentWS.on('connected', () => {
    state.isConnected = true;
    render();
  });

  agentWS.on('disconnected', () => {
    state.isConnected = false;
    render();
  });

  agentWS.on('thought', (data) => {
    state.messages.push({
      id: 'thought-' + Date.now(),
      role: 'assistant',
      content: data.content,
      type: 'thought',
      timestamp: Date.now(),
    });
    state.agentStatus = 'thinking';
    renderMessages();
  });

  agentWS.on('tool_call', (data) => {
    state.messages.push({
      id: 'tool-' + Date.now(),
      role: 'assistant',
      content: `Calling tool: ${data.tool || ''}`,
      type: 'tool_call',
      toolName: data.tool,
      toolArgs: data.args,
      timestamp: Date.now(),
    });
    state.agentStatus = 'executing';
    renderMessages();
  });

  agentWS.on('assistant_message', async (data) => {
    state.messages.push({
      id: 'msg-' + Date.now(),
      role: 'assistant',
      content: data.content,
      type: 'text',
      timestamp: Date.now(),
    });
    state.agentStatus = 'idle';
    renderMessages();
    // Refresh artifacts + sandbox panel after agent produces output
    if (state.currentProjectId) {
      await loadArtifacts(state.currentProjectId);
      renderSandboxPanelOnly();
    }
  });

  agentWS.on('ask_human', (data) => {
    state.messages.push({
      id: 'ask-' + Date.now(),
      role: 'assistant',
      content: data.content,
      type: 'ask_human',
      timestamp: Date.now(),
    });
    state.agentStatus = 'idle';
    renderMessages();
  });

  agentWS.on('error', (data) => {
    state.messages.push({
      id: 'err-' + Date.now(),
      role: 'assistant',
      content: data.content,
      type: 'error',
      timestamp: Date.now(),
    });
    state.agentStatus = 'error';
    showToast(data.content || 'Agent error', 'error');
    renderMessages();
  });

  agentWS.on('status', (data) => {
    // Handle stopped status to reset UI
    if (data.content === 'stopped' || data.content === 'idle') {
      state.agentStatus = 'idle';
      renderMessages();
      updateSendStopButton();
    }
  });

  // ---- Structured sandbox events ----
  agentWS.on('phase_start', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      const phaseName = payload.phase || 'unknown';
      // Mark previous phase as completed
      state.sandbox.phases.forEach(p => {
        if (p.status === 'running') p.status = 'completed';
      });
      state.sandbox.phases.push({
        name: phaseName,
        status: 'running',
        steps: [],
      });
      state.sandbox.currentPhase = phaseName;
      renderSandboxPanelOnly();
    } catch (e) { console.warn('phase_start parse error:', e); }
  });

  agentWS.on('phase_plan', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      const phase = state.sandbox.phases.find(p => p.name === payload.phase);
      if (phase && payload.step_titles) {
        phase.steps = payload.step_titles.map(title => ({
          title,
          status: 'pending',
          result: '',
        }));
        renderSandboxPanelOnly();
      }
    } catch (e) { console.warn('phase_plan parse error:', e); }
  });

  agentWS.on('step_start', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      const phase = state.sandbox.phases.find(p => p.name === payload.phase);
      if (phase && phase.steps[payload.step_index]) {
        phase.steps[payload.step_index].status = 'running';
        renderSandboxPanelOnly();
      }
    } catch (e) { console.warn('step_start parse error:', e); }
  });

  agentWS.on('step_complete', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      const phase = state.sandbox.phases.find(p => p.name === payload.phase);
      if (phase && phase.steps[payload.step_index]) {
        phase.steps[payload.step_index].status = 'completed';
        phase.steps[payload.step_index].result = payload.result_preview || '';
        renderSandboxPanelOnly();
      }
    } catch (e) { console.warn('step_complete parse error:', e); }
  });

  agentWS.on('artifact_saved', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      const artType = payload.artifact_type || 'unknown';
      const content = payload.content || '';

      // Add extracted code blocks to code files
      if (artType === 'code') {
        const extractedFiles = getCodeFilesFromArtifact(artType, content);
        if (extractedFiles.length > 0) {
          state.sandbox.codeFiles = [
            ...state.sandbox.codeFiles.filter(file => !file.name.startsWith('code_')),
            ...extractedFiles,
          ];
          state.sandbox.selectedFileIndex = 0;
        }
      }

      // Update document content for report/paper/blueprint
      if (['report', 'paper', 'blueprint'].includes(artType)) {
        state.sandbox.documentContent = content;
        // Also add as a "file"
        const existingIdx = state.sandbox.codeFiles.findIndex(f => f.name.startsWith(artType));
        const fileEntry = {
          name: `${artType}.md`,
          content: content,
          language: 'markdown',
        };
        if (existingIdx >= 0) {
          state.sandbox.codeFiles[existingIdx] = fileEntry;
        } else {
          state.sandbox.codeFiles.push(fileEntry);
        }
      }

      // Re-fetch artifacts from API too
      if (state.currentProjectId) {
        loadArtifacts(state.currentProjectId);
      }
      renderSandboxPanelOnly();
    } catch (e) { console.warn('artifact_saved parse error:', e); }
  });

  agentWS.on('phase_complete', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      state.phaseConfirmPending = true;
      state.phaseConfirmData = { phase: payload.phase, summary: payload.summary || '' };
      state.agentStatus = 'idle';
      // Mark phase as completed in timeline
      const phase = state.sandbox.phases.find(p => p.name === payload.phase);
      if (phase) phase.status = 'completed';
      renderMessages();
      renderSandboxPanelOnly();
    } catch (e) { console.warn('phase_complete parse error:', e); }
  });

  agentWS.on('problem_understanding', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      state.sandbox.problemUnderstanding = payload;
      renderSandboxPanelOnly();
    } catch (e) { console.warn('problem_understanding parse error:', e); }
  });

  agentWS.on('eval_step', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      const key = `${payload.phase}_${payload.step_index}`;
      if (!state.sandbox.evalLoops[key]) state.sandbox.evalLoops[key] = [];
      state.sandbox.evalLoops[key].push({ tag: payload.tag, text: payload.text, iter: payload.iter || 1 });
      renderSandboxPanelOnly();
    } catch (e) { console.warn('eval_step parse error:', e); }
  });

  agentWS.on('memory_update', (data) => {
    try {
      const payload = typeof data.content === 'string' ? JSON.parse(data.content) : data.content;
      state.memoryLayers = payload;
      const drawer = document.getElementById('memory-drawer-body');
      if (drawer && state.memoryPanelOpen) renderMemoryDrawerBody(drawer);
    } catch (e) { console.warn('memory_update parse error:', e); }
  });

  agentWS.connect(projectId);
}

/* ============================================
   Data Loading
   ============================================ */
async function loadProjects() {
  try {
    state.projects = await api.listProjects();
  } catch (e) {
    console.warn('Could not load projects:', e.message);
    state.projects = [];
  }
}

async function loadChatHistory(projectId) {
  try {
    const history = await api.getChatHistory(projectId);
    state.messages = history.map(log => ({
      id: log.id,
      role: log.sender === 'user' ? 'user' : 'assistant',
      content: log.content,
      type: log.type === 'thought' ? 'thought' :
        log.type === 'tool_call' ? 'tool_call' :
          log.type === 'ask_human' ? 'ask_human' : 'text',
      toolName: log.tool,
      toolArgs: log.args,
      timestamp: log.timestamp ? new Date(log.timestamp).getTime() : Date.now(),
    }));
  } catch (e) {
    console.warn('Could not load chat history:', e.message);
    state.messages = [];
  }
}

async function loadArtifacts(projectId) {
  try {
    state.artifacts = await api.getArtifacts(projectId);
    // Restore codeFiles from artifacts
    state.sandbox.codeFiles = [];
    for (const art of state.artifacts) {
      const artType = art.artifact_type || art.type || 'unknown';
      const content = art.content || '';
      if (artType === 'code') {
        state.sandbox.codeFiles.push(...getCodeFilesFromArtifact(artType, content));
      } else if (['report', 'paper', 'blueprint'].includes(artType)) {
        state.sandbox.documentContent = content;
        const existingIdx = state.sandbox.codeFiles.findIndex(f => f.name.startsWith(artType));
        const fileEntry = { name: `${artType}.md`, content, language: 'markdown' };
        if (existingIdx >= 0) state.sandbox.codeFiles[existingIdx] = fileEntry;
        else state.sandbox.codeFiles.push(fileEntry);
      }
    }
  } catch (e) {
    console.warn('Could not load artifacts:', e.message);
    state.artifacts = [];
  }
}

async function selectProject(projectId) {
  state.currentProjectId = projectId;
  state.messages = [];
  state.artifacts = [];
  state.agentStatus = 'idle';
  state.phaseConfirmPending = false;
  state.phaseConfirmData = null;
  state.memoryLayers = null;
  state.memoryPanelOpen = false;
  state.sandbox.phases = [];
  state.sandbox.codeFiles = [];
  state.sandbox.documentContent = '';
  state.sandbox.currentPhase = null;
  state.sandbox.selectedFileIndex = 0;
  state.sandbox.problemUnderstanding = null;
  state.sandbox.evalLoops = {};
  navigate('chat');
  await loadChatHistory(projectId);
  await loadArtifacts(projectId);
  // Restore timeline from persisted project data
  try {
    const project = await api.getProject(projectId);
    if (project.timeline && project.timeline.length > 0) {
      state.sandbox.phases = project.timeline;
    }

    // Primary: restore phase confirm card from explicitly persisted state
    if (project.phase_confirm && project.phase_confirm.phase) {
      state.phaseConfirmPending = true;
      state.phaseConfirmData = {
        phase: project.phase_confirm.phase,
        summary: project.phase_confirm.summary || '',
      };
    } else if (project.timeline && project.timeline.length > 0) {
      // Fallback: infer from timeline (phase completed, no subsequent running phase)
      const allPhaseIds = ['inception', 'blueprinting', 'coding', 'writing'];
      const completedPhases = project.timeline.filter(p => p.status === 'completed');
      const runningPhases = project.timeline.filter(p => p.status === 'running');
      if (completedPhases.length > 0 && runningPhases.length === 0) {
        const lastCompleted = completedPhases[completedPhases.length - 1];
        const lastIdx = allPhaseIds.indexOf(lastCompleted.name);
        if (lastIdx >= 0 && lastIdx < allPhaseIds.length - 1) {
          state.phaseConfirmPending = true;
          state.phaseConfirmData = {
            phase: lastCompleted.name,
            summary: lastCompleted.steps?.map(s => s.title).join(', ') || '',
          };
        }
      }
    }
  } catch (e) {
    console.warn('Could not load timeline:', e.message);
  }
  initWebSocket(projectId);
  renderMessages();
  renderSandboxPanelOnly(); // Render restored timeline without a full re-render
}

async function createNewProject() {
  const title = `Project ${new Date().toLocaleDateString()}`;
  const btn = document.getElementById('btn-new-project');
  if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner"></span> Creating...`; }
  try {
    const project = await api.createProject(title, 'MCM');
    await loadProjects();
    await selectProject(project.project_id);
    showToast('Project created', 'success');
  } catch (e) {
    console.error('Failed to create project:', e);
    showToast('Failed to create project', 'error');
    // Fallback: generate a UUID client-side and connect directly
    const fallbackId = crypto.randomUUID();
    state.projects.push({ project_id: fallbackId, title, competition: 'MCM', status: 'inception', created_at: new Date().toISOString() });
    await selectProject(fallbackId);
  } finally {
    if (btn) { btn.disabled = false; btn.innerHTML = `${icons.plus} ${t('sidebar.newProject')}`; }
  }
}

/* ============================================
   Message Sending
   ============================================ */
function sendMessage(content) {
  if (!content.trim() && state.pendingFiles.length === 0) return;
  if (!agentWS.isConnected) {
    console.error('WebSocket not connected');
    return;
  }

  // Build full message with file context
  let fullContent = content;
  if (state.pendingFiles.length > 0) {
    const fileContexts = state.pendingFiles.map(f => {
      if (f.parsed && f.content) {
        return `\n\n---\n📎 File: ${f.filename} (${f.file_type})\n\n${f.content}`;
      }
      return `\n\n---\n📎 File: ${f.filename} (${f.file_type}, parse failed)`;
    }).join('');
    fullContent = content + fileContexts;
    state.pendingFiles = [];
    updateFilePreview();
  }

  // Optimistic UI update
  state.messages.push({
    id: Date.now().toString(),
    role: 'user',
    content: content || '📎 Uploaded files',
    type: 'text',
    timestamp: Date.now(),
  });
  state.agentStatus = 'thinking';
  renderMessages();
  updateSendStopButton();

  agentWS.sendMessage(fullContent);
}

/** Dynamically swap the send/stop button without full re-render. */
function updateSendStopButton() {
  const isActive = state.agentStatus === 'thinking' || state.agentStatus === 'executing';

  // Find existing button (could be #btn-send or #btn-stop)
  const existing = document.getElementById('btn-send') || document.getElementById('btn-stop');
  if (!existing) return;

  const newBtn = document.createElement('button');
  if (isActive) {
    newBtn.className = 'btn-send btn-stop';
    newBtn.id = 'btn-stop';
    newBtn.title = 'Stop';
    newBtn.innerHTML = icons.stop;
    newBtn.addEventListener('click', () => {
      agentWS.sendStop();
      state.agentStatus = 'idle';
      updateSendStopButton();
    });
  } else {
    newBtn.className = 'btn-send';
    newBtn.id = 'btn-send';
    newBtn.innerHTML = icons.send;
    if (!state.isConnected) newBtn.disabled = true;
    newBtn.addEventListener('click', () => {
      const chatInput = document.getElementById('chat-input');
      if (chatInput) {
        const val = chatInput.value.trim();
        if (val || state.pendingFiles.length > 0) {
          sendMessage(val);
          chatInput.value = '';
          chatInput.style.height = 'auto';
        }
      }
    });
  }

  existing.replaceWith(newBtn);
}

function sendHumanResponse(content) {
  if (!content.trim()) return;
  agentWS.sendHumanResponse(content);

  state.messages.push({
    id: Date.now().toString(),
    role: 'user',
    content: content,
    type: 'text',
    timestamp: Date.now(),
  });
  renderMessages();
}

/* ============================================
   Renderers
   ============================================ */
function render() {
  const app = $('#app');
  if (state.currentView === 'login') {
    app.innerHTML = renderLoginPage();
    bindLoginEvents();
  } else {
    app.innerHTML = renderAppShell();
    bindAppEvents();
  }
  applyTheme(state.settings.theme);
}

function renderLoginPage() {
  return `
    <div class="login-page grid-bg">
      <div class="login-glow"></div>
      <div class="login-card">
        <div class="logo">M</div>
        <h1>${t('login.title')}</h1>
        <p class="subtitle">${t('login.subtitle')}</p>
        <div class="form-group">
          <label>${t('login.email')}</label>
          <input type="email" class="form-input" id="login-email" value="demo@example.com" placeholder="you@example.com">
        </div>
        <div class="form-group">
          <label>${t('login.password')}</label>
          <input type="password" class="form-input" id="login-password" value="demo" placeholder="••••••••">
        </div>
        <button class="btn-primary" id="btn-login">${t('login.signIn')}</button>
        <div class="divider">${t('login.or')}</div>
        <button class="btn-google" id="btn-google">
          <svg width="18" height="18" viewBox="0 0 24 24"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>
          ${t('login.google')}
        </button>
        <p class="login-terms">${t('login.terms')}</p>
      </div>
    </div>`;
}

function renderAppShell() {
  const sidebarClass = state.sidebarOpen ? 'sidebar open' : 'sidebar collapsed';
  const overlayClass = state.sidebarOpen ? 'sidebar-overlay visible' : 'sidebar-overlay';

  return `
    <div class="${overlayClass}" id="sidebar-overlay"></div>
    <nav class="${sidebarClass}" id="sidebar">
      ${renderSidebar()}
    </nav>
    <div class="main-content">
      ${state.currentView === 'chat' ? renderChatPage() : renderSettingsPage()}
    </div>`;
}

function renderSidebar() {
  const initial = (state.settings.name || 'D')[0].toUpperCase();
  const projectItems = state.projects.map(p => `
    <div class="project-item ${p.project_id === state.currentProjectId ? 'active' : ''}" data-project-id="${p.project_id}">
      <span class="icon">${icons.messageSquare}</span>
      <span class="truncate">${escapeHtml(p.title)}</span>
      <button class="project-delete-btn" data-delete-id="${p.project_id}" title="Delete project">${icons.x}</button>
    </div>
  `).join('');

  const settingsActive = state.currentView === 'settings' ? 'active' : '';

  return `
    <div class="sidebar-header">
      <div class="sidebar-brand">
        <div class="sidebar-logo">M</div>
        <span>MathModeler</span>
      </div>
      <button class="sidebar-toggle" id="btn-toggle-sidebar">${icons.layoutGrid}</button>
    </div>
    <button class="btn-new-project" id="btn-new-project">
      ${icons.plus} ${t('sidebar.newProject')}
    </button>
    <div class="sidebar-projects custom-scrollbar">
      ${projectItems || '<div style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 12px;">No projects yet</div>'}
    </div>
    <div class="sidebar-footer">
      <button class="sidebar-footer-btn ${settingsActive}" id="btn-settings">
        ${icons.settings} ${t('sidebar.settings')}
      </button>
      <div style="height: 1px; background: var(--border-color); margin: 4px 0;"></div>
      <div class="sidebar-user" id="btn-logout">
        <div class="user-avatar">${initial}</div>
        <div class="user-info">
          <div class="name">${escapeHtml(state.settings.name)}</div>
          <div class="plan">${t('sidebar.plan')}</div>
        </div>
        <span style="color: var(--text-muted); margin-left: auto;">${icons.logOut}</span>
      </div>
    </div>`;
}

function renderChatPage() {
  const connDot = state.isConnected
    ? `<span class="connection-dot connected"></span>${t('chat.connected')}`
    : `<span class="connection-dot disconnected"></span>${t('chat.connecting')}`;

  return `
    <header class="header-bar">
      <div class="header-left">
        <button class="header-btn" id="btn-menu">${icons.menu}</button>
        <span style="color: var(--border-color);">/</span>
        <span style="color: var(--text-primary); font-weight: 500; display: flex; align-items: center; gap: 4px;">
          ${connDot}
        </span>
      </div>
      <div class="header-right">
        <button class="header-btn" title="Zap">${icons.zap}</button>
        <button class="header-btn ${state.memoryPanelOpen ? 'active' : ''}" id="btn-memory" title="${t('chat.memory')}">${icons.brain}</button>
        <button class="header-btn" id="btn-header-settings" title="${t('sidebar.settings')}">${icons.settings}</button>
      </div>
    </header>
    <div class="chat-body">
      <div class="chat-messages-column">
        <div class="chat-scroll custom-scrollbar" id="chat-scroll">
          ${state.messages.length === 0 ? renderEmptyState() : renderMessageList()}
        </div>
        ${renderInputArea()}
      </div>
      ${renderSandboxPanel()}
    </div>
    <button class="sandbox-toggle-btn" id="btn-sandbox-toggle" title="${t('chat.toggleSandbox')}">
      ${icons.zap}
    </button>
    ${renderMemoryDrawer()}`;
}

function renderEmptyState() {
  return `
    <div class="empty-state">
      <h1>${t('chat.greeting')}</h1>
      <p class="subtitle">${t('chat.subtitle')}</p>
      <div class="suggestion-chips">
        <button class="chip" data-chip="${t('chat.chip1')}">${t('chat.chip1')}</button>
        <button class="chip" data-chip="${t('chat.chip2')}">${t('chat.chip2')}</button>
        <button class="chip" data-chip="${t('chat.chip3')}">${t('chat.chip3')}</button>
      </div>
    </div>`;
}

function renderMessageList() {
  let html = '<div class="messages-container">';

  // Group consecutive thought/tool_call messages
  const groups = [];
  let currentGroup = null;
  for (const msg of state.messages) {
    const isThoughtLike = msg.type === 'thought' || msg.type === 'tool_call';
    if (isThoughtLike) {
      if (!currentGroup) { currentGroup = []; groups.push(currentGroup); }
      currentGroup.push(msg);
    } else {
      if (currentGroup) { currentGroup = null; }
      groups.push(msg);
    }
  }

  const thoughtGroupCount = groups.filter(g => Array.isArray(g)).length;
  let thoughtGroupIdx = 0;

  for (const item of groups) {
    if (Array.isArray(item)) {
      // Collapsible thought/tool group
      thoughtGroupIdx++;
      const isLast = thoughtGroupIdx === thoughtGroupCount;
      const count = item.length;
      const lastMsg = item[item.length - 1];
      const summaryLabel = lastMsg.type === 'tool_call'
        ? `${count} ${t('chat.toolSteps')}`
        : `${count} ${t('chat.thoughtSteps')}`;
      html += `<details class="thought-group"${isLast ? ' open' : ''}>
        <summary class="thought-group-summary"><span class="icon">${icons.brain}</span> ${summaryLabel}</summary>
        <div class="thought-group-body">`;
      for (const msg of item) { html += renderMessage(msg); }
      html += `</div></details>`;
    } else {
      html += renderMessage(item);
    }
  }

  // Typing indicator
  if (state.agentStatus === 'thinking' || state.agentStatus === 'executing') {
    html += `
      <div class="typing-indicator">
        <div class="msg-avatar assistant">M</div>
        <div class="typing-label">
          <span class="spinner"></span>
          ${state.agentStatus === 'thinking' ? t('chat.thinking') : t('chat.executing')}
        </div>
      </div>`;
  }

  html += '<div id="messages-end" style="height: 16px;"></div></div>';
  return html;
}

function renderMessage(msg) {
  const isUser = msg.role === 'user';
  const rowClass = `message-row ${isUser ? 'user' : ''}`;
  const avatarClass = `msg-avatar ${isUser ? 'user' : 'assistant'}`;
  const avatarContent = isUser ? icons.user : 'M';
  const label = isUser ? t('sidebar.user') : 'MathModeler';

  let bubbleHtml = '';

  switch (msg.type) {
    case 'thought':
      bubbleHtml = `<div class="msg-thought"><span class="icon">${icons.brain}</span><span>${escapeHtml(msg.content)}</span></div>`;
      break;
    case 'tool_call':
      bubbleHtml = `
        <div class="msg-tool-call">
          <span class="icon">${icons.terminal}</span>
          <span class="tool-name">${escapeHtml(msg.toolName || 'tool')}</span>
          <span class="truncate" style="max-width: 180px; color: var(--text-muted); font-size: 12px;">${escapeHtml(msg.toolArgs || '')}</span>
          <span class="spinner"></span>
        </div>`;
      break;
    case 'ask_human':
      bubbleHtml = `
        <div class="msg-ask-human" data-msg-id="${msg.id}">
          <div class="question">${escapeHtml(msg.content)}</div>
          <div class="response-area">
            <input type="text" class="response-input" placeholder="${t('chat.replyPlaceholder')}" data-ask-id="${msg.id}">
            <button class="btn-respond" data-ask-id="${msg.id}">${t('chat.replySend')}</button>
          </div>
        </div>`;
      break;
    case 'error':
      bubbleHtml = `<div class="msg-error">⚠️ ${escapeHtml(msg.content)}</div>`;
      break;
    default:
      if (isUser) {
        bubbleHtml = `<div class="msg-bubble user">${escapeHtml(msg.content)}</div>`;
      } else {
        bubbleHtml = `<div class="msg-bubble assistant markdown-body">${renderMarkdown(msg.content)}</div>`;
      }
  }

  return `
    <div class="${rowClass}">
      <div class="${avatarClass}">${avatarContent}</div>
      <div class="msg-body">
        <div class="msg-label">${label}</div>
        ${bubbleHtml}
      </div>
    </div>`;
}

function renderInputArea() {
  return `
    <div class="input-area">
      <div class="input-container">
        <div class="input-wrapper">
          <div class="input-glow"></div>
          <div id="file-preview-bar" class="file-preview-bar" style="${state.pendingFiles.length === 0 ? 'display:none' : ''}"></div>
          <textarea id="chat-input" placeholder="${t('chat.placeholder')}" ${!state.isConnected ? 'disabled' : ''} rows="1"></textarea>
          <div class="input-actions">
            <div class="input-actions-left">
              <button class="input-action-btn" id="btn-attach" title="${t('chat.attach')}">${icons.paperclip}</button>
              <input type="file" id="file-input" accept=".pdf,.png,.jpg,.jpeg,.gif,.bmp,.webp,.txt,.md,.tex,.csv,.json,.py,.r,.m" multiple style="display:none">
              <button class="input-action-btn" title="${t('chat.search')}">${icons.search}</button>
            </div>
            ${(state.agentStatus === 'thinking' || state.agentStatus === 'executing')
      ? `<button class="btn-send btn-stop" id="btn-stop" title="${t('chat.stop')}">${icons.stop}</button>`
      : `<button class="btn-send" id="btn-send" ${!state.isConnected ? 'disabled' : ''}>${icons.send}</button>`
    }
          </div>
        </div>
      </div>
      <div class="input-disclaimer">${t('chat.disclaimer')}</div>
    </div>`;
}

/* ============================================
   File Upload
   ============================================ */
const FILE_TYPE_ICONS = {
  pdf: '📄',
  image: '🖼️',
  text: '📝',
};

async function uploadFile(file) {
  if (state.uploadingFile) return;
  state.uploadingFile = true;
  updateFilePreview();

  try {
    const result = await api.uploadFile(file);
    state.pendingFiles.push(result);
  } catch (e) {
    console.error('Upload failed:', e);
    showToast(`Upload failed: ${e.message}`, 'error');
    // Show inline error chip
    state.pendingFiles.push({
      file_id: 'err-' + Date.now(),
      filename: file.name,
      file_type: 'unknown',
      size: file.size,
      content: '',
      parsed: false,
      error: e.message,
    });
  } finally {
    state.uploadingFile = false;
    updateFilePreview();
  }
}

function updateFilePreview() {
  const bar = document.getElementById('file-preview-bar');
  if (!bar) return;

  if (state.pendingFiles.length === 0 && !state.uploadingFile) {
    bar.style.display = 'none';
    bar.innerHTML = '';
    return;
  }

  bar.style.display = 'flex';
  let html = '';

  // Show uploading indicator
  if (state.uploadingFile) {
    html += `<div class="file-chip file-chip-loading">
      <span class="file-chip-spinner"></span>
      <span>Uploading...</span>
    </div>`;
  }

  // Render attached files
  state.pendingFiles.forEach((f, idx) => {
    const icon = FILE_TYPE_ICONS[f.file_type] || '📎';
    const sizeKB = f.size ? (f.size / 1024).toFixed(1) + ' KB' : '';
    const status = f.parsed ? '✓' : (f.error ? '✗' : '…');
    const statusClass = f.parsed ? 'file-chip-ok' : (f.error ? 'file-chip-err' : '');
    html += `<div class="file-chip ${statusClass}" title="${f.error || sizeKB}">
      <span class="file-chip-icon">${icon}</span>
      <span class="file-chip-name">${escapeHtml(f.filename)}</span>
      <span class="file-chip-status">${status}</span>
      <button class="file-chip-remove" data-file-idx="${idx}">${icons.x}</button>
    </div>`;
  });

  bar.innerHTML = html;

  // Bind remove buttons
  bar.querySelectorAll('.file-chip-remove').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.fileIdx);
      state.pendingFiles.splice(idx, 1);
      updateFilePreview();
    });
  });
}

/* ============================================
   Problem Understanding Panel
   ============================================ */
function renderProblemUnderstanding() {
  const pu = state.sandbox.problemUnderstanding;
  if (!pu) return '';

  const expanded = state.sandbox.probPanelExpanded;
  const typeColors = {
    '优化问题': 'prob-type-opt',
    '预测问题': 'prob-type-pred',
    '模拟问题': 'prob-type-sim',
    '评价问题': 'prob-type-eval',
  };
  const typeClass = typeColors[pu.type] || 'prob-type-opt';
  const conf = Math.round((pu.confidence || 0) * 100);

  const vars = (pu.variables || []).map(v => `<span class="prob-chip prob-chip-var">${escapeHtml(v)}</span>`).join('');
  const cons = (pu.constraints || []).map(c => `<span class="prob-chip prob-chip-con">${escapeHtml(c)}</span>`).join('');
  const tools = (pu.tools || []).map(t => `<span class="prob-chip prob-chip-tool">${escapeHtml(t)}</span>`).join('');

  return `
    <div class="prob-panel ${expanded ? 'expanded' : ''}" id="prob-panel">
      <div class="prob-panel-head" id="prob-panel-toggle">
        <span class="prob-type-badge ${typeClass}">${escapeHtml(pu.type || '问题分析')}</span>
        <span class="prob-summary">${(pu.variables || []).length} 变量 · ${(pu.constraints || []).length} 约束</span>
        <span class="prob-conf-badge">${conf}%</span>
        <svg class="prob-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <div class="prob-panel-body">
        <div class="prob-panel-inner">
          <div class="prob-section">
            <div class="prob-section-label">决策变量</div>
            <div class="prob-chips">${vars || '<span style="color:var(--text-muted);font-size:11px">暂无</span>'}</div>
          </div>
          <div class="prob-section">
            <div class="prob-section-label">约束条件</div>
            <div class="prob-chips">${cons || '<span style="color:var(--text-muted);font-size:11px">暂无</span>'}</div>
          </div>
          <div class="prob-section">
            <div class="prob-section-label">候选工具</div>
            <div class="prob-chips">${tools || '<span style="color:var(--text-muted);font-size:11px">暂无</span>'}</div>
            <div class="prob-conf-bar-wrap">
              <div class="prob-conf-row"><span>置信度</span><span>${conf}%</span></div>
              <div class="prob-conf-track"><div class="prob-conf-fill" style="width:${conf}%"></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>`;
}

/* ============================================
   Memory Drawer
   ============================================ */
function renderMemoryDrawer() {
  const layers = state.memoryLayers || {
    working:  { vars: [], usage: 0 },
    session:  { items: [], usage: 0 },
    project:  { items: [], usage: 0 },
    longterm: { items: [], count: 0, usage: 0 },
  };

  const mkItems = (arr) => (arr || []).slice(0, 3).map(i =>
    `<div class="mem-item"><div class="mem-item-dot"></div><span>${escapeHtml(String(i))}</span></div>`
  ).join('') || '<div style="font-size:11px;color:var(--text-muted);padding:4px 0">暂无数据</div>';

  return `
    <div class="mem-overlay ${state.memoryPanelOpen ? 'open' : ''}" id="mem-overlay"></div>
    <div class="mem-drawer ${state.memoryPanelOpen ? 'open' : ''}" id="mem-drawer">
      <div class="mem-drawer-head">
        <div>
          <div class="mem-drawer-title">记忆层状态</div>
          <div class="mem-drawer-sub">4 层 · 实时同步</div>
        </div>
        <button class="mem-close-btn" id="btn-mem-close">✕</button>
      </div>
      <div class="mem-drawer-body" id="memory-drawer-body">
        <div class="mem-card">
          <div class="mem-card-head">
            <div class="mem-icon mem-icon-working">⚡</div>
            <div class="mem-info"><div class="mem-name">工作记忆</div><div class="mem-desc">沙盒变量 · 步骤级</div></div>
            <span class="mem-count mem-count-working">${(layers.working.vars || []).length} vars</span>
          </div>
          <div class="mem-items">${mkItems(layers.working.vars)}</div>
          <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-working" style="width:${layers.working.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.working.usage || 0}%</span></div>
        </div>
        <div class="mem-card">
          <div class="mem-card-head">
            <div class="mem-icon mem-icon-session">🔮</div>
            <div class="mem-info"><div class="mem-name">阶段记忆</div><div class="mem-desc">本阶段关键发现</div></div>
            <span class="mem-count mem-count-session">${(layers.session.items || []).length} 条</span>
          </div>
          <div class="mem-items">${mkItems(layers.session.items)}</div>
          <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-session" style="width:${layers.session.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.session.usage || 0}%</span></div>
        </div>
        <div class="mem-card">
          <div class="mem-card-head">
            <div class="mem-icon mem-icon-project">📌</div>
            <div class="mem-info"><div class="mem-name">项目记忆</div><div class="mem-desc">题目约束 · 模型决策</div></div>
            <span class="mem-count mem-count-project">${(layers.project.items || []).length} 条</span>
          </div>
          <div class="mem-items">${mkItems(layers.project.items)}</div>
          <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-project" style="width:${layers.project.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.project.usage || 0}%</span></div>
        </div>
        <div class="mem-card">
          <div class="mem-card-head">
            <div class="mem-icon mem-icon-longterm">🧠</div>
            <div class="mem-info"><div class="mem-name">长期记忆</div><div class="mem-desc">历史竞赛经验</div></div>
            <span class="mem-count mem-count-longterm">${layers.longterm.count || 0} 条</span>
          </div>
          <div class="mem-items">${mkItems(layers.longterm.items)}</div>
          <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-longterm" style="width:${layers.longterm.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.longterm.usage || 0}%</span></div>
        </div>
      </div>
    </div>`;
}

function renderMemoryDrawerBody(el) {
  const layers = state.memoryLayers || {
    working:  { vars: [], usage: 0 },
    session:  { items: [], usage: 0 },
    project:  { items: [], usage: 0 },
    longterm: { items: [], count: 0, usage: 0 },
  };
  const mkItems = (arr) => (arr || []).slice(0, 3).map(i =>
    `<div class="mem-item"><div class="mem-item-dot"></div><span>${escapeHtml(String(i))}</span></div>`
  ).join('') || '<div style="font-size:11px;color:var(--text-muted);padding:4px 0">暂无数据</div>';

  el.innerHTML = `
    <div class="mem-card">
      <div class="mem-card-head">
        <div class="mem-icon mem-icon-working">⚡</div>
        <div class="mem-info"><div class="mem-name">工作记忆</div><div class="mem-desc">沙盒变量 · 步骤级</div></div>
        <span class="mem-count mem-count-working">${(layers.working.vars || []).length} vars</span>
      </div>
      <div class="mem-items">${mkItems(layers.working.vars)}</div>
      <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-working" style="width:${layers.working.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.working.usage || 0}%</span></div>
    </div>
    <div class="mem-card">
      <div class="mem-card-head">
        <div class="mem-icon mem-icon-session">🔮</div>
        <div class="mem-info"><div class="mem-name">阶段记忆</div><div class="mem-desc">本阶段关键发现</div></div>
        <span class="mem-count mem-count-session">${(layers.session.items || []).length} 条</span>
      </div>
      <div class="mem-items">${mkItems(layers.session.items)}</div>
      <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-session" style="width:${layers.session.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.session.usage || 0}%</span></div>
    </div>
    <div class="mem-card">
      <div class="mem-card-head">
        <div class="mem-icon mem-icon-project">📌</div>
        <div class="mem-info"><div class="mem-name">项目记忆</div><div class="mem-desc">题目约束 · 模型决策</div></div>
        <span class="mem-count mem-count-project">${(layers.project.items || []).length} 条</span>
      </div>
      <div class="mem-items">${mkItems(layers.project.items)}</div>
      <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-project" style="width:${layers.project.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.project.usage || 0}%</span></div>
    </div>
    <div class="mem-card">
      <div class="mem-card-head">
        <div class="mem-icon mem-icon-longterm">🧠</div>
        <div class="mem-info"><div class="mem-name">长期记忆</div><div class="mem-desc">历史竞赛经验</div></div>
        <span class="mem-count mem-count-longterm">${layers.longterm.count || 0} 条</span>
      </div>
      <div class="mem-items">${mkItems(layers.longterm.items)}</div>
      <div class="mem-bar-row"><div class="mem-bar-track"><div class="mem-bar-fill mem-bar-longterm" style="width:${layers.longterm.usage || 0}%"></div></div><span class="mem-bar-pct">${layers.longterm.usage || 0}%</span></div>
    </div>`;
}

function renderPhaseStepper() {
  const allPhases = [
    { id: 'inception', label: '破题' },
    { id: 'blueprinting', label: '建模' },
    { id: 'coding', label: '代码' },
    { id: 'writing', label: '论文' },
  ];
  if (state.sandbox.phases.length === 0) return '';
  return `<div class="phase-stepper">
    ${allPhases.map((p, i) => {
      const found = state.sandbox.phases.find(sp => sp.name === p.id);
      const status = found ? found.status : 'pending';
      const cls = status === 'completed' ? 'done' : status === 'running' ? 'active' : 'pending';
      return `<div class="phase-step ${cls}">
        <div class="phase-step-dot">${status === 'completed' ? '✓' : i + 1}</div>
        <div class="phase-step-label">${p.label}</div>
      </div>${i < allPhases.length - 1 ? '<div class="phase-step-line"></div>' : ''}`;
    }).join('')}
  </div>`;
}

function renderSandboxPanel() {
  const tabs = [
    { id: 'timeline', label: t('sandbox.timeline'), badge: state.sandbox.phases.reduce((n, p) => n + p.steps.length, 0) },
    { id: 'code', label: t('sandbox.code'), badge: getRenderableCodeFiles().length },
    { id: 'document', label: t('sandbox.document'), badge: state.sandbox.documentContent ? 1 : 0 },
    { id: 'files', label: t('sandbox.files'), badge: state.artifacts.length },
  ];

  const tabBar = tabs.map(tab => `
    <div class="sandbox-tab ${state.sandbox.activeTab === tab.id ? 'active' : ''}" data-tab="${tab.id}">
      ${tab.label}
      ${tab.badge > 0 ? `<span class="tab-badge">${tab.badge}</span>` : ''}
    </div>`).join('');

  return `
    <div class="sandbox-panel ${state.sandbox.sandboxOpen ? 'open' : ''}">
      <div class="sandbox-resize-handle" id="sandbox-resize"></div>
      ${renderProblemUnderstanding()}
      ${renderPhaseStepper()}
      <div class="sandbox-tabs">${tabBar}</div>
      <div class="sandbox-content">
        <div class="sandbox-tab-content ${state.sandbox.activeTab === 'timeline' ? 'active' : ''}" data-tab-content="timeline">
          ${renderTimelineTab()}
        </div>
        <div class="sandbox-tab-content ${state.sandbox.activeTab === 'code' ? 'active' : ''}" data-tab-content="code">
          ${renderCodeTab()}
        </div>
        <div class="sandbox-tab-content ${state.sandbox.activeTab === 'document' ? 'active' : ''}" data-tab-content="document">
          ${renderDocumentTab()}
        </div>
        <div class="sandbox-tab-content ${state.sandbox.activeTab === 'files' ? 'active' : ''}" data-tab-content="files">
          ${renderFilesTab()}
        </div>
      </div>
    </div>`;
}

function stripMarkdown(str) {
  return str
    .replace(/#{1,6}\s*/g, '')
    .replace(/\*\*|__|\*|_|~~|`/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/^\s*[-*>]\s*/gm, '')
    .replace(/\n+/g, ' ')
    .trim();
}

function inferCodeLanguage(content = '') {
  const source = content.toLowerCase();
  if (source.includes('import ') || source.includes('def ') || source.includes('print(')) return 'python';
  if (source.includes('{') && source.includes('}') && source.includes('"')) return 'json';
  return 'text';
}

function codeFileExtension(language = '') {
  if (language === 'python') return 'py';
  if (language === 'json') return 'json';
  if (language === 'javascript') return 'js';
  if (language === 'typescript') return 'ts';
  return 'txt';
}

function extractCodeFilesFromArtifact(content = '', baseName = 'code') {
  const blocks = [];
  const fenceRe = /```([a-zA-Z0-9_+-]*)\n([\s\S]*?)```/g;
  let match;
  let idx = 0;

  while ((match = fenceRe.exec(content)) !== null) {
    const lang = (match[1] || '').trim().toLowerCase();
    const blockContent = (match[2] || '').trim();
    if (!blockContent) continue;
    const language = lang || inferCodeLanguage(blockContent);
    const ext = codeFileExtension(language);
    idx += 1;
    blocks.push({
      name: `${baseName}_${idx}.${ext}`,
      content: blockContent,
      language,
    });
  }

  if (blocks.length > 0) return blocks;

  const maybeCode = content.trim();
  if (!maybeCode) return [];

  return [{
    name: `${baseName}_1.${codeFileExtension(inferCodeLanguage(maybeCode))}`,
    content: maybeCode,
    language: inferCodeLanguage(maybeCode),
  }];
}

function getCodeFilesFromArtifact(artifactType, content) {
  if (artifactType !== 'code') return [];
  return extractCodeFilesFromArtifact(content, 'code');
}

function getPrimaryCodeLanguage(files = []) {
  const preferred = ['python', 'json', 'javascript', 'typescript'];
  for (const language of preferred) {
    if (files.some(file => file.language === language)) return language;
  }
  return files[0]?.language || 'text';
}

function getRenderableCodeFiles() {
  return state.sandbox.codeFiles.filter(f => f.language && f.language !== 'markdown');
}

function getPhaseConfirmMeta() {
  if (!state.phaseConfirmPending || !state.phaseConfirmData) return null;

  const phaseNames = { inception: '破题分析', blueprinting: '建模方案', coding: '代码实现', writing: '论文撰写' };
  const nextPhaseMap = { inception: 'blueprinting', blueprinting: 'coding', coding: 'writing' };
  const currentLabel = phaseNames[state.phaseConfirmData.phase] || state.phaseConfirmData.phase;
  const nextLabel = phaseNames[nextPhaseMap[state.phaseConfirmData.phase]] || '下一阶段';
  const summaryRaw = stripMarkdown(state.phaseConfirmData.summary || '').slice(0, 150);

  return {
    currentLabel,
    nextLabel,
    summary: summaryRaw || `${currentLabel} 已完成，可继续进入 ${nextLabel}。`,
  };
}

function renderPhaseConfirmCard(variant = 'chat') {
  const meta = getPhaseConfirmMeta();
  if (!meta) return '';

  return `<div class="phase-confirm-card ${variant === 'timeline' ? 'timeline-phase-confirm-card' : ''}">
    <div class="phase-confirm-title">✅ ${meta.currentLabel} 阶段完成</div>
    <div class="phase-confirm-summary">${escapeHtml(meta.summary)}${meta.summary.length >= 150 ? '…' : ''}</div>
    <button class="phase-confirm-btn" data-phase-confirm="true">进入${meta.nextLabel}阶段 →</button>
  </div>`;
}

function renderTimelineTab() {
  if (state.sandbox.phases.length === 0) {
    return `<div class="timeline-empty">
      <div class="icon">⏱️</div>
      <div>${t('sandbox.timelineEmptyTitle')}</div>
      <div style="font-size:11px;">${t('sandbox.timelineEmptySubtitle')}</div>
    </div>`;
  }

  const phaseIcons = { inception: '🔍', blueprinting: '📐', coding: '💻', writing: '📝' };
  const phaseLabels = { inception: '破题分析', blueprinting: '建模方案', coding: '代码实现', writing: '论文撰写' };
  const phaseConfirmCard = renderPhaseConfirmCard('timeline');

  return `<div class="timeline-container custom-scrollbar">
    ${phaseConfirmCard}
    ${state.sandbox.phases.map(phase => {
    const completedCount = phase.steps.filter(s => s.status === 'completed').length;
    const phaseStatusCls = phase.status === 'running' ? 'running' : phase.status === 'completed' ? 'completed' : 'pending';

    return `
      <div class="tl-phase ${phaseStatusCls}">
        <div class="tl-phase-header">
          <div class="tl-phase-icon ${phase.name}">${phaseIcons[phase.name] || '📋'}</div>
          <div class="tl-phase-name">${phaseLabels[phase.name] || phase.name}</div>
          <div class="tl-phase-progress">${completedCount}/${phase.steps.length}</div>
          ${phase.status === 'completed' ? '<span class="tl-phase-done">✓</span>' : ''}
        </div>
        <div class="tl-steps">
          ${phase.steps.map((step, i) => {
      const key = `${phase.name}_${i}`;
      const evalEntries = state.sandbox.evalLoops[key] || [];
      const statusCls = step.status === 'completed' ? 'completed' : step.status === 'running' ? 'active' : 'pending';
      const iconHtml = step.status === 'completed' ? '✓' : step.status === 'running' ? '⟳' : String(i + 1);
      const titleText = stripMarkdown(step.title) || step.title;
      const resultText = stripMarkdown(step.result || '');
      const metaText = resultText ? `${resultText.slice(0, 80)}${resultText.length > 80 ? '…' : ''}` : '';
      const shouldAutoOpen = step.status === 'running' || evalEntries.length > 0;

      const evalHtml = evalEntries.length > 0 ? `
        <div class="tl-eval-loop">
          ${evalEntries.map(e => `
            <div class="tl-eval-step tl-eval-${e.tag.toLowerCase()}">
              <span class="tl-eval-tag">${e.tag}</span>
              <span class="tl-eval-text">${escapeHtml(e.text)}</span>
            </div>`).join('')}
        </div>` : '';

      return `
        <div class="tl-step ${statusCls} ${shouldAutoOpen ? 'open' : ''}" data-step-key="${key}">
          <div class="tl-step-head">
            <div class="tl-step-icon ${statusCls}">${iconHtml}</div>
            <div class="tl-step-info">
              <div class="tl-step-title">${escapeHtml(titleText)}</div>
              ${metaText ? `<div class="tl-step-meta">${escapeHtml(metaText)}</div>` : ''}
            </div>
            ${metaText || evalEntries.length > 0 ? `<svg class="tl-step-chevron" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>` : ''}
          </div>
          ${evalHtml}
        </div>`;
    }).join('')}
        </div>
      </div>`;
  }).join('')}
  </div>`;
}

function renderCodeTab() {
  const codeFiles = getRenderableCodeFiles();

  if (codeFiles.length === 0) {
    return `<div class="code-empty">
      <div class="icon">💻</div>
      <div>${t('sandbox.codeEmptyTitle')}</div>
      <div style="font-size:11px;">${t('sandbox.codeEmptySubtitle')}</div>
    </div>`;
  }

  const selectedIdx = Math.min(state.sandbox.selectedFileIndex, codeFiles.length - 1);
  const selectedFile = codeFiles[selectedIdx] || codeFiles[0];
  const lang = selectedFile.language || getPrimaryCodeLanguage(codeFiles);

  const fileTabs = codeFiles.map((f, i) => `
    <div class="code-file-tab ${i === selectedIdx ? 'active' : ''}" data-file-idx="${i}">
      <span class="file-dot ${f.language}"></span>
      ${escapeHtml(f.name)}
    </div>`).join('');

  // Use Prism.js for highlighting if available
  let highlightedCode = escapeHtml(selectedFile.content);
  if (typeof Prism !== 'undefined' && Prism.languages[lang]) {
    try {
      highlightedCode = Prism.highlight(selectedFile.content, Prism.languages[lang], lang);
    } catch (e) { /* fallback to escaped */ }
  }

  return `<div class="code-container">
    <div class="code-file-tabs">${fileTabs}</div>
    <div class="code-editor custom-scrollbar">
      <pre><code class="language-${lang}">${highlightedCode}</code></pre>
    </div>
  </div>`;
}

function renderDocumentTab() {
  if (!state.sandbox.documentContent) {
    return `<div class="document-empty">
      <div class="icon">📄</div>
      <div>${t('sandbox.documentEmptyTitle')}</div>
      <div style="font-size:11px;">${t('sandbox.documentEmptySubtitle')}</div>
    </div>`;
  }

  // Use Marked.js for markdown rendering if available
  let renderedHtml = escapeHtml(state.sandbox.documentContent);
  if (typeof marked !== 'undefined') {
    try {
      renderedHtml = marked.parse(state.sandbox.documentContent);
    } catch (e) { /* fallback */ }
  }

  return `<div class="document-container custom-scrollbar">
    <div class="document-viewer">${renderedHtml}</div>
  </div>`;
}

function renderFilesTab() {
  if (state.artifacts.length === 0 && state.sandbox.codeFiles.length === 0) {
    return `<div class="files-empty">
      <div class="icon">📁</div>
      <div>${t('sandbox.filesEmptyTitle')}</div>
      <div style="font-size:11px;">${t('sandbox.filesEmptySubtitle')}</div>
    </div>`;
  }

  const typeIcons = { report: '📊', blueprint: '📐', code: '💻', paper: '📝' };
  const typeNames = {
    report: t('artifact.report'),
    blueprint: t('artifact.blueprint'),
    code: t('artifact.code'),
    paper: t('artifact.paper'),
  };

  // Combine API artifacts + sandbox code files
  const items = state.artifacts.map(a => {
    const artType = a.type || a.artifact_type || 'unknown';
    return `
      <div class="file-tree-item" data-artifact-type="${artType}" data-artifact-id="${a.id}">
        <div class="file-icon ${artType}">${typeIcons[artType] || '📄'}</div>
        <div class="file-info">
          <div class="file-name">${typeNames[artType] || artType}</div>
          <div class="file-meta">v${a.version} · ${a.frozen ? `🔒 ${t('artifact.frozen')}` : `✏️ ${t('artifact.draft')}`}</div>
        </div>
        <span class="file-badge ${artType}">${artType}</span>
      </div>`;
  }).join('');

  return `<div class="files-container custom-scrollbar">${items}</div>`;
}

function renderSettingsPage() {
  const s = state.settings;
  const initial = (s.name || 'D')[0].toUpperCase();

  return `
    <header class="header-bar">
      <div class="header-left">
        <button class="header-btn" id="btn-menu">${icons.menu}</button>
        <span style="color: var(--border-color);">/</span>
        <span style="color: var(--text-primary); font-weight: 500;">${t('settings.title')}</span>
      </div>
      <div class="header-right">
        <button class="header-btn" id="btn-back-chat" style="font-size: 12px; color: var(--text-muted);">${t('settings.backToChat')}</button>
      </div>
    </header>
    <div class="settings-page custom-scrollbar">
      <div class="settings-content">
        <!-- Account -->
        <div class="settings-section">
          <div class="settings-section-header"><span class="icon">${icons.user}</span> ${t('settings.account')}</div>
          <div class="settings-section-body">
            <div class="settings-avatar">
              <div class="avatar-circle">${initial}</div>
              <button class="btn-change">${t('settings.changeAvatar')}</button>
            </div>
            <div class="settings-row">
              <span class="label">${t('settings.name')}</span>
              <input type="text" id="setting-name" value="${escapeHtml(s.name)}">
            </div>
            <div class="settings-row">
              <span class="label">${t('settings.email')}</span>
              <input type="email" id="setting-email" value="${escapeHtml(s.email)}">
            </div>
          </div>
        </div>

        <!-- General -->
        <div class="settings-section">
          <div class="settings-section-header"><span class="icon">${icons.monitor}</span> ${t('settings.general')}</div>
          <div class="settings-section-body">
            <div class="settings-row">
              <span class="label">${t('settings.theme')}</span>
              <select id="setting-theme">
                <option value="light" ${s.theme === 'light' ? 'selected' : ''}>Light</option>
                <option value="dark" ${s.theme === 'dark' ? 'selected' : ''}>Dark</option>
                <option value="system" ${s.theme === 'system' ? 'selected' : ''}>System</option>
              </select>
            </div>
            <div class="settings-row">
              <span class="label">${t('settings.language')}</span>
              <select id="setting-language">
                <option value="English" ${s.language === 'English' ? 'selected' : ''}>English</option>
                <option value="Chinese" ${s.language === 'Chinese' ? 'selected' : ''}>中文</option>
              </select>
            </div>
          </div>
        </div>

        <!-- AI Configuration -->
        <div class="settings-section">
          <div class="settings-section-header"><span class="icon">${icons.cpu}</span> ${t('settings.aiConfig')}</div>
          <div class="settings-section-body">
            <div class="settings-row">
              <span class="label">${t('settings.model')}</span>
              <select id="setting-model">
                <option value="gpt-4o" ${s.model === 'gpt-4o' ? 'selected' : ''}>GPT-4o</option>
                <option value="deepseek-chat" ${s.model === 'deepseek-chat' ? 'selected' : ''}>DeepSeek Chat</option>
                <option value="qwen-max" ${s.model === 'qwen-max' ? 'selected' : ''}>Qwen Max</option>
                <option value="doubao-pro-32k" ${s.model === 'doubao-pro-32k' ? 'selected' : ''}>Doubao Pro</option>
              </select>
            </div>
            <div class="settings-row">
              <span class="label">${t('settings.temperature')}</span>
              <div class="settings-slider">
                <input type="range" id="setting-temperature" min="0" max="1" step="0.1" value="${s.temperature}">
                <span class="value" id="temperature-value">${s.temperature}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Notifications -->
        <div class="settings-section">
          <div class="settings-section-header"><span class="icon">${icons.bell}</span> ${t('settings.notifications')}</div>
          <div class="settings-section-body">
            <div class="settings-row">
              <span class="label">${t('settings.marketing')}</span>
              <div class="toggle ${s.marketingEmails ? 'active' : ''}" id="toggle-marketing"><div class="knob"></div></div>
            </div>
            <div class="settings-row">
              <span class="label">${t('settings.security')}</span>
              <div class="toggle ${s.securityAlerts ? 'active' : ''}" id="toggle-security"><div class="knob"></div></div>
            </div>
          </div>
        </div>

        <!-- Billing -->
        <div class="settings-section">
          <div class="settings-section-header"><span class="icon">${icons.creditCard}</span> ${t('settings.billing')}</div>
          <div class="settings-section-body">
            <div style="padding: 8px 0; color: var(--text-secondary); font-size: 13px;">${state.settings.language === 'Chinese' ? '免费版 · Beta 期间不限量' : 'Free Plan - Unlimited during beta'}</div>
          </div>
        </div>

        <!-- Danger Zone -->
        <div class="settings-section danger-section">
          <div class="settings-section-header"><span class="icon">${icons.shield}</span> ${t('settings.danger')}</div>
          <div class="settings-section-body">
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px;">${t('settings.deleteWarning')}</p>
            <button class="btn-danger">${t('settings.deleteAccount')}</button>
          </div>
        </div>
      </div>
    </div>`;
}

/** Partial re-render of just the sandbox panel (avoids full re-render). */
function renderSandboxPanelOnly() {
  const panel = document.querySelector('.sandbox-panel');
  if (!panel) return;
  const temp = document.createElement('div');
  temp.innerHTML = renderSandboxPanel();
  const newPanel = temp.firstElementChild;
  if (!newPanel) return;
  panel.replaceWith(newPanel);
  bindSandboxEvents();
  // Re-render KaTeX in document tab if visible
  if (state.sandbox.activeTab === 'document' && typeof renderMathInElement !== 'undefined') {
    const docViewer = newPanel.querySelector('.document-viewer');
    if (docViewer) {
      try {
        renderMathInElement(docViewer, {
          delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false },
            { left: '\\(', right: '\\)', display: false },
            { left: '\\[', right: '\\]', display: true },
          ]
        });
      } catch (e) { }
    }
  }
}

/* ============================================
   Partial Render: Messages Only
   ============================================ */
function renderMessages() {
  const scroll = $('#chat-scroll');
  if (!scroll) return; // Not on chat view — state is already updated, will render on next navigate('chat')
  const phaseConfirmCard = renderPhaseConfirmCard('chat');
  let html = '';

  if (state.messages.length === 0) {
    html = phaseConfirmCard
      ? `<div class="messages-container messages-container-phase-confirm">${phaseConfirmCard}</div>`
      : renderEmptyState();
  } else {
    html = renderMessageList();
    if (phaseConfirmCard) html += phaseConfirmCard;
  }

  scroll.innerHTML = html;

  // Post-process assistant markdown messages (Prism + KaTeX)
  scroll.querySelectorAll('.msg-bubble.assistant.markdown-body').forEach(postProcessMessage);

  scrollToBottom();
  bindMessageEvents();
  updateConnectionStatus();
  scroll.querySelectorAll('[data-phase-confirm="true"]').forEach(confirmBtn => {
    confirmBtn.addEventListener('click', () => {
      state.phaseConfirmPending = false;
      state.phaseConfirmData = null;
      agentWS.sendPhaseConfirm();
      renderMessages();
      renderSandboxPanelOnly();
    });
  });
}

function scrollToBottom(force) {
  const scroll = $('#chat-scroll');
  if (!scroll) return;
  if (force || !state._userScrolledUp) {
    const end = $('#messages-end');
    if (end) end.scrollIntoView({ behavior: 'smooth' });
    // Remove indicator if present
    const indicator = scroll.querySelector('.scroll-indicator');
    if (indicator) indicator.remove();
  } else {
    // Show "New messages" pill if user is scrolled up
    if (!scroll.querySelector('.scroll-indicator')) {
      const pill = document.createElement('button');
      pill.className = 'scroll-indicator';
      pill.textContent = 'New messages ↓';
      pill.addEventListener('click', () => {
        state._userScrolledUp = false;
        scrollToBottom(true);
      });
      scroll.appendChild(pill);
    }
  }
}

function updateConnectionStatus() {
  // Minimal update without full re-render
}

/** Bind sandbox panel interactive events. */
function bindSandboxEvents() {
  // Problem Understanding panel toggle
  const probToggle = document.getElementById('prob-panel-toggle');
  if (probToggle) {
    probToggle.addEventListener('click', () => {
      state.sandbox.probPanelExpanded = !state.sandbox.probPanelExpanded;
      document.getElementById('prob-panel')?.classList.toggle('expanded', state.sandbox.probPanelExpanded);
    });
  }

  // Memory panel toggle (header button)
  document.getElementById('btn-memory')?.addEventListener('click', () => {
    state.memoryPanelOpen = !state.memoryPanelOpen;
    document.getElementById('mem-overlay')?.classList.toggle('open', state.memoryPanelOpen);
    document.getElementById('mem-drawer')?.classList.toggle('open', state.memoryPanelOpen);
    document.getElementById('btn-memory')?.classList.toggle('active', state.memoryPanelOpen);
  });
  document.getElementById('mem-overlay')?.addEventListener('click', () => {
    state.memoryPanelOpen = false;
    document.getElementById('mem-overlay')?.classList.remove('open');
    document.getElementById('mem-drawer')?.classList.remove('open');
    document.getElementById('btn-memory')?.classList.remove('active');
  });
  document.getElementById('btn-mem-close')?.addEventListener('click', () => {
    state.memoryPanelOpen = false;
    document.getElementById('mem-overlay')?.classList.remove('open');
    document.getElementById('mem-drawer')?.classList.remove('open');
    document.getElementById('btn-memory')?.classList.remove('active');
  });

  // Timeline step expand (click on tl-step)
  document.querySelectorAll('.tl-step').forEach(step => {
    step.addEventListener('click', () => step.classList.toggle('open'));
  });
  document.querySelectorAll('[data-phase-confirm="true"]').forEach(btn => {
    btn.addEventListener('click', () => {
      state.phaseConfirmPending = false;
      state.phaseConfirmData = null;
      agentWS.sendPhaseConfirm();
      renderMessages();
      renderSandboxPanelOnly();
    });
  });
  document.querySelectorAll('.sandbox-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      state.sandbox.activeTab = tab.dataset.tab;
      renderSandboxPanelOnly();
    });
  });

  // Code file tab switching
  document.querySelectorAll('.code-file-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      state.sandbox.selectedFileIndex = parseInt(tab.dataset.fileIdx, 10) || 0;
      renderSandboxPanelOnly();
    });
  });

  // (timeline-step legacy removed — now using tl-step)

  // Files tab: click to view artifact in document/code tab
  document.querySelectorAll('.file-tree-item').forEach(item => {
    item.addEventListener('click', () => {
      const artType = item.dataset.artifactType;
      if (artType === 'code') {
        state.sandbox.activeTab = 'code';
      } else {
        // Show content in document tab
        const artifact = state.artifacts.find(a => a.id === item.dataset.artifactId);
        if (artifact) {
          state.sandbox.documentContent = artifact.content || '';
          state.sandbox.activeTab = 'document';
        }
      }
      renderSandboxPanelOnly();
    });
  });

  // Sandbox panel resize drag
  const resizeHandle = document.getElementById('sandbox-resize');
  if (resizeHandle) {
    let dragging = false;
    resizeHandle.addEventListener('mousedown', (e) => {
      e.preventDefault();
      dragging = true;
      resizeHandle.classList.add('active');
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    });
    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const panel = document.querySelector('.sandbox-panel');
      if (!panel) return;
      const newWidth = window.innerWidth - e.clientX;
      const clamped = Math.max(320, Math.min(newWidth, window.innerWidth * 0.58));
      panel.style.flex = 'none';
      panel.style.width = clamped + 'px';
    });
    document.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      resizeHandle.classList.remove('active');
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    });
  }
}

/* ============================================
   Event Binding
   ============================================ */
function bindLoginEvents() {
  const btnLogin = $('#btn-login');
  const btnGoogle = $('#btn-google');

  const doLogin = async (btn) => {
    if (btn) { btn.disabled = true; btn.textContent = t('chat.loginLoading'); }
    try {
      state.settings.email = $('#login-email')?.value || 'demo@example.com';
      await loadProjects();
      if (state.projects.length > 0) {
        await selectProject(state.projects[0].project_id);
      } else {
        await createNewProject();
      }
    } catch (e) {
      showToast(t('chat.loginFailed'), 'error');
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = t('login.signIn'); }
    }
  };

  btnLogin?.addEventListener('click', () => doLogin(btnLogin));
  btnGoogle?.addEventListener('click', () => doLogin(btnGoogle));
}

/** Toggle sidebar via DOM class manipulation (no full re-render). */
function toggleSidebarDOM(open) {
  state.sidebarOpen = typeof open === 'boolean' ? open : !state.sidebarOpen;
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar) {
    sidebar.classList.toggle('open', state.sidebarOpen);
    sidebar.classList.toggle('collapsed', !state.sidebarOpen);
  }
  if (overlay) overlay.classList.toggle('visible', state.sidebarOpen);
}

function bindAppEvents() {
  // Sidebar overlay
  $('#sidebar-overlay')?.addEventListener('click', () => toggleSidebarDOM(false));

  // Toggle sidebar
  $('#btn-toggle-sidebar')?.addEventListener('click', () => toggleSidebarDOM(false));

  // Menu button
  $('#btn-menu')?.addEventListener('click', () => toggleSidebarDOM());

  // New project
  $('#btn-new-project')?.addEventListener('click', createNewProject);

  // Project items
  $$('.project-item').forEach(item => {
    item.addEventListener('click', () => {
      const pid = item.dataset.projectId;
      if (pid) selectProject(pid);
    });
  });

  // Project delete buttons
  $$('.project-delete-btn').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const pid = btn.dataset.deleteId;
      if (!pid) return;
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner" style="width:12px;height:12px;"></span>';
      try {
        await api.deleteProject(pid);
        if (state.currentProjectId === pid) {
          state.currentProjectId = null;
          state.messages = [];
          state.artifacts = [];
          state.sandbox.phases = [];
          state.sandbox.codeFiles = [];
          state.sandbox.documentContent = '';
          agentWS.disconnect();
        }
        await loadProjects();
        showToast('Project deleted', 'success');
        render();
      } catch (e) {
        console.error('Failed to delete project:', e);
        showToast('Failed to delete project', 'error');
        btn.disabled = false;
        btn.innerHTML = icons.x;
      }
    });
  });

  // Settings nav
  $('#btn-settings')?.addEventListener('click', () => navigate('settings'));
  $('#btn-header-settings')?.addEventListener('click', () => navigate('settings'));
  $('#btn-back-chat')?.addEventListener('click', () => navigate('chat'));

  // Logout
  $('#btn-logout')?.addEventListener('click', () => {
    agentWS.disconnect();
    state.currentView = 'login';
    state.isConnected = false;
    state.messages = [];
    state.currentProjectId = null;
    render();
  });

  // Chat input
  const chatInput = $('#chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        const val = chatInput.value.trim();
        if (val) {
          sendMessage(val);
          chatInput.value = '';
          chatInput.style.height = 'auto';
        }
      }
    });

    // Auto-resize
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 150) + 'px';
    });

    // Click on input wrapper delegates focus to textarea
    const inputWrapper = $('.input-wrapper');
    if (inputWrapper) {
      inputWrapper.addEventListener('click', (e) => {
        if (e.target === inputWrapper || e.target.classList.contains('input-glow')) {
          chatInput.focus();
        }
      });
    }
  }

  // Send button
  $('#btn-send')?.addEventListener('click', () => {
    const chatInput = $('#chat-input');
    if (chatInput) {
      const val = chatInput.value.trim();
      if (val || state.pendingFiles.length > 0) {
        sendMessage(val);
        chatInput.value = '';
        chatInput.style.height = 'auto';
      }
    }
  });

  // Stop button
  $('#btn-stop')?.addEventListener('click', () => {
    agentWS.sendStop();
    state.agentStatus = 'idle';
    updateSendStopButton();
  });

  // Attach button → trigger hidden file input
  $('#btn-attach')?.addEventListener('click', () => {
    $('#file-input')?.click();
  });

  // File input change → upload each file
  $('#file-input')?.addEventListener('change', (e) => {
    const files = Array.from(e.target.files || []);
    files.forEach(f => uploadFile(f));
    e.target.value = ''; // reset so same file can be re-selected
  });

  // Drag-and-drop on input wrapper
  const inputWrapper = $('.input-wrapper');
  if (inputWrapper) {
    ['dragenter', 'dragover'].forEach(evt => {
      inputWrapper.addEventListener(evt, (e) => {
        e.preventDefault();
        inputWrapper.classList.add('drag-over');
      });
    });
    ['dragleave', 'drop'].forEach(evt => {
      inputWrapper.addEventListener(evt, (e) => {
        e.preventDefault();
        inputWrapper.classList.remove('drag-over');
      });
    });
    inputWrapper.addEventListener('drop', (e) => {
      const files = Array.from(e.dataTransfer?.files || []);
      files.forEach(f => uploadFile(f));
    });
  }

  // Suggestion chips
  $$('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.dataset.chip;
      if (text) {
        const chatInput = $('#chat-input');
        if (chatInput) chatInput.value = text;
      }
    });
  });

  // Settings controls
  bindSettingsEvents();
  bindMessageEvents();
  bindSandboxEvents();

  // Mobile sandbox toggle
  $('#btn-sandbox-toggle')?.addEventListener('click', () => {
    state.sandbox.sandboxOpen = !state.sandbox.sandboxOpen;
    const panel = document.querySelector('.sandbox-panel');
    if (panel) panel.classList.toggle('open', state.sandbox.sandboxOpen);
  });

  // ARIA attributes
  const sidebar = document.getElementById('sidebar');
  if (sidebar) { sidebar.setAttribute('role', 'navigation'); sidebar.setAttribute('aria-label', 'Project navigation'); }
  const chatScroll = document.getElementById('chat-scroll');
  if (chatScroll) { chatScroll.setAttribute('role', 'log'); chatScroll.setAttribute('aria-live', 'polite'); }

  // Scroll listener for "user scrolled up" detection
  if (chatScroll) {
    chatScroll.addEventListener('scroll', () => {
      const { scrollTop, scrollHeight, clientHeight } = chatScroll;
      state._userScrolledUp = scrollHeight - scrollTop - clientHeight > 80;
      if (!state._userScrolledUp) {
        const indicator = chatScroll.querySelector('.scroll-indicator');
        if (indicator) indicator.remove();
      }
    });
  }

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl+/ or Cmd+/ → focus chat input
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
      e.preventDefault();
      const input = document.getElementById('chat-input');
      if (input) input.focus();
    }
    // Escape → close sidebar or sandbox
    if (e.key === 'Escape') {
      if (state.sandbox.sandboxOpen) {
        state.sandbox.sandboxOpen = false;
        const panel = document.querySelector('.sandbox-panel');
        if (panel) panel.classList.remove('open');
      } else if (state.sidebarOpen && window.innerWidth < 768) {
        toggleSidebarDOM(false);
      }
    }
  });

  // Touch swipe gestures for mobile sandbox
  let touchStartX = 0;
  let touchStartY = 0;
  document.addEventListener('touchstart', (e) => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
  }, { passive: true });
  document.addEventListener('touchend', (e) => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;
    if (Math.abs(dx) < 60 || Math.abs(dy) > Math.abs(dx)) return; // too short or vertical
    if (dx > 0 && state.sandbox.sandboxOpen) {
      // Right swipe → close sandbox
      state.sandbox.sandboxOpen = false;
      const panel = document.querySelector('.sandbox-panel');
      if (panel) panel.classList.remove('open');
    } else if (dx < 0 && touchStartX > window.innerWidth - 30 && !state.sandbox.sandboxOpen) {
      // Left swipe from right edge → open sandbox
      state.sandbox.sandboxOpen = true;
      const panel = document.querySelector('.sandbox-panel');
      if (panel) panel.classList.add('open');
    }
  }, { passive: true });

  // Auto-focus chat input
  const chatInput2 = document.getElementById('chat-input');
  if (chatInput2) chatInput2.focus();
}

function bindSettingsEvents() {
  // Theme
  $('#setting-theme')?.addEventListener('change', (e) => {
    state.settings.theme = e.target.value;
    persistSettings();
    applyTheme(state.settings.theme);
  });

  // Language
  $('#setting-language')?.addEventListener('change', (e) => {
    state.settings.language = e.target.value;
    persistSettings();
    render(); // Full re-render needed for i18n
  });

  // Model
  $('#setting-model')?.addEventListener('change', (e) => {
    state.settings.model = e.target.value;
    persistSettings();
  });

  // Temperature
  $('#setting-temperature')?.addEventListener('input', (e) => {
    state.settings.temperature = parseFloat(e.target.value);
    persistSettings();
    const display = $('#temperature-value');
    if (display) display.textContent = state.settings.temperature;
  });

  // Name
  $('#setting-name')?.addEventListener('change', (e) => {
    state.settings.name = e.target.value;
  });

  // Email
  $('#setting-email')?.addEventListener('change', (e) => {
    state.settings.email = e.target.value;
  });

  // Toggles
  $('#toggle-marketing')?.addEventListener('click', (e) => {
    state.settings.marketingEmails = !state.settings.marketingEmails;
    e.currentTarget.classList.toggle('active', state.settings.marketingEmails);
  });

  $('#toggle-security')?.addEventListener('click', (e) => {
    state.settings.securityAlerts = !state.settings.securityAlerts;
    e.currentTarget.classList.toggle('active', state.settings.securityAlerts);
  });
}

function bindMessageEvents() {
  // AskHuman respond buttons
  $$('.btn-respond').forEach(btn => {
    btn.addEventListener('click', () => {
      const askId = btn.dataset.askId;
      const input = document.querySelector(`.response-input[data-ask-id="${askId}"]`);
      if (input && input.value.trim()) {
        sendHumanResponse(input.value.trim());
        // Disable the input area after responding
        const container = btn.closest('.msg-ask-human');
        if (container) {
          container.innerHTML = `<div style="color: var(--text-muted); font-size: 13px;">✅ Response sent</div>`;
        }
      }
    });
  });

  // AskHuman input Enter key
  $$('.response-input').forEach(input => {
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const askId = input.dataset.askId;
        const btn = document.querySelector(`.btn-respond[data-ask-id="${askId}"]`);
        if (btn) btn.click();
      }
    });
  });
}

/* ============================================
   Initialization
   ============================================ */
function init() {
  loadStoredSettings();
  applyTheme(state.settings.theme);
  render();

  // Responsive sidebar toggle on resize
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 768 && !state.sidebarOpen && state.currentView !== 'login') {
      // Optional: auto-open on wide screen
    }
  });
}

document.addEventListener('DOMContentLoaded', init);

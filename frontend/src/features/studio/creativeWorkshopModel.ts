import type {
  CreativeBriefInput,
  CreativeBundle,
  RuleCandidateInput,
} from '@/app/apiCreativeContract';

export const STORY_FORMATS = ['短篇故事', '中长篇', '长篇连载'] as const;
export type StoryFormat = (typeof STORY_FORMATS)[number];
export type Candidate = {
  id: string;
  backendId?: string;
  title: string;
  hook: string;
  conflict: string;
  promise: string;
  audience: string;
  scale: string;
  difficulty: string;
  risk: string;
  discarded?: boolean;
};

export const ACTIVE_BRIEF_KEY = 'kunlei.activeCreativeBriefId';
export const STORY_FORMAT_VALUES: Record<StoryFormat, CreativeBriefInput['story_format']> = {
  短篇故事: 'short',
  中长篇: 'medium',
  长篇连载: 'long_serial',
};
export const STORY_FORMAT_LABELS: Record<CreativeBriefInput['story_format'], StoryFormat> = {
  short: '短篇故事',
  medium: '中长篇',
  long_serial: '长篇连载',
};

export const commandKey = (prefix: string) =>
  `${prefix}-${globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random()}`}`;

export const toRuleCandidate = (candidate: Candidate): RuleCandidateInput => ({
  title: candidate.title,
  logline: candidate.hook,
  core_conflict: candidate.conflict,
  emotional_promise: candidate.promise,
  audience_fit: candidate.audience,
  scalability: candidate.scale,
  difficulty: candidate.difficulty,
  risk: candidate.risk,
});

export const fromBundle = (bundle: CreativeBundle): Candidate[] =>
  bundle.candidates.map((candidate, index) => ({
    id: String.fromCharCode(65 + index),
    backendId: candidate.id,
    title: candidate.title,
    hook: candidate.logline,
    conflict: candidate.core_conflict,
    promise: candidate.emotional_promise,
    audience: candidate.audience_fit,
    scale: candidate.scalability,
    difficulty: candidate.difficulty,
    risk: candidate.risk,
  }));

export function buildCandidates(theme: string, premise: string, format: StoryFormat): Candidate[] {
  const subject = premise.trim() || `一个关于「${theme || '真相与救赎'}」的选择`;
  const scale =
    format === '短篇故事'
      ? '单一核心事件，高密度收束'
      : format === '长篇连载'
        ? '多卷谜团，主支线并行'
        : '主线谜团与人物弧光并行';
  return [
    {
      id: 'A',
      title: '《消失的第十三张监控》',
      hook: `一段消失的监控，逼主角承认：${subject}。`,
      conflict: '主角必须伤害最想保护的人，才能证明真相。',
      promise: '在信任与真相之间做一次无法撤回的选择。',
      audience: '偏爱反转、伦理困境的读者',
      scale,
      difficulty: '中等：线索需精准回收',
      risk: '反转太密会削弱人物情感',
    },
    {
      id: 'B',
      title: '《最后的证人》',
      hook: `即将被执行死刑的嫌疑人突然改口，唯一指认的凶手与「${theme || '真相'}」有关。`,
      conflict: '唯一证言会毁掉主角已有的全部信念。',
      promise: '时间倒计时中辨认真相，拯救的可能不是好人。',
      audience: '喜欢高概念悬疑与紧迫节奏的读者',
      scale,
      difficulty: '中等偏高：受时间压力约束',
      risk: '倒计时设定容易盖过角色细节',
    },
    {
      id: 'C',
      title: '《回声档案》',
      hook: `每当有人说谎，女主就会听见与「${subject}」有关的回声，但她的记忆也不完整。`,
      conflict: '她无法相信任何人，包括自己对同一事件的记忆。',
      promise: '在自我怀疑中找回真实，并承受真相的代价。',
      audience: '偏爱心理悬疑与人格困境的读者',
      scale,
      difficulty: '较高：需严格管理信息差',
      risk: '能力设定不够可信会破坏代入感',
    },
  ];
}

import { useState, type FormEvent } from 'react';
import {
  ArrowRight,
  Check,
  GitMerge,
  Lightbulb,
  Pencil,
  RotateCcw,
  Sparkles,
  X,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { api } from '@/app/api';

const STORY_FORMATS = ['短篇故事', '中长篇', '长篇连载'] as const;

type StoryFormat = (typeof STORY_FORMATS)[number];
// prettier-ignore
type Candidate = { id: string; title: string; hook: string; conflict: string; promise: string; audience: string; scale: string; difficulty: string; risk: string; discarded?: boolean };

const buildCandidates = (theme: string, premise: string, format: StoryFormat): Candidate[] => {
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
};

// prettier-ignore
function CandidateLane({ candidate, selected, onSelect, onDiscard, onMerge, onEdit, editing, draftHook, onDraftChange }: { candidate: Candidate; selected: boolean; onSelect: () => void; onDiscard: () => void; onMerge: () => void; onEdit: () => void; editing: boolean; draftHook: string; onDraftChange: (value: string) => void }) {
  // Compact JSX preserves the repository's 300-line feature limit.
  // prettier-ignore
  const content = (
    <article className={`idea-lane${selected ? ' selected' : ''}${candidate.discarded ? ' discarded' : ''}`} data-candidate-id={candidate.id}>
      <header>
        <span>方向 {candidate.id}</span>
        {selected ? (
          <strong>
            <Check />
            已选
          </strong>
        ) : null}
      </header>
      <div className="idea-lane__lead">
        <h3>{candidate.title}</h3>
        {editing ? <textarea aria-label={`编辑方向 ${candidate.id} 的故事钩子`} onChange={(event) => onDraftChange(event.target.value)} rows={4} value={draftHook} /> : <p>{candidate.hook}</p>}
      </div>
      <dl>
        <div>
          <dt>核心冲突</dt>
          <dd>{candidate.conflict}</dd>
        </div>
        <div>
          <dt>情感承诺</dt>
          <dd>{candidate.promise}</dd>
        </div>
        <div>
          <dt>受众匹配</dt>
          <dd>{candidate.audience}</dd>
        </div>
        <div>
          <dt>扩展空间</dt>
          <dd>{candidate.scale}</dd>
        </div>
        <div>
          <dt>完成难度</dt>
          <dd>{candidate.difficulty}</dd>
        </div>
        <div>
          <dt>主要风险</dt>
          <dd>{candidate.risk}</dd>
        </div>
      </dl>
      <footer>
        <button onClick={onEdit} type="button">
          {editing ? <Check /> : <Pencil />}
          {editing ? '保存' : '编辑'}
        </button>
        <button disabled={selected || candidate.discarded} onClick={onMerge} type="button">
          <GitMerge />
          并入已选
        </button>
        <button onClick={onDiscard} type="button">
          {candidate.discarded ? <RotateCcw /> : <X />}
          {candidate.discarded ? '恢复' : '淘汰'}
        </button>
        <button className="idea-lane__select" disabled={candidate.discarded} onClick={onSelect} type="button">
          {selected ? <Check /> : null}
          {selected ? '已选择' : '选择此方向'}
        </button>
      </footer>
    </article>
  );
  return content;
}

// prettier-ignore
function SeedDecision({ candidate, isCreating, onConfirm }: { candidate: Candidate; isCreating: boolean; onConfirm: () => void }) {
  // Compact JSX preserves the repository's 300-line feature limit.
  // prettier-ignore
  const content = (
    <footer className="seed-decision">
      <div>
        <Check />
        <span>
          <small>当前已选：方向 {candidate.id}</small>
          <strong>{candidate.title}</strong>
          <p>{candidate.hook}</p>
        </span>
      </div>
      <dl>
        <div>
          <dt>核心冲突</dt>
          <dd>{candidate.conflict}</dd>
        </div>
        <div>
          <dt>完成难度</dt>
          <dd>{candidate.difficulty}</dd>
        </div>
      </dl>
      <button aria-label="Create project" disabled={isCreating} onClick={onConfirm} type="button">
        <Sparkles />
        {isCreating ? '正在创建…' : '确认为故事种子'}
        <ArrowRight />
      </button>
    </footer>
  );
  return content;
}

// prettier-ignore
export function CreativeWorkshop() {
  const navigate = useNavigate();
  const [format, setFormat] = useState<StoryFormat>('中长篇');
  const [genre, setGenre] = useState('悬疑');
  const [theme, setTheme] = useState('真相与救赎');
  const [premise, setPremise] = useState('当一个人被迫隐瞒真相以保护所爱之人，真相是否还值得被发现？');
  const [preferences, setPreferences] = useState('禁区：宣扬暴力、低俗情节。\n偏好：逻辑严密、现实感强、反转合理。');
  const [candidates, setCandidates] = useState(() => buildCandidates(theme, premise, format));
  const [selectedId, setSelectedId] = useState('B');
  const [notice, setNotice] = useState('当前候选由本地规则草拟；模型 Job / Proposal 接入将在下一批完成。');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [draftHook, setDraftHook] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const selected = candidates.find((candidate) => candidate.id === selectedId) ?? candidates[0];

  const regenerate = (event: FormEvent) => {
    event.preventDefault();
    setCandidates(buildCandidates(theme, premise, format));
    setSelectedId('B');
    setNotice('已按当前创作要求重新草拟 3 个方向。');
  };
  const toggleDiscard = (id: string) => setCandidates((items) => items.map((item) => (item.id === id ? { ...item, discarded: !item.discarded } : item)));
  const mergeIntoSelected = (candidate: Candidate) => {
    setCandidates((items) => items.map((item) => (item.id === selectedId ? { ...item, hook: `${item.hook} 同时吸收「${candidate.title}」的记忆疑点。` } : item)));
    setNotice(`已将方向 ${candidate.id} 的关键疑点并入当前方向。`);
  };
  const editCandidate = (candidate: Candidate) => {
    if (editingId !== candidate.id) {
      setEditingId(candidate.id);
      setDraftHook(candidate.hook);
      return;
    }
    const hook = draftHook.trim();
    if (!hook) return;
    setCandidates((items) => items.map((item) => (item.id === candidate.id ? { ...item, hook } : item)));
    setEditingId(null);
    setNotice(`已更新方向 ${candidate.id} 的故事钩子。`);
  };
  const confirmSeed = async () => {
    setIsCreating(true);
    try {
      const project = await api.createProject(selected.title.replace(/[《》]/g, ''), `${format} · ${genre} · ${theme}｜${selected.hook}｜核心冲突：${selected.conflict}`);
      navigate(`/projects/${project.id}/manuscript`);
    } catch (reason) {
      setNotice(reason instanceof Error ? reason.message : '故事种子创建失败。');
      setIsCreating(false);
    }
  };

  // Compact JSX preserves the repository's 300-line feature limit.
  // prettier-ignore
  const content = (
    <section className="creative-workshop" id="create-project">
      <form className="creative-brief" onSubmit={regenerate}>
        <header>
          <div>
            <span>从要求开始</span>
            <h2>创作要求</h2>
          </div>
          <Lightbulb />
        </header>
        <fieldset>
          <legend>篇幅</legend>
          <div className="creative-brief__formats">
            {STORY_FORMATS.map((item) => (
              <button aria-pressed={format === item} className={format === item ? 'selected' : ''} key={item} onClick={() => setFormat(item)} type="button">
                {item}
              </button>
            ))}
          </div>
        </fieldset>
        <div className="creative-brief__row">
          <label>
            <span>类型</span>
            <select value={genre} onChange={(event) => setGenre(event.target.value)}>
              <option>悬疑</option>
              <option>都市</option>
              <option>科幻</option>
              <option>奇幻</option>
              <option>历史</option>
              <option>言情</option>
            </select>
          </label>
          <label>
            <span>主题</span>
            <input value={theme} onChange={(event) => setTheme(event.target.value)} />
          </label>
        </div>
        <div className="creative-brief__row">
          <label>
            <span>目标读者</span>
            <select defaultValue="18-35 岁 / 悬疑爱好者">
              <option>18-35 岁 / 悬疑爱好者</option>
              <option>大众文学读者</option>
              <option>网络连载读者</option>
            </select>
          </label>
          <label>
            <span>发布平台</span>
            <select defaultValue="起点中文网">
              <option>起点中文网</option>
              <option>番茄小说</option>
              <option>出版投稿</option>
            </select>
          </label>
        </div>
        <label>
          <span>风格倾向</span>
          <select defaultValue="现实感 / 反转密集 / 节奏紧凑">
            <option>现实感 / 反转密集 / 节奏紧凑</option>
            <option>细腻克制 / 人物驱动</option>
            <option>强情节 / 章末钩子</option>
          </select>
        </label>
        <label>
          <span>核心命题</span>
          <textarea aria-label="Title" rows={2} value={premise} onChange={(event) => setPremise(event.target.value)} />
        </label>
        <label>
          <span>禁区与作者偏好</span>
          <textarea rows={3} value={preferences} onChange={(event) => setPreferences(event.target.value)} />
        </label>
        <button className="creative-brief__generate" type="submit">
          <Sparkles />
          形成 3 个创意方向
        </button>
        <small>{notice}</small>
      </form>
      <section className="idea-compare">
        <header>
          <div>
            <span>让可能性竞争</span>
            <h2>候选创意比较</h2>
          </div>
          <small>选择前可淘汰或合并</small>
        </header>
        <div className="idea-compare__lanes">
          {candidates.map((candidate) => (
            <CandidateLane candidate={candidate} draftHook={draftHook} editing={editingId === candidate.id} key={candidate.id} onDraftChange={setDraftHook} selected={candidate.id === selectedId} onDiscard={() => toggleDiscard(candidate.id)} onEdit={() => editCandidate(candidate)} onMerge={() => mergeIntoSelected(candidate)} onSelect={() => setSelectedId(candidate.id)} />
          ))}
        </div>
      </section>
      <SeedDecision candidate={selected} isCreating={isCreating} onConfirm={() => void confirmSeed()} />
    </section>
  );
  return content;
}

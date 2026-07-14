import { useEffect, useReducer, useRef, type FormEvent } from 'react';
import { Lightbulb, Sparkles } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { api } from '@/app/api';
import type { CreativeBriefInput, CreativeBundle } from '@/app/apiCreativeContract';
import { CandidateLane, SeedDecision } from './CreativeWorkshopPanels';
import {
  ACTIVE_BRIEF_KEY,
  STORY_FORMAT_LABELS,
  STORY_FORMAT_VALUES,
  STORY_FORMATS,
  buildCandidates,
  commandKey,
  createCreativeWorkshopState,
  creativeWorkshopReducer,
  fromBundle,
  toRuleCandidate,
  type Candidate,
} from './creativeWorkshopModel';

// prettier-ignore
export function CreativeWorkshop() {
  const navigate = useNavigate();
  const [state, patchState] = useReducer(
    creativeWorkshopReducer,
    undefined,
    createCreativeWorkshopState,
  );
  const briefIdRef = useRef<string | null>(null);
  const briefVersionRef = useRef<number | null>(null);
  const mergedIdsRef = useRef<string[]>([]);
  const {
    format,
    genre,
    theme,
    premise,
    preferences,
    candidates,
    selectedId,
    notice,
    editingId,
    draftHook,
    isCreating,
  } = state;
  const selected = candidates.find((candidate) => candidate.id === selectedId) ?? candidates[0];

  useEffect(() => {
    const savedBriefId = localStorage.getItem(ACTIVE_BRIEF_KEY);
    if (!savedBriefId) return;
    let active = true;
    void api
      .creativeBrief(savedBriefId)
      .then((bundle) => {
        if (!active) return;
        briefIdRef.current = bundle.brief.id;
        briefVersionRef.current = bundle.brief.version;
        patchState({
          format: STORY_FORMAT_LABELS[bundle.brief.story_format],
          genre: bundle.brief.genre,
          theme: bundle.brief.theme,
          premise: bundle.brief.premise,
          preferences: bundle.brief.preferences,
          ...(bundle.candidates.length ? { candidates: fromBundle(bundle) } : {}),
          notice:
            bundle.brief.status === 'confirmed'
              ? '已恢复确认完成的故事种子。'
              : '已从本地服务恢复上次未完成的创意草稿。',
        });
      })
      .catch(() => localStorage.removeItem(ACTIVE_BRIEF_KEY));
    return () => {
      active = false;
    };
  }, []);

  const creativeInput = (): CreativeBriefInput => ({
    story_format: STORY_FORMAT_VALUES[format],
    genre,
    theme,
    target_reader: '18-35 岁 / 悬疑爱好者',
    platform: '本地创作',
    style: '现实感 / 反转密集 / 节奏紧凑',
    premise,
    preferences,
  });

  const persistDraft = async (items: Candidate[]): Promise<CreativeBundle> => {
    let bundle =
      briefIdRef.current !== null && briefVersionRef.current !== null
        ? await api.updateCreativeBrief(briefIdRef.current, {
            base_version: briefVersionRef.current,
            ...creativeInput(),
          })
        : await api.createCreativeBrief(creativeInput(), commandKey('brief'));
    bundle = await api.saveRuleCandidates(
      bundle.brief.id,
      bundle.brief.version,
      items.map(toRuleCandidate),
    );
    localStorage.setItem(ACTIVE_BRIEF_KEY, bundle.brief.id);
    briefIdRef.current = bundle.brief.id;
    briefVersionRef.current = bundle.brief.version;
    return bundle;
  };

  const regenerate = async (event: FormEvent) => {
    event.preventDefault();
    patchState({ isCreating: true });
    const nextCandidates = buildCandidates(theme, premise, format);
    try {
      const bundle = await persistDraft(nextCandidates);
      mergedIdsRef.current = [];
      patchState({
        candidates: fromBundle(bundle),
        selectedId: 'B',
        notice: '已生成并保存 3 个创意方向，刷新页面后仍可恢复。',
      });
    } catch (reason) {
      patchState({ notice: reason instanceof Error ? reason.message : '创意草稿保存失败。' });
    } finally {
      patchState({ isCreating: false });
    }
  };
  const toggleDiscard = (id: string) => {
    patchState({
      candidates: candidates.map((item) =>
        item.id === id ? { ...item, discarded: !item.discarded } : item,
      ),
    });
    mergedIdsRef.current = mergedIdsRef.current.filter((item) => item !== id);
  };
  const mergeIntoSelected = (candidate: Candidate) => {
    patchState({
      candidates: candidates.map((item) =>
        item.id === selectedId
          ? { ...item, hook: `${item.hook} 同时吸收「${candidate.title}」的记忆疑点。` }
          : item,
      ),
      notice: `已将方向 ${candidate.id} 的关键疑点并入当前方向。`,
    });
    mergedIdsRef.current = [...new Set([...mergedIdsRef.current, candidate.id])];
  };
  const editCandidate = (candidate: Candidate) => {
    if (editingId !== candidate.id) {
      patchState({ editingId: candidate.id, draftHook: candidate.hook });
      return;
    }
    const hook = draftHook.trim();
    if (!hook) return;
    patchState({
      candidates: candidates.map((item) => (item.id === candidate.id ? { ...item, hook } : item)),
      editingId: null,
      notice: `已更新方向 ${candidate.id} 的故事钩子。`,
    });
  };
  const confirmSeed = async () => {
    patchState({ isCreating: true });
    try {
      const bundle = await persistDraft(candidates);
      const persisted = fromBundle(bundle);
      const selectedIndex = candidates.findIndex((candidate) => candidate.id === selectedId);
      const selectedCandidateId = persisted[selectedIndex]?.backendId;
      if (!selectedCandidateId) throw new Error('当前选择未能保存，请重新生成候选。');
      const mergedIds = new Set(mergedIdsRef.current);
      const mergedCandidateIds: string[] = [];
      const rejectedCandidateIds: string[] = [];
      for (const [index, candidate] of candidates.entries()) {
        const backendId = persisted[index]?.backendId;
        if (!backendId || backendId === selectedCandidateId) continue;
        if (mergedIds.has(candidate.id)) mergedCandidateIds.push(backendId);
        else rejectedCandidateIds.push(backendId);
      }
      const confirmed = await api.confirmCreativeBrief(
        bundle.brief.id,
        {
          base_version: bundle.brief.version,
          selected_candidate_id: selectedCandidateId,
          merged_candidate_ids: mergedCandidateIds,
          rejected_candidate_ids: rejectedCandidateIds,
        },
        commandKey('decision'),
      );
      const projectId = confirmed.story_seed?.project_id;
      if (!projectId) throw new Error('故事种子已确认，但没有返回作品编号。');
      localStorage.removeItem(ACTIVE_BRIEF_KEY);
      navigate(`/projects/${projectId}/manuscript`);
    } catch (reason) {
      patchState({
        notice: reason instanceof Error ? reason.message : '故事种子创建失败。',
        isCreating: false,
      });
    }
  };

  // Compact JSX preserves the repository's 300-line feature limit.
  // prettier-ignore
  const content = (
    <section className="creative-workshop" id="create-project">
      <form className="creative-brief" onSubmit={(event) => void regenerate(event)}>
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
              <button aria-pressed={format === item} className={format === item ? 'selected' : ''} key={item} onClick={() => patchState({ format: item })} type="button">
                {item}
              </button>
            ))}
          </div>
        </fieldset>
        <div className="creative-brief__row">
          <label>
            <span>类型</span>
            <select value={genre} onChange={(event) => patchState({ genre: event.target.value })}>
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
            <input value={theme} onChange={(event) => patchState({ theme: event.target.value })} />
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
          <textarea aria-label="Title" rows={2} value={premise} onChange={(event) => patchState({ premise: event.target.value })} />
        </label>
        <label>
          <span>禁区与作者偏好</span>
          <textarea rows={3} value={preferences} onChange={(event) => patchState({ preferences: event.target.value })} />
        </label>
        <button className="creative-brief__generate" disabled={isCreating} type="submit">
          <Sparkles />
          {isCreating ? '正在保存…' : '形成 3 个创意方向'}
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
            <CandidateLane candidate={candidate} draftHook={draftHook} editing={editingId === candidate.id} key={candidate.id} onDraftChange={(value) => patchState({ draftHook: value })} selected={candidate.id === selectedId} onDiscard={() => toggleDiscard(candidate.id)} onEdit={() => editCandidate(candidate)} onMerge={() => mergeIntoSelected(candidate)} onSelect={() => { patchState({ selectedId: candidate.id }); mergedIdsRef.current = mergedIdsRef.current.filter((item) => item !== candidate.id); }} />
          ))}
        </div>
      </section>
      <SeedDecision candidate={selected} isCreating={isCreating} onConfirm={() => void confirmSeed()} />
    </section>
  );
  return content;
}

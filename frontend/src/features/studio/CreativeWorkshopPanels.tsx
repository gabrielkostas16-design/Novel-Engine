import { ArrowRight, Check, GitMerge, Pencil, RotateCcw, Sparkles, X } from 'lucide-react';

import type { Candidate } from './creativeWorkshopModel';

interface CandidateLaneProps {
  candidate: Candidate;
  selected: boolean;
  onSelect: () => void;
  onDiscard: () => void;
  onMerge: () => void;
  onEdit: () => void;
  editing: boolean;
  draftHook: string;
  onDraftChange: (value: string) => void;
}

export function CandidateLane(props: CandidateLaneProps) {
  const { candidate, selected, onSelect, onDiscard, onMerge, onEdit } = props;
  return (
    <article
      className={`idea-lane${selected ? ' selected' : ''}${candidate.discarded ? ' discarded' : ''}`}
      data-candidate-id={candidate.id}
    >
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
        {props.editing ? (
          <textarea
            aria-label={`编辑方向 ${candidate.id} 的故事钩子`}
            onChange={(event) => props.onDraftChange(event.target.value)}
            rows={4}
            value={props.draftHook}
          />
        ) : (
          <p>{candidate.hook}</p>
        )}
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
          {props.editing ? <Check /> : <Pencil />}
          {props.editing ? '保存' : '编辑'}
        </button>
        <button disabled={selected || candidate.discarded} onClick={onMerge} type="button">
          <GitMerge />
          并入已选
        </button>
        <button onClick={onDiscard} type="button">
          {candidate.discarded ? <RotateCcw /> : <X />}
          {candidate.discarded ? '恢复' : '淘汰'}
        </button>
        <button
          className="idea-lane__select"
          disabled={candidate.discarded}
          onClick={onSelect}
          type="button"
        >
          {selected ? <Check /> : null}
          {selected ? '已选择' : '选择此方向'}
        </button>
      </footer>
    </article>
  );
}

export function SeedDecision({
  candidate,
  isCreating,
  onConfirm,
}: {
  candidate: Candidate;
  isCreating: boolean;
  onConfirm: () => void;
}) {
  return (
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
}

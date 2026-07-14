import {
  arrayField,
  literalField,
  nullableStringField,
  numberField,
  objectValue,
  stringField,
  stringValue,
} from '@/app/apiContract';

export type CreativeStoryFormat = 'short' | 'medium' | 'long_serial';
export type CreativeBriefStatus = 'draft' | 'generating' | 'comparing' | 'confirmed' | 'abandoned';

export interface CreativeBriefInput {
  story_format: CreativeStoryFormat;
  genre: string;
  theme: string;
  target_reader: string;
  platform: string;
  style: string;
  premise: string;
  preferences: string;
}

export interface RuleCandidateInput {
  title: string;
  logline: string;
  core_conflict: string;
  emotional_promise: string;
  audience_fit: string;
  scalability: string;
  difficulty: string;
  risk: string;
}

export interface CreativeCandidate extends RuleCandidateInput {
  id: string;
  brief_id: string;
  source: 'author' | 'rule' | 'ai';
  source_job_id: string | null;
  source_proposal_id: string | null;
  revision_of_candidate_id: string | null;
  revision_number: number;
  lifecycle_status: 'active' | 'superseded';
  position: number;
  created_at: string;
}

export interface CreativeBundle {
  brief: CreativeBriefInput & {
    id: string;
    status: CreativeBriefStatus;
    version: number;
    created_at: string;
    updated_at: string;
  };
  candidates: CreativeCandidate[];
  decision: {
    id: string;
    brief_id: string;
    selected_candidate_id: string;
    merged_candidate_ids: string[];
    rejected_candidate_ids: string[];
    decided_by_session_id: string;
    base_brief_version: number;
    created_at: string;
  } | null;
  story_seed: {
    id: string;
    brief_id: string;
    decision_id: string;
    source_candidate_ids: string[];
    title: string;
    premise: string;
    core_conflict: string;
    emotional_promise: string;
    project_id: string | null;
    created_at: string;
  } | null;
}

const storyFormats = ['short', 'medium', 'long_serial'] as const;
const briefStatuses = ['draft', 'generating', 'comparing', 'confirmed', 'abandoned'] as const;
const candidateSources = ['author', 'rule', 'ai'] as const;
const lifecycleStatuses = ['active', 'superseded'] as const;

function parseStringArray(value: unknown, label: string): string[] {
  const wrapper = { values: value };
  return arrayField(wrapper, 'values', label, (item, index) =>
    stringValue(item, `${label}[${index}]`),
  );
}

function parseCandidate(value: unknown, index: number): CreativeCandidate {
  const label = `creative.candidates[${index}]`;
  const item = objectValue(value, label);
  return {
    id: stringField(item, 'id', label),
    brief_id: stringField(item, 'brief_id', label),
    title: stringField(item, 'title', label),
    logline: stringField(item, 'logline', label),
    core_conflict: stringField(item, 'core_conflict', label),
    emotional_promise: stringField(item, 'emotional_promise', label),
    audience_fit: stringField(item, 'audience_fit', label),
    scalability: stringField(item, 'scalability', label),
    difficulty: stringField(item, 'difficulty', label),
    risk: stringField(item, 'risk', label),
    source: literalField(item, 'source', label, candidateSources),
    source_job_id: nullableStringField(item, 'source_job_id', label),
    source_proposal_id: nullableStringField(item, 'source_proposal_id', label),
    revision_of_candidate_id: nullableStringField(item, 'revision_of_candidate_id', label),
    revision_number: numberField(item, 'revision_number', label),
    lifecycle_status: literalField(item, 'lifecycle_status', label, lifecycleStatuses),
    position: numberField(item, 'position', label),
    created_at: stringField(item, 'created_at', label),
  };
}

export function parseCreativeBundle(value: unknown): CreativeBundle {
  const root = objectValue(value, 'creative');
  const brief = objectValue(root.brief, 'creative.brief');
  const decision = root.decision === null ? null : objectValue(root.decision, 'creative.decision');
  const seed =
    root.story_seed === null ? null : objectValue(root.story_seed, 'creative.story_seed');
  return {
    brief: {
      id: stringField(brief, 'id', 'creative.brief'),
      story_format: literalField(brief, 'story_format', 'creative.brief', storyFormats),
      genre: stringField(brief, 'genre', 'creative.brief'),
      theme: stringField(brief, 'theme', 'creative.brief'),
      target_reader: stringField(brief, 'target_reader', 'creative.brief'),
      platform: stringField(brief, 'platform', 'creative.brief'),
      style: stringField(brief, 'style', 'creative.brief'),
      premise: stringField(brief, 'premise', 'creative.brief'),
      preferences: stringField(brief, 'preferences', 'creative.brief'),
      status: literalField(brief, 'status', 'creative.brief', briefStatuses),
      version: numberField(brief, 'version', 'creative.brief'),
      created_at: stringField(brief, 'created_at', 'creative.brief'),
      updated_at: stringField(brief, 'updated_at', 'creative.brief'),
    },
    candidates: arrayField(root, 'candidates', 'creative', parseCandidate),
    decision: decision
      ? {
          id: stringField(decision, 'id', 'creative.decision'),
          brief_id: stringField(decision, 'brief_id', 'creative.decision'),
          selected_candidate_id: stringField(
            decision,
            'selected_candidate_id',
            'creative.decision',
          ),
          merged_candidate_ids: parseStringArray(
            decision.merged_candidate_ids,
            'creative.decision.merged_candidate_ids',
          ),
          rejected_candidate_ids: parseStringArray(
            decision.rejected_candidate_ids,
            'creative.decision.rejected_candidate_ids',
          ),
          decided_by_session_id: stringField(
            decision,
            'decided_by_session_id',
            'creative.decision',
          ),
          base_brief_version: numberField(decision, 'base_brief_version', 'creative.decision'),
          created_at: stringField(decision, 'created_at', 'creative.decision'),
        }
      : null,
    story_seed: seed
      ? {
          id: stringField(seed, 'id', 'creative.story_seed'),
          brief_id: stringField(seed, 'brief_id', 'creative.story_seed'),
          decision_id: stringField(seed, 'decision_id', 'creative.story_seed'),
          source_candidate_ids: parseStringArray(
            seed.source_candidate_ids,
            'creative.story_seed.source_candidate_ids',
          ),
          title: stringField(seed, 'title', 'creative.story_seed'),
          premise: stringField(seed, 'premise', 'creative.story_seed'),
          core_conflict: stringField(seed, 'core_conflict', 'creative.story_seed'),
          emotional_promise: stringField(seed, 'emotional_promise', 'creative.story_seed'),
          project_id: nullableStringField(seed, 'project_id', 'creative.story_seed'),
          created_at: stringField(seed, 'created_at', 'creative.story_seed'),
        }
      : null,
  };
}

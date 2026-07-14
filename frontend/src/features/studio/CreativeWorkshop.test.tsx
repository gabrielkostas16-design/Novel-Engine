import { fireEvent, waitFor } from '@testing-library/dom';
import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { CreativeBundle } from '@/app/apiCreativeContract';
import { CreativeWorkshop } from './CreativeWorkshop';

const apiMock = vi.hoisted(() => ({
  createCreativeBrief: vi.fn(),
  creativeBrief: vi.fn(),
  updateCreativeBrief: vi.fn(),
  saveRuleCandidates: vi.fn(),
  confirmCreativeBrief: vi.fn(),
}));

vi.mock('@/app/api', () => ({ api: apiMock }));

const brief = {
  id: 'brief-1',
  story_format: 'medium' as const,
  genre: '悬疑',
  theme: '真相与救赎',
  target_reader: '成年读者',
  platform: '本地创作',
  style: '现实感',
  premise: '必须在真相与亲情之间选择。',
  preferences: '逻辑严密',
  status: 'comparing' as const,
  version: 2,
  created_at: '2026-07-14T00:00:00Z',
  updated_at: '2026-07-14T00:00:00Z',
};

const candidates = ['A', 'B', 'C'].map((label, position) => ({
  id: `candidate-${label.toLowerCase()}`,
  brief_id: brief.id,
  title: `候选 ${label}`,
  logline: `故事钩子 ${label}`,
  core_conflict: `核心冲突 ${label}`,
  emotional_promise: '真相需要代价',
  audience_fit: '悬疑读者',
  scalability: '三幕结构',
  difficulty: '中等',
  risk: '避免空洞反转',
  source: 'rule' as const,
  source_job_id: null,
  source_proposal_id: null,
  revision_of_candidate_id: null,
  revision_number: 1,
  lifecycle_status: 'active' as const,
  position,
  created_at: '2026-07-14T00:00:00Z',
}));

const bundle = (version = 2): CreativeBundle => ({
  brief: { ...brief, version },
  candidates,
  decision: null,
  story_seed: null,
});

let root: Root | null = null;
let container: HTMLDivElement | null = null;

function renderWorkshop(): HTMLDivElement {
  container = document.createElement('div');
  document.body.appendChild(container);
  root = createRoot(container);
  act(() => {
    root?.render(
      <MemoryRouter initialEntries={['/projects']}>
        <Routes>
          <Route path="/projects" element={<CreativeWorkshop />} />
          <Route path="/projects/:projectId/manuscript" element={<p>作品工作室已打开</p>} />
        </Routes>
      </MemoryRouter>,
    );
  });
  return container;
}

afterEach(() => {
  act(() => root?.unmount());
  container?.remove();
  root = null;
  container = null;
  localStorage.clear();
  vi.clearAllMocks();
});

describe('CreativeWorkshop persistence', () => {
  it('restores a server draft and confirms through the creative API', async () => {
    localStorage.setItem('kunlei.activeCreativeBriefId', brief.id);
    apiMock.creativeBrief.mockResolvedValue(bundle());
    apiMock.updateCreativeBrief.mockResolvedValue(bundle(3));
    apiMock.saveRuleCandidates.mockResolvedValue(bundle(4));
    apiMock.confirmCreativeBrief.mockResolvedValue({
      ...bundle(5),
      brief: { ...brief, version: 5, status: 'confirmed' },
      story_seed: {
        id: 'seed-1',
        brief_id: brief.id,
        decision_id: 'decision-1',
        source_candidate_ids: ['candidate-b'],
        title: '候选 B',
        premise: '故事钩子 B',
        core_conflict: '核心冲突 B',
        emotional_promise: '真相需要代价',
        project_id: 'project-1',
        created_at: '2026-07-14T00:00:00Z',
      },
    });

    const view = renderWorkshop();
    await waitFor(() => expect(view.textContent).toContain('候选 B'));
    expect(view.textContent).toContain('已从本地服务恢复上次未完成的创意草稿。');

    const confirm = view.querySelector('button[aria-label="Create project"]');
    await act(async () => {
      if (confirm instanceof HTMLButtonElement) fireEvent.click(confirm);
    });

    await waitFor(() => expect(view.textContent).toContain('作品工作室已打开'));
    expect(apiMock.updateCreativeBrief).toHaveBeenCalledWith(
      brief.id,
      expect.objectContaining({ base_version: 2 }),
    );
    expect(apiMock.confirmCreativeBrief).toHaveBeenCalledWith(
      brief.id,
      expect.objectContaining({ selected_candidate_id: 'candidate-b' }),
      expect.any(String),
    );
    expect(localStorage.getItem('kunlei.activeCreativeBriefId')).toBeNull();
  });
});

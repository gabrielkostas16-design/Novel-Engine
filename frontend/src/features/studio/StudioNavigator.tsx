import { ArrowDown, ArrowUp, FileText, Loader2, Plus, Search } from 'lucide-react';
import type { FormEvent } from 'react';

import type { DocumentKind, Project } from '@/app/types/studio';

import { GROUPS, SECTIONS } from './studioConstants';

const SECTION_LABELS: Record<(typeof SECTIONS)[number][0], string> = {
  manuscript: '正文写作',
  outline: '故事大纲',
  characters: '人物角色',
  world: '世界观',
  review: '质量检查',
  history: '版本记录',
  export: '出版导出',
  settings: '项目设置',
};

const GROUP_LABELS: Record<DocumentKind, string> = {
  chapter: '正文篇章',
  outline: '故事大纲',
  character: '人物角色',
  world: '世界设定',
  note: '创作笔记',
};

interface SearchResult {
  document_id: string;
  title: string;
  excerpt: string;
}

interface StudioNavigatorProps {
  project: Project;
  section: string;
  activeId: string | null;
  search: string;
  isSearching: boolean;
  searchResults: SearchResult[];
  onSearchChange: (value: string) => void;
  onSearchSubmit: (event: FormEvent) => void;
  onNavigateSection: (section: string) => void;
  onSelectDocument: (documentId: string) => void;
  onCreateDocument: (kind: DocumentKind) => void;
  onMoveDocument: (documentId: string, direction: -1 | 1) => void;
}

export function StudioNavigator({
  project,
  section,
  activeId,
  search,
  isSearching,
  searchResults,
  onSearchChange,
  onSearchSubmit,
  onNavigateSection,
  onSelectDocument,
  onCreateDocument,
  onMoveDocument,
}: StudioNavigatorProps) {
  const visibleGroups = GROUPS.flatMap((group) => {
    if (section === 'outline' && group.kind !== 'outline') return [];
    if (section === 'characters' && group.kind !== 'character') return [];
    if (section === 'world' && group.kind !== 'world') return [];
    return [group];
  });

  return (
    <aside className="studio-nav">
      <nav className="section-nav" aria-label="作品创作区">
        {SECTIONS.map(([path]) => (
          <button
            className={section === path ? 'active' : ''}
            key={path}
            onClick={() => onNavigateSection(path)}
            type="button"
          >
            {SECTION_LABELS[path]}
          </button>
        ))}
      </nav>
      <form className="studio-search" onSubmit={onSearchSubmit}>
        {isSearching ? <Loader2 className="spin" /> : <Search />}
        <input
          aria-label="搜索作品内容"
          disabled={isSearching}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="搜索正文、设定与笔记"
          value={search}
        />
      </form>
      {searchResults.length ? (
        <div className="search-results">
          {searchResults.map((result) => (
            <button
              key={result.document_id}
              onClick={() => onSelectDocument(result.document_id)}
              type="button"
            >
              <strong>{result.title}</strong>
              <span>{result.excerpt}</span>
            </button>
          ))}
        </div>
      ) : null}
      <div className="document-tree">
        {visibleGroups.map(({ kind, label, icon: Icon }) => {
          const documents = project.documents?.filter((document) => document.kind === kind) ?? [];
          const displayLabel = GROUP_LABELS[kind];
          return (
            <section className="document-group" key={kind}>
              <header>
                <span>
                  <Icon /> {displayLabel}
                </span>
                <button
                  aria-label={`Add ${label}`}
                  onClick={() => onCreateDocument(kind)}
                  title={`新增${displayLabel}`}
                  type="button"
                >
                  <Plus />
                </button>
              </header>
              {documents.map((document, index) => (
                <div className="document-row-wrap" key={document.id}>
                  <button
                    className={
                      document.id === activeId
                        ? 'document-row document-row--active'
                        : 'document-row'
                    }
                    onClick={() => onSelectDocument(document.id)}
                    type="button"
                  >
                    <FileText />
                    <span>{document.title}</span>
                  </button>
                  <span className="document-order">
                    <button
                      disabled={index === 0}
                      onClick={() => onMoveDocument(document.id, -1)}
                      title="向上移动"
                      type="button"
                    >
                      <ArrowUp />
                    </button>
                    <button
                      disabled={index === documents.length - 1}
                      onClick={() => onMoveDocument(document.id, 1)}
                      title="向下移动"
                      type="button"
                    >
                      <ArrowDown />
                    </button>
                  </span>
                </div>
              ))}
            </section>
          );
        })}
      </div>
    </aside>
  );
}

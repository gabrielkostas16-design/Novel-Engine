import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  BookOpen,
  ChevronRight,
  Download,
  Feather,
  GitBranch,
  Globe2,
  Library,
  Lightbulb,
  ListTree,
  LogOut,
  PenLine,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { api } from '@/app/api';
import type { Project } from '@/app/types/studio';
import { CreativeWorkshop } from '@/features/studio/CreativeWorkshop';

const WORKFLOW_ITEMS = [
  { label: '正文写作', icon: PenLine },
  { label: '故事大纲', icon: ListTree },
  { label: '人物角色', icon: Users },
  { label: '世界观', icon: Globe2 },
  { label: '时间线与伏笔', icon: GitBranch },
  { label: '质量中心', icon: ShieldCheck },
  { label: '版本与导出', icon: Download },
] as const;

const CREATION_STEPS = ['创意', '世界观', '人物', '大纲', '正文', '质检', '出版'];
const PROJECT_DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  month: 'short',
  day: 'numeric',
});

function formatProjectDate(value: string): string {
  const date = new Date(value);
  const today = new Date();
  if (date.toDateString() === today.toDateString()) return '今天';
  return PROJECT_DATE_FORMATTER.format(date);
}

export function ProjectLibraryPage() {
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [, response] = await Promise.all([api.session(), api.projects()]);
      setProjects(response.projects);
    } catch {
      navigate('/', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    document.title = '坤雷小说工厂';
    void load();
  }, [load]);

  const logout = async () => {
    try {
      await api.logout();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '退出失败，请稍后再试。');
      return;
    }
    navigate('/');
  };

  return (
    <main className="library library--workshop">
      <aside className="library-sidebar">
        <div className="library-sidebar__brand">
          <span className="library-sidebar__brand-mark" aria-hidden="true">
            <BookOpen />
            <Feather />
          </span>
          <span>
            坤雷小说工厂
            <small>本地智能创作中心</small>
          </span>
        </div>
        <nav className="library-sidebar__nav" aria-label="坤雷小说工厂导航">
          <a className="active" href="#create-project">
            <Lightbulb aria-hidden="true" />
            创意项目
          </a>
          <a href="#recent-projects">
            <Library aria-hidden="true" />
            我的作品
          </a>
          <p>进入作品后</p>
          {WORKFLOW_ITEMS.map(({ label, icon: Icon }) => (
            <span className="library-sidebar__workflow" key={label}>
              <Icon aria-hidden="true" />
              {label}
            </span>
          ))}
        </nav>
        <div className="library-sidebar__footnote">从创意到成稿，一站完成</div>
      </aside>

      <section className="library-shell">
        <header className="library__header">
          <strong>
            <Activity aria-hidden="true" />
            创作控制台
          </strong>
          <div className="library__header-actions">
            <span className="library__account">本地作者</span>
            <button
              className="icon-command"
              onClick={() => void logout()}
              title="退出登录"
              type="button"
            >
              <LogOut aria-hidden="true" />
            </button>
          </div>
        </header>

        <div className="library__content">
          <section className="library__intro">
            <span>坤雷创作系统</span>
            <h1>创意工坊</h1>
            <p>先定义方向，再让不同的故事可能性彼此竞争。</p>
          </section>

          <ol className="creation-path" aria-label="小说生产流程">
            {CREATION_STEPS.map((step, index) => (
              <li className={index === 0 ? 'active' : ''} key={step}>
                <span>{index + 1}</span>
                {step}
                {index < CREATION_STEPS.length - 1 ? <ChevronRight aria-hidden="true" /> : null}
              </li>
            ))}
          </ol>

          <CreativeWorkshop />

          <div className="library__grid">
            <section className="recent-projects" id="recent-projects">
              <header>
                <div>
                  <span>继续创作</span>
                  <h2>最近作品</h2>
                </div>
                <small>{projects.length} 部作品</small>
              </header>
              <div className="recent-projects__list">
                {projects.length ? (
                  projects.map((project) => (
                    <button
                      className="project-row"
                      key={project.id}
                      onClick={() => navigate(`/projects/${project.id}/manuscript`)}
                      type="button"
                    >
                      <BookOpen aria-hidden="true" />
                      <span className="project-row__copy">
                        <strong>{project.title}</strong>
                        <small>{project.description || '还没有写下核心创意'}</small>
                      </span>
                      <span className="project-row__stage">正文写作</span>
                      <time>{formatProjectDate(project.updated_at)}</time>
                      <span className="project-row__action">
                        继续创作 <ChevronRight aria-hidden="true" />
                      </span>
                    </button>
                  ))
                ) : (
                  <div className="recent-projects__empty">
                    <BookOpen aria-hidden="true" />
                    <h3>还没有作品</h3>
                    <p>从左侧写下第一个创意，作品会出现在这里。</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}

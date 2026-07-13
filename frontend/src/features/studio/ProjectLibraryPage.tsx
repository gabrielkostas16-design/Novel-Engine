import { useCallback, useEffect, useState, type FormEvent } from 'react';
import {
  BookOpen,
  ChevronRight,
  Clock3,
  Download,
  GitBranch,
  Globe2,
  Library,
  Lightbulb,
  ListTree,
  LogOut,
  PenLine,
  Plus,
  ShieldCheck,
  Users,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { api } from '@/app/api';
import type { Project, Session } from '@/app/types/studio';

const STORY_FORMATS = [
  { value: '短篇故事', detail: '1 万字以内' },
  { value: '中长篇', detail: '5 万—30 万字' },
  { value: '长篇连载', detail: '30 万字以上' },
] as const;

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
  const [session, setSession] = useState<Session | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [storyFormat, setStoryFormat] = useState<(typeof STORY_FORMATS)[number]['value']>('中长篇');
  const [genre, setGenre] = useState('悬疑');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [nextSession, response] = await Promise.all([api.session(), api.projects()]);
      setSession(nextSession);
      setProjects(response.projects);
    } catch {
      navigate('/', { replace: true });
    }
  }, [navigate]);

  useEffect(() => {
    void load();
  }, [load]);

  const createProject = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setIsCreating(true);
    try {
      const premise = [`${storyFormat} · ${genre}`, description.trim()].filter(Boolean).join('｜');
      const project = await api.createProject(title.trim(), premise);
      navigate(`/projects/${project.id}/manuscript`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '项目创建失败，请稍后再试。');
      setIsCreating(false);
    }
  };

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
    <main className="library">
      <aside className="library-sidebar">
        <div className="library-sidebar__brand">
          <BookOpen aria-hidden="true" />
          <span>小说创作工厂</span>
        </div>
        <nav className="library-sidebar__nav" aria-label="小说创作工厂导航">
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
          <strong>创意工作台</strong>
          <div className="library__header-actions">
            {session?.kind === 'guest' ? (
              <span className="session-expiry">
                <Clock3 aria-hidden="true" />
                临时工作区将在{' '}
                {session.expires_at ? new Date(session.expires_at).toLocaleString('zh-CN') : ''}
                失效
              </span>
            ) : (
              <span className="library__account">本地作者</span>
            )}
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
            <span>创意工作台</span>
            <h1>从一个念头，开始一部小说</h1>
            <p>选择篇幅与类型，把核心创意变成可以继续写作、检查和出版的作品。</p>
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

          <div className="library__grid">
            <form className="project-create" id="create-project" onSubmit={createProject}>
              <header>
                <div>
                  <span>新作品</span>
                  <h2>新建创意项目</h2>
                </div>
                <Lightbulb aria-hidden="true" />
              </header>

              <fieldset className="story-format">
                <legend>选择篇幅</legend>
                <div>
                  {STORY_FORMATS.map((option) => (
                    <button
                      aria-pressed={storyFormat === option.value}
                      className={storyFormat === option.value ? 'selected' : ''}
                      key={option.value}
                      onClick={() => setStoryFormat(option.value)}
                      type="button"
                    >
                      <strong>{option.value}</strong>
                      <small>{option.detail}</small>
                    </button>
                  ))}
                </div>
              </fieldset>

              <label>
                <span>故事类型</span>
                <select value={genre} onChange={(event) => setGenre(event.target.value)}>
                  <option>悬疑</option>
                  <option>都市</option>
                  <option>科幻</option>
                  <option>奇幻</option>
                  <option>历史</option>
                  <option>言情</option>
                  <option>现实主义</option>
                </select>
              </label>
              <label>
                <span>作品名称</span>
                <input
                  aria-label="Title"
                  maxLength={80}
                  onChange={(event) => setTitle(event.target.value)}
                  placeholder="给这个故事起一个暂定名"
                  required
                  value={title}
                />
              </label>
              <label>
                <span>核心创意</span>
                <textarea
                  maxLength={500}
                  onChange={(event) => setDescription(event.target.value)}
                  placeholder="主角是谁？他想要什么？最大的阻碍是什么？"
                  rows={5}
                  value={description}
                />
                <small className="field-count">{description.length}/500</small>
              </label>
              {error ? <p className="form-error">{error}</p> : null}
              <button
                aria-label="Create project"
                className="command command--primary project-create__submit"
                disabled={isCreating}
                type="submit"
              >
                <Plus aria-hidden="true" />
                {isCreating ? '正在创建…' : '创建创意项目'}
              </button>
            </form>

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

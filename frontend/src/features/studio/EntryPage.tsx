import { useEffect, useState, type CSSProperties, type FormEvent } from 'react';
import {
  Activity,
  BookOpen,
  Database,
  Feather,
  History,
  Lightbulb,
  LogIn,
  ShieldCheck,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { api } from '@/app/api';
import type { SetupStatus } from '@/app/types/studio';

const CREATION_STEPS = ['创意', '大纲', '人物', '世界观', '写作', '质检', '交付'];

const ENTRY_WORKFLOW = [
  { label: '灵感与创意', icon: Lightbulb },
  { label: '大纲与结构', icon: BookOpen },
  { label: '版本与回退', icon: History },
  { label: '质量与交付', icon: ShieldCheck },
] as const;

const HERO_IMAGE_STYLE: CSSProperties = {
  width: '100%',
  maxHeight: 330,
  marginTop: 24,
  border: '1px solid rgba(81, 230, 194, .2)',
  borderRadius: 12,
  objectFit: 'cover',
  objectPosition: 'center 46%',
  boxShadow: '0 24px 55px rgba(0, 0, 0, .3)',
};

export function EntryPage() {
  const navigate = useNavigate();
  const [setup, setSetup] = useState<SetupStatus | null>(null);
  const [username, setUsername] = useState('longge');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.title = '坤雷小说工厂';
    let mounted = true;
    void api
      .session()
      .then(() => {
        if (mounted) navigate('/projects', { replace: true });
      })
      .catch(() =>
        api
          .setupStatus()
          .then((status) => {
            if (mounted) setSetup(status);
          })
          .catch((reason: unknown) => {
            if (mounted) {
              setError(reason instanceof Error ? reason.message : '无法连接本地小说工厂。');
            }
          }),
      );
    return () => {
      mounted = false;
    };
  }, [navigate]);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (!setup?.owner_configured) await api.setupOwner(username, password);
      await api.login(username, password);
      navigate('/projects');
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : '登录失败，请检查账号和密码。');
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="library">
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
        <nav className="library-sidebar__nav" aria-label="坤雷小说工厂创作流程">
          {ENTRY_WORKFLOW.map(({ label, icon: Icon }) => (
            <span className="library-sidebar__workflow" key={label}>
              <Icon aria-hidden="true" />
              {label}
            </span>
          ))}
        </nav>
        <div className="library-sidebar__footnote">只属于龙哥的本地小说生产线</div>
      </aside>

      <section className="library-shell">
        <header className="library__header">
          <strong>
            <Activity aria-hidden="true" />
            登录控制台
          </strong>
          <span className="library__account">本地服务已连接</span>
        </header>

        <div className="library__content">
          <section className="library__intro">
            <h1>
              让每一个故事，<span>在这里被认真完成</span>
            </h1>
            <p>从一个灵感开始，完成创意、大纲、人物、世界观、章节写作与质量检查。</p>
            <img
              alt="灯火照亮书稿，远山与楼阁构成故事世界"
              src="/kunlei-novel-factory-login-v1.png"
              style={HERO_IMAGE_STYLE}
            />
          </section>

          <ol className="creation-path" aria-label="小说生产流程">
            {CREATION_STEPS.map((step, index) => (
              <li className={index === 0 ? 'active' : ''} key={step}>
                <span>{index + 1}</span>
                {step}
              </li>
            ))}
          </ol>

          <div className="library__grid">
            <form className="project-create" onSubmit={submit}>
              <header>
                <div>
                  <span>欢迎回来</span>
                  <h2>{setup?.owner_configured ? '进入坤雷小说工厂' : '创建本地账号'}</h2>
                </div>
                <LogIn aria-hidden="true" />
              </header>
              <p style={{ color: 'var(--factory-muted)', lineHeight: 1.75 }}>
                登录后继续管理你的创意、作品、章节和每一次修订。
              </p>
              <label>
                <span>账号</span>
                <input
                  autoComplete="username"
                  onChange={(event) => setUsername(event.target.value)}
                  required
                  value={username}
                />
              </label>
              <label>
                <span>密码</span>
                <input
                  autoComplete={setup?.owner_configured ? 'current-password' : 'new-password'}
                  minLength={10}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  type="password"
                  value={password}
                />
              </label>
              {error ? <p className="form-error">{error}</p> : null}
              <button className="command command--primary" disabled={busy || !setup} type="submit">
                <LogIn aria-hidden="true" />
                {busy ? '正在进入…' : setup?.owner_configured ? '登录工作台' : '创建并登录'}
              </button>
            </form>

            <section className="recent-projects">
              <header>
                <div>
                  <span>本地可信</span>
                  <h2>作品和创作记录由你掌控</h2>
                </div>
              </header>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
                  gap: 20,
                  paddingTop: 18,
                  color: 'var(--factory-muted)',
                  lineHeight: 1.65,
                }}
              >
                <span>
                  <Database aria-hidden="true" /> 本地保存
                </span>
                <span>
                  <History aria-hidden="true" /> 版本留痕
                </span>
                <span>
                  <ShieldCheck aria-hidden="true" /> AI 建议可审可拒
                </span>
              </div>
            </section>
          </div>
        </div>
      </section>
    </main>
  );
}

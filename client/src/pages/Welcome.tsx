import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "@/hooks/useTranslation";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Logo } from "@/components/Logo";
import {
  ArrowRight, Play, Satellite, BrainCircuit, Coins, Zap,
  Leaf, Waves, Flame, Snowflake, ChevronRight, Star
} from "lucide-react";

/* ──────────────────────────────────────────────
   Hook: Intersection Observer for scroll-reveal
   ────────────────────────────────────────────── */
function useScrollReveal() {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!ref.current) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) { setVisible(true); obs.disconnect(); } },
      { threshold: 0.12 }
    );
    obs.observe(ref.current);
    return () => obs.disconnect();
  }, []);
  return { ref, visible };
}

/* ──────────────────────────────────────────────
   Hook: Animated Counter
   ────────────────────────────────────────────── */
function useCounter(target: number, duration = 2200, active = false) {
  const [count, setCount] = useState(0);
  useEffect(() => {
    if (!active) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [active, target, duration]);
  return count;
}

/* ──────────────────────────────────────────────
   Metric Card
   ────────────────────────────────────────────── */
function MetricCard({ icon, value, suffix, label, active }: {
  icon: JSX.Element; value: number; suffix: string; label: string; active: boolean;
}) {
  const { language } = useTranslation();
  const count = useCounter(value, 2200, active);
  return (
    <div className="lp-metric-card">
      <div className="flex justify-center mb-3 text-green-400">{icon}</div>
      <div className="lp-metric-number">
        {count.toLocaleString(language)}{suffix}
      </div>
      <div className="mt-2 text-sm font-medium" style={{ color: 'var(--lp-text-muted)' }}>{label}</div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Timeline Step
   ────────────────────────────────────────────── */
function TimelineStep({ icon, number, title, desc }: {
  icon: JSX.Element; number: string; title: string; desc: string;
}) {
  return (
    <div className="lp-timeline-step flex-1 px-4">
      <div className="lp-timeline-step-icon text-green-400 relative">
        {icon}
        <span className="absolute -top-2 -right-2 w-5 h-5 rounded-full bg-green-500 text-white text-xs font-bold flex items-center justify-center">
          {number}
        </span>
      </div>
      <h4 className="font-bold text-white mb-1 text-sm">{title}</h4>
      <p className="text-xs leading-relaxed" style={{ color: 'var(--lp-text-muted)' }}>{desc}</p>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Mission Tile
   ────────────────────────────────────────────── */
function MissionTile({ src, label, impact, className = "" }: {
  src: string; label: string; impact: string; className?: string;
}) {
  return (
    <div className={`lp-mission-tile ${className}`} style={{ minHeight: 200 }}>
      <img src={src} alt={label} loading="lazy" />
      <div className="lp-mission-tile-overlay">
        <span className="text-xs font-semibold uppercase tracking-widest mb-1" style={{ color: 'var(--lp-text-muted)' }}>{label}</span>
        <p className="text-white text-sm font-medium">{impact}</p>
      </div>
    </div>
  );
}

/* ──────────────────────────────────────────────
   Main Page
   ────────────────────────────────────────────── */
export function WelcomePage() {
  const navigate = useNavigate();
  const { t, language } = useTranslation();

  // Live event count
  const [liveCount, setLiveCount] = useState(847);
  useEffect(() => {
    const id = setInterval(() => {
      setLiveCount(c => c + Math.floor(Math.random() * 3));
    }, 4000);
    return () => clearInterval(id);
  }, []);

  // Scroll reveal refs
  const metricsReveal = useScrollReveal();
  const timelineReveal = useScrollReveal();
  const ctaReveal = useScrollReveal();
  const missionReveal = useScrollReveal();

  // Ticker items — built from translations, duplicated for seamless loop
  const tickerItems = [
    `🌧️ ${liveCount.toLocaleString(language)} ${t('lp.ticker.events')}`,
    `🌳 ${t('lp.ticker.risk.value')} ${t('lp.ticker.risk')}`,
    `📡 23 ${t('lp.ticker.states')}`,
    `⚡ ${t('lp.ticker.update')}`,
    `🛰️ ${t('lp.ticker.cemaden')}`,
    `🔗 ${t('lp.ticker.hathor')}`,
  ];
  const tickerFull = [...tickerItems, ...tickerItems];

  // Testimonials — names/roles stay fixed, quotes use t()
  const testimonials = [
    {
      quote: t('lp.testimonials.quote1'),
      name: t('lp.testimonials.name1'),
      role: t('lp.testimonials.role1'),
      initial: "RO",
    },
    {
      quote: t('lp.testimonials.quote2'),
      name: t('lp.testimonials.name2'),
      role: t('lp.testimonials.role2'),
      initial: "CM",
    },
    {
      quote: t('lp.testimonials.quote3'),
      name: t('lp.testimonials.name3'),
      role: t('lp.testimonials.role3'),
      initial: "AF",
    },
  ];

  return (
    <div className="lp-root min-h-screen">

      {/* ── NAV ── */}
      <header
        className="lp-glass fixed top-0 left-0 right-0 z-50"
        style={{ borderBottom: '1px solid var(--lp-glass-border)' }}
      >
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Logo size={36} showText={true} className="drop-shadow-[0_0_8px_rgba(34,197,94,0.4)]"
              style={{ color: '#f0fdf4' } as any}
            />
          </div>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <button
              onClick={() => navigate('/auth')}
              className="lp-btn-primary px-5 py-2 rounded-lg text-sm font-semibold flex items-center gap-2"
            >
              {t('lp.nav.enter')} <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* ── HERO — VIDEO FULL SCREEN ── */}
      <section className="relative min-h-screen flex items-center overflow-hidden">
        {/* Video background — multiple fallback sources */}
        <video
          className="absolute inset-0 w-full h-full object-cover"
          autoPlay
          muted
          loop
          playsInline
          style={{ animation: 'lp-ken-burns 30s ease-in-out infinite' }}
          poster="https://images.unsplash.com/photo-1448375240586-882707db888b?w=1920&q=80&auto=format&fit=crop"
        >
          {/* Pexels free HD video — forest rain. Direct download URL, no auth */}
          <source
            src="https://videos.pexels.com/video-files/3173854/3173854-uhd_2560_1440_25fps.mp4"
            type="video/mp4"
          />
          <source
            src="https://videos.pexels.com/video-files/1448735/1448735-uhd_2560_1440_24fps.mp4"
            type="video/mp4"
          />
        </video>

        {/* Overlay */}
        <div className="lp-video-overlay absolute inset-0" />
        {/* Dots pattern */}
        <div className="lp-dots-bg absolute inset-0 opacity-20" />

        {/* Content */}
        <div className="relative z-10 container mx-auto px-6 pt-32 pb-24">
          {/* Live badge */}
          <div className="mb-8 lp-animate-fade-up flex justify-center">
            <div
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold"
              style={{
                background: 'rgba(34,197,94,0.12)',
                border: '1px solid rgba(34,197,94,0.3)',
                color: '#86efac',
              }}
            >
              <span className="lp-live-dot" />
              {t('lp.hero.live.badge')} — {liveCount.toLocaleString(language)} {t('lp.hero.live')}
            </div>
          </div>

          {/* Headline */}
          <div className="text-center max-w-4xl mx-auto">
            <h1
              className="font-black leading-[1.05] mb-6 lp-animate-fade-up lp-delay-100"
              style={{
                fontSize: 'clamp(2.8rem, 7vw, 6rem)',
                color: '#fff',
                opacity: 0,
              }}
            >
              {t('lp.hero.headline1')}{' '}
              <span className="lp-gradient-text">{t('lp.hero.headline2')}</span>
              <br />
              {t('lp.hero.headline3')}
            </h1>
            <p
              className="text-lg md:text-xl mb-10 leading-relaxed lp-animate-fade-up lp-delay-200 max-w-2xl mx-auto"
              style={{ color: 'rgba(240,253,244,0.75)', opacity: 0 }}
            >
              {t('lp.hero.sub')}
            </p>

            {/* CTAs */}
            <div
              className="flex flex-col sm:flex-row gap-4 justify-center lp-animate-fade-up lp-delay-300"
              style={{ opacity: 0 }}
            >
              <button
                onClick={() => navigate('/dashboard')}
                className="lp-btn-primary lp-btn-glow-pulse px-8 py-4 rounded-xl text-base font-bold flex items-center justify-center gap-3"
              >
                <Leaf className="w-5 h-5" />
                {t('lp.hero.cta.primary')}
                <ArrowRight className="w-5 h-5" />
              </button>
              <button
                onClick={() => navigate('/demo')}
                className="lp-btn-ghost px-8 py-4 rounded-xl text-base font-bold flex items-center justify-center gap-3"
              >
                <Play className="w-5 h-5" />
                {t('lp.hero.cta.secondary')}
              </button>
            </div>
          </div>

          {/* Scroll indicator */}
          <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-50">
            <span className="text-xs font-medium tracking-widest uppercase" style={{ color: 'var(--lp-text-muted)' }}>
              {t('lp.hero.scroll')}
            </span>
            <div className="w-px h-12 bg-gradient-to-b from-green-400 to-transparent" />
          </div>
        </div>
      </section>

      {/* ── IMPACT TICKER ── */}
      <div className="lp-ticker-wrap py-4" style={{ background: 'var(--lp-bg-2)' }}>
        <div className="lp-ticker-track">
          {tickerFull.map((item, i) => (
            <span key={i} className="px-8 text-sm font-medium" style={{ color: 'var(--lp-text-muted)' }}>
              {item}
              <span className="mx-6 opacity-20">·</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── NOSSA MISSÃO — Photo Grid ── */}
      <section className="py-24 px-6" style={{ background: 'var(--lp-bg)' }}>
        <div
          ref={missionReveal.ref}
          className={missionReveal.visible ? 'lp-section-visible' : 'lp-section-hidden'}
        >
          <div className="container mx-auto max-w-6xl">
            <div className="mb-12">
              <span className="text-xs font-bold tracking-[0.2em] uppercase lp-gradient-text">
                {t('lp.mission.tag')}
              </span>
              <h2
                className="font-black mt-3 leading-tight"
                style={{ fontSize: 'clamp(2rem, 5vw, 3.5rem)', color: '#fff' }}
              >
                {t('lp.mission.h1')}
                <br />
                <span className="lp-gradient-text">{t('lp.mission.h2')}</span>
              </h2>
              <p className="mt-4 text-base md:text-lg max-w-2xl leading-relaxed" style={{ color: 'rgba(240,253,244,0.6)' }}>
                {t('lp.mission.desc')}
              </p>
            </div>

            {/* Asymmetric grid — Unsplash images (CORS-free, always available) */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <MissionTile
                className="col-span-2 row-span-2"
                src="https://images.unsplash.com/photo-1448375240586-882707db888b?w=800&q=80&auto=format&fit=crop"
                label={t('lp.mission.tile.forest')}
                impact={t('lp.mission.tile.forest.impact')}
              />
              <MissionTile
                src="https://images.unsplash.com/photo-1547683905-f686c993aae5?w=600&h=300&q=80&auto=format&fit=crop"
                label={t('lp.mission.tile.floods')}
                impact={t('lp.mission.tile.floods.impact')}
              />
              <MissionTile
                src="https://images.unsplash.com/photo-1504701954957-2010ec3bcec1?w=600&h=300&q=80&auto=format&fit=crop"
                label={t('lp.mission.tile.drought')}
                impact={t('lp.mission.tile.drought.impact')}
              />
              <MissionTile
                src="https://images.unsplash.com/photo-1508193638397-1c4234db14d8?w=600&h=300&q=80&auto=format&fit=crop"
                label={t('lp.mission.tile.storms')}
                impact={t('lp.mission.tile.storms.impact')}
              />
              <MissionTile
                src="https://images.unsplash.com/photo-1491002052546-bf38f186af56?w=600&h=300&q=80&auto=format&fit=crop"
                label={t('lp.mission.tile.frost')}
                impact={t('lp.mission.tile.frost.impact')}
              />
            </div>
          </div>
        </div>
      </section>

      {/* ── METRICS ── */}
      <section className="py-24 px-6 lp-dots-bg" style={{ background: 'var(--lp-bg-2)' }}>
        <div
          ref={metricsReveal.ref}
          className={`container mx-auto max-w-5xl ${metricsReveal.visible ? 'lp-section-visible' : 'lp-section-hidden'}`}
        >
          <div className="text-center mb-14">
            <span className="text-xs font-bold tracking-[0.2em] uppercase lp-gradient-text">
              {t('lp.metrics.tag')}
            </span>
            <h2 className="font-black mt-3 text-3xl md:text-5xl text-white">{t('lp.metrics.title')}</h2>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            <MetricCard icon={<Leaf className="w-7 h-7" />} value={1200000} suffix="+" label={t('lp.metrics.co2')} active={metricsReveal.visible} />
            <MetricCard icon={<Waves className="w-7 h-7" />} value={5847} suffix="" label={t('lp.metrics.events')} active={metricsReveal.visible} />
            <MetricCard icon={<Coins className="w-7 h-7" />} value={2400} suffix="M" label={t('lp.metrics.risk')} active={metricsReveal.visible} />
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="py-24 px-6" style={{ background: 'var(--lp-bg)' }}>
        <div
          ref={timelineReveal.ref}
          className={`container mx-auto max-w-5xl ${timelineReveal.visible ? 'lp-section-visible' : 'lp-section-hidden'}`}
        >
          <div className="text-center mb-16">
            <span className="text-xs font-bold tracking-[0.2em] uppercase lp-gradient-text">{t('lp.how.tag')}</span>
            <h2 className="font-black mt-3 text-3xl md:text-5xl text-white">{t('lp.how.title')}</h2>
            <p className="mt-3 max-w-xl mx-auto text-base" style={{ color: 'rgba(240,253,244,0.55)' }}>
              {t('lp.how.sub')}
            </p>
          </div>
          {/* Desktop: horizontal */}
          <div className="hidden md:flex items-start relative">
            <TimelineStep icon={<Satellite className="w-7 h-7" />} number="1" title={t('lp.how.step1.title')} desc={t('lp.how.step1.desc')} />
            <div className="lp-timeline-connector mt-8" />
            <TimelineStep icon={<BrainCircuit className="w-7 h-7" />} number="2" title={t('lp.how.step2.title')} desc={t('lp.how.step2.desc')} />
            <div className="lp-timeline-connector mt-8" />
            <TimelineStep icon={<Coins className="w-7 h-7" />} number="3" title={t('lp.how.step3.title')} desc={t('lp.how.step3.desc')} />
            <div className="lp-timeline-connector mt-8" />
            <TimelineStep icon={<Zap className="w-7 h-7" />} number="4" title={t('lp.how.step4.title')} desc={t('lp.how.step4.desc')} />
          </div>
          {/* Mobile: vertical */}
          <div className="flex md:hidden flex-col gap-8">
            {([
              { icon: <Satellite className="w-6 h-6" />, n: "1", title: t('lp.how.step1.title'), desc: t('lp.how.step1.desc') },
              { icon: <BrainCircuit className="w-6 h-6" />, n: "2", title: t('lp.how.step2.title'), desc: t('lp.how.step2.desc') },
              { icon: <Coins className="w-6 h-6" />, n: "3", title: t('lp.how.step3.title'), desc: t('lp.how.step3.desc') },
              { icon: <Zap className="w-6 h-6" />, n: "4", title: t('lp.how.step4.title'), desc: t('lp.how.step4.desc') },
            ] as const).map((s) => (
              <div key={s.n} className="flex gap-4 items-start">
                <div className="lp-timeline-step-icon text-green-400 relative shrink-0" style={{ width: 52, height: 52 }}>
                  {s.icon}
                  <span className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-green-500 text-white text-xs font-bold flex items-center justify-center">{s.n}</span>
                </div>
                <div>
                  <h4 className="font-bold text-white mb-1">{s.title}</h4>
                  <p className="text-sm leading-relaxed" style={{ color: 'var(--lp-text-muted)' }}>{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ── */}
      <section className="py-24 px-6" style={{ background: 'var(--lp-bg-2)' }}>
        <div className="container mx-auto max-w-5xl">
          <div className="text-center mb-14">
            <span className="text-xs font-bold tracking-[0.2em] uppercase lp-gradient-text">{t('lp.testimonials.tag')}</span>
            <h2 className="font-black mt-3 text-3xl md:text-4xl text-white">{t('lp.testimonials.title')}</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((testimony, i) => (
              <div key={i} className="lp-testimonial">
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_, k) => (
                    <Star key={k} className="w-4 h-4 fill-green-400 text-green-400" />
                  ))}
                </div>
                <p className="text-sm leading-relaxed mb-6" style={{ color: 'rgba(240,253,244,0.7)' }}>
                  {testimony.quote}
                </p>
                <div className="flex items-center gap-3">
                  <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold text-white"
                    style={{ background: 'linear-gradient(135deg, #22c55e, #0891b2)' }}
                  >
                    {testimony.initial}
                  </div>
                  <div>
                    <div className="font-semibold text-sm text-white">{testimony.name}</div>
                    <div className="text-xs" style={{ color: 'var(--lp-text-muted)' }}>{testimony.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── EVENT TYPES STRIP ── */}
      <section className="py-16 px-6" style={{ background: 'var(--lp-bg)' }}>
        <div className="container mx-auto max-w-4xl">
          <p className="text-center text-sm font-semibold mb-8 uppercase tracking-widest" style={{ color: 'rgba(240,253,244,0.35)' }}>
            {t('lp.events.label')}
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {([
              { icon: <Waves className="w-6 h-6" />, key: 'lp.events.floods', color: "#06b6d4" },
              { icon: <Flame className="w-6 h-6" />, key: 'lp.events.fires', color: "#f97316" },
              { icon: <Snowflake className="w-6 h-6" />, key: 'lp.events.frost', color: "#a5f3fc" },
              { icon: <Leaf className="w-6 h-6" />, key: 'lp.events.drought', color: "#84cc16" },
            ] as const).map((ev) => (
              <div
                key={ev.key}
                className="lp-glass rounded-xl p-5 flex flex-col items-center gap-3 text-center"
              >
                <span style={{ color: ev.color }}>{ev.icon}</span>
                <span className="text-sm font-semibold text-white">{t(ev.key)}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA FINAL ── */}
      <section
        className="py-32 px-6 relative overflow-hidden"
        style={{ background: 'linear-gradient(to bottom, var(--lp-bg-2), var(--lp-bg))' }}
      >
        <div className="lp-cta-glow absolute inset-0" />
        <div
          ref={ctaReveal.ref}
          className={`relative z-10 container mx-auto max-w-3xl text-center ${ctaReveal.visible ? 'lp-section-visible' : 'lp-section-hidden'}`}
        >
          <span className="text-green-400 text-xs font-bold tracking-[0.25em] uppercase">{t('lp.cta.tag')}</span>
          <h2
            className="font-black mt-4 leading-tight text-white"
            style={{ fontSize: 'clamp(2.2rem, 5vw, 4rem)' }}
          >
            {t('lp.cta.title1')}<br />
            <span className="lp-gradient-text">{t('lp.cta.title2')}</span>
          </h2>
          <p className="mt-6 text-lg mb-10" style={{ color: 'rgba(240,253,244,0.60)' }}>
            {t('lp.cta.sub')}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={() => navigate('/auth')}
              className="lp-btn-primary lp-btn-glow-pulse px-10 py-5 rounded-xl text-lg font-bold flex items-center justify-center gap-3"
            >
              <Leaf className="w-5 h-5" />
              {t('lp.cta.primary')}
            </button>
            <button
              onClick={() => navigate('/auth')}
              className="lp-btn-ghost px-10 py-5 rounded-xl text-lg font-bold flex items-center justify-center gap-3"
            >
              {t('lp.cta.secondary')}
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer
        className="py-16 px-6"
        style={{ background: 'var(--lp-bg)', borderTop: '1px solid var(--lp-glass-border)' }}
      >
        <div className="container mx-auto max-w-6xl">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-12">
            <div className="md:col-span-2">
              <div className="flex items-center gap-3 mb-4">
                <Logo size={36} showText={true}
                  className="drop-shadow-[0_0_8px_rgba(34,197,94,0.4)]"
                />
              </div>
              <p className="text-sm leading-relaxed max-w-xs" style={{ color: 'rgba(240,253,244,0.45)' }}>
                {t('lp.footer.tagline')}
              </p>
              <p className="mt-6 text-xs" style={{ color: 'rgba(240,253,244,0.25)' }}>
                {t('lp.footer.copyright')}
              </p>
            </div>
            <div>
              <h5 className="font-bold text-white mb-4 text-sm">{t('lp.footer.platform')}</h5>
              <ul className="space-y-2">
                {['Dashboard', 'Atlas', 'Tokenização', 'Analytics', 'Lab Atuarial'].map(l => (
                  <li key={l}>
                    <button
                      onClick={() => navigate('/auth')}
                      className="text-sm hover:text-green-400 transition-colors"
                      style={{ color: 'rgba(240,253,244,0.45)' }}
                    >
                      {l}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h5 className="font-bold text-white mb-4 text-sm">{t('lp.footer.company')}</h5>
              <ul className="space-y-2">
                {['Blog', 'Suporte', 'Termos', 'Privacidade'].map(l => (
                  <li key={l}>
                    <span className="text-sm cursor-default" style={{ color: 'rgba(240,253,244,0.45)' }}>{l}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
          <div
            className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4"
            style={{ borderTop: '1px solid var(--lp-glass-border)' }}
          >
            <div className="flex gap-4">
              {[
                { label: "CEMADEN", tip: "Integração oficial" },
                { label: "Hathor", tip: "Blockchain parceira" },
                { label: "SUSEP", tip: "Em conformidade" },
              ].map(b => (
                <span
                  key={b.label}
                  className="text-xs px-3 py-1 rounded-full font-semibold"
                  style={{
                    background: 'rgba(34,197,94,0.1)',
                    border: '1px solid rgba(34,197,94,0.2)',
                    color: '#86efac',
                  }}
                  title={b.tip}
                >
                  {b.label}
                </span>
              ))}
            </div>
            <span className="text-xs" style={{ color: 'rgba(240,253,244,0.2)' }}>
              {t('lp.footer.motto')}
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}

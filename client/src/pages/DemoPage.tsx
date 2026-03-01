import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "@/hooks/useTranslation";
import { Logo } from "@/components/Logo";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import {
    ArrowRight, X, Play, Pause, ChevronLeft, ChevronRight,
    LayoutDashboard, Globe2, Coins, BarChart3, FlaskConical,
    Zap, Satellite, BrainCircuit, Shield, CheckCircle2, ArrowUpRight,
} from "lucide-react";

/* ──────────────────────────────────────────────
   Browser mockup wrapper
   ────────────────────────────────────────────── */
function BrowserFrame({ src, alt }: { src: string; alt: string }) {
    return (
        <div className="rounded-xl overflow-hidden shadow-2xl border" style={{ borderColor: "rgba(255,255,255,0.1)" }}>
            <div
                className="flex items-center gap-2 px-4 py-3"
                style={{ background: "rgba(15,20,15,0.95)", borderBottom: "1px solid rgba(255,255,255,0.08)" }}
            >
                <span className="w-3 h-3 rounded-full bg-red-500 opacity-70" />
                <span className="w-3 h-3 rounded-full bg-yellow-400 opacity-70" />
                <span className="w-3 h-3 rounded-full bg-green-500 opacity-70" />
                <div
                    className="ml-3 flex-1 rounded-md px-3 py-1 text-xs font-mono"
                    style={{ background: "rgba(255,255,255,0.06)", color: "rgba(255,255,255,0.4)" }}
                >
                    localhost:5173
                </div>
            </div>
            <img src={src} alt={alt} className="w-full block" style={{ maxHeight: 480, objectFit: "cover", objectPosition: "top" }} />
        </div>
    );
}

/* ──────────────────────────────────────────────
   Auto-play progress bar
   ────────────────────────────────────────────── */
function ProgressBar({ duration, active, onComplete }: { duration: number; active: boolean; onComplete: () => void }) {
    const [width, setWidth] = useState(0);
    const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    useEffect(() => {
        if (!active) { setWidth(0); return; }
        setWidth(0);
        const step = 100 / (duration / 100);
        intervalRef.current = setInterval(() => {
            setWidth(w => {
                if (w >= 100) { clearInterval(intervalRef.current!); onComplete(); return 100; }
                return w + step;
            });
        }, 100);
        return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
    }, [active, duration]);

    return (
        <div className="h-0.5 w-full rounded-full" style={{ background: "rgba(255,255,255,0.1)" }}>
            <div className="h-full rounded-full transition-none" style={{ width: `${width}%`, background: "var(--active-accent, #22c55e)" }} />
        </div>
    );
}

/* ──────────────────────────────────────────────
   Main DemoPage
   ────────────────────────────────────────────── */
export function DemoPage() {
    const navigate = useNavigate();
    const { t } = useTranslation();
    const [activeIdx, setActiveIdx] = useState(0);
    const [playing, setPlaying] = useState(true);
    const SLIDE_DURATION = 6000;

    const features = [
        {
            id: "dashboard",
            icon: <LayoutDashboard className="w-5 h-5" />,
            label: t('demo.feature.dashboard.label'),
            subtitle: t('demo.feature.dashboard.subtitle'),
            description: t('demo.feature.dashboard.description'),
            image: "/demo/dashboard.png",
            imageAlt: "Climate Dashboard",
            highlights: [
                t('demo.feature.dashboard.h1'),
                t('demo.feature.dashboard.h2'),
                t('demo.feature.dashboard.h3'),
                t('demo.feature.dashboard.h4'),
            ],
            accent: "#22c55e",
            accentLight: "rgba(34,197,94,0.12)",
        },
        {
            id: "charts",
            icon: <BarChart3 className="w-5 h-5" />,
            label: t('demo.feature.charts.label'),
            subtitle: t('demo.feature.charts.subtitle'),
            description: t('demo.feature.charts.description'),
            image: "/demo/dashboard-charts.png",
            imageAlt: "Climate Charts",
            highlights: [
                t('demo.feature.charts.h1'),
                t('demo.feature.charts.h2'),
                t('demo.feature.charts.h3'),
                t('demo.feature.charts.h4'),
            ],
            accent: "#06b6d4",
            accentLight: "rgba(6,182,212,0.12)",
        },
        {
            id: "atlas",
            icon: <Globe2 className="w-5 h-5" />,
            label: t('demo.feature.atlas.label'),
            subtitle: t('demo.feature.atlas.subtitle'),
            description: t('demo.feature.atlas.description'),
            image: "/demo/atlas.png",
            imageAlt: "Digital Atlas 3D Globe",
            highlights: [
                t('demo.feature.atlas.h1'),
                t('demo.feature.atlas.h2'),
                t('demo.feature.atlas.h3'),
                t('demo.feature.atlas.h4'),
            ],
            accent: "#8b5cf6",
            accentLight: "rgba(139,92,246,0.12)",
        },
        {
            id: "tokenization",
            icon: <Coins className="w-5 h-5" />,
            label: t('demo.feature.tokenization.label'),
            subtitle: t('demo.feature.tokenization.subtitle'),
            description: t('demo.feature.tokenization.description'),
            image: "/demo/tokenization.png",
            imageAlt: "Tokenization Page",
            highlights: [
                t('demo.feature.tokenization.h1'),
                t('demo.feature.tokenization.h2'),
                t('demo.feature.tokenization.h3'),
                t('demo.feature.tokenization.h4'),
            ],
            accent: "#f59e0b",
            accentLight: "rgba(245,158,11,0.12)",
        },
        {
            id: "analytics",
            icon: <BarChart3 className="w-5 h-5" />,
            label: t('demo.feature.analytics.label'),
            subtitle: t('demo.feature.analytics.subtitle'),
            description: t('demo.feature.analytics.description'),
            image: "/demo/analytics.png",
            imageAlt: "Analytics Page",
            highlights: [
                t('demo.feature.analytics.h1'),
                t('demo.feature.analytics.h2'),
                t('demo.feature.analytics.h3'),
                t('demo.feature.analytics.h4'),
            ],
            accent: "#ec4899",
            accentLight: "rgba(236,72,153,0.12)",
        },
        {
            id: "actuarial",
            icon: <FlaskConical className="w-5 h-5" />,
            label: t('demo.feature.actuarial.label'),
            subtitle: t('demo.feature.actuarial.subtitle'),
            description: t('demo.feature.actuarial.description'),
            image: "/demo/actuarial-lab.png",
            imageAlt: "Actuarial Lab",
            highlights: [
                t('demo.feature.actuarial.h1'),
                t('demo.feature.actuarial.h2'),
                t('demo.feature.actuarial.h3'),
                t('demo.feature.actuarial.h4'),
            ],
            accent: "#10b981",
            accentLight: "rgba(16,185,129,0.12)",
        },
    ];

    const active = features[activeIdx];

    const goNext = () => setActiveIdx(i => (i + 1) % features.length);
    const goPrev = () => setActiveIdx(i => (i - 1 + features.length) % features.length);

    return (
        <div className="min-h-screen" style={{ background: "#070d0a", fontFamily: "'Plus Jakarta Sans', 'Inter', sans-serif", color: "#f0fdf4" }}>

            {/* ── NAV ── */}
            <header
                className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4"
                style={{ background: "rgba(7,13,10,0.9)", backdropFilter: "blur(16px)", borderBottom: "1px solid rgba(255,255,255,0.07)" }}
            >
                <button onClick={() => navigate("/")} className="hover:opacity-80 transition-opacity">
                    <Logo size={32} showText />
                </button>
                <div className="flex items-center gap-4">
                    <LanguageSwitcher />
                    <span className="text-xs font-semibold px-3 py-1 rounded-full" style={{ background: "rgba(34,197,94,0.15)", border: "1px solid rgba(34,197,94,0.3)", color: "#86efac" }}>
                        {t('demo.nav.interactive')}
                    </span>
                    <button
                        onClick={() => navigate("/auth")}
                        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold text-white"
                        style={{ background: "linear-gradient(135deg, #22c55e, #16a34a)" }}
                    >
                        {t('demo.nav.getStarted')} <ArrowRight className="w-4 h-4" />
                    </button>
                    <button onClick={() => navigate("/")} className="p-2 rounded-lg hover:bg-white/5 transition-colors" style={{ color: "rgba(240,253,244,0.5)" }}>
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </header>

            {/* ── HERO ── */}
            <section className="pt-32 pb-16 px-6 text-center">
                <div className="max-w-3xl mx-auto">
                    <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold mb-6" style={{ background: "rgba(34,197,94,0.1)", border: "1px solid rgba(34,197,94,0.25)", color: "#86efac" }}>
                        <span className="w-2 h-2 rounded-full animate-pulse" style={{ background: "#22c55e" }} />
                        {t('demo.hero.badge')}
                    </div>
                    <h1 className="font-black leading-tight mb-4" style={{ fontSize: "clamp(2.2rem, 5vw, 4rem)" }}>
                        {t('demo.hero.titlePart1')}
                        <span style={{ background: "linear-gradient(135deg, #22c55e, #06b6d4)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>
                            {t('demo.hero.titlePart2')}
                        </span>
                    </h1>
                    <p className="text-lg mb-8" style={{ color: "rgba(240,253,244,0.6)" }}>
                        {t('demo.hero.description')}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-3 justify-center">
                        <button
                            onClick={() => navigate("/auth")}
                            className="px-8 py-4 rounded-xl text-base font-bold flex items-center justify-center gap-3 text-white"
                            style={{ background: "linear-gradient(135deg, #22c55e, #16a34a)", boxShadow: "0 0 32px rgba(34,197,94,0.3)" }}
                        >
                            {t('demo.hero.cta.platform')} <ArrowUpRight className="w-5 h-5" />
                        </button>
                        <button
                            onClick={() => navigate("/")}
                            className="px-8 py-4 rounded-xl text-base font-bold"
                            style={{ border: "1px solid rgba(255,255,255,0.15)", color: "rgba(240,253,244,0.7)" }}
                        >
                            {t('demo.hero.cta.home')}
                        </button>
                    </div>
                </div>
            </section>

            {/* ── INTERACTIVE SHOWCASE ── */}
            <section className="py-8 px-6 max-w-7xl mx-auto">

                {/* Feature tab bar */}
                <div className="flex flex-wrap gap-2 justify-center mb-10">
                    {features.map((f, i) => (
                        <button
                            key={f.id}
                            onClick={() => { setActiveIdx(i); setPlaying(false); }}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-semibold transition-all"
                            style={{
                                background: i === activeIdx ? f.accent + "22" : "rgba(255,255,255,0.04)",
                                border: `1px solid ${i === activeIdx ? f.accent + "55" : "rgba(255,255,255,0.08)"}`,
                                color: i === activeIdx ? f.accent : "rgba(240,253,244,0.5)",
                                transform: i === activeIdx ? "scale(1.04)" : "scale(1)",
                            }}
                        >
                            <span style={{ color: i === activeIdx ? f.accent : "rgba(240,253,244,0.4)" }}>{f.icon}</span>
                            {f.label}
                        </button>
                    ))}
                </div>

                {/* Main content split */}
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-8 items-start">

                    {/* Left: info panel */}
                    <div className="lg:col-span-2 space-y-6">
                        <div>
                            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest mb-3" style={{ background: active.accentLight, color: active.accent }}>
                                <span>{active.icon}</span> {active.label}
                            </div>
                            <h2 className="font-black text-3xl text-white leading-tight mb-2">{active.subtitle}</h2>
                            <p className="text-base leading-relaxed" style={{ color: "rgba(240,253,244,0.6)" }}>{active.description}</p>
                        </div>

                        <div className="space-y-3">
                            {active.highlights.map((h, i) => (
                                <div key={i} className="flex items-start gap-3">
                                    <CheckCircle2 className="w-5 h-5 mt-0.5 shrink-0" style={{ color: active.accent }} />
                                    <span className="text-sm leading-snug" style={{ color: "rgba(240,253,244,0.75)" }}>{h}</span>
                                </div>
                            ))}
                        </div>

                        <button
                            onClick={() => navigate("/auth")}
                            className="w-full py-3 rounded-xl font-bold text-sm flex items-center justify-center gap-2 text-white transition-all hover:scale-[1.02]"
                            style={{ background: `linear-gradient(135deg, ${active.accent}, ${active.accent}99)`, boxShadow: `0 0 24px ${active.accent}44` }}
                        >
                            {t('demo.feature.tryNow').replace('{{feature}}', active.label)} <ArrowRight className="w-4 h-4" />
                        </button>

                        {/* Slide nav */}
                        <div className="flex items-center justify-between pt-2">
                            <button onClick={goPrev} className="p-2 rounded-lg hover:bg-white/5 transition-colors" style={{ color: "rgba(240,253,244,0.4)", border: "1px solid rgba(255,255,255,0.1)" }}>
                                <ChevronLeft className="w-5 h-5" />
                            </button>
                            <div className="flex gap-1.5">
                                {features.map((_, i) => (
                                    <button
                                        key={i}
                                        onClick={() => { setActiveIdx(i); setPlaying(false); }}
                                        className="rounded-full transition-all"
                                        style={{ width: i === activeIdx ? 20 : 6, height: 6, background: i === activeIdx ? active.accent : "rgba(255,255,255,0.2)" }}
                                    />
                                ))}
                            </div>
                            <button onClick={goNext} className="p-2 rounded-lg hover:bg-white/5 transition-colors" style={{ color: "rgba(240,253,244,0.4)", border: "1px solid rgba(255,255,255,0.1)" }}>
                                <ChevronRight className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="space-y-2">
                            <div className="flex items-center justify-between">
                                <span className="text-xs" style={{ color: "rgba(240,253,244,0.35)" }}>{activeIdx + 1} / {features.length}</span>
                                <button onClick={() => setPlaying(p => !p)} className="flex items-center gap-1.5 text-xs transition-colors" style={{ color: "rgba(240,253,244,0.5)" }}>
                                    {playing ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                                    {playing ? t('demo.controls.pause') : t('demo.controls.play')}
                                </button>
                            </div>
                            <div style={{ "--active-accent": active.accent } as React.CSSProperties}>
                                <ProgressBar duration={SLIDE_DURATION} active={playing} onComplete={goNext} key={`${activeIdx}-${playing}`} />
                            </div>
                        </div>
                    </div>

                    {/* Right: screenshot */}
                    <div className="lg:col-span-3">
                        <BrowserFrame src={active.image} alt={active.imageAlt} />
                    </div>
                </div>
            </section>

            {/* ── PLATFORM PILLARS ── */}
            <section className="py-20 px-6" style={{ background: "rgba(12,23,16,0.8)" }}>
                <div className="max-w-5xl mx-auto">
                    <div className="text-center mb-14">
                        <h2 className="font-black text-3xl md:text-4xl text-white mb-3">{t('demo.pillars.title')}</h2>
                        <p className="text-base" style={{ color: "rgba(240,253,244,0.55)" }}>
                            {t('demo.pillars.subtitle')}
                        </p>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                        {[
                            { icon: <Satellite className="w-7 h-7" />, color: "#06b6d4", title: t('demo.pillars.p1.title'), desc: t('demo.pillars.p1.desc') },
                            { icon: <BrainCircuit className="w-7 h-7" />, color: "#22c55e", title: t('demo.pillars.p2.title'), desc: t('demo.pillars.p2.desc') },
                            { icon: <Shield className="w-7 h-7" />, color: "#8b5cf6", title: t('demo.pillars.p3.title'), desc: t('demo.pillars.p3.desc') },
                            { icon: <Zap className="w-7 h-7" />, color: "#f59e0b", title: t('demo.pillars.p4.title'), desc: t('demo.pillars.p4.desc') },
                            { icon: <Globe2 className="w-7 h-7" />, color: "#ec4899", title: t('demo.pillars.p5.title'), desc: t('demo.pillars.p5.desc') },
                            { icon: <BarChart3 className="w-7 h-7" />, color: "#10b981", title: t('demo.pillars.p6.title'), desc: t('demo.pillars.p6.desc') },
                        ].map((p, i) => (
                            <div key={i} className="rounded-xl p-6 transition-all hover:-translate-y-1" style={{ background: `${p.color}0d`, border: `1px solid ${p.color}22` }}>
                                <div className="mb-4" style={{ color: p.color }}>{p.icon}</div>
                                <h3 className="font-bold text-white mb-2 text-sm">{p.title}</h3>
                                <p className="text-xs leading-relaxed" style={{ color: "rgba(240,253,244,0.55)" }}>{p.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </section>

            {/* ── FINAL CTA ── */}
            <section className="py-24 px-6 text-center relative overflow-hidden">
                <div className="absolute inset-0" style={{ background: "radial-gradient(ellipse 50% 50% at 50% 100%, rgba(34,197,94,0.18) 0%, transparent 70%)" }} />
                <div className="relative max-w-2xl mx-auto">
                    <h2 className="font-black text-white leading-tight mb-4" style={{ fontSize: "clamp(2rem, 4vw, 3.5rem)" }}>
                        {t('demo.final.title')}
                    </h2>
                    <p className="text-lg mb-10" style={{ color: "rgba(240,253,244,0.6)" }}>
                        {t('demo.final.subtitle')}
                    </p>
                    <div className="flex flex-col sm:flex-row gap-4 justify-center">
                        <button
                            onClick={() => navigate("/auth")}
                            className="px-10 py-5 rounded-xl text-lg font-bold text-white flex items-center justify-center gap-3"
                            style={{ background: "linear-gradient(135deg, #22c55e, #16a34a)", boxShadow: "0 0 48px rgba(34,197,94,0.35)" }}
                        >
                            {t('demo.final.cta')} <ArrowRight className="w-5 h-5" />
                        </button>
                        <button
                            onClick={() => navigate("/")}
                            className="px-10 py-5 rounded-xl text-lg font-bold"
                            style={{ border: "1px solid rgba(255,255,255,0.15)", color: "rgba(240,253,244,0.7)" }}
                        >
                            {t('demo.hero.cta.home')}
                        </button>
                    </div>
                </div>
            </section>

            {/* ── FOOTER ── */}
            <footer className="py-8 px-6 text-center" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                <Logo size={28} showText className="justify-center mx-auto mb-3" />
                <p className="text-xs" style={{ color: "rgba(240,253,244,0.25)" }}>
                    {t('demo.footer.copyright')}
                </p>
            </footer>
        </div>
    );
}

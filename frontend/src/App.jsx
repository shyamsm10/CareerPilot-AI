import { useState, useRef, useEffect, useCallback } from "react";
import { 
  Menu, X, Rocket, ArrowRight, ArrowLeft, Sparkles, Zap, 
  Target, TrendingUp, FileText, Briefcase, MessageSquare, 
  Brain, Activity, Upload, Check, Mic, PartyPopper, 
  Play, Star, ChevronRight
} from "lucide-react";
import "./App.css";

const API = "http://127.0.0.1:8000"; 
const STEPS = ["Upload", "Analysis", "Skills", "Jobs", "Interview"];

// ── Palette ─────────────────────────────────────────────────────────────────
const C = {
  violet: "#7B5CF0", mint: "#00FFB3", amber: "#FF9F1C", coral: "#FF4D6D",
  text: "#F0F0F8", dim: "#8080A0", muted: "#3a3a55",
};

// ── Particle Canvas ────────────────────────────────────────────────────────
function ParticleCanvas() {
  const ref = useRef(null);
  const mouse = useRef({ x: -9999, y: -9999 });

  useEffect(() => {
    const canvas = ref.current;
    const ctx = canvas.getContext("2d");
    let W, H, pts, raf;

    const resize = () => {
      W = canvas.width = window.innerWidth;
      H = canvas.height = window.innerHeight;
      pts = Array.from({ length: 80 }, () => ({
        x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.25, vy: (Math.random() - 0.5) * 0.25,
        r: Math.random() * 1.2 + 0.3,
        color: [C.violet, C.mint, "#fff"][Math.floor(Math.random() * 3)],
        opacity: Math.random() * 0.4 + 0.1
      }));
    };

    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      pts.forEach(p => {
        const dx = mouse.current.x - p.x;
        const dy = mouse.current.y - p.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
          p.vx -= dx * 0.0003;
          p.vy -= dy * 0.0003;
        }
        p.x += p.vx; p.y += p.vy;
        p.vx *= 0.99; p.vy *= 0.99;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + Math.round(p.opacity * 255).toString(16).padStart(2, '0');
        ctx.fill();
      });
      for (let i = 0; i < pts.length; i++) {
        for (let j = i + 1; j < pts.length; j++) {
          const dx = pts[i].x - pts[j].x, dy = pts[i].y - pts[j].y;
          const d = Math.sqrt(dx * dx + dy * dy);
          if (d < 110) {
            ctx.beginPath();
            ctx.moveTo(pts[i].x, pts[i].y);
            ctx.lineTo(pts[j].x, pts[j].y);
            ctx.strokeStyle = `rgba(123,92,240,${(1 - d / 110) * 0.12})`;
            ctx.lineWidth = 0.5;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(draw);
    };

    resize();
    draw();
    window.addEventListener("resize", resize);
    const onMouse = e => { mouse.current.x = e.clientX; mouse.current.y = e.clientY; };
    window.addEventListener("mousemove", onMouse);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouse);
    };
  }, []);

  return <canvas ref={ref} id="particle-canvas" />;
}

// ── Shared Components ──────────────────────────────────────────────────────
function Card({ children, style = {}, hover, aurora, className = "", onClick }) {
  const cls = ["card", hover ? "card-hover" : "", aurora ? "card-aurora" : "", className].filter(Boolean).join(" ");
  return <div className={cls} style={style} onClick={onClick}>{children}</div>;
}

function Chip({ children, color = C.mint, size = "sm" }) {
  const pad = size === "sm" ? "3px 10px" : "5px 14px";
  const fs = size === "sm" ? 11 : 13;
  return (
    <span className="chip" style={{
      background: color + "1a", color, border: `1px solid ${color}30`,
      padding: pad, fontSize: fs
    }}>{children}</span>
  );
}

function Tag({ children, type = "match" }) {
  const map = { match: C.mint, missing: C.coral, bonus: C.amber };
  return <Chip color={map[type]}>{children}</Chip>;
}

function ScoreBar({ value }) {
  const color = value >= 70 ? C.mint : value >= 45 ? C.amber : C.coral;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
      <div className="score-track" style={{ flex: 1 }}>
        <div className="score-fill" style={{ width: `${value}%`, background: `linear-gradient(90deg,${color},${color}88)` }} />
      </div>
      <span style={{ color, fontSize: 13, fontFamily: "var(--font-mono)", minWidth: 36, textAlign: "right" }}>{value}%</span>
    </div>
  );
}

function StatBlock({ label, value, color = C.violet, sub }) {
  return (
    <Card style={{ textAlign: "center", padding: "22px 16px" }} className="shimmer-wrap">
      <div style={{ fontSize: 30, fontWeight: 800, color, lineHeight: 1, marginBottom: 4, fontFamily: "var(--font-display)" }}>{value}</div>
      {sub && <div style={{ color: C.mint, fontSize: 10, fontFamily: "var(--font-mono)", marginBottom: 4 }}>{sub}</div>}
      <div className="lbl" style={{ marginBottom: 0 }}>{label}</div>
    </Card>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// LANDING PAGE COMPONENTS
// ════════════════════════════════════════════════════════════════════════════

// ── Navbar ─────────────────────────────────────────────────────────────────
function Navbar({ activeSection, scrollToSection, onGetStarted }) {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const links = [
    { id: "hero", label: "Home" },
    { id: "features", label: "Features" },
    { id: "how-it-works", label: "How it Works" },
    { id: "agents", label: "9 AI Agents" },
    { id: "stats", label: "Impact" },
  ];

  return (
    <>
      <nav className={`navbar ${scrolled ? "scrolled" : ""}`} aria-label="Main navigation">
        <div className="navbar-inner">
          <a href="#hero" className="navbar-logo" onClick={(e) => { e.preventDefault(); scrollToSection(0); }}>
            <div style={{
              width: 36, height: 36, borderRadius: 10,
              background: "linear-gradient(135deg, var(--violet), var(--mint))",
              display: "flex", alignItems: "center", justifyContent: "center",
              boxShadow: "0 4px 20px rgba(123,92,240,0.4)"
            }}>
              <Rocket size={18} color="#fff" />
            </div>
            <span>CareerPilot <span className="grad-mint">AI</span></span>
          </a>

          <div className="navbar-links">
            {links.map((link, idx) => (
              <a
                key={link.id}
                href={`#${link.id}`}
                className="navbar-link"
                onClick={(e) => { e.preventDefault(); scrollToSection(idx); }}
                style={activeSection === idx ? { color: "var(--mint)" } : {}}
              >
                {link.label}
              </a>
            ))}
            <button onClick={onGetStarted} className="navbar-cta">
              Launch Now <ArrowRight size={14} style={{ marginLeft: 4 }} />
            </button>
          </div>

          <button
            className="navbar-mobile-toggle"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </nav>

      {mobileOpen && (
        <div className="mobile-menu">
          {links.map((link, idx) => (
            <a
              key={link.id}
              href={`#${link.id}`}
              className="mobile-menu-link"
              onClick={(e) => {
                e.preventDefault();
                scrollToSection(idx);
                setMobileOpen(false);
              }}
            >
              {link.label}
            </a>
          ))}
          <button
            onClick={() => { onGetStarted(); setMobileOpen(false); }}
            className="btn btn-primary"
            style={{ width: "100%", marginTop: 12 }}
          >
            Launch Now →
          </button>
        </div>
      )}
    </>
  );
}

// ── Section Wrapper ────────────────────────────────────────────────────────
function Section({ id, children }) {
  return (
    <section id={id} className="snap-section">
      <div className="snap-content">
        {children}
      </div>
    </section>
  );
}

// ── Hero Section ────────────────────────────────────────────────────────────
function HeroSection({ onLaunch }) {
  return (
    <Section id="hero">
      <div className="hero-content">
        <div className="hero-badge">
          <Sparkles size={14} /> 9 AI AGENTS · POWERED BY GROQ · BUILT FOR WINNERS
        </div>

        <h1 className="hero-title">
          <span className="grad-violet">LAUNCH</span>
          <br />
          <span className="hero-title-outline">YOUR CAREER</span>
        </h1>

        <p className="hero-subtitle">
          Upload your resume. 9 AI agents analyze, optimize & guide your entire career journey — from skill gaps to job matches to interview prep.
        </p>

        <div className="hero-cta">
          <button className="btn btn-primary hero-btn" onClick={onLaunch}>
            <Rocket size={18} /> START FREE ANALYSIS
          </button>
          <button className="btn btn-ghost hero-btn-secondary">
            <Play size={16} /> Watch Demo
          </button>
        </div>

        <div className="hero-stats">
          <div className="hero-stat">
            <div className="hero-stat-value">10K+</div>
            <div className="hero-stat-label">Resumes Analyzed</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">87%</div>
            <div className="hero-stat-label">Match Rate</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">9</div>
            <div className="hero-stat-label">AI Agents</div>
          </div>
          <div className="hero-stat">
            <div className="hero-stat-value">24/7</div>
            <div className="hero-stat-label">Available</div>
          </div>
        </div>

        <div className="hero-scroll-hint">
          <span>SCROLL TO EXPLORE</span>
          <ChevronRight size={16} className="scroll-arrow" />
        </div>
      </div>
    </Section>
  );
}

// ── Features Section ────────────────────────────────────────────────────────
function FeaturesSection() {
  const features = [
    { icon: <FileText size={28} />, title: "Smart Resume Parsing", desc: "AI extracts skills, experience, and projects from PDF/DOCX in seconds.", color: C.violet },
    { icon: <Target size={28} />, title: "Skill Gap Analysis", desc: "Compare your profile with target roles. Know exactly what to learn next.", color: C.mint },
    { icon: <Sparkles size={28} />, title: "ATS Optimization", desc: "Beat applicant tracking systems with AI-tailored keywords and formatting.", color: C.amber },
    { icon: <Briefcase size={28} />, title: "Job Matching", desc: "Search LinkedIn, Indeed, Naukri & more. Ranked by your fit score.", color: C.coral },
    { icon: <TrendingUp size={28} />, title: "Learning Roadmap", desc: "Personalized month-by-month plan to close skill gaps efficiently.", color: C.violet },
    { icon: <MessageSquare size={28} />, title: "Mock Interviews", desc: "Practice HR, technical & project questions with real-time AI feedback.", color: C.mint },
  ];

  return (
    <Section id="features">
      <div className="section-header">
        <div className="section-tag">FEATURES</div>
        <h2 className="section-title">Everything You Need to <span className="grad-mint">Land Your Dream Job</span></h2>
        <p className="section-subtitle">6 powerful features. 1 unified platform. Powered by LangChain, LangGraph, and Groq AI.</p>
      </div>

      <div className="features-grid">
        {features.map((f, i) => (
          <Card key={i} hover className="feature-card">
            <div className="feature-icon" style={{ color: f.color, borderColor: f.color + "30", background: f.color + "10" }}>
              {f.icon}
            </div>
            <h3 className="feature-title">{f.title}</h3>
            <p className="feature-desc">{f.desc}</p>
          </Card>
        ))}
      </div>
    </Section>
  );
}

// ── How It Works Section ───────────────────────────────────────────────────
function HowItWorksSection({ onLaunch }) {
  const steps = [
    { num: "01", title: "Upload Resume", desc: "Drop your PDF/DOCX. Tell us your dream role.", icon: <Upload size={24} /> },
    { num: "02", title: "AI Analysis", desc: "9 agents analyze your profile in parallel.", icon: <Brain size={24} /> },
    { num: "03", title: "Get Insights", desc: "Skill gaps, ATS score, job matches, roadmap.", icon: <Activity size={24} /> },
    { num: "04", title: "Apply & Interview", desc: "Tailored resumes, cover letters, mock interviews.", icon: <Briefcase size={24} /> },
  ];

  return (
    <Section id="how-it-works">
      <div className="section-header">
        <div className="section-tag">HOW IT WORKS</div>
        <h2 className="section-title">From Resume to <span className="grad-mint">Hired</span> in 4 Steps</h2>
      </div>

      <div className="steps-flow">
        {steps.map((s, i) => (
          <div key={i} className="step-flow-item">
            <div className="step-flow-number">{s.num}</div>
            <div className="step-flow-icon">{s.icon}</div>
            <h3 className="step-flow-title">{s.title}</h3>
            <p className="step-flow-desc">{s.desc}</p>
            {i < steps.length - 1 && <div className="step-flow-arrow"><ArrowRight size={20} /></div>}
          </div>
        ))}
      </div>

      <div style={{ textAlign: "center", marginTop: 60 }}>
        <button className="btn btn-primary" onClick={onLaunch} style={{ padding: "16px 32px", fontSize: 15 }}>
          <Rocket size={18} /> TRY IT NOW — IT'S FREE
        </button>
      </div>
    </Section>
  );
}

// ── Agents Section ──────────────────────────────────────────────────────────
function AgentsSection() {
  const agents = [
    { name: "Resume Parser", desc: "Extracts skills, education, projects", icon: "📄" },
    { name: "Skill Gap", desc: "Compares profile with target role", icon: "🎯" },
    { name: "ATS Optimizer", desc: "Improves resume score", icon: "✨" },
    { name: "Job Ranker", desc: "Matches jobs by fit score", icon: "💼" },
    { name: "Interview Coach", desc: "Generates Q&A + mock mode", icon: "🎤" },
    { name: "Career Goal", desc: "Identifies target role", icon: "🚀" },
    { name: "Application", desc: "Cover letters & emails", icon: "✉️" },
    { name: "Resume Gen", desc: "Role-specific versions", icon: "📝" },
    { name: "Pipeline", desc: "Orchestrates everything", icon: "⚡" },
  ];

  return (
    <Section id="agents">
      <div className="section-header">
        <div className="section-tag">THE BRAIN</div>
        <h2 className="section-title">9 AI Agents <span className="grad-mint">Working Together</span></h2>
        <p className="section-subtitle">A multi-agent system built with LangGraph. Each agent specializes. Together they're unstoppable.</p>
      </div>

      <div className="agents-grid">
        {agents.map((a, i) => (
          <div key={i} className="agent-card">
            <div className="agent-emoji">{a.icon}</div>
            <div className="agent-name">{a.name}</div>
            <div className="agent-desc">{a.desc}</div>
          </div>
        ))}
      </div>
    </Section>
  );
}

// ── Stats Section ───────────────────────────────────────────────────────────
function StatsSection() {
  const stats = [
    { value: "10,247", label: "Resumes Analyzed", icon: <FileText size={20}/> },
    { value: "3,891", label: "Jobs Matched", icon: <Briefcase size={20}/> },
    { value: "87%", label: "Match Accuracy", icon: <Target size={20}/> },
    { value: "2.3x", label: "Faster Hiring", icon: <Zap size={20}/> },
  ];

  return (
    <Section id="stats">
      <div className="section-header">
        <div className="section-tag">IMPACT</div>
        <h2 className="section-title">Real Results, <span className="grad-mint">Real People</span></h2>
      </div>

      <div className="stats-grid">
        {stats.map((s, i) => (
          <div key={i} className="stat-card">
            <div className="stat-icon">{s.icon}</div>
            <div className="stat-value">{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="testimonials">
        <Card className="testimonial">
          <div className="testimonial-stars">
            {[...Array(5)].map((_, i) => <Star key={i} size={16} fill={C.amber} color={C.amber}/>)}
          </div>
          <p className="testimonial-text">"CareerPilot AI helped me identify 5 missing skills for my target role. Got hired at Google in 3 months!"</p>
          <div className="testimonial-author">— Priya S., AI Engineer @ Google</div>
        </Card>
        <Card className="testimonial">
          <div className="testimonial-stars">
            {[...Array(5)].map((_, i) => <Star key={i} size={16} fill={C.amber} color={C.amber}/>)}
          </div>
          <p className="testimonial-text">"The mock interview feature is insane. It asked harder questions than the actual interview."</p>
          <div className="testimonial-author">— Rahul M., ML Engineer @ Microsoft</div>
        </Card>
      </div>
    </Section>
  );
}

// ── CTA Section ────────────────────────────────────────────────────────────
function CTASection({ onLaunch }) {
  return (
    <Section id="cta">
      <div className="cta-content">
        <h2 className="cta-title">
          Ready to <span className="grad-mint">Transform</span> Your Career?
        </h2>
        <p className="cta-subtitle">Join 10,000+ professionals who've already leveled up with AI.</p>
        <button className="btn btn-primary cta-btn" onClick={onLaunch}>
          <Rocket size={20} /> LAUNCH YOUR ANALYSIS
        </button>
        <div className="cta-features">
          <div className="cta-feature"><Check size={14}/> No signup required</div>
          <div className="cta-feature"><Check size={14}/> 100% free</div>
          <div className="cta-feature"><Check size={14}/> Results in 30 seconds</div>
        </div>
      </div>
    </Section>
  );
}

// ── Footer ─────────────────────────────────────────────────────────────────
function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <div style={{
              width: 32, height: 32, borderRadius: 8,
              background: "linear-gradient(135deg, var(--violet), var(--mint))",
              display: "flex", alignItems: "center", justifyContent: "center"
            }}>
              <Rocket size={16} color="#fff" />
            </div>
            <span style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 18 }}>
              CareerPilot <span className="grad-mint">AI</span>
            </span>
          </div>
          <p style={{ color: C.dim, fontSize: 13, maxWidth: 300 }}>
            Your AI-powered career co-pilot. Built with LangChain, LangGraph, and Groq.
          </p>
        </div>
        <div className="footer-col">
          <div className="footer-col-title">Product</div>
          <a href="#features" className="footer-link">Features</a>
          <a href="#how-it-works" className="footer-link">How it Works</a>
          <a href="#agents" className="footer-link">AI Agents</a>
        </div>
        <div className="footer-col">
          <div className="footer-col-title">Resources</div>
          <a href="#" className="footer-link">Documentation</a>
          <a href="#" className="footer-link">API</a>
          <a href="#" className="footer-link">GitHub</a>
        </div>
        <div className="footer-col">
          <div className="footer-col-title">Legal</div>
          <a href="#" className="footer-link">Privacy</a>
          <a href="#" className="footer-link">Terms</a>
          <a href="#" className="footer-link">Cookies</a>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© 2026 CareerPilot AI. Built with ❤️ for job seekers.</span>
      </div>
    </footer>
  );
}

// ── Logo (for workflow steps) ──────────────────────────────────────────────
function Logo() {
  return (
    <div style={{ textAlign: "center", marginBottom: 52, position: "relative", zIndex: 2 }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 14, marginBottom: 10 }}>
        <div style={{
          width: 44, height: 44, borderRadius: 14,
          background: `linear-gradient(135deg,${C.violet},${C.mint})`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 22, boxShadow: `0 4px 28px rgba(123,92,240,0.45)`,
          animation: "floatY 3s ease-in-out infinite"
        }}>
          <Rocket size={22} color="#fff" />
        </div>
        <span style={{ fontSize: 24, fontWeight: 800, fontFamily: "var(--font-display)", letterSpacing: -0.5 }}>
          CareerPilot <span className="grad-mint">AI</span>
        </span>
      </div>
      <div className="lbl" style={{ marginBottom: 0, letterSpacing: 3 }}>9 AI AGENTS · POWERED BY GROQ · BUILT FOR WINNERS</div>
    </div>
  );
}

// ── Step Progress ───────────────────────────────────────────────────────────
function ProgressBar({ current, onStepClick, maxUnlocked }) {
  const icons = [<Upload size={17}/>, <Activity size={17}/>, <Brain size={17}/>, <Briefcase size={17}/>, <MessageSquare size={17}/>];
  
  return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", marginBottom: 52, position: "relative", zIndex: 2, flexWrap: "wrap", gap: 8 }}>
      {STEPS.map((label, i) => (
        <div key={i} style={{ display: "flex", alignItems: "center" }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 7 }}>
            <button
              onClick={() => i <= maxUnlocked && onStepClick(i)}
              disabled={i > maxUnlocked}
              className={i === current ? "step-circle-active" : ""}
              style={{
                width: 48, height: 48, borderRadius: "50%", fontSize: 17,
                display: "flex", alignItems: "center", justifyContent: "center",
                cursor: i <= maxUnlocked ? "pointer" : "default",
                opacity: i > maxUnlocked ? 0.25 : 1,
                transition: "all 0.35s cubic-bezier(0.16,1,0.3,1)",
                background: i < current
                  ? `linear-gradient(135deg,${C.mint},${C.violet})`
                  : i === current
                    ? `linear-gradient(135deg,${C.violet},${C.mint})`
                    : "rgba(255,255,255,0.04)",
                border: i === current ? `2px solid ${C.violet}` : "2px solid transparent",
                color: "#fff"
              }}
              aria-label={`Step ${i + 1}: ${label}`}
            >
              {i < current ? <Check size={17}/> : icons[i]}
            </button>
            <span style={{
              fontSize: 9, fontFamily: "var(--font-mono)", letterSpacing: 1.5, textTransform: "uppercase",
              color: i === current ? C.mint : i < current ? "#666" : C.muted,
            }}>{label}</span>
          </div>
          {i < STEPS.length - 1 && (
            <div className="step-connector" style={{
              background: i < current ? `linear-gradient(90deg,${C.mint},${C.violet})` : "rgba(255,255,255,0.07)"
            }} />
          )}
        </div>
      ))}
    </div>
  );
}

// ── Step 0: Upload ──────────────────────────────────────────────────────────
function UploadStep({ onSubmit, loading }) {
  const [file, setFile] = useState(null);
  const [goal, setGoal] = useState("");
  const [drag, setDrag] = useState(false);
  const ready = file && goal.trim() && !loading;

  const agents = ["Resume Parser","Skill Gap","ATS Optimizer","Job Ranker","Interview Coach","Career Goal","Application","Resume Gen","Pipeline"];

  return (
    <div className="fu" style={{ maxWidth: 520, margin: "0 auto" }}>
      <div style={{ marginBottom: 44, textAlign: "center" }}>
        <h1 className="grad-violet" style={{
          fontSize: 44, fontWeight: 800, lineHeight: 1.1, marginBottom: 14,
          letterSpacing: -1.5, fontFamily: "var(--font-display)"
        }}>Launch Your Career</h1>
        <p style={{ color: C.dim, fontSize: 15, lineHeight: 1.75, maxWidth: 380, margin: "0 auto" }}>
          Upload your resume. 9 AI agents analyze, optimize & guide your entire career journey.
        </p>
      </div>

      <div
        className={`dropzone ${drag ? "dropzone-drag" : file ? "dropzone-ready" : ""}`}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); setFile(e.dataTransfer.files[0]); }}
        onClick={() => document.getElementById("fi").click()}
        style={{ marginBottom: 14 }}
        role="button"
        tabIndex={0}
        aria-label="Upload resume file"
      >
        <input id="fi" type="file" accept=".pdf,.docx" style={{ display: "none" }} onChange={e => setFile(e.target.files[0])} />
        <div style={{ marginBottom: 12, color: file ? C.mint : C.violet }}>
          {file ? <Check size={40} /> : <FileText size={40} />}
        </div>
        <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4, color: file ? C.text : C.dim }}>
          {file ? file.name : "Drop your resume here"}
        </div>
        <div style={{ color: C.muted, fontSize: 12, fontFamily: "var(--font-mono)" }}>
          {file ? `${(file.size / 1024).toFixed(1)} KB · ready to analyze` : "PDF or DOCX · drag or click"}
        </div>
        {file && (
          <button onClick={e => { e.stopPropagation(); setFile(null); }} style={{
            position: "absolute", top: 12, right: 14,
            background: "rgba(255,77,109,0.12)", border: "1px solid rgba(255,77,109,0.25)",
            color: C.coral, borderRadius: 8, padding: "3px 9px", fontSize: 12, cursor: "pointer"
          }} aria-label="Remove file">✕</button>
        )}
      </div>

      <input
        className="input-field" value={goal} onChange={e => setGoal(e.target.value)}
        onKeyDown={e => e.key === "Enter" && ready && onSubmit(file, goal)}
        placeholder="e.g. I want to become an AI Engineer"
        style={{ marginBottom: 14 }}
        aria-label="Career goal"
      />

      <button className="btn btn-primary" onClick={() => ready && onSubmit(file, goal)} disabled={!ready} style={{
        width: "100%", padding: 17, borderRadius: 14, fontSize: 15,
      }}>
        {loading
          ? <><span className="spinner" /> Running 9 AI Agents <span className="ld" /></>
          : <>Analyze My Career <ArrowRight size={16} /></>}
      </button>

      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 7, marginTop: 24 }}>
        {agents.map(a => <span key={a} className="agent-badge">{a}</span>)}
      </div>
    </div>
  );
}

// ── Step 1: Analysis ────────────────────────────────────────────────────────
function AnalysisStep({ data }) {
  const g = data.goal_analysis, a = data.ats;
  const mc = g.match_score >= 70 ? C.mint : g.match_score >= 45 ? C.amber : C.coral;

  return (
    <div className="fu">
      <div style={{ marginBottom: 28 }}>
        <div className="lbl">STEP 01 — CAREER ANALYSIS</div>
        <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: -0.5, fontFamily: "var(--font-display)" }}>Your Career Snapshot</h2>
      </div>

      <div className="fu1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12, marginBottom: 20 }}>
        <StatBlock label="Match Score" value={`${g.match_score}%`} color={mc} />
        <StatBlock label="ATS Score" value={a?.original_ats_score ?? "-"} sub={`→ ${a?.optimized_ats_score ?? "-"} optimized`} color={C.violet} />
        <StatBlock label="Target Role" value={(g.normalized_role ?? "-").split(" ").slice(0, 2).join(" ")} color={C.amber} />
      </div>

      <Card className="fu2" style={{ marginBottom: 14, padding: "20px 24px" }}>
        <div className="lbl">Match Strength</div>
        <ScoreBar value={g.match_score} />
      </Card>

      <div className="fu3" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
        <Card>
          <div className="lbl">✅ Matched ({g.matched_skills?.length ?? 0})</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {g.matched_skills?.map(s => <Tag key={s} type="match">{s}</Tag>)}
          </div>
        </Card>
        {g.missing_skills?.length > 0 && (
          <Card>
            <div className="lbl">❌ Gaps ({g.missing_skills?.length ?? 0})</div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
              {g.missing_skills?.map(s => <Tag key={s} type="missing">{s}</Tag>)}
            </div>
          </Card>
        )}
      </div>

      {g.bonus_skills?.length > 0 && (
        <Card className="fu4" style={{ marginBottom: 12 }}>
          <div className="lbl">⭐ Bonus Skills</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {g.bonus_skills?.map(s => <Tag key={s} type="bonus">{s}</Tag>)}
          </div>
        </Card>
      )}

      <Card aurora>
        <div className="lbl">AI Assessment</div>
        <p style={{ color: C.dim, lineHeight: 1.85, fontSize: 14, margin: 0 }}>{g.personalized_assessment}</p>
      </Card>
    </div>
  );
}

// ── Step 2: Skills ──────────────────────────────────────────────────────────
function SkillsStep({ data }) {
  const s = data.skill_gap;
  const [open, setOpen] = useState(null);
  const rc = s?.readiness?.toLowerCase().includes("job ready") ? C.mint
    : s?.readiness?.toLowerCase().includes("almost") ? C.amber : C.coral;

  return (
    <div className="fu">
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div className="lbl">STEP 02 — SKILL ROADMAP</div>
        <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: -0.5, fontFamily: "var(--font-display)" }}>Learning Path</h2>
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 10 }}>
          <Chip color={rc} size="md">{s?.readiness}</Chip>
          <span style={{ color: C.muted, fontSize: 13 }}>{s?.total_gaps} gaps to close</span>
        </div>
      </div>

      {/* Priority Grid */}
      <div className="fu1" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 28 }}>
        <Card style={{ borderTop: `2px solid ${C.coral}` }}>
          <div className="lbl" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: C.coral, display: "inline-block" }} />
            High Priority
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {s?.gap_categories?.high?.length > 0
              ? s.gap_categories.high.map(sk => <Tag key={sk} type="missing">{sk}</Tag>)
              : <span style={{ color: C.muted, fontSize: 13 }}>None</span>}
          </div>
        </Card>
        <Card style={{ borderTop: `2px solid ${C.amber}` }}>
          <div className="lbl" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: C.amber, display: "inline-block" }} />
            Medium Priority
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {s?.gap_categories?.medium?.length > 0
              ? s.gap_categories.medium.map(sk => <Chip key={sk} color={C.amber}>{sk}</Chip>)
              : <span style={{ color: C.muted, fontSize: 13 }}>None</span>}
          </div>
        </Card>
      </div>

      {/* Timeline */}
      {s?.roadmap?.months?.length > 0 && (
        <div style={{ marginBottom: 28 }}>
          <div className="lbl" style={{ marginBottom: 16 }}>Monthly Roadmap</div>
          <div style={{ position: "relative" }}>
            {/* vertical line */}
            <div style={{
              position: "absolute", left: 19, top: 24, bottom: 24, width: 1,
              background: `linear-gradient(180deg, ${C.violet}, ${C.mint}, transparent)`
            }} />
            <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
              {s.roadmap.months.map((m, i) => (
                <div key={i} style={{ display: "flex", gap: 16, paddingBottom: 20, animationDelay: `${i * 0.08}s` }} className="fu">
                  {/* dot */}
                  <div style={{
                    flexShrink: 0, width: 38, height: 38, borderRadius: "50%",
                    background: `linear-gradient(135deg, ${C.violet}, ${C.mint})`,
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 11, fontWeight: 800, color: "#0a0a0f", marginTop: 2,
                    animation: "floatY 3s ease-in-out infinite",
                    animationDelay: `${i * 0.4}s`
                  }}>M{m.month}</div>
                  {/* card */}
                  <Card style={{ flex: 1, borderLeft: `2px solid ${C.violet}`, borderRadius: "0 12px 12px 0", padding: "14px 18px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
                      <div>
                        <div style={{ color: C.violet, fontSize: 10, letterSpacing: 2, fontWeight: 600, textTransform: "uppercase" }}>Month {m.month}</div>
                        <div style={{ fontWeight: 700, fontSize: 16, marginTop: 2, fontFamily: "var(--font-display)" }}>{m.theme}</div>
                      </div>
                      <Chip color={C.violet}>M{m.month}</Chip>
                    </div>
                    <div style={{ color: C.dim, fontSize: 13, marginBottom: 10, lineHeight: 1.65 }}>{m.goal}</div>
                    <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                      {m.skills?.map(sk => <Chip key={sk} color={C.violet}>{sk}</Chip>)}
                    </div>
                    {m.build && <div style={{ marginTop: 10, color: C.muted, fontSize: 12, fontFamily: "var(--font-mono)" }}>🏗 {m.build}</div>}
                  </Card>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Resources */}
      {s?.resources && Object.keys(s.resources).length > 0 && (
        <div>
          <div className="lbl" style={{ marginBottom: 12 }}>Resources by Skill</div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {Object.entries(s.resources).map(([skill, res]) => (
              <div key={skill} style={{
                background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: 12, overflow: "hidden",
                transition: "border-color .25s"
              }}>
                {/* header */}
                <div
                  onClick={() => setOpen(open === skill ? null : skill)}
                  style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "14px 18px", cursor: "pointer" }}
                >
                  <span style={{ fontWeight: 600, fontSize: 14 }}>{skill}</span>
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    {res?.youtube?.length > 0 && <Chip color={C.coral}>▶ YouTube</Chip>}
                    {res?.practice && <Chip color={C.mint}>🏋 Practice</Chip>}
                    {res?.docs && <Chip color={C.violet}>📖 Docs</Chip>}
                    <span style={{
                      color: C.muted, fontSize: 11, marginLeft: 4,
                      transition: "transform .3s",
                      display: "inline-block",
                      transform: open === skill ? "rotate(180deg)" : "rotate(0deg)"
                    }}>▼</span>
                  </div>
                </div>
                {/* body — CSS transition trick */}
                <div style={{
                  maxHeight: open === skill ? 500 : 0,
                  overflow: "hidden",
                  opacity: open === skill ? 1 : 0,
                  transition: "max-height .35s cubic-bezier(.4,0,.2,1), opacity .25s ease",
                  padding: open === skill ? "0 18px 16px" : "0 18px"
                }}>
                  {res?.youtube?.length > 0 && (
                    <div style={{ marginBottom: 10 }}>
                      <div style={{ color: C.coral, fontSize: 10, letterSpacing: 1, fontWeight: 600, marginBottom: 8 }}>▶ YOUTUBE</div>
                      {res.youtube.map((v, i) => (
                        <a key={i} href={v.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="yt-link">
                          {v.thumbnail
                            ? <img src={v.thumbnail} alt={v.title} style={{ width: 72, height: 42, borderRadius: 6, objectFit: "cover", flexShrink: 0 }} />
                            : <div style={{ width: 72, height: 42, borderRadius: 6, flexShrink: 0, background: "rgba(255,107,107,0.1)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>▶</div>}
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{ color: C.text, fontSize: 13, fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{v.title}</div>
                            {v.channel && <div style={{ color: "#ff8888", fontSize: 11 }}>{v.channel}</div>}
                          </div>
                          <span style={{ color: C.coral, fontSize: 12, flexShrink: 0 }}>→</span>
                        </a>
                      ))}
                    </div>
                  )}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                    {res?.practice && (
                      <a href={res.practice} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                        style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", borderRadius: 8, background: "rgba(0,255,179,0.07)", border: `1px solid rgba(0,255,179,0.2)`, color: C.mint, fontSize: 12, fontWeight: 600, textDecoration: "none" }}>
                        🏋 Practice →
                      </a>
                    )}
                    {res?.docs && (
                      <a href={res.docs} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                        style={{ display: "flex", alignItems: "center", gap: 6, padding: "7px 14px", borderRadius: 8, background: "rgba(123,92,240,0.07)", border: `1px solid rgba(123,92,240,0.2)`, color: C.violet, fontSize: 12, fontWeight: 600, textDecoration: "none" }}>
                        📖 Docs →
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Step 3: Jobs ────────────────────────────────────────────────────────────
// ── Step 3: Jobs ────────────────────────────────────────────────────────────
function JobsStep({ data, downloads }) {
  const jobs = data.jobs?.ranked_jobs || [];
  const [exp, setExp] = useState(null);

  if (!jobs.length) return (
    <div className="fu" style={{ textAlign: "center", padding: "80px 0" }}>
      <div style={{ marginBottom: 16, color: C.dim }}><Briefcase size={52} /></div>
      <div style={{ color: C.dim, fontSize: 15 }}>No jobs returned from pipeline.</div>
    </div>
  );

  return (
    <div className="fu">
      <div style={{ marginBottom: 28 }}>
        <div className="lbl">STEP 03 — JOB MATCHES</div>
        <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: -0.5, fontFamily: "var(--font-display)" }}>Top Opportunities</h2>
        <div style={{ color: C.dim, fontSize: 14, marginTop: 4 }}>{jobs.length} jobs ranked by profile fit</div>
      </div>

      {/* ── NEW: Resume download section ── */}
      {downloads && downloads.length > 0 && (
        <Card aurora style={{ marginBottom: 20 }}>
          <div className="lbl">📄 YOUR OPTIMIZED RESUME</div>
          <p style={{ color: C.dim, fontSize: 13, marginBottom: 12 }}>
            ATS-optimized resume ready. Download and apply!
          </p>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {downloads.map(d => (
              <a
                key={d.filename}
                href={`http://127.0.0.1:8000${d.download_url}`}
                target="_blank"
                rel="noreferrer"
                className="btn btn-primary"
                style={{ padding: "10px 18px", borderRadius: 10, fontSize: 13, textDecoration: "none" }}
              >
                📄 Download {d.format.toUpperCase()}
              </a>
            ))}
          </div>
        </Card>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {jobs.slice(0, 8).map((job, i) => {
          const sc = job.total_score >= 70 ? C.mint : job.total_score >= 50 ? C.amber : C.coral;
          return (
            <Card key={i} hover style={{
              borderLeft: job.recommended ? `3px solid ${C.mint}` : "3px solid rgba(255,255,255,0.05)",
              cursor: "pointer", animationDelay: `${i * 0.04}s`
            }} className="fu" onClick={() => setExp(exp === i ? null : i)}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                <div style={{ flex: 1 }}>
                  {job.recommended && <div style={{ color: C.mint, fontSize: 10, fontFamily: "var(--font-mono)", letterSpacing: 1.5, marginBottom: 5 }}>⭐ TOP PICK</div>}
                  <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 3, fontFamily: "var(--font-display)" }}>{job.title}</div>
                  <div style={{ color: C.dim, fontSize: 13 }}>
                    {job.company}{job.location && <span style={{ color: C.muted }}> · {job.location}</span>}
                  </div>
                  {job.salary && job.salary !== "N/A" && <div style={{ color: C.amber, fontSize: 12, marginTop: 4, fontFamily: "var(--font-mono)" }}>{job.salary}</div>}
                </div>
                <div style={{ textAlign: "right", minWidth: 58 }}>
                  <div style={{ fontSize: 26, fontWeight: 800, color: sc, lineHeight: 1, fontFamily: "var(--font-display)" }}>{job.total_score}%</div>
                  <div style={{ fontSize: 9, color: C.muted, fontFamily: "var(--font-mono)", marginTop: 2 }}>MATCH</div>
                </div>
              </div>
              {exp === i && (
                <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid rgba(255,255,255,0.07)" }}>
                  {job.match_reason && <div style={{ color: C.dim, fontSize: 13, marginBottom: 10 }}>💡 {job.match_reason}</div>}
                  <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                    {job.source && <Chip color={C.violet}>{job.source}</Chip>}
                    {job.link && job.link !== "N/A" && (
                      <a href={job.link} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                        style={{ color: "#fff", fontSize: 13, fontWeight: 700, background: `linear-gradient(135deg,${C.violet},${C.mint})`, borderRadius: 8, padding: "5px 14px", textDecoration: "none" }}>
                        Apply Now →
                      </a>
                    )}
                  </div>
                </div>
              )}
              <div style={{ color: C.muted, fontSize: 10, marginTop: 8, fontFamily: "var(--font-mono)" }}>{exp === i ? "▲ collapse" : "▼ details"}</div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}


// ── Step 4: Interview ───────────────────────────────────────────────────────
function InterviewStep({ data }) {
  const q = data.interview_questions || {};
  const role = q._meta?.role || "AI Engineer";

  const [mode, setMode] = useState("browse");
  const [tab, setTab] = useState("hr");
  const [revealed, setRevealed] = useState({});

  const allQ = [
    ...(q.hr_questions || []).map(x => ({ ...x, type: "HR" })),
    ...(q.technical_questions || []).map(x => ({ ...x, type: "Technical" })),
    ...(q.project_questions || []).map(x => ({ ...x, type: "Project" })),
  ];
  const [qi, setQi] = useState(0);
  const [answer, setAnswer] = useState("");
  const [chat, setChat] = useState([]);
  const [feedback, setFB] = useState("");
  const [aiLoad, setAILoad] = useState(false);
  const [done, setDone] = useState(false);
  const endRef = useRef(null);

  const tabs = [
    { key: "hr", label: "HR", emoji: "🤝", items: q.hr_questions || [] },
    { key: "tech", label: "Technical", emoji: "⚙️", items: q.technical_questions || [] },
    { key: "proj", label: "Projects", emoji: "🏗", items: q.project_questions || [] },
  ];
  const active = tabs.find(t => t.key === tab);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth" }); }, [feedback, aiLoad]);

  const submit = async () => {
    if (!answer.trim() || aiLoad) return;
    setAILoad(true); setFB("");
    try {
      const res = await fetch(`${API}/api/mock-interview`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer, question: allQ[qi].question, role, history: chat.slice(-6) })
      });
      const j = await res.json();
      setChat(h => [...h, { role: "user", content: answer }, { role: "assistant", content: j.feedback }]);
      setFB(j.feedback); setAnswer("");
    } catch { setFB("⚠️ Could not reach backend."); }
    finally { setAILoad(false); }
  };

  const next = () => qi < allQ.length - 1 ? (setQi(i => i + 1), setFB(""), setAnswer("")) : setDone(true);
  const reset = () => { setQi(0); setAnswer(""); setFB(""); setChat([]); setDone(false); };
  const typeColor = t => t === "HR" ? C.mint : t === "Technical" ? C.violet : C.amber;

  if (mode === "browse") return (
    <div className="fu">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 6 }}>
        <div>
          <div className="lbl">STEP 04 — INTERVIEW PREP</div>
          <h2 style={{ fontSize: 28, fontWeight: 800, letterSpacing: -0.5, fontFamily: "var(--font-display)" }}>Practice Questions</h2>
        </div>
        <button className="btn btn-primary" onClick={() => { setMode("mock"); reset(); }} style={{ padding: "11px 22px", borderRadius: 24, fontSize: 13 }}>
          <Mic size={14} /> Mock Interview
        </button>
      </div>
      <div style={{ color: C.dim, fontSize: 14, marginBottom: 24 }}>{tabs.reduce((a, t) => a + t.items.length, 0)} questions · browse or practice live</div>

      <div style={{ display: "flex", gap: 8, marginBottom: 24, flexWrap: "wrap" }}>
        {tabs.map(t => (
          <button key={t.key} onClick={() => { setTab(t.key); setRevealed({}); }}
            className={`btn btn-${tab === t.key ? "tab-active" : "tab"}`}
            style={{ padding: "9px 18px", borderRadius: 24, fontSize: 13, fontWeight: 600 }}>
            {t.emoji} {t.label} ({t.items.length})
          </button>
        ))}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {active.items.length === 0 && <div style={{ textAlign: "center", color: C.muted, padding: "40px 0", fontSize: 14 }}>No questions here.</div>}
        {active.items.map((item, i) => (
          <Card key={`${tab}-${i}`} hover>
            <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8, lineHeight: 1.55 }}>
              <span style={{ color: C.violet, fontFamily: "var(--font-mono)", fontSize: 10, marginRight: 8 }}>Q{i + 1}</span>
              {item.question}
            </div>
            {item.tip && <div style={{ color: C.mint, fontSize: 12, marginBottom: 6, fontFamily: "var(--font-mono)" }}>💡 {item.tip}</div>}
            {item.expected_answer && (
              <>
                <button onClick={() => setRevealed(r => ({ ...r, [`${tab}-${i}`]: !r[`${tab}-${i}`] }))}
                  style={{ background: "none", border: "none", color: C.muted, fontSize: 11, cursor: "pointer", fontFamily: "var(--font-mono)", padding: 0, marginTop: 4 }}>
                  {revealed[`${tab}-${i}`] ? "▲ hide" : "▼ show answer"}
                </button>
                {revealed[`${tab}-${i}`] && (
                  <div style={{ color: C.dim, fontSize: 13, marginTop: 8, lineHeight: 1.7, borderLeft: `2px solid rgba(123,92,240,0.3)`, paddingLeft: 12 }}>
                    {item.expected_answer}
                  </div>
                )}
              </>
            )}
          </Card>
        ))}
      </div>
    </div>
  );

  if (done) return (
    <div className="fu" style={{ textAlign: "center", padding: "80px 0" }}>
      <div style={{ marginBottom: 16, color: C.amber }}><PartyPopper size={56} /></div>
      <h2 style={{ fontSize: 28, fontWeight: 800, marginBottom: 8, fontFamily: "var(--font-display)" }}>Interview Complete!</h2>
      <p style={{ color: C.dim, fontSize: 14, marginBottom: 36 }}>You answered {allQ.length} questions.</p>
      <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
        <button className="btn btn-primary" onClick={reset} style={{ padding: "13px 28px", borderRadius: 12, fontSize: 14 }}>🔄 Practice Again</button>
        <button className="btn btn-ghost" onClick={() => setMode("browse")} style={{ padding: "13px 28px", borderRadius: 12, fontSize: 14 }}>Browse Questions</button>
      </div>
    </div>
  );

  const cq = allQ[qi];
  return (
    <div className="fu">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 800, margin: 0, fontFamily: "var(--font-display)" }}>🎤 Mock Interview</h2>
          <div style={{ color: C.muted, fontSize: 11, fontFamily: "var(--font-mono)", marginTop: 4 }}>{role} · Q{qi + 1} of {allQ.length}</div>
        </div>
        <button className="btn btn-ghost" onClick={() => setMode("browse")} style={{ padding: "7px 14px", borderRadius: 10, fontSize: 12 }}>✕ Exit</button>
      </div>

      <div className="interview-prog-track">
        <div className="interview-prog-fill" style={{ width: `${((qi + 1) / allQ.length) * 100}%` }} />
      </div>

      <Card aurora style={{ marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
          <Chip color={typeColor(cq.type)}>{cq.type}</Chip>
          <span style={{ color: C.muted, fontSize: 10, fontFamily: "var(--font-mono)" }}>Q{qi + 1}</span>
        </div>
        <div style={{ fontWeight: 600, fontSize: 15, lineHeight: 1.65 }}>{cq.question}</div>
        {cq.tip && <div style={{ color: C.mint, fontSize: 12, marginTop: 8, fontFamily: "var(--font-mono)" }}>💡 {cq.tip}</div>}
      </Card>

      {chat.length > 0 && (
        <div style={{ maxHeight: 280, overflowY: "auto", marginBottom: 16, display: "flex", flexDirection: "column", gap: 10 }}>
          {chat.map((msg, i) => (
            <div key={i} style={{ display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
              <div className={`bubble ${msg.role === "user" ? "bubble-user" : "bubble-ai"}`}>
                {msg.role === "assistant" && <div style={{ color: C.violet, fontSize: 10, fontFamily: "var(--font-mono)", marginBottom: 5, letterSpacing: 1 }}>🤖 AI INTERVIEWER</div>}
                {msg.content}
              </div>
            </div>
          ))}
          {aiLoad && (
            <div style={{ display: "flex", justifyContent: "flex-start" }}>
              <div className="bubble bubble-ai"><span className="spinner" />&nbsp;Evaluating<span className="ld" /></div>
            </div>
          )}
          <div ref={endRef} />
        </div>
      )}

      {!feedback ? (
        <div>
          <textarea className="textarea-field" value={answer} onChange={e => setAnswer(e.target.value)}
            onKeyDown={e => e.key === "Enter" && e.ctrlKey && submit()}
            placeholder="Type your answer… (Ctrl+Enter to submit)" rows={4}
            style={{ marginBottom: 10 }} />
          <div style={{ display: "flex", gap: 10 }}>
            <button className="btn btn-primary" onClick={submit} disabled={!answer.trim() || aiLoad} style={{ flex: 1, padding: 13, borderRadius: 12, fontSize: 14 }}>
              {aiLoad ? <><span className="spinner" />&nbsp;Evaluating…</> : "Submit Answer →"}
            </button>
            <button className="btn btn-ghost" onClick={next} style={{ padding: "13px 18px", borderRadius: 12, fontSize: 13 }}>Skip ⏭</button>
          </div>
        </div>
      ) : (
        <button className="btn btn-primary" onClick={next} style={{ width: "100%", padding: 13, borderRadius: 12, fontSize: 14 }}>
          {qi < allQ.length - 1 ? "Next Question →" : "Finish Interview 🎉"}
        </button>
      )}
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN APP
// ════════════════════════════════════════════════════════════════════════════
export default function App() {
  const [step, setStep]   = useState(0);
  const [maxU, setMaxU]   = useState(0);
  const [loading, setLoad] = useState(false);
  const [data, setData]   = useState(null);
  const [error, setError] = useState("");
  const [activeSection, setActiveSection] = useState(0);
  const [mode, setMode] = useState("landing");

  const sections = ["hero", "features", "how-it-works", "agents", "stats", "cta"];

  useEffect(() => {
    if (mode !== "landing") return;
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const idx = sections.indexOf(entry.target.id);
            if (idx !== -1) setActiveSection(idx);
          }
        });
      },
      { threshold: 0.4 }
    );

    sections.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [mode]);

  const scrollToSection = useCallback((idx) => {
    const id = sections[idx];
    const el = document.getElementById(id);
    if (el) el.scrollIntoView({ behavior: "smooth" });
  }, []);

const analyze = async (file, goal) => {
  setLoad(true); setError("");
  try {
    const form = new FormData();
    form.append("resume", file);
    form.append("career_goal", goal);
    const res = await fetch(`${API}/api/analyze`, { method: "POST", body: form });
    const json = await res.json();
    if (!res.ok) throw new Error(json.detail || "Analysis failed");

    const mapped = {
      goal_analysis: {
        normalized_role: json.goal_analysis?.normalized_role || "Software Engineer",
        match_score: json.goal_analysis?.match_score || 0,
        matched_skills: json.goal_analysis?.matched_skills || [],
        missing_skills: json.goal_analysis?.missing_skills || [],
        bonus_skills: json.goal_analysis?.bonus_skills || [],
        personalized_assessment: json.goal_analysis?.personalized_assessment || ""
      },
      skill_gap: {
        readiness: json.skill_gap?.readiness || "",
        total_gaps: json.skill_gap?.total_gaps || 0,
        gap_categories: json.skill_gap?.gap_categories || { high: [], medium: [], low: [] },
        roadmap: json.skill_gap?.roadmap || { months: [] },
        resources: json.skill_gap?.resources || {}
      },
      ats: {
        original_ats_score: json.ats?.original_ats_score,
        optimized_ats_score: json.ats?.optimized_ats_score,
      },
      jobs: {
        ranked_jobs: json.jobs?.ranked_jobs || []
      },
      interview_questions: json.interview_questions || {},
      download_links: []
    };

    setData(mapped);
    setStep(1);
    setMaxU(STEPS.length - 1);
  } catch (e) {
    setError(e.message);
  } finally {
    setLoad(false);
  }
};

  const onLaunch = () => {
    setMode("workflow");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  if (mode === "landing") {
    return (
      <div style={{ minHeight: "100vh", position: "relative", zIndex: 1, fontFamily: "var(--font-body)", color: C.text }}>
        {/* ═══ Cool Background Animations ═══ */}
        <ParticleCanvas />
        <div className="mesh-gradient" />
        <div className="animated-blobs">
          <div className="blob blob-1" />
          <div className="blob blob-2" />
          <div className="blob blob-3" />
          <div className="blob blob-4" />
        </div>
        <div className="constellation">
          <div className="constellation-line" />
          <div className="constellation-line" />
          <div className="constellation-line" />
          <div className="constellation-line" />
          <div className="glow-orb" />
          <div className="glow-orb violet" />
          <div className="glow-orb amber" />
          <div className="glow-orb" />
        </div>
        <div className="grid-texture" />

        <Navbar 
          activeSection={activeSection} 
          scrollToSection={scrollToSection} 
          onGetStarted={onLaunch} 
        />

        <HeroSection onLaunch={onLaunch} />
        <FeaturesSection />
        <HowItWorksSection onLaunch={onLaunch} />
        <AgentsSection />
        <StatsSection />
        <CTASection onLaunch={onLaunch} />
        <Footer />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", position: "relative", zIndex: 1, padding: "40px 20px 100px", fontFamily: "var(--font-body)", color: C.text }}>
      <ParticleCanvas />
      <div className="aurora-overlay" />
      <div className="grid-texture" />

      <button 
        onClick={() => { setMode("landing"); window.scrollTo({ top: 0, behavior: "smooth" }); }}
        style={{
          position: "fixed", top: 20, left: 20, zIndex: 100,
          background: "var(--glass)", border: "1px solid var(--border)",
          borderRadius: 10, padding: "8px 14px", color: C.text, cursor: "pointer",
          display: "flex", alignItems: "center", gap: 6, fontSize: 13, fontWeight: 600,
          backdropFilter: "blur(20px)"
        }}
        aria-label="Back to home"
      >
        <ArrowLeft size={14} /> Home
      </button>

      <div style={{ position: "relative", zIndex: 2 }}>
        <Logo />

        {step > 0 && <ProgressBar current={step} maxUnlocked={maxU} onStepClick={setStep} />}

        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          {error && <div className="error-banner">⚠️ {error}</div>}

          {step === 0 && <UploadStep onSubmit={analyze} loading={loading} />}
          {step === 1 && data && <AnalysisStep data={data} />}
          {step === 2 && data && <SkillsStep data={data} />}
          {step === 3 && data && <JobsStep data={data} />}
          {step === 4 && data && <InterviewStep data={data} />}

          {step > 0 && (
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 40 }}>
              <button className="btn btn-ghost" onClick={() => setStep(s => Math.max(0, s - 1))} style={{ padding: "11px 24px", borderRadius: 10, fontSize: 14 }}>
                <ArrowLeft size={14} /> Back
              </button>
              <span style={{ color: C.muted, fontSize: 11, fontFamily: "var(--font-mono)" }}>{step} / {STEPS.length - 1}</span>
              {step < STEPS.length - 1
                ? <button className="btn btn-primary" onClick={() => setStep(s => s + 1)} style={{ padding: "11px 24px", borderRadius: 10, fontSize: 14 }}>{STEPS[step + 1]} <ArrowRight size={14} /></button>
                : <button className="btn btn-primary" onClick={() => { setStep(0); setData(null); setMaxU(0); setError(""); setMode("landing"); }} style={{ padding: "11px 24px", borderRadius: 10, fontSize: 14 }}>🔄 New Analysis</button>
              }
            </div>
          )}
        </div>
      </div>
    </div>
  );
}


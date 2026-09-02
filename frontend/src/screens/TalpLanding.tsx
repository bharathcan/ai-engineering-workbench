import '../styles/talp-design.css'
import { NetworkBackground } from '../components/NetworkBackground'
import type { ScreenId } from '../components/AppShell'

export function TalpLanding({ onNavigate }: { onNavigate: (screen: ScreenId) => void }) {
  return (
    <>
      <NetworkBackground />

      {/* Header */}
      <header className="header">
        <div className="header__logo">⚡ AI Workbench</div>
        <nav className="header__nav">
          <a href="#features">Features</a>
          <a href="#workflow">How it works</a>
          <a href="#about">About</a>
          <button className="header__cta" onClick={() => onNavigate('requirement')}>
            Get Started
          </button>
        </nav>
      </header>

      {/* Main Container */}
      <div className="container">
        {/* Hero Section */}
        <section className="hero">
          <div className="hero__content">
            <span className="hero__category">.engineering</span>
            <h1 className="hero__title">
              Transform Requirements Into <span className="hero__accent">Production Code</span>
            </h1>
            <p className="hero__subtitle">
              AI-assisted engineering platform where you maintain full control. Get task breakdowns,
              intelligent recommendations, generated artifacts, and rigorous validation.
            </p>
            <button className="hero__cta" onClick={() => onNavigate('requirement')}>
              Start Building
            </button>
          </div>
        </section>

        {/* Features Section */}
        <section className="features" id="features">
          <span className="features__category">.benefits</span>
          <h2 className="features__title">Why Teams Choose <span className="features__accent">This Platform</span></h2>
          <div className="features__grid">
            <div className="feature">
              <h3 className="feature__title">Engineer-Led</h3>
              <p className="feature__description">
                You make every decision. AI assists, you approve. Complete audit trail of all choices.
              </p>
            </div>
            <div className="feature">
              <h3 className="feature__title">AI-Powered</h3>
              <p className="feature__description">
                Analyze requirements, decompose tasks, generate code—all with intelligent assistance.
              </p>
            </div>
            <div className="feature">
              <h3 className="feature__title">Validated</h3>
              <p className="feature__description">
                7-stage validation pipeline ensures every artifact meets quality standards.
              </p>
            </div>
            <div className="feature">
              <h3 className="feature__title">Transparent</h3>
              <p className="feature__description">
                See exactly what was generated, review every decision, understand every step.
              </p>
            </div>
          </div>
        </section>

        {/* Workflow Section */}
        <section className="workflow" id="workflow">
          <span className="workflow__category">.how-it-works</span>
          <h2 className="workflow__title">Build What <span className="workflow__accent">Actually Works</span></h2>
          <div className="workflow__steps">
            <div className="step">
              <div className="step__number">1</div>
              <h3 className="step__title">Requirement</h3>
              <p className="step__description">Define what you want to build</p>
            </div>
            <div className="step">
              <div className="step__number">2</div>
              <h3 className="step__title">Analysis</h3>
              <p className="step__description">AI identifies scope and constraints</p>
            </div>
            <div className="step">
              <div className="step__number">3</div>
              <h3 className="step__title">Planning</h3>
              <p className="step__description">Generate task breakdown with dependencies</p>
            </div>
            <div className="step">
              <div className="step__number">4</div>
              <h3 className="step__title">Execute</h3>
              <p className="step__description">Request AI assistance for each task</p>
            </div>
            <div className="step">
              <div className="step__number">5</div>
              <h3 className="step__title">Artifacts</h3>
              <p className="step__description">AI generates code, tests, documentation</p>
            </div>
            <div className="step">
              <div className="step__number">6</div>
              <h3 className="step__title">Validate</h3>
              <p className="step__description">Automated quality assurance before approval</p>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="cta">
          <span className="cta__category">.ready</span>
          <h2 className="cta__title">Ready to <span className="cta__accent">Transform</span> Your Engineering?</h2>
          <p className="cta__subtitle">Start with a new project or explore existing ones</p>
          <button className="cta__button" onClick={() => onNavigate('requirement')}>
            Create Project
          </button>
        </section>
      </div>
    </>
  )
}

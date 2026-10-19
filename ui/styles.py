"""
UI Styling, CSS tokens, and component builders for Evolutionary Market Lab.
Deep navy palette (#0B1020), panel backgrounds (#131D30), fine borders (#263247),
cyan/teal primary accent (#00D2D3 / #00ADB5), emerald (#10B981) for gains,
coral (#F43F5E) for losses, amber (#F59E0B) for warnings.
"""

NAVY_BG = "#0B1020"
PANEL_BG = "#131D30"
BORDER_COLOR = "#263247"
TEXT_PRIMARY = "#F1F5F9"
TEXT_MUTED = "#94A3B8"
ACCENT_CYAN = "#00D2D3"
ACCENT_TEAL = "#0EA5E9"
GAIN_EMERALD = "#10B981"
LOSS_CORAL = "#F43F5E"
WARN_AMBER = "#F59E0B"

CUSTOM_CSS = """
<style>
    /* Global background and typography */
    .stApp {
        background-color: #0B1020;
        color: #F1F5F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }
    
    /* Header layout */
    .eml-header {
        display: flex;
        flex-direction: column;
        gap: 4px;
        padding: 4px 0 16px 0;
        border-bottom: 1px solid #263247;
        margin-bottom: 16px;
    }
    .eml-title {
        font-size: 1.65rem;
        font-weight: 700;
        color: #F1F5F9;
        letter-spacing: -0.02em;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .eml-title-badge {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        background: rgba(0, 210, 211, 0.12);
        color: #00D2D3;
        border: 1px solid rgba(0, 210, 211, 0.3);
        padding: 2px 8px;
        border-radius: 6px;
    }
    .eml-subtitle {
        font-size: 0.92rem;
        color: #94A3B8;
        margin: 0;
    }
    
    /* Chips bar */
    .eml-chip-bar {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
        margin-top: 8px;
    }
    .eml-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #131D30;
        border: 1px solid #263247;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 0.78rem;
        color: #94A3B8;
    }
    .eml-chip strong {
        color: #F1F5F9;
    }
    .eml-chip-status {
        border-left: 3px solid #00D2D3;
    }

    /* Warning & info banners */
    .eml-banner {
        border-radius: 8px;
        padding: 10px 14px;
        margin: 12px 0;
        font-size: 0.85rem;
        line-height: 1.45;
        display: flex;
        align-items: flex-start;
        gap: 10px;
    }
    .eml-banner-warning {
        background-color: rgba(245, 158, 11, 0.08);
        border: 1px solid rgba(245, 158, 11, 0.35);
        color: #FDE68A;
    }
    .eml-banner-info {
        background-color: rgba(14, 165, 233, 0.08);
        border: 1px solid rgba(14, 165, 233, 0.35);
        color: #BAE6FD;
    }
    .eml-banner-success {
        background-color: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #A7F3D0;
    }

    /* First run empty state card */
    .eml-empty-card {
        background: #131D30;
        border: 1px solid #263247;
        border-radius: 12px;
        padding: 32px 24px;
        text-align: center;
        margin: 24px 0;
    }
    .eml-empty-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 8px;
    }
    .eml-empty-desc {
        font-size: 0.9rem;
        color: #94A3B8;
        max-width: 620px;
        margin: 0 auto 24px auto;
        line-height: 1.5;
    }
    .eml-steps-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        max-width: 820px;
        margin: 0 auto 24px auto;
        text-align: left;
    }
    .eml-step-item {
        background: #0B1020;
        border: 1px solid #263247;
        border-radius: 8px;
        padding: 16px;
    }
    .eml-step-num {
        font-size: 0.75rem;
        font-weight: 700;
        color: #00D2D3;
        background: rgba(0, 210, 211, 0.12);
        display: inline-block;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .eml-step-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 4px;
    }
    .eml-step-desc {
        font-size: 0.8rem;
        color: #94A3B8;
        line-height: 1.4;
    }

    /* Quantitative Metric Cards */
    .eml-kpi-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
        gap: 12px;
        margin-bottom: 18px;
    }
    .eml-kpi-card {
        background: #131D30;
        border: 1px solid #263247;
        border-radius: 10px;
        padding: 14px 16px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .eml-kpi-label {
        font-size: 0.74rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
    }
    .eml-kpi-value {
        font-size: 1.45rem;
        font-weight: 700;
        color: #F1F5F9;
        font-feature-settings: "tnum";
    }
    .eml-kpi-delta {
        font-size: 0.78rem;
        font-weight: 500;
    }
    .eml-kpi-subtext {
        font-size: 0.72rem;
        color: #64748B;
    }
    .eml-delta-gain { color: #10B981; }
    .eml-delta-loss { color: #F43F5E; }
    .eml-delta-neutral { color: #94A3B8; }

    /* Strategy Selection Card */
    .eml-strat-status {
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
        font-size: 0.82rem;
        line-height: 1.4;
    }
    .eml-strat-primary {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #A7F3D0;
    }
    .eml-strat-exploratory {
        background: rgba(14, 165, 233, 0.08);
        border: 1px solid rgba(14, 165, 233, 0.35);
        color: #BAE6FD;
    }

    /* Gene Parameter Table/Cards */
    .eml-panel {
        background: #131D30;
        border: 1px solid #263247;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .eml-panel-title {
        font-size: 0.92rem;
        font-weight: 600;
        color: #F1F5F9;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }

    /* Streamlit widget overrides */
    div[data-testid="stSidebar"] {
        background-color: #0B1020;
        border-right: 1px solid #263247;
    }
    div[data-testid="stSidebarNav"] {
        background-color: #0B1020;
    }

    /* Compact, quiet research workspace. */
    .block-container { max-width: 1440px; padding-top: 1.5rem; padding-bottom: 2rem; }
    .eml-header { padding-bottom: 20px; margin-bottom: 18px; }
    .eml-title { font-size: 1.7rem; letter-spacing: -0.045em; flex-wrap: wrap; }
    .eml-title-badge { font-size: .61rem; letter-spacing: .12em; padding: 4px 8px; }
    .eml-subtitle { font-size: .82rem; line-height: 1.55; }
    .eml-chip-bar { gap: 7px; margin-bottom: 16px; }
    .eml-chip { padding: 5px 9px; font-size: .72rem; border-color: rgba(148,163,184,.16); }
    .eml-kpi-grid { gap: 12px; margin-top: 16px; }
    .eml-kpi-card { padding: 18px 16px; border-color: rgba(148,163,184,.18); border-radius: 14px; background: linear-gradient(145deg, #152136, #111a2b); }
    .eml-kpi-label { font-size: .67rem; letter-spacing: .055em; display: flex; align-items: center; gap: 6px; }
    .eml-kpi-value { font-size: 1.65rem; font-weight: 650; letter-spacing: -.035em; padding: 5px 0; }
    .eml-kpi-subtext { color: #94a3b8; }
    .eml-section-title { font-size: 1rem; font-weight: 600; letter-spacing: -.02em; color: #e2e8f0; display: flex; align-items: center; gap: 7px; margin: 14px 0 14px; }
    .eml-strat-status { padding: 9px 12px; font-size: .78rem; }
    .eml-empty-card { padding: 42px 30px; border: 1px solid rgba(148,163,184,.18); border-radius: 18px; background: linear-gradient(135deg, #152136, #10182a); }
    .eml-empty-title { font-size: 1.6rem; letter-spacing: -.035em; }
    .eml-empty-desc { margin-bottom: 28px; }
    .eml-step-item { border-color: rgba(148,163,184,.12); border-radius: 10px; background: rgba(11,16,32,.5); }
    .eml-step-num { font-size: .65rem; letter-spacing: .04em; }
    .eml-step-desc { font-size: .78rem; }
    section[data-testid="stSidebar"] { background: #101827; border-right: 1px solid rgba(148,163,184,.15); }
    section[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }
    div[data-baseweb="tab-list"] { gap: 22px; }
    button[data-baseweb="tab"] { font-size: .85rem; }

    /* Native details gives hover, click/touch and keyboard access to explanations. */
    .eml-info { position: relative; display: inline-block; flex: 0 0 auto; line-height: 1; text-transform: none; letter-spacing: normal; }
    .eml-info > summary { display: inline-flex; align-items: center; justify-content: center; list-style: none; cursor: help; color: #94a3b8; width: 20px; height: 20px; border-radius: 50%; font-size: .9rem; font-weight: 400; }
    .eml-info > summary::-webkit-details-marker { display: none; }
    .eml-info > summary:hover, .eml-info > summary:focus-visible { color: #67e8f9; background: rgba(103,232,249,.08); outline: 2px solid #0ea5e9; outline-offset: 2px; }
    .eml-info > .eml-tooltip { display: none; position: absolute; z-index: 1000; top: calc(100% + 7px); left: 0; width: min(320px, calc(100vw - 56px)); padding: 12px 14px; color: #e2e8f0; background: #1b2940; border: 1px solid #475569; border-radius: 10px; box-shadow: 0 12px 32px rgba(0,0,0,.4); font-size: .78rem; font-weight: 400; line-height: 1.6; text-align: left; text-transform: none; letter-spacing: normal; }
    .eml-info:hover > .eml-tooltip, .eml-info:focus-within > .eml-tooltip, .eml-info[open] > .eml-tooltip { display: block; }
    .eml-kpi-card:nth-child(n+3) .eml-tooltip { left: auto; right: 0; }
    @media (max-width: 760px) {
        .block-container { padding-left: 1rem; padding-right: 1rem; }
        .eml-title { font-size: 1.4rem; }
        .eml-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
        .eml-kpi-card { padding: 14px 12px; }
        .eml-kpi-value { font-size: 1.4rem; }
        .eml-empty-card { padding: 28px 18px; }
        .eml-steps-grid { grid-template-columns: 1fr; }
        .eml-empty-title { font-size: 1.3rem; }
        .eml-kpi-card:nth-child(odd) .eml-tooltip { left: -12px; right: auto; }
        .eml-kpi-card:nth-child(even) .eml-tooltip { left: auto; right: -12px; }
    }

</style>
"""


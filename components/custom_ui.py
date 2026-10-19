import streamlit as st

def apply_custom_theme():
    """애플리케이션 전체에 적용되는 프리미엄 모던 CSS 스타일"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@300;400;500;600;700;800&family=Outfit:wght@400;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, system-ui, Roboto, sans-serif;
    }

    /* 상단 헤더 컨테이너 */
    .hero-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(12px);
    }
    
    .hero-title {
        font-family: 'Outfit', 'Pretendard', sans-serif;
        font-size: 1.95rem;
        font-weight: 800;
        background: linear-gradient(120deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .hero-subtitle {
        color: #94a3b8;
        font-size: 0.98rem;
        line-height: 1.5;
        margin: 0;
    }

    .hero-badge {
        display: inline-block;
        padding: 3px 10px;
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-bottom: 8px;
    }

    /* 입력 가이드 카드 */
    .input-box-card {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 22px;
        height: 100%;
        box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    }

    .input-step-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 8px;
        background: rgba(56, 189, 248, 0.2);
        color: #38bdf8;
        font-weight: 700;
        font-size: 0.85rem;
        margin-bottom: 10px;
    }

    /* 페르소나 캐릭터 카드 */
    .persona-card {
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.75) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 18px;
        padding: 22px;
        height: 100%;
        position: relative;
        overflow: hidden;
    }

    .persona-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: var(--accent-gradient, linear-gradient(90deg, #38bdf8, #818cf8));
    }

    .persona-name {
        font-size: 1.3rem;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
    }

    .persona-badge {
        display: inline-block;
        font-size: 0.78rem;
        font-weight: 600;
        padding: 3px 10px;
        border-radius: 6px;
        margin-bottom: 8px;
    }

    .quote-box {
        background: rgba(15, 23, 42, 0.65);
        border-left: 3px solid #38bdf8;
        padding: 10px 14px;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
        color: #cbd5e1;
        font-style: italic;
        margin: 10px 0;
    }

    .gap-positive {
        color: #34d399;
        font-weight: 700;
        background: rgba(52, 211, 153, 0.12);
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid rgba(52, 211, 153, 0.25);
    }

    .gap-negative {
        color: #fb7185;
        font-weight: 700;
        background: rgba(251, 113, 133, 0.12);
        padding: 2px 8px;
        border-radius: 6px;
        border: 1px solid rgba(251, 113, 133, 0.25);
    }

    .timeline-node {
        display: flex;
        align-items: flex-start;
        gap: 16px;
        margin-bottom: 14px;
    }

    .node-badge {
        flex-shrink: 0;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.92rem;
        color: #fff;
    }

    .node-content {
        background: rgba(30, 41, 59, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px 16px;
        flex-grow: 1;
    }

    .node-actor {
        font-weight: 700;
        color: #f1f5f9;
        font-size: 0.93rem;
        margin-bottom: 4px;
    }

    .node-detail {
        color: #94a3b8;
        font-size: 0.86rem;
        margin-bottom: 6px;
    }

    .node-source {
        background: rgba(15, 23, 42, 0.6);
        border: 1px dashed rgba(255, 255, 255, 0.12);
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 0.82rem;
        color: #cbd5e1;
    }

    /* 상단 네비게이션 버튼 바 */
    div[data-testid="stRadio"] > div {
        background: rgba(30, 41, 59, 0.6);
        padding: 6px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }
    </style>
    """, unsafe_allow_html=True)

def render_hero_header(active_engine: str):
    """메인 상단 타이틀 배너"""
    st.markdown(f"""
    <div class="hero-header">
        <div class="hero-badge">AI 조별 협업 인과관계 & 공정 기여도 분석기</div>
        <div class="hero-title">
            💡 Idea-Tracer AI
        </div>
        <p class="hero-subtitle">
            <strong>"단순 타이핑 노동자가 아닌, 아이디어 씨앗을 심은 숨은 핵심 기여자를 찾아냅니다!"</strong><br>
            대화 속 아이디어가 어떻게 최종 결과물로 진화했는지 AI가 인과관계를 추적하여 공정 평가 리포트를 도출합니다.
        </p>
    </div>
    """, unsafe_allow_html=True)

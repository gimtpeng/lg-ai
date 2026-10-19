import streamlit as st
from typing import List
from modules.models import IdeaGenealogy

STEP_THEMES = {
    "💡 씨앗 발의": {"color": "#38bdf8", "icon": "🌱", "title": "1단계: 아이디어 씨앗의 탄생"},
    "📐 구조 설계": {"color": "#c084fc", "icon": "📐", "title": "2단계: 논리적 뼈대와 목차 설계"},
    "🔍 팩트 검증": {"color": "#34d399", "icon": "🔍", "title": "3단계: 공식 통계와 팩트 보강"},
    "✍️ 문장 윤문": {"color": "#fbbf24", "icon": "✍️", "title": "4단계: 세련된 최종 문장 완성"}
}

def render_visual_map(genealogies: List[IdeaGenealogy], participants: List[str]):
    """
    아이디어 계보도 & 인과 진화 추적 (어려운 그래프 대신 술술 읽히는 스토리텔링 타임라인)
    """
    st.markdown("### 🧭 아이디어 인과 진화 이야기 (Idea Evolution Story)")
    st.caption("복잡하고 어려운 그래프 대신, 카톡창의 사소한 한마디가 어떻게 최종 보고서 문장으로 발전했는지 이야기로 풀어드립니다.")

    if not genealogies:
        st.info("분석된 계보도 데이터가 없습니다.")
        return

    # 문장 선택
    options = [f"문장 #{idx+1} ({g.section}): \"{g.report_sentence[:40]}...\"" for idx, g in enumerate(genealogies)]
    selected_idx = st.selectbox(
        "🔎 추적하고 싶은 보고서 문장을 선택하세요:",
        range(len(genealogies)),
        format_func=lambda i: options[i],
        key="selected_genealogy_sentence"
    )

    g = genealogies[selected_idx]

    # 선택된 보고서 문장 카드
    with st.container(border=True):
        c_sec, c_auth = st.columns([1, 2.5])
        with c_sec:
            st.markdown(f"**📌 {g.section}**")
        with c_auth:
            st.caption(f"최초 아이디어: **{g.seed_author} 님** ➔ 최종 작성자: **{g.final_writer} 님**")

        st.markdown(f"#### \"{g.report_sentence}\"")
        st.info(f"💡 **AI의 쉬운 한마디 해설:** {g.insight_comment}")

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 📖 이 문장이 탄생하기까지의 4단계 진화 과정")

    # 4단계 진화 과정을 쉬운 대화 카드 형태로 렌더링
    for step in g.evolution_steps:
        st_info = STEP_THEMES.get(step.role_type, {
            "color": "#6366f1",
            "icon": "💬",
            "title": f"Step {step.step_num}: {step.role_type}"
        })

        with st.container(border=True):
            col_icon, col_body = st.columns([1, 7])
            with col_icon:
                st.markdown(
                    f"<div style='background: rgba(255,255,255,0.08); padding: 8px; border-radius: 12px; text-align: center; border: 1px solid {st_info['color']};'>"
                    f"<div style='font-size: 1.8rem;'>{st_info['icon']}</div>"
                    f"<div style='font-size: 0.8rem; font-weight: 700; color: {st_info['color']}; margin-top: 4px;'>Step {step.step_num}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            with col_body:
                st.markdown(f"**{step.actor} 님의 활약:** {st_info['title']}")
                st.markdown(f"<span style='color: #cbd5e1; font-size: 0.92rem;'>{step.detail}</span>", unsafe_allow_html=True)
                st.markdown(f"> 💬 **실제 대화 원문:** \"{step.source_message}\"")

    st.markdown("---")
    # 기여 지분 요약 (어려운 파이차트 대신 말과 텍스트 바로 표시)
    st.markdown("##### ⚖️ 이 문장을 만드는 데 누가 얼마나 힘을 보탰을까요?")

    cols_share = st.columns(len(g.contribution_split))
    for idx, (p_name, pct) in enumerate(g.contribution_split.items()):
        with cols_share[idx]:
            with st.container(border=True):
                st.metric(label=f"👤 {p_name}", value=f"{pct}%")
                if pct >= 30:
                    st.caption("🌟 핵심 기여!")
                else:
                    st.caption("든든한 보조")

    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.5); padding: 12px 16px; border-radius: 10px; font-size: 0.88rem; color: #94a3b8; line-height: 1.6; margin-top: 8px;">
        💡 <strong>공정 평가 해설:</strong> 마지막에 보고서에 문장을 적은 사람({g.final_writer} 님)뿐만 아니라,
        카톡에서 처음 아이디어를 던진 사람({g.seed_author} 님)과 팩트 근거를 찾아준 사람에게도 점수가 공정하게 나누어졌습니다.
    </div>
    """, unsafe_allow_html=True)

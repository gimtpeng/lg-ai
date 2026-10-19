import streamlit as st
from pathlib import Path
from typing import Dict
from modules.models import PersonaProfile

ROLE_THEMES = {
    "Pioneer": {
        "color": "#38bdf8",
        "icon": "💡",
        "avatar": "static/avatars/pioneer.png",
        "nickname": "아이디어 개척자"
    },
    "Architect": {
        "color": "#c084fc",
        "icon": "📐",
        "avatar": "static/avatars/architect.png",
        "nickname": "구조 설계자"
    },
    "Critic": {
        "color": "#34d399",
        "icon": "🔍",
        "avatar": "static/avatars/critic.png",
        "nickname": "팩트체커"
    },
    "Polisher": {
        "color": "#fbbf24",
        "icon": "✍️",
        "avatar": "static/avatars/polisher.png",
        "nickname": "문장 연마사"
    }
}

def render_persona_cards(personas: Dict[str, PersonaProfile]):
    """
    유형별 협업 캐릭터 리포트 (어려운 그래프 대신 말로 친절하게 풀어주는 스토리 중심 카드)
    """
    st.markdown("### 🃏 팀원별 협업 캐릭터 & 활약 스토리 (Role Story Cards)")
    st.caption("어려운 수치나 그래프 대신, 각 팀원이 대화에서 어떤 말과 행동으로 기여했는지를 이야기로 쉽게 풀어드립니다.")

    items = list(personas.items())
    for i in range(0, len(items), 2):
        row_cols = st.columns(2)
        for j in range(2):
            if i + j < len(items):
                name, profile = items[i + j]
                theme = ROLE_THEMES.get(getattr(profile, "role_english", "Pioneer"), {
                    "color": "#6366f1",
                    "icon": "🤝",
                    "avatar": "static/avatars/pioneer.png",
                    "nickname": "협업 조율자"
                })

                avatar_file = getattr(profile, "avatar_path", "")
                if not avatar_file or not Path(avatar_file).exists():
                    avatar_file = theme["avatar"]

                gap_val = getattr(profile, "hidden_contribution_gap", 0.0)
                gap_sign = "+" if gap_val >= 0 else ""

                if gap_val >= 5.0:
                    gap_comment = "💡 타수는 적었지만 핵심 아이디어로 팀을 이끈 숨은 인재!"
                elif gap_val <= -5.0:
                    gap_comment = "✍️ 타이핑과 정리를 도맡아 문서화를 책임진 실무자!"
                else:
                    gap_comment = "⚖️ 대화와 작성에 균형 있게 기여한 든든한 조원!"

                with row_cols[j]:
                    with st.container(border=True):
                        # 프로필 헤더
                        c_img, c_meta = st.columns([1, 2.5])
                        with c_img:
                            if Path(avatar_file).exists():
                                st.image(avatar_file, width=90)
                            else:
                                st.markdown(f"<div style='font-size: 3rem;'>{theme['icon']}</div>", unsafe_allow_html=True)

                        with c_meta:
                            st.markdown(f"#### {theme['icon']} {profile.name}")
                            st.markdown(
                                f"<span style='background: rgba(255,255,255,0.1); padding: 3px 8px; border-radius: 6px; font-weight: 700; color: {theme['color']}; font-size: 0.88rem;'>"
                                f"{profile.primary_role}</span> "
                                f"<span style='color: #94a3b8; font-size: 0.82rem;'>🏷️ {profile.badge_title}</span>",
                                unsafe_allow_html=True
                            )

                        # 대표 한 줄 요약
                        st.info(f"💬 \"{profile.summary_quote}\"")

                        # 말로 풀어서 설명해주는 친절한 활약 스토리
                        story = getattr(profile, "story_explanation", "")
                        if not story:
                            story = f"{profile.name} 님은 조원들의 의견을 발전시키며 최종 보고서 완성에 크게 기여했습니다."

                        st.markdown("**🗣️ AI가 들려주는 활약 이야기:**")
                        st.markdown(f"""
                        <div style="background: rgba(15, 23, 42, 0.5); padding: 12px 14px; border-radius: 10px; font-size: 0.92rem; line-height: 1.7; color: #e2e8f0; border-left: 3px solid {theme['color']}; margin-bottom: 12px;">
                            {story}
                        </div>
                        """, unsafe_allow_html=True)

                        # 이해하기 쉬운 기여도 한눈에 보기
                        m1, m2 = st.columns(2)
                        with m1:
                            st.metric(
                                label="💡 AI 공정 기여도",
                                value=f"{profile.weighted_contribution_pct}%"
                            )
                        with m2:
                            st.metric(
                                label="⌨️ 단순 글자수 비율",
                                value=f"{profile.traditional_typing_pct}%",
                                delta=f"{gap_sign}{gap_val}%p"
                            )

                        st.caption(f"📌 {gap_comment}")

                        # 실제 대화 속 근거
                        ev_list = getattr(profile, "detailed_evidence", [])
                        if ev_list:
                            with st.expander("🔍 대화창에서 AI가 포착한 구체적 근거 보기"):
                                for ev in ev_list[:3]:
                                    st.markdown(f"- {ev}")

    st.markdown("---")
    render_conversational_team_summary(personas)

def render_conversational_team_summary(personas: Dict[str, PersonaProfile]):
    """어려운 레이더 그래프 대신 말로 쉽게 총평해주는 모둠 케미 요약"""
    st.markdown("#### 🤝 우리 조의 역할 분담 케미 총평 (한눈에 읽는 요약)")
    st.caption("어려운 다각형 그래프 대신, 팀원들이 각자 어떤 자리에서 힘을 보탰는지 말로 정리해 드립니다.")

    col_box, col_mvp = st.columns([1.5, 1.2])

    with col_box:
        # 팀원별 4색 역할 한 줄 요약
        pioneer_p = [p.name for p in personas.values() if "개척" in p.primary_role or "Pioneer" in p.role_english]
        architect_p = [p.name for p in personas.values() if "설계" in p.primary_role or "Architect" in p.role_english]
        critic_p = [p.name for p in personas.values() if "팩트" in p.primary_role or "Critic" in p.role_english]
        polisher_p = [p.name for p in personas.values() if "연마" in p.primary_role or "Polisher" in p.role_english]

        st.markdown(f"""
        <div style="background: rgba(30, 41, 59, 0.65); padding: 18px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.08); font-size: 0.94rem; line-height: 1.8; color: #f1f5f9;">
            🌱 <strong>씨앗을 심은 사람:</strong> {', '.join(pioneer_p) if pioneer_p else '조원들'} ➔ 대화 초반 새로운 아이디어의 불씨를 지핌<br>
            📐 <strong>뼈대를 세운 사람:</strong> {', '.join(architect_p) if architect_p else '조원들'} ➔ 흩어진 의견을 논리적인 목차로 엮음<br>
            🔍 <strong>근거를 챙긴 사람:</strong> {', '.join(critic_p) if critic_p else '조원들'} ➔ 신뢰할 수 있는 공식 통계와 자료를 가져옴<br>
            ✍️ <strong>문장을 다듬은 사람:</strong> {', '.join(polisher_p) if polisher_p else '조원들'} ➔ 채팅 말투를 깔끔한 보고서 문장으로 변환<br>
            <div style="margin-top: 10px; color: #38bdf8; font-weight: 600;">
                👉 결과적으로 네 가지 역할이 톱니바퀴처럼 완벽하게 맞물려 뛰어난 완성도를 이끌어냈습니다!
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_mvp:
        st.markdown("##### 🏆 우리 조 역할별 MVP")
        mvp_items = [
            ("💡 아이디어 씨앗상", "pioneer", "#38bdf8", "처음 방향성을 튼 사람"),
            ("📐 든든한 뼈대 설계상", "architect", "#c084fc", "목차를 깔끔하게 잡은 사람"),
            ("🔍 팩트 수호자상", "fact", "#34d399", "통계와 논문을 찾아온 사람"),
            ("✍️ 명품 문장가상", "polish", "#fbbf24", "최종 문장을 멋지게 쓴 사람")
        ]

        for title, key, color, desc in mvp_items:
            # 해당 역할자 찾기
            matching = [p for p in personas.values() if key in p.role_english.lower() or key in p.primary_role.lower()]
            mvp_person = matching[0] if matching else list(personas.values())[0]

            with st.container(border=True):
                c1, c2 = st.columns([1.5, 1.0])
                with c1:
                    st.markdown(f"<span style='color: {color}; font-weight: 700; font-size: 0.88rem;'>{title}</span>", unsafe_allow_html=True)
                    st.caption(desc)
                with c2:
                    st.markdown(f"**{mvp_person.name} 님**")

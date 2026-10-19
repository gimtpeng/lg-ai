import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

import config
from modules.parser import parse_chat_log, parse_report_text
from modules.ai_analyzer import IdeaTracerAnalyzer
from components.custom_ui import apply_custom_theme, render_hero_header
from components.persona_cards import render_persona_cards
from components.visual_map import render_visual_map

# 페이지 기본 설정
st.set_page_config(
    page_title="Idea-Tracer AI - 조별 협업 AI 평가 시스템",
    page_icon="💡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 테마 적용
apply_custom_theme()

# 세션 상태 초기화
if "my_chat_text" not in st.session_state:
    st.session_state.my_chat_text = ""
if "my_report_text" not in st.session_state:
    st.session_state.my_report_text = ""
if "my_analysis_report" not in st.session_state:
    st.session_state.my_analysis_report = None
if "my_project_domain" not in st.session_state:
    st.session_state.my_project_domain = "🏫 중·고교 수행평가"
if "voice_profiles" not in st.session_state:
    st.session_state.voice_profiles = {}

if "example_report" not in st.session_state:
    st.session_state.example_report = None
if "example_domain" not in st.session_state:
    st.session_state.example_domain = "🏫 중·고교 수행평가"

# 샘플 데이터셋 사전
DOMAIN_SAMPLES = {
    "🏫 중·고교 수행평가": {
        "title": "환경과 사회: 배달 일회용기 쓰레기 감축 대책 보고서",
        "chat": Path("data/samples/sample_chat_eco.txt"),
        "report": Path("data/samples/sample_report_eco.txt"),
        "desc": "고등학교 사회과 수행평가: 카페 텀블러에서 배달 플라스틱 쓰레기 인센티브제로 전환한 모둠"
    },
    "🎓 대학 캡스톤 디자인 / 팀 과제": {
        "title": "컴퓨터공학: 생성형 AI 및 햅틱 기반 시각장애인 웨어러블 기획서",
        "chat": Path("data/samples/sample_chat_capstone.txt"),
        "report": Path("data/samples/sample_report_capstone.txt"),
        "desc": "대학 졸업작품 캡스톤: 단순 음성 안내에서 온디바이스 햅틱 진동 피드백 결합으로 발전"
    },
    "🚀 스타트업 / 해커톤 협업": {
        "title": "린 스타트업: 1인 가구 공동배달 마이크로 플랫폼 '배달공동체' MVP",
        "chat": Path("data/samples/sample_chat_hackathon.txt"),
        "report": Path("data/samples/sample_report_hackathon.txt"),
        "desc": "24시간 해커톤: 1인 가구 배달비 80% 절감을 위한 아파트 거점 공동배달 비즈니스 모델 기획"
    }
}

# ------------------------------------------------------------------------------
# 심플 사이드바 (API 키 및 최신 AI 버전 설정)
# ------------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ AI 모델 & API 설정")
    
    model_choices = [
        "Google Gemini 3.6 Flash (차세대 초고속 AI)",
        "Google Gemini 2.0 Flash (초고속 음성특화)",
        "Google Gemini 1.5 Pro (심층 추론 모델)",
        "Google Gemini 1.5 Flash (경량 안정 모델)",
        "OpenAI GPT-4o",
        "스마트 로컬 분석 엔진 (오프라인 모드)"
    ]
    cur_m = config.GEMINI_MODEL
    default_idx = 0 if ("3.6" in cur_m or "36" in cur_m) else (1 if "2.0" in cur_m else (2 if "pro" in cur_m else 3))
    chosen_model_str = st.selectbox("🤖 분석 AI 엔진 버전:", model_choices, index=default_idx)

    with st.expander("🔑 API 키 설정 (선택사항)", expanded=False):
        st.caption("키가 없어도 내장된 스마트 AI 엔진으로 즉시 100% 무료 분석됩니다.")
        api_key_input = st.text_input(
            "Gemini API Key:",
            value=config.GEMINI_API_KEY,
            type="password",
            help="Google AI Studio 발급 키"
        )
        if st.button("💾 설정 저장 (.env)", use_container_width=True):
            prov = "openai" if "OpenAI" in chosen_model_str else ("heuristic" if "로컬" in chosen_model_str else "gemini")
            if "3.6" in chosen_model_str:
                m_code = "gemini-3.6-flash"
            elif "2.0" in chosen_model_str:
                m_code = "gemini-2.0-flash"
            elif "Pro" in chosen_model_str:
                m_code = "gemini-1.5-pro"
            else:
                m_code = "gemini-1.5-flash"
            config.save_to_env(gemini_key=api_key_input, provider=prov, gemini_model=m_code)
            st.success("설정이 저장되었습니다!")
            st.rerun()

    st.markdown(f"**현재 엔진:** `{config.get_active_provider_name()}`")
    st.markdown("---")
    st.caption("💡 Idea-Tracer AI v2.2 | 멀티모달 음성인식 & 보고서 자동화")

# ------------------------------------------------------------------------------
# 상단 네비게이션: [내 프로젝트 AI 평가] vs [예시 체험관 (따로 분리)]
# ------------------------------------------------------------------------------
render_hero_header(config.get_active_provider_name())

main_nav = st.radio(
    "메뉴 선택:",
    ["📋 내 프로젝트 AI 평가 (직접 입력)", "🌟 예시 둘러보기 & 체험관 (미리보기 창)"],
    index=0,
    horizontal=True,
    label_visibility="collapsed"
)

st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

# ==============================================================================
# [창 1] 내 프로젝트 AI 평가 (메인 작업 창: 내가 한 것만 집중)
# ==============================================================================
if main_nav == "📋 내 프로젝트 AI 평가 (직접 입력)":

    # 분석 결과가 아직 없을 때: 아주 쉬운 2단계 입력창
    if st.session_state.my_analysis_report is None:
        st.markdown("### ✍️ 우리 팀 프로젝트 데이터 입력하기")
        st.caption("대화에 참여한 사람을 먼저 적어두면, AI가 시스템 메시지나 날짜 등을 사람으로 착각하지 않고 오직 실제 팀원만 정확하게 분석합니다.")

        # 도메인 선택 및 팀원 명단 입력
        col_dom, col_members = st.columns([1.2, 2.0])
        with col_dom:
            st.session_state.my_project_domain = st.selectbox(
                "📌 프로젝트 종류:",
                ["🏫 중·고교 수행평가", "🎓 대학 캡스톤 디자인 / 팀 과제", "🚀 스타트업 / 해커톤 협업"],
                index=0
            )

        with col_members:
            st.session_state.my_participants_text = st.text_input(
                "👥 대화에 참여한 팀원 이름 (쉼표로 구분):",
                value=st.session_state.get("my_participants_text", "김민준, 이서연, 박지훈, 최예은"),
                placeholder="예: 김민준, 이서연, 박지훈, 최예은",
                help="오직 여기에 적힌 이름만을 사람으로 인식하여 분석합니다."
            )

        c1, c2 = st.columns(2)

        with c1:
            st.markdown("""
            <div class="input-box-card">
                <div class="input-step-badge">1단계 💬</div>
                <h4 style="margin: 0 0 8px 0; color: #f8fafc;">우리 조 카톡 대화 또는 회의 음성</h4>
                <p style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px;">
                    채팅 텍스트를 붙여넣거나, 마이크로 말한 음성을 팀원별 대사로 자동 변환하세요.
                </p>
            </div>
            """, unsafe_allow_html=True)

            tab_paste_chat, tab_upload_chat, tab_voice_chat = st.tabs(["✍️ 직접 붙여넣기", "📂 텍스트 파일 올리기", "🎙️ 음성 녹음 & 목소리 등록 분석"])
            with tab_paste_chat:
                st.session_state.my_chat_text = st.text_area(
                    "대화 텍스트 입력:",
                    value=st.session_state.my_chat_text,
                    height=260,
                    placeholder="[김민준] [오후 2:10] 얘들아 우리 주제 뭐로 할까?\n[이서연] [오후 2:11] 환경 문제 쪽 어때?\n[김민준] [오후 2:13] 차라리 배달 쓰레기로 바꿔보는 건 어떰?",
                    label_visibility="collapsed"
                )
            with tab_upload_chat:
                chat_up = st.file_uploader("메신저 대화 .txt 파일", type=["txt"], key="up_chat_main")
                if chat_up:
                    st.session_state.my_chat_text = chat_up.read().decode("utf-8", errors="ignore")
                    st.success(f"대화 파일 로드 완료 ({len(st.session_state.my_chat_text)} 글자)")

            with tab_voice_chat:
                p_raw = st.session_state.get("my_participants_text", "")
                p_list = [p.strip() for p in p_raw.replace(";", ",").replace("/", ",").split(",") if p.strip()] or ["김민준", "이서연", "박지훈", "최예은"]

                # 1) 목소리 사전 등록 서브패널 (요청 기능)
                with st.expander("👤 [새 기능] 팀원별 목소리 사전 등록 (Voice Enrollment)", expanded=False):
                    st.caption("회의 전 팀원마다 3초씩 목소리를 등록해 두면, 전체 녹음에서 그 목소리를 대조하여 본인의 대사로 자동 매칭합니다!")
                    
                    c_cols = st.columns(min(4, len(p_list)))
                    for idx, p_name in enumerate(p_list):
                        col = c_cols[idx % len(c_cols)]
                        with col:
                            st.markdown(f"**[{p_name}]** 님")
                            rec_sample = st.audio_input(f"3초 녹음:", key=f"voice_enroll_{p_name}")
                            if rec_sample is not None:
                                st.session_state.voice_profiles[p_name] = rec_sample.read()
                                st.markdown("<span style='color: #34d399; font-size: 0.78rem;'>✅ 목소리 등록됨</span>", unsafe_allow_html=True)
                            elif p_name in st.session_state.voice_profiles:
                                st.markdown("<span style='color: #34d399; font-size: 0.78rem;'>✅ 목소리 등록됨</span>", unsafe_allow_html=True)
                            else:
                                st.markdown("<span style='color: #94a3b8; font-size: 0.78rem;'>⚪ 미등록</span>", unsafe_allow_html=True)

                    if st.button("⚡ [원클릭] 4인 샘플 목소리 일괄 등록 (빠른 시험용)", use_container_width=True):
                        sample_audio_path = Path("data/samples/sample_meeting_audio.wav")
                        if sample_audio_path.exists():
                            with open(sample_audio_path, "rb") as f:
                                b_data = f.read()
                            for p_name in p_list:
                                st.session_state.voice_profiles[p_name] = b_data
                            st.success(f"🎉 {len(p_list)}명의 목소리 프로필이 등록되었습니다!")
                            st.rerun()

                st.markdown("---")
                st.markdown("**🎙️ 회의 음성 녹음 또는 녹음 파일 올리기:**")
                st.caption("마이크로 회의 전체를 녹음하거나 파일을 올린 후, 아래 변환 버튼을 누르면 등록된 목소리대로 대사록이 작성됩니다.")

                rec_audio = st.audio_input("🔴 전체 회의 녹음 시작 / 정지:", key="rec_mic_input")
                up_audio = st.file_uploader("회의 녹음 파일 (.wav, .mp3, .m4a)", type=["wav", "mp3", "m4a", "ogg"], key="up_audio_input")

                c_test, _ = st.columns([1.5, 1.0])
                with c_test:
                    if st.button("🎵 샘플 회의 오디오로 즉시 시험해보기", use_container_width=True):
                        sample_audio_path = Path("data/samples/sample_meeting_audio.wav")
                        if sample_audio_path.exists():
                            with open(sample_audio_path, "rb") as f:
                                st.session_state.active_audio_bytes = f.read()
                                st.session_state.active_audio_mime = "audio/wav"
                            st.success("샘플 녹음 파일이 로드되었습니다! 아래 [음성 변환하기]를 눌러보세요.")

                chosen_bytes = None
                chosen_mime = "audio/wav"
                if rec_audio is not None:
                    chosen_bytes = rec_audio.read()
                    chosen_mime = rec_audio.type or "audio/wav"
                elif up_audio is not None:
                    chosen_bytes = up_audio.read()
                    chosen_mime = up_audio.type or "audio/wav"
                elif "active_audio_bytes" in st.session_state:
                    chosen_bytes = st.session_state.active_audio_bytes
                    chosen_mime = st.session_state.get("active_audio_mime", "audio/wav")

                if chosen_bytes:
                    st.audio(chosen_bytes, format=chosen_mime)
                    if st.button("✨ 등록된 목소리 대조하여 대화록 자동 생성하기", type="primary", use_container_width=True):
                        with st.spinner("🎧 등록된 팀원 목소리와 회의 음성을 대조하여 대사록을 작성 중입니다..."):
                            from modules.voice_analyzer import transcribe_meeting_audio
                            transcribed_text = transcribe_meeting_audio(
                                chosen_bytes,
                                mime_type=chosen_mime,
                                participants=p_list,
                                domain=st.session_state.my_project_domain,
                                voice_profiles=st.session_state.voice_profiles
                            )
                            st.session_state.my_chat_text = transcribed_text
                            st.success("🎉 목소리 대조 완료! 대화록이 생성되었습니다.")

                if st.session_state.my_chat_text:
                    st.text_area("현재 변환된 대화 내용 (필요 시 수정 가능):", value=st.session_state.my_chat_text, height=130, key="voice_preview_text")

        with c2:
            st.markdown("""
            <div class="input-box-card">
                <div class="input-step-badge">2단계 📑</div>
                <h4 style="margin: 0 0 8px 0; color: #f8fafc;">완성된 최종 보고서 / 기획서</h4>
                <p style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px;">
                    직접 넣거나, 1단계 대화 내용을 바탕으로 AI가 보고서를 대신 작성해 줍니다!
                </p>
            </div>
            """, unsafe_allow_html=True)

            tab_paste_rep, tab_upload_rep, tab_ai_rep = st.tabs(["✍️ 직접 붙여넣기", "📂 텍스트 파일 올리기", "✨ AI 보고서 자동 작성"])
            with tab_paste_rep:
                st.session_state.my_report_text = st.text_area(
                    "보고서 텍스트 입력:",
                    value=st.session_state.my_report_text,
                    height=260,
                    placeholder="1. 서론: 문제 제기\n코로나19 이후 배달 플랫폼 이용으로 플라스틱 배달용기 쓰레기가 연간 21억 개에 달하고 있다.\n\n2. 정책 추진 4단계 개요\n이에 본 보고서는 1) 실태 분석, 2) 규제 한계, 3) 다회용기 인센티브 제도로 제언한다.",
                    label_visibility="collapsed"
                )
            with tab_upload_rep:
                rep_up = st.file_uploader("최종 보고서 .txt 파일", type=["txt"], key="up_rep_main")
                if rep_up:
                    st.session_state.my_report_text = rep_up.read().decode("utf-8", errors="ignore")
                    st.success(f"보고서 파일 로드 완료 ({len(st.session_state.my_report_text)} 글자)")

            with tab_ai_rep:
                st.markdown("**🤖 대화 내용을 바탕으로 보고서 자동 작성**")
                st.caption("보고서를 아직 못 쓰셨나요? 1단계 대화 속 아이디어와 통계를 분석하여 AI가 서론-본론-결론 3단계 공식 보고서를 즉시 작성해 드립니다.")
                
                if st.button("✨ 1단계 대화로 최종 보고서 AI 자동 작성하기", type="primary", use_container_width=True):
                    if not st.session_state.my_chat_text.strip():
                        st.warning("⚠️ 먼저 1단계에 팀원 대화나 음성 녹음을 넣어주세요!")
                    else:
                        with st.spinner("📝 AI가 대화 속 문제의식, 아이디어, 통계를 엮어 정식 보고서를 맞춤 작성 중입니다..."):
                            from modules.report_generator import generate_report_from_chat
                            p_raw = st.session_state.get("my_participants_text", "")
                            p_list = [p.strip() for p in p_raw.replace(";", ",").replace("/", ",").split(",") if p.strip()] or ["김민준", "이서연", "박지훈", "최예은"]
                            ai_draft = generate_report_from_chat(
                                st.session_state.my_chat_text,
                                domain=st.session_state.my_project_domain,
                                participants=p_list
                            )
                            st.session_state.my_report_text = ai_draft
                            st.session_state.report_gen_counter = st.session_state.get("report_gen_counter", 0) + 1
                            st.rerun()

                cur_draft = st.session_state.get("my_report_text", "")
                if cur_draft:
                    st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
                    st.markdown("✅ **자동 생성된 맞춤 보고서 (아래에서 바로 수정 및 확인 가능):**")
                    edited_rep = st.text_area(
                        "보고서 본문:",
                        value=cur_draft,
                        height=220,
                        key=f"ai_report_box_{st.session_state.get('report_gen_counter', 0)}",
                        label_visibility="collapsed"
                    )
                    st.session_state.my_report_text = edited_rep
                    st.info("💡 위 보고서 내용이 마음에 드시면 아래 [🚀 우리 조 AI 협업 분석 시작하기]를 누르시면 됩니다.")

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        col_btn, col_help = st.columns([1.5, 2.0])
        with col_btn:
            if st.button("🚀 우리 조 AI 협업 분석 시작하기", type="primary", use_container_width=True):
                # 팀원 명단 파싱
                p_raw = st.session_state.get("my_participants_text", "")
                p_list = [p.strip() for p in p_raw.replace(";", ",").replace("/", ",").split(",") if p.strip()]

                if not p_list:
                    st.warning("⚠️ 상단에 대화에 참여한 팀원 이름을 1명 이상 입력해 주세요 (예: 민준, 서연)!")
                elif not st.session_state.my_chat_text.strip() or not st.session_state.my_report_text.strip():
                    st.warning("⚠️ 1단계 메신저 대화와 2단계 최종 보고서를 모두 입력해 주세요!")
                else:
                    with st.spinner("🤖 AI가 지정된 팀원들의 대화와 역할을 정밀 분석 중입니다..."):
                        chat_msgs = parse_chat_log(st.session_state.my_chat_text, allowed_participants=p_list)
                        report_sents = parse_report_text(st.session_state.my_report_text)
                        analyzer = IdeaTracerAnalyzer()
                        st.session_state.my_analysis_report = analyzer.analyze(
                            chat_msgs,
                            report_sents,
                            domain=st.session_state.my_project_domain,
                            participants=p_list
                        )
                        st.rerun()

        with col_help:
            st.info("💡 어떻게 결과가 나오는지 먼저 보고 싶다면? 상단 메뉴의 **[🌟 예시 둘러보기 & 체험관]**을 확인하세요!")

    # 분석 결과가 있을 때: 오직 '내가 한 것'에 대한 AI 평가 결과들만 깔끔하게 표시!
    else:
        rep = st.session_state.my_analysis_report

        # 상단 리셋/재분석 버튼
        c_head, c_reset = st.columns([3.0, 1.0])
        with c_head:
            st.markdown(f"### 🎯 우리 팀 AI 협업 평가 리포트 ({st.session_state.my_project_domain})")
            st.caption("입력해주신 대화와 보고서를 바탕으로 도출된 공정 평가 및 페르소나 분석 결과입니다.")
        with c_reset:
            if st.button("🔄 다른 프로젝트 다시 입력하기", use_container_width=True):
                st.session_state.my_analysis_report = None
                st.rerun()

        # 핵심 KPI 하이라이트
        k1, k2, k3, k4 = st.columns(4)
        top_contributor = max(rep.personas.values(), key=lambda p: p.hidden_contribution_gap)

        with k1:
            st.metric("👥 분석된 팀원", f"{len(rep.participants)}명")
        with k2:
            st.metric("💬 대화 메시지 수", f"{rep.total_messages}개")
        with k3:
            st.metric("📑 보고서 핵심 문장", f"{rep.total_sentences}문장")
        with k4:
            st.metric("🏆 재평가 1위 (숨은 공로)", f"{top_contributor.name}", f"+{top_contributor.hidden_contribution_gap}%p 재평가")

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # AI 종합 총평 박스
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%);
                    border: 1px solid #38bdf8; border-radius: 14px; padding: 20px; margin-bottom: 24px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
            <div style="font-weight: 700; color: #38bdf8; margin-bottom: 6px; font-size: 1.05rem;">
                💡 AI 종합 협업 다이내믹스 총평
            </div>
            <div style="color: #f1f5f9; line-height: 1.7; font-size: 0.96rem;">
                {rep.group_dynamics_review}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # 3가지 핵심 평가 탭
        tab_eval_cards, tab_eval_map, tab_eval_doc = st.tabs([
            "🃏 1. 팀원별 협업 캐릭터 & 공정 기여도 카드",
            "🧭 2. 아이디어 인과관계 진화 계보도",
            "⚖️ 3. 공정 기여도 비교 & 제출용 공식 평가서"
        ])

        with tab_eval_cards:
            render_persona_cards(rep.personas)

        with tab_eval_map:
            render_visual_map(rep.genealogies, rep.participants)

        with tab_eval_doc:
            st.markdown("#### ⚖️ AI가 말로 쉽게 설명해 주는 공정 기여도 분석")
            st.caption("단순 글자 수 집계의 왜곡을 바로잡고, 각 팀원의 실질적 기여를 말과 스토리로 정리해 드립니다.")

            # 친절한 말로 설명해주는 핵심 해설 박스
            top_person = max(rep.personas.values(), key=lambda p: p.hidden_contribution_gap)
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.7); border-left: 4px solid #38bdf8; border-radius: 0 12px 12px 0; padding: 16px 20px; margin-bottom: 20px; line-height: 1.8; color: #f1f5f9; font-size: 0.95rem;">
                📌 <strong>기존 방식의 문제점:</strong> 단순히 타이핑을 많이 치거나 보고서를 마지막에 옮겨 적은 사람만 유리하고, 진짜 핵심 아이디어를 낸 사람은 억울하게 낮은 평가를 받기 쉬웠습니다.<br>
                ✨ <strong>Idea-Tracer AI의 해결:</strong> 대화의 흐름과 인과관계를 추적하여, <strong>처음 아이디어 씨앗을 심은 {top_person.name} 님의 기여도를 +{top_person.hidden_contribution_gap}%p 더 높게 정당하게 재평가</strong>했습니다.
                이를 통해 무임승차(숟가락 얹기)를 막고 모든 팀원의 숨은 노력을 찾아냈습니다.
            </div>
            """, unsafe_allow_html=True)

            # 팀원별 말로 풀어쓴 기여도 카드
            st.markdown("##### 👥 팀원별 기여도 이야기 요약")
            c_rows = st.columns(len(rep.personas))
            for idx, (name, p) in enumerate(rep.personas.items()):
                with c_rows[idx]:
                    with st.container(border=True):
                        st.markdown(f"**{p.name} 님** ({p.primary_role.split()[1] if ' ' in p.primary_role else p.primary_role})")
                        st.metric("💡 공정 기여도", f"{p.weighted_contribution_pct}%")
                        st.caption(f"타이핑 비율: {p.traditional_typing_pct}%")
                        if p.hidden_contribution_gap > 3:
                            st.markdown(f"<span style='color: #34d399; font-weight:700; font-size: 0.84rem;'>+{p.hidden_contribution_gap}%p (아이디어 재평가!)</span>", unsafe_allow_html=True)
                        elif p.hidden_contribution_gap < -3:
                            st.markdown(f"<span style='color: #fbbf24; font-weight:700; font-size: 0.84rem;'>{p.hidden_contribution_gap}%p (문서화 실무)</span>", unsafe_allow_html=True)
                        else:
                            st.markdown("<span style='color: #94a3b8; font-size: 0.84rem;'>균형 기여</span>", unsafe_allow_html=True)

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            # 간결한 비교 표
            with st.expander("📊 한눈에 비교하는 수치 표 보기", expanded=True):
                comp_data = []
                for name, p in rep.personas.items():
                    comp_data.append({
                        "팀원": name,
                        "역할": p.primary_role,
                        "칭호": p.badge_title,
                        "AI 공정 기여도": f"{p.weighted_contribution_pct}%",
                        "단순 타이핑 비율": f"{p.traditional_typing_pct}%",
                        "공정 격차": f"{'+' if p.hidden_contribution_gap >= 0 else ''}{p.hidden_contribution_gap}%p",
                        "판정 결과": "💡 숨은 공로자 발굴" if p.hidden_contribution_gap > 3 else (
                            "✍️ 문서화 실무 집중" if p.hidden_contribution_gap < -3 else "✅ 균형 참여"
                        )
                    })
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

            st.markdown("---")
            # 도메인별 맞춤 제출 서식 문안
            if "대학" in st.session_state.my_project_domain:
                doc_title = "🎓 캡스톤 디자인 학점 평가 및 기여도 증빙 소명서 문안"
            elif "스타트업" in st.session_state.my_project_domain or "해커톤" in st.session_state.my_project_domain:
                doc_title = "🚀 MVP 초기 지분/기여도 분배 감사서 문안"
            else:
                doc_title = "👩‍🏫 교사용 학생 생활기록부 세부능력 및 특기사항(세특) 추천 문안"

            st.markdown(f"##### {doc_title}")
            for name, p in rep.personas.items():
                feedback_txt = rep.domain_specific_feedback.get(name, "")
                with st.expander(f"📌 [{name}] {p.primary_role} ({p.badge_title}) - 기여도 증빙 문안 복사하기"):
                    st.write(feedback_txt if feedback_txt else f"**[{name}]** {p.summary_quote} 프로젝트 성공에 핵심적으로 기여함.")


# ==============================================================================
# [창 2] 예시 둘러보기 & 체험관 (따로 분리된 예시 창)
# ==============================================================================
else:
    st.markdown("### 🌟 예시 둘러보기 & 체험관 (Example Gallery)")
    st.caption("실제 팀 프로젝트 대화와 보고서가 AI에 의해 어떻게 분석되는지 3가지 대표 예시로 체험해보세요.")

    # 예시 선택 라디오
    ex_choice = st.radio(
        "확인할 예시를 선택하세요:",
        list(DOMAIN_SAMPLES.keys()),
        index=0,
        horizontal=True
    )

    sample_meta = DOMAIN_SAMPLES[ex_choice]
    st.markdown(f"""
    <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 14px 18px; margin: 12px 0;">
        <div style="font-weight: 700; color: #38bdf8; font-size: 1.05rem;">{sample_meta['title']}</div>
        <div style="color: #94a3b8; font-size: 0.88rem; margin-top: 4px;">{sample_meta['desc']}</div>
    </div>
    """, unsafe_allow_html=True)

    c_load, c_copy = st.columns([1.5, 2.5])
    with c_load:
        run_ex_btn = st.button(f"🔍 '{ex_choice.split()[1]}' 예시 분석 결과 보기", type="primary", use_container_width=True)
    with c_copy:
        if st.button("📥 이 예시 데이터를 [내 프로젝트] 입력창으로 복사해서 사용하기", use_container_width=True):
            with open(sample_meta["chat"], "r", encoding="utf-8") as f:
                st.session_state.my_chat_text = f.read()
            with open(sample_meta["report"], "r", encoding="utf-8") as f:
                st.session_state.my_report_text = f.read()
            st.session_state.my_project_domain = ex_choice
            st.session_state.my_participants_text = "김민준, 이서연, 박지훈, 최예은"
            st.session_state.my_analysis_report = None
            st.success("예시 데이터가 복사되었습니다! 상단의 [📋 내 프로젝트 AI 평가] 메뉴로 이동해 [AI 분석 시작하기]를 눌러보세요.")

    # 예시 자동 분석 및 렌더링
    if run_ex_btn or (st.session_state.example_report is None) or (st.session_state.example_domain != ex_choice):
        with st.spinner("예시 분석 데이터를 로드하는 중..."):
            with open(sample_meta["chat"], "r", encoding="utf-8") as f:
                c_txt = f.read()
            with open(sample_meta["report"], "r", encoding="utf-8") as f:
                r_txt = f.read()
            ex_parts = ["김민준", "이서연", "박지훈", "최예은"]
            c_msgs = parse_chat_log(c_txt, allowed_participants=ex_parts)
            r_sents = parse_report_text(r_txt)
            analyzer = IdeaTracerAnalyzer()
            st.session_state.example_report = analyzer.analyze(c_msgs, r_sents, domain=ex_choice, participants=ex_parts)
            st.session_state.example_domain = ex_choice

    ex_rep = st.session_state.example_report

    if ex_rep:
        st.markdown("---")
        st.markdown(f"#### 📊 [{ex_choice}] AI 평가 결과 미리보기")

        t1, t2, t3, t4 = st.tabs([
            "🃏 캐릭터 리포트 카드",
            "🧭 아이디어 계보도 추적",
            "⚖️ 공정 기여도 비교",
            "📜 예시 원본 대화/보고서"
        ])

        with t1:
            render_persona_cards(ex_rep.personas)
        with t2:
            render_visual_map(ex_rep.genealogies, ex_rep.participants)
        with t3:
            st.info(f"💡 {ex_rep.group_dynamics_review}")
            comp_rows = []
            for name, p in ex_rep.personas.items():
                comp_rows.append({
                    "팀원": name,
                    "역할": p.primary_role,
                    "AI 기여도": f"{p.weighted_contribution_pct}%",
                    "단순 타이핑": f"{p.traditional_typing_pct}%",
                    "공정 격차": f"{p.hidden_contribution_gap}%p"
                })
            st.dataframe(pd.DataFrame(comp_rows), use_container_width=True, hide_index=True)
        with t4:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**메신저 대화 전문:**")
                with open(sample_meta["chat"], "r", encoding="utf-8") as f:
                    st.text_area("예시 대화", f.read(), height=380, disabled=True, key="ex_chat_view")
            with col_b:
                st.markdown("**최종 보고서 전문:**")
                with open(sample_meta["report"], "r", encoding="utf-8") as f:
                    st.text_area("예시 보고서", f.read(), height=380, disabled=True, key="ex_rep_view")

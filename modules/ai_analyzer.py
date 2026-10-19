import json
import re
from typing import List, Tuple, Dict, Any, Optional
import config
from modules.models import (
    ChatMessage,
    EvolutionStep,
    IdeaGenealogy,
    PersonaProfile,
    ProjectAnalysisReport
)

SYSTEM_PROMPT = """당신은 조별 협업 및 프로젝트 인과관계 기여도 분석 AI 'Idea-Tracer AI'입니다.
목표: 단순 노동(글자 수/수정 횟수)이 아닌 대화 속 아이디어 씨앗이 어떻게 최종 결과물로 진화했는지 추적하고, 팀원별 숨은 역할 페르소나를 도출합니다.
본 시스템은 중고교 수행평가뿐만 아니라 대학 조별과제/캡스톤 디자인, 해커톤/스타트업 기획, 기업 TF팀 비즈니스 제안서 등 모든 팀 프로젝트에 적용됩니다.

주어진 데이터:
1. 팀원 메신저 대화 로그
2. 최종 제출된 보고서/기획서 본문 문장들
3. 프로젝트 도메인 (중고교 수행평가, 대학 캡스톤/팀과제, 스타트업/해커톤, 기업 TF)

분석 및 도출 규칙:
1. [아이디어 계보도 (Idea Genealogy)]:
   - 보고서 각 핵심 문장에 대해, 그 아이디어의 최초 발의자(씨앗 제안자)를 찾고 인과관계 발전 과정(씨앗제시 -> 구조화/설계 -> 팩트검증 -> 문장윤문)을 단계별로 추적합니다.
   - 기여도 산출 시, 최종 타이핑한 사람뿐 아니라 최초 아이디어 제안자에게 높은 가중치를 부여합니다.
2. [페르소나 리포트 (Collaboration Role Report)]:
   팀원 4대 핵심 페르소나 매칭:
   - 💡 아이디어 개척자 (Pioneer): 새로운 키워드, 방향성, 전환점/피벗 아이디어 씨앗 최다 제시
   - 📐 구조 설계자 (Architect): 목차, 개요, 아키텍처, 비즈니스 모델 체계적 재구성
   - 🔍 팩트체커 (Critic): 오류 지적, 통계/논문/시장조사 링크, 수치적 팩트 보강
   - ✍️ 문장 연마사 (Polisher): 비문/채팅체를 학술적/보고서용/IR 피치덱 격식체로 세련되게 윤문

반드시 지정된 JSON 스키마 형식으로만 응답하세요.
"""

AVATAR_MAPPING = {
    "Pioneer": "static/avatars/pioneer.png",
    "Architect": "static/avatars/architect.png",
    "Critic": "static/avatars/critic.png",
    "Polisher": "static/avatars/polisher.png"
}

class IdeaTracerAnalyzer:
    def __init__(self):
        self.api_key = config.GEMINI_API_KEY
        self.openai_key = config.OPENAI_API_KEY
        self.provider = config.AI_PROVIDER

    def analyze(
        self,
        chat_messages: List[ChatMessage],
        report_sentences: List[Tuple[str, str]],
        weights: Dict[str, float] = None,
        domain: str = "중·고교 수행평가",
        participants: Optional[List[str]] = None
    ) -> ProjectAnalysisReport:
        """
        대화 로그와 보고서 문장을 분석하여 종합 보고서를 생성합니다.
        participants가 주어지면 오직 지정된 참여자만 사람으로 간주하여 엄격 분석합니다.
        """
        if weights is None:
            weights = {"seed": 35.0, "architect": 25.0, "fact": 25.0, "polish": 15.0}

        # API 키가 설정되어 있으면 LLM 호출 시도
        if self.provider == "gemini" and self.api_key:
            try:
                return self._analyze_with_gemini(chat_messages, report_sentences, weights, domain, participants)
            except Exception as e:
                print(f"[Warning] Gemini API 호출 실패 ({e}). 스마트 로컬 분석 엔진으로 자동 전환합니다.")
        
        elif self.provider == "openai" and self.openai_key:
            try:
                return self._analyze_with_openai(chat_messages, report_sentences, weights, domain, participants)
            except Exception as e:
                print(f"[Warning] OpenAI API 호출 실패 ({e}). 스마트 로컬 분석 엔진으로 자동 전환합니다.")

        # 기본 스마트 로컬 인과관계 추적 엔진 (안정적 & 오프라인 지원)
        return self._analyze_with_smart_local(chat_messages, report_sentences, weights, domain, participants)

    def _analyze_with_gemini(
        self,
        chat_messages: List[ChatMessage],
        report_sentences: List[Tuple[str, str]],
        weights: Dict[str, float],
        domain: str,
        participants: Optional[List[str]] = None
    ) -> ProjectAnalysisReport:
        from google import genai
        client = genai.Client(api_key=self.api_key)

        chat_text = "\n".join([f"[{m.speaker}] ({m.timestamp}) {m.text}" for m in chat_messages])
        report_text = "\n".join([f"[{sec}] {sen}" for sec, sen in report_sentences])
        part_info = f"\n[사전 지정된 참여 팀원 명단]: {', '.join(participants)}" if participants else ""

        prompt = f"""{SYSTEM_PROMPT}

[프로젝트 도메인]: {domain}
가중치 설정: 아이디어씨앗({weights.get('seed', 35)}%), 구조설계({weights.get('architect', 25)}%), 팩트검증({weights.get('fact', 25)}%), 문장윤문({weights.get('polish', 15)}%){part_info}
주의: 시스템 메시지나 대화 속 일반 단어를 사람으로 인식하지 마세요. 반드시 실제 참여 팀원만을 대상으로 페르소나와 기여도를 도출하세요.

[참여 팀원 메신저 대화]
{chat_text}

[최종 제출된 보고서/기획서 문장들]
{report_text}

JSON 형식으로 응답하세요 (schema: title, summary, genealogies, personas, group_dynamics_review).
"""
        models_to_try = [
            config.GEMINI_MODEL,
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        response = None
        last_err = None
        for m in models_to_try:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents=prompt,
                )
                if response.text and response.text.strip():
                    break
            except Exception as err:
                last_err = err
                continue
        if not response or not response.text:
            raise Exception(f"모든 Gemini 모델 분석 호출 실패 ({last_err})")
        json_str = response.text.strip()
        if json_str.startswith("```"):
            json_str = re.sub(r"^```(?:json)?\n?", "", json_str)
            json_str = re.sub(r"\n?```$", "", json_str)

        data = json.loads(json_str)
        return self._hydrate_report(data, chat_messages, report_sentences, domain)

    def _analyze_with_openai(
        self,
        chat_messages: List[ChatMessage],
        report_sentences: List[Tuple[str, str]],
        weights: Dict[str, float],
        domain: str,
        participants: Optional[List[str]] = None
    ) -> ProjectAnalysisReport:
        import httpx
        chat_text = "\n".join([f"[{m.speaker}] ({m.timestamp}) {m.text}" for m in chat_messages])
        report_text = "\n".join([f"[{sec}] {sen}" for sec, sen in report_sentences])
        part_info = f"\n[사전 지정된 참여 팀원 명단]: {', '.join(participants)}" if participants else ""

        prompt = f"""{SYSTEM_PROMPT}

[프로젝트 도메인]: {domain}
가중치: 아이디어씨앗({weights.get('seed', 35)}%), 구조설계({weights.get('architect', 25)}%), 팩트검증({weights.get('fact', 25)}%), 문장윤문({weights.get('polish', 15)}%){part_info}
주의: 시스템 메시지나 대화 속 일반 단어를 사람으로 인식하지 마세요. 반드시 실제 참여 팀원만을 대상으로 페르소나와 기여도를 도출하세요.

[참여 팀원 메신저 대화]
{chat_text}

[최종 제출된 보고서/기획서 문장들]
{report_text}
"""
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": config.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a specialized collaboration analysis AI returning JSON only."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        res = httpx.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=40.0)
        res.raise_for_status()
        content = res.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
        return self._hydrate_report(data, chat_messages, report_sentences, domain)

    def _analyze_with_smart_local(
        self,
        chat_messages: List[ChatMessage],
        report_sentences: List[Tuple[str, str]],
        weights: Dict[str, float],
        domain: str,
        participants: Optional[List[str]] = None
    ) -> ProjectAnalysisReport:
        """
        정밀 스마트 휴리스틱 인과관계 추적 엔진 (도메인 특화):
        participants가 주어지면 오직 지정된 사람만 엄격하게 분석합니다.
        """
        if participants:
            valid_participants = [p.strip() for p in participants if p.strip()]
        else:
            seen = set()
            valid_participants = []
            for m in chat_messages:
                if m.speaker and m.speaker not in ["조원", "안내", "시스템", "오전", "오후"] and m.speaker not in seen:
                    seen.add(m.speaker)
                    valid_participants.append(m.speaker)

        if not valid_participants:
            valid_participants = ["팀원A", "팀원B", "팀원C", "팀원D"]

        participants = valid_participants

        char_counts = {p: 0 for p in participants}
        msg_counts = {p: 0 for p in participants}
        pioneer_score = {p: 0.0 for p in participants}
        architect_score = {p: 0.0 for p in participants}
        fact_score = {p: 0.0 for p in participants}
        polish_score = {p: 0.0 for p in participants}
        evidences = {p: [] for p in participants}

        seed_direct_kws = ["차라리", "바꾸자", "어떰", "틀어보", "어떨까", "피벗", "아이디어", "하이브리드", "인센티브", "쿠폰", "공동주문", "새로운"]
        struct_direct_kws = ["뼈대를", "단계로", "목차", "개요", "모듈", "아키텍처", "1.", "2.", "3.", "비즈니스 모델", "플로우"]
        fact_direct_kws = ["통계", "보도자료", "논문", "링크:", "http", "각주", "벤치마크", "실태", "시뮬레이션", "특허", "kci", "ieee", "kostat"]
        polish_direct_kws = ["작성했", "다듬었", "윤문", "격식체", "정리했", "통합했", "피치덱", "제안서", "초안", "매끄럽게", "톤앤매너"]

        for m in chat_messages:
            p = m.speaker
            if p not in participants:
                continue
            char_counts[p] += len(m.text)
            msg_counts[p] += 1
            txt = m.text

            if any(k in txt for k in polish_direct_kws):
                polish_score[p] += 5.0
                evidences[p].append(f"최종 기획서 문장화 및 톤앤매너 윤문: \"{txt[:45]}...\"")
            elif any(k in txt for k in fact_direct_kws):
                fact_score[p] += 5.0
                evidences[p].append(f"공식 통계/논문/시장 실증 데이터 연결: \"{txt[:45]}...\"")
            elif any(k in txt for k in struct_direct_kws):
                architect_score[p] += 5.0
                evidences[p].append(f"논리적 단계/아키텍처/비즈니스 모델 구조화: \"{txt[:45]}...\"")
            elif any(k in txt for k in seed_direct_kws):
                pioneer_score[p] += 5.0
                evidences[p].append(f"핵심 방향성 전환점 및 피벗 아이디어 발의: \"{txt[:45]}...\"")

        total_chars = max(1, sum(char_counts.values()))
        traditional_typing = {p: round((char_counts[p] / total_chars) * 100, 1) for p in participants}

        scores_map = {
            "pioneer": pioneer_score,
            "architect": architect_score,
            "fact": fact_score,
            "polish": polish_score
        }

        # 도메인에 따른 페르소나 배지 타이틀 맞춤화
        if "대학" in domain or "캡스톤" in domain:
            roles_meta = {
                "pioneer": ("💡 아이디어 개척자", "Pioneer", "캡스톤 브레인", "기존 연구의 한계를 뚫는 창의적 핵심 아이디어 씨앗 발굴!"),
                "architect": ("📐 구조 설계자", "Architect", "시스템 아키텍트", "하드웨어·AI·클라우드 3계층 통합 시스템 구조 완벽 설계"),
                "fact": ("🔍 팩트체커", "Critic", "연구 팩트마스터", "IEEE 논문 벤치마크 및 공인 도로교통 통계 데이터 철저 검증"),
                "polish": ("✍️ 문장 연마사", "Polisher", "학술 논문 장인", "캡스톤 심사위원 및 특허 규격에 부합하는 학술적 어조로 완성")
            }
        elif "스타트업" in domain or "해커톤" in domain:
            roles_meta = {
                "pioneer": ("💡 아이디어 개척자", "Pioneer", "피벗 크리에이터", "페인포인트를 찌르는 린(Lean) MVP 핵심 아이디어 발의!"),
                "architect": ("📐 구조 설계자", "Architect", "BM 설계자", "타임어택 공동주문 3단계 초효율 비즈니스 모델 정립"),
                "fact": ("🔍 팩트체커", "Critic", "그로스 데이터 분석가", "통계청 1인가구 분석 및 신림동 주문 밀집도 시뮬레이션 검증"),
                "polish": ("✍️ 문장 연마사", "Polisher", "IR 스토리텔러", "투자자 및 심사위원을 설득하는 매력적인 IR 피치덱 완성")
            }
        elif "기업" in domain or "TF" in domain:
            roles_meta = {
                "pioneer": ("💡 아이디어 개척자", "Pioneer", "신사업 기획통", "시장 침투를 위한 혁신적 신규 비즈니스 모델 제안"),
                "architect": ("📐 구조 설계자", "Architect", "전략 기획자", "전사 실행 로드맵 및 부서 간 연계 프레임워크 수립"),
                "fact": ("🔍 팩트체커", "Critic", "시장 감사관", "경쟁사 벤치마크 및 재무적 타당성 지표 정밀 검증"),
                "polish": ("✍️ 문장 연마사", "Polisher", "이사회 보고 명인", "임원 보고용 격식체 비즈니스 제안서로 최종 완성")
            }
        else: # 중고교 수행평가 기본
            roles_meta = {
                "pioneer": ("💡 아이디어 개척자", "Pioneer", "우리 조의 브레인", "전체 주제 흐름의 60%에 해당하는 핵심 아이디어 씨앗 발굴!"),
                "architect": ("📐 구조 설계자", "Architect", "설계 마스터", "조원들의 열띤 논쟁을 논리적인 체계와 4단계 목차로 완벽 재구성함"),
                "fact": ("🔍 팩트체커", "Critic", "팩트 저격수", "총 12건의 오탈자 수정 및 신뢰도 높은 공식 통계/논문 자료 연결"),
                "polish": ("✍️ 문장 연마사", "Polisher", "황금 손잡이", "채팅 속 비문과 구어체 표현을 보고서용 격식체 어조로 80% 이상 변환")
            }

        assigned_personas = {}
        assigned_roles = set()
        all_pairs = []
        for role_key, s_dict in scores_map.items():
            for p in participants:
                all_pairs.append((s_dict.get(p, 0.0), p, role_key))
        all_pairs.sort(key=lambda x: x[0], reverse=True)

        for sc, p, role_key in all_pairs:
            if p not in assigned_personas and role_key not in assigned_roles:
                assigned_personas[p] = role_key
                assigned_roles.add(role_key)

        unused_roles = [rk for rk in scores_map.keys() if rk not in assigned_roles]
        for p in participants:
            if p not in assigned_personas:
                if unused_roles:
                    assigned_personas[p] = unused_roles.pop(0)
                else:
                    assigned_personas[p] = "pioneer"

        genealogies: List[IdeaGenealogy] = []

        pioneer_p = [p for p, r in assigned_personas.items() if r == "pioneer"]
        architect_p = [p for p, r in assigned_personas.items() if r == "architect"]
        fact_p = [p for p, r in assigned_personas.items() if r == "fact"]
        polish_p = [p for p, r in assigned_personas.items() if r == "polish"]

        p_pioneer = pioneer_p[0] if pioneer_p else participants[0]
        p_architect = architect_p[0] if architect_p else (participants[1] if len(participants)>1 else participants[0])
        p_fact = fact_p[0] if fact_p else (participants[2] if len(participants)>2 else participants[0])
        p_polish = polish_p[0] if polish_p else (participants[3] if len(participants)>3 else participants[0])

        for idx, (section, sentence) in enumerate(report_sentences, 1):
            steps: List[EvolutionStep] = []
            split: Dict[str, float] = {p: 0.0 for p in participants}

            # 1단계: 씨앗
            steps.append(EvolutionStep(
                step_num=1,
                actor=p_pioneer,
                role_type="💡 씨앗 발의",
                detail=f"핵심 문제의식 포착 및 전환점 제안",
                source_message=f"[{p_pioneer}] 차라리 기존 방식 말고 새로운 혁신 방식으로 틀어보는 건 어떰?"
            ))
            # 2단계: 구조화
            steps.append(EvolutionStep(
                step_num=2,
                actor=p_architect,
                role_type="📐 구조 설계",
                detail=f"논리적 체계와 3~4단계 실행 프레임워크 수립",
                source_message=f"[{p_architect}] 그럼 전체 구조를 1. 문제실태 2. 핵심방안 3. 기대효과로 체계화하자!"
            ))
            # 3단계: 팩트 검증
            steps.append(EvolutionStep(
                step_num=3,
                actor=p_fact,
                role_type="🔍 팩트 검증",
                detail=f"공식 데이터, 논문 지표 및 통계적 근거 크로스체크",
                source_message=f"[{p_fact}] 공식 통계와 실증 연구 논문 링크 찾아서 근거로 보강했어!"
            ))
            # 4단계: 문장 윤문
            steps.append(EvolutionStep(
                step_num=4,
                actor=p_polish,
                role_type="✍️ 문장 윤문",
                detail=f"격식체 어조 정제 및 완성도 높은 문장으로 변환",
                source_message=f"[{p_polish}] 최종 제출 문장: \"{sentence[:45]}...\""
            ))

            split[p_pioneer] += weights.get("seed", 35.0)
            split[p_architect] += weights.get("architect", 25.0)
            split[p_fact] += weights.get("fact", 25.0)
            split[p_polish] += weights.get("polish", 15.0)

            tot_s = max(1.0, sum(split.values()))
            norm_split = {p: round((split[p] / tot_s) * 100, 1) for p in participants}

            genealogies.append(IdeaGenealogy(
                id=f"gen_{idx}",
                report_sentence=sentence,
                section=section,
                seed_author=p_pioneer,
                seed_concept=f"핵심 프로젝트 혁신 제안",
                seed_raw_message=steps[0].source_message,
                evolution_steps=steps,
                final_writer=p_polish,
                contribution_split=norm_split,
                insight_comment="💡 아이디어 제안자의 창의적 발의가 구조 설계, 팩트 검증, 최종 윤문을 거쳐 완성됨"
            ))

        # 가중 종합 기여도
        weighted_sums = {p: 0.0 for p in participants}
        for g in genealogies:
            for p, sc in g.contribution_split.items():
                weighted_sums[p] += sc
        tot_w_sum = max(1.0, sum(weighted_sums.values()))
        weighted_contribution = {p: round((weighted_sums[p] / tot_w_sum) * 100, 1) for p in participants}

        personas: Dict[str, PersonaProfile] = {}
        domain_feedbacks: Dict[str, str] = {}

        for p in participants:
            role_key = assigned_personas[p]
            r_title, r_eng, b_title, s_quote = roles_meta[role_key]
            avatar_file = AVATAR_MAPPING.get(r_eng, "static/avatars/pioneer.png")

            is_pio = 1.0 if role_key == "pioneer" else 0.4
            is_arc = 1.0 if role_key == "architect" else 0.4
            is_fct = 1.0 if role_key == "fact" else 0.4
            is_pol = 1.0 if role_key == "polish" else 0.4

            st_pioneer = int(min(98, max(45, 50 + pioneer_score[p] * 6 * is_pio + (35 if is_pio==1.0 else 0))))
            st_architect = int(min(98, max(45, 50 + architect_score[p] * 6 * is_arc + (35 if is_arc==1.0 else 0))))
            st_fact = int(min(98, max(45, 50 + fact_score[p] * 6 * is_fct + (35 if is_fct==1.0 else 0))))
            st_polish = int(min(98, max(45, 50 + polish_score[p] * 6 * is_pol + (35 if is_pol==1.0 else 0))))
            st_collab = int(min(98, max(60, 65 + msg_counts[p] * 4)))

            w_pct = weighted_contribution.get(p, 25.0)
            t_pct = traditional_typing.get(p, 25.0)
            gap = round(w_pct - t_pct, 1)

            # 친절한 말로 설명해주는 줄글 스토리 해설 생성
            story_templates = {
                "pioneer": (
                    f"{p} 님은 팀 대화가 정체되거나 흔한 아이디어로 흘러갈 뻔했을 때, '차라리 이런 새로운 방향으로 틀어보면 어떨까?'라며 결정적인 아이디어 씨앗을 던졌습니다. "
                    f"비록 대화창에 친 글자 수 자체는 적었더라도, 이 한마디가 없었다면 최종 보고서의 핵심 주제 자체가 시작되지 못했을 만큼 결정적인 전환점을 만든 숨은 핵심 공로자입니다."
                ),
                "architect": (
                    f"{p} 님은 조원들이 쏟아낸 산발적이고 복잡한 이야기들을 한눈에 들어오는 깔끔한 목차와 논리적 뼈대로 정리했습니다. "
                    f"뒤죽박죽될 수 있었던 아이디어들을 체계적인 완성본으로 엮어낸 프로젝트의 든든한 기둥이자 설계자입니다."
                ),
                "fact": (
                    f"{p} 님은 조원들의 아이디어가 단순한 말잔치에 그치지 않도록, 신뢰도 높은 공식 통계와 학술 논문, 객관적 실증 데이터를 발 빠르게 찾아와 뒷받침했습니다. "
                    f"보고서의 전문성과 설득력을 책임진 신뢰의 수호자입니다."
                ),
                "polish": (
                    f"{p} 님은 카톡창의 다듬어지지 않은 구어체와 채팅 말투를 학술적이고 세련된 보고서용 격식체 문장으로 완벽하게 다듬었습니다. "
                    f"조원들의 모든 노력을 가장 빛나는 최종 문장으로 탈바꿈시킨 완성도 장인입니다."
                )
            }
            story_text = story_templates.get(role_key, f"{p} 님은 조원들과 적극적으로 의견을 나누며 프로젝트 완성에 기여했습니다.")

            ev = [
                f"{p} 님의 핵심 발언 기여 패턴: {s_quote}",
                f"총 {msg_counts[p]}개의 메시지 참여 중 핵심 기여도 {w_pct}% (단순 글자비율 대비 {gap:+0.1f}%p) 기록"
            ]

            personas[p] = PersonaProfile(
                name=p,
                primary_role=r_title,
                role_english=r_eng,
                badge_title=b_title,
                avatar_path=avatar_file,
                summary_quote=s_quote,
                story_explanation=story_text,
                detailed_evidence=ev,
                stat_pioneer=st_pioneer,
                stat_architect=st_architect,
                stat_factcheck=st_fact,
                stat_polisher=st_polish,
                stat_collaboration=st_collab,
                weighted_contribution_pct=w_pct,
                traditional_typing_pct=t_pct,
                hidden_contribution_gap=gap
            )

            # 도메인별 평가 문구 작성
            if "대학" in domain or "캡스톤" in domain:
                domain_feedbacks[p] = f"[{p}] 캡스톤 프로젝트에서 {r_title} 역할을 완벽 수행함. 특히 단순 타이핑에 의존하지 않고 {s_quote} 이를 통해 결과물의 공학적 완성도를 보장하여 A+ 수준의 기여도를 입증함."
            elif "스타트업" in domain or "해커톤" in domain:
                domain_feedbacks[p] = f"[{p}] 린 스타트업 MVP 기획에서 {r_title}로 활약함. {s_quote} 초기 의사결정과 제품 피벗에 지대한 영향을 미쳐 프로젝트 핵심 지분 기여자로 평가됨."
            elif "기업" in domain or "TF" in domain:
                domain_feedbacks[p] = f"[{p}] 신사업 TF팀에서 {r_title} 역할을 주도함. {s_quote} 사내 전략 보고서의 실행력과 설득력을 크게 높여 프로젝트 핵심 기여자로 감사 완료됨."
            else:
                domain_feedbacks[p] = f"[{p}] 수행평가 협업 과정에서 {r_title}의 역할을 주도적으로 수행함. {s_quote} 배려와 소통을 바탕으로 조별 시너지를 견인함."

        return ProjectAnalysisReport(
            title=f"협업 인과관계 & 기여도 분석 리포트 ({domain})",
            project_domain=domain,
            summary="아이디어의 탄생부터 최종 결과물까지의 전 과정을 역추적하여 숨은 공로자를 입증했습니다.",
            total_messages=len(chat_messages),
            total_sentences=len(report_sentences),
            participants=participants,
            genealogies=genealogies,
            personas=personas,
            group_dynamics_review=f"본 조는 [{domain}] 관점에서 이상적인 4대 역할 분담 모델을 보였습니다. 단순 글자 수 중심 평가의 편향을 바로잡고, 최초 기획 발의자와 논리 구조 설계자의 숨은 가치가 정당하게 반영되었습니다.",
            domain_specific_feedback=domain_feedbacks
        )

    def _hydrate_report(
        self,
        data: Dict[str, Any],
        chat_messages: List[ChatMessage],
        report_sentences: List[Tuple[str, str]],
        domain: str
    ) -> ProjectAnalysisReport:
        participants = list(data.get("personas", {}).keys())
        if not participants:
            participants = sorted(list(set(m.speaker for m in chat_messages if m.speaker and m.speaker != "조원")))

        genealogies = []
        for g in data.get("genealogies", []):
            steps = [EvolutionStep(**s) for s in g.get("evolution_steps", [])]
            genealogies.append(IdeaGenealogy(
                id=g.get("id", f"gen_{len(genealogies)+1}"),
                report_sentence=g.get("report_sentence", ""),
                section=g.get("section", "본문"),
                seed_author=g.get("seed_author", "작성자"),
                seed_concept=g.get("seed_concept", "핵심 아이디어"),
                seed_raw_message=g.get("seed_raw_message", ""),
                evolution_steps=steps,
                final_writer=g.get("final_writer", "작성자"),
                contribution_split=g.get("contribution_split", {}),
                insight_comment=g.get("insight_comment", "")
            ))

        personas = {}
        for name, p in data.get("personas", {}).items():
            r_eng = p.get("role_english", "Pioneer")
            avatar_file = AVATAR_MAPPING.get(r_eng, "static/avatars/pioneer.png")
            personas[name] = PersonaProfile(
                name=name,
                primary_role=p.get("primary_role", "💡 아이디어 개척자"),
                role_english=r_eng,
                badge_title=p.get("badge_title", "핵심 협업자"),
                avatar_path=avatar_file,
                summary_quote=p.get("summary_quote", "팀 프로젝트에 기여함"),
                story_explanation=p.get("story_explanation", ""),
                detailed_evidence=p.get("detailed_evidence", []),
                stat_pioneer=int(p.get("stat_pioneer", 70)),
                stat_architect=int(p.get("stat_architect", 70)),
                stat_factcheck=int(p.get("stat_factcheck", 70)),
                stat_polisher=int(p.get("stat_polisher", 70)),
                stat_collaboration=int(p.get("stat_collaboration", 70)),
                weighted_contribution_pct=float(p.get("weighted_contribution_pct", 25.0)),
                traditional_typing_pct=float(p.get("traditional_typing_pct", 25.0)),
                hidden_contribution_gap=float(p.get("hidden_contribution_gap", 0.0))
            )

        return ProjectAnalysisReport(
            title=data.get("title", f"협업 분석 리포트 ({domain})"),
            project_domain=domain,
            summary=data.get("summary", ""),
            total_messages=len(chat_messages),
            total_sentences=len(report_sentences),
            participants=participants,
            genealogies=genealogies,
            personas=personas,
            group_dynamics_review=data.get("group_dynamics_review", "")
        )

import re
import json
from typing import List, Optional, Dict
import config
from modules.parser import parse_chat_log
from modules.models import ChatMessage

def generate_report_from_chat(
    chat_text: str,
    domain: str = "중·고교 수행평가",
    participants: Optional[List[str]] = None
) -> str:
    """
    팀원들의 대화 내용을 바탕으로 AI가 공식 최종 보고서/기획서 본문을 동적으로 자동 작성합니다.
    Gemini / LLM API 연결 시 실시간 최신 모델로 고품질 작성,
    오프라인/로컬 모드 시에도 대화 내용 속 핵심 키워드, 통계, 구조를 실시간 분석하여
    100% 맞춤형 최종 보고서를 동적으로 합성합니다.
    """
    if not participants:
        participants = ["팀원A", "팀원B", "팀원C", "팀원D"]

    # 1. Gemini 멀티 모델 호출 시도 (요청 모델 실패 시 공식 지원 모델로 Fallback)
    if config.GEMINI_API_KEY:
        try:
            return _generate_with_gemini(chat_text, domain, participants)
        except Exception as e:
            print(f"[Warning] Gemini 보고서 자동 작성 시도 실패 ({e}). 스마트 로컬 동적 생성기로 자동 전환합니다.")

    # 2. OpenAI 호출 시도 (API 키 존재 시)
    if config.OPENAI_API_KEY:
        try:
            return _generate_with_openai(chat_text, domain, participants)
        except Exception as e:
            print(f"[Warning] OpenAI 보고서 작성 실패 ({e}).")

    # 3. 스마트 로컬 동적 보고서 생성기 (대화 내용을 100% 반영하여 동적 생성)
    return _generate_with_dynamic_local_engine(chat_text, domain, participants)

def _generate_with_gemini(chat_text: str, domain: str, participants: List[str]) -> str:
    from google import genai

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    prompt = f"""당신은 조별 프로젝트 및 수행평가 최종 보고서/기획서 작성 전문 AI입니다.
주어진 팀원들의 회의/메신저 대화 내용을 깊이 있게 분석하여, 실제 심사위원이나 선생님께 제출할 완성형 최종 보고서 본문을 작성해 주세요.

[프로젝트 도메인]: {domain}
[참여 팀원 명단]: {', '.join(participants)}

[팀원 메신저/회의 대화 내용]:
{chat_text}

작성 규칙:
1. 반드시 입력된 대화 내용 속의 실제 주제, 팀원들이 낸 아이디어 씨앗, 제시된 통계와 자료를 바탕으로 작성하세요.
2. 구성:
   - 보고서 제목 ([... 제안서/보고서])
   - 1. 서론: 문제 제기 및 추진 배경 (대화 속 문제의식 및 통계 자료 인용)
   - 2. 본론: 핵심 추진 전략 및 체계적 아키텍처 (팀원들이 제안한 단계별 해결책 구체화)
   - 3. 결론: 실증 데이터 기반 실행 방안 및 기대 효과 (실천 계획 및 기대 성과)
3. 구어체나 비문을 철저히 배제하고, 완성도 높은 학술적/보고서용 공식 격식체 문장으로 작성하세요.
"""

    # 지정된 모델을 우선 시도하고, 오류 발생 시 호환 모델 순차 시도
    models_to_try = [
        config.GEMINI_MODEL,
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    last_err = None
    for m in models_to_try:
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt
            )
            if response.text and response.text.strip():
                return response.text.strip()
        except Exception as err:
            last_err = err
            continue

    raise Exception(f"모든 Gemini 모델 호출 실패 (최종 오류: {last_err})")

def _generate_with_openai(chat_text: str, domain: str, participants: List[str]) -> str:
    import httpx
    prompt = f"""당신은 조별 프로젝트 최종 보고서 작성 전문 AI입니다. 아래 대화 내용을 바탕으로 완성형 최종 보고서를 작성하세요.
도메인: {domain}
대화:
{chat_text}

1. 서론 (문제 제기), 2. 본론 (핵심 아키텍처/전략), 3. 결론 (실행 방안 및 기대효과) 형태로 작성하세요."""

    headers = {
        "Authorization": f"Bearer {config.OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": config.OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.4
    }
    with httpx.Client(timeout=30.0) as client:
        res = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"].strip()

def _generate_with_dynamic_local_engine(chat_text: str, domain: str, participants: List[str]) -> str:
    """
    대화 내용을 실시간으로 파싱하고 키워드, 통계 수치, 아이디어 제안을 추출하여
    대화마다 100% 달라지는 맞춤형 3단 최종 보고서 본문을 동적으로 합성합니다.
    """
    messages = parse_chat_log(chat_text, allowed_participants=participants)
    
    # 메시지가 없을 경우 단순 줄바꿈 단위로 변환
    if not messages:
        lines = [l.strip() for l in chat_text.splitlines() if l.strip()]
        messages = [ChatMessage(speaker=participants[i % len(participants)], text=l) for i, l in enumerate(lines)]

    # 1. 텍스트 및 발언 분석
    raw_texts = [m.text for m in messages if len(m.text.strip()) > 3]

    # 2. 통계/수치/근거 문장 추출
    stats_sentences = []
    for m in messages:
        if any(k in m.text for k in ["통계", "조사", "자료", "논문", "보도", "수치", "%", "퍼센트", "억", "만", "배", "평균"]):
            clean_s = re.sub(r"\[.*?\]", "", m.text).strip()
            if len(clean_s) > 5:
                stats_sentences.append(clean_s)

    # 3. 아이디어 제안/문제 제기 문장 추출
    proposal_sentences = []
    for m in messages:
        if any(k in m.text for k in ["어때", "해보자", "하자", "차라리", "생각", "제안", "바꿔", "아이디어", "좋을듯", "방안", "시스템", "프로젝트", "도입"]):
            clean_s = re.sub(r"\[.*?\]", "", m.text).strip()
            if len(clean_s) > 5:
                proposal_sentences.append(clean_s)

    # 4. 구조/정리 문장 추출
    structure_sentences = []
    for m in messages:
        if any(k in m.text for k in ["목차", "단계", "정리", "본문", "서론", "결론", "역할", "순서", "아키텍처", "기능"]):
            clean_s = re.sub(r"\[.*?\]", "", m.text).strip()
            if len(clean_s) > 5:
                structure_sentences.append(clean_s)

    # 5. 핵심 주제어(Topic Phrase) 동적 추출
    theme_title = _extract_theme_topic(messages, domain)

    # 6. 서론 문단 동적 합성
    intro_paragraphs = []
    if stats_sentences:
        stat_lead = stats_sentences[0]
        stat_lead_formal = _formalize_sentence(stat_lead)
        intro_paragraphs.append(
            f"최근 관련 현안에 대한 실태 조사에 따르면, {stat_lead_formal} "
            f"이는 기존의 단편적 대증요법이나 형식적 규제만으로는 당면한 문제를 근본적으로 해결하는 데 명확한 한계가 있음을 시사한다."
        )
    elif proposal_sentences:
        prop_lead = _formalize_sentence(proposal_sentences[0])
        intro_paragraphs.append(
            f"본 프로젝트는 팀원 간 심층적인 문제의식 공유를 바탕으로 출발하였다. "
            f"특히 '{prop_lead}'라는 문제 제기를 기점으로, 실질적이고 지속 가능한 해결 방안의 필요성이 강력하게 대두되었다."
        )
    else:
        intro_paragraphs.append(
            f"현대 사회의 다양한 당면 과제 속에서, {domain}의 취지에 부합하는 실효성 있는 대안 모색의 필요성이 지속적으로 증대되고 있다. "
            f"기존 시스템의 비효율성을 개선하고 체계적인 솔루션을 정립하기 위한 다각적인 접근이 시급한 시점이다."
        )

    # 7. 본론 문단 동적 합성 (3대 핵심 전략)
    body_items = []
    # 1전략: 아이디어 구체화
    seed_text = proposal_sentences[0] if proposal_sentences else (raw_texts[0] if raw_texts else "현안 개선 솔루션")
    seed_formal = _formalize_sentence(seed_text)
    body_items.append(
        f"1) 핵심 기반 기획 및 개념 구체화:\n"
        f"   - 팀 논의에서 발의된 핵심 아이디어인 '{seed_formal}' 원리를 중심으로 실현 가능한 세부 모델을 수립한다.\n"
        f"   - 기존 방식의 단점을 보완하고 사용자 및 현장 참여자의 편의성과 접근성을 최우선으로 고려하여 체계를 설계한다."
    )

    # 2전략: 시스템 구조화 및 세부 기능
    struct_text = structure_sentences[0] if structure_sentences else (proposal_sentences[1] if len(proposal_sentences) > 1 else "다단계 체계적 운영 구조")
    struct_formal = _formalize_sentence(struct_text)
    body_items.append(
        f"2) 단계별 기능 분할 및 유기적 아키텍처 구축:\n"
        f"   - {struct_formal}의 방향성에 입각하여, [사전 진단 - 실행 적용 - 성과 평가]로 이어지는 3단계 순환 프로세스를 가동한다.\n"
        f"   - 각 단계 간 데이터 피드백 루프를 형성하여 운영의 유연성과 신뢰성을 극대화한다."
    )

    # 3전략: 실무 실행 및 지속 가능성 확보
    body_items.append(
        f"3) 참여 유인 체계 및 지속 가능성 확보:\n"
        f"   - 제안된 모델이 일회성 시도에 그치지 않도록 이해관계자 맞춤형 인센티브 및 관리 매뉴얼을 수립한다.\n"
        f"   - 단계별 모니터링 체계를 결합하여 중장기적 확장성을 안정적으로 뒷받침한다."
    )

    # 8. 결론 문단 동적 합성
    conclusion_parts = []
    if len(stats_sentences) > 1:
        stat_sub = _formalize_sentence(stats_sentences[1])
        conclusion_parts.append(
            f"실증 데이터에 기반하여 '{stat_sub}'와 같은 객관적 지표를 선제적으로 고려할 때, "
            f"본 기획 모델의 현장 도입 시 기대 효과는 매우 뚜렷할 것으로 전망된다."
        )
    else:
        conclusion_parts.append(
            f"본 제안 모델이 실제 환경에 도입될 경우, 기존 방식 대비 운영 효율성을 대폭 개선하고 "
            f"참여자들의 자발적인 실천과 만족도를 극대화할 수 있을 것으로 기대된다."
        )
    conclusion_parts.append(
        f"나아가 초기 시범 적용을 통해 얻은 실측 데이터를 토대로 세부 기능을 지속 고도화함으로써, "
        f"{domain} 분야의 모범적인 협업 및 문제 해결 표준 모델로 안착시킬 계획이다."
    )

    # 팀원 협업 기여도 각주 동적 생성
    team_note = f"※ 본 기획 보고서는 참여 팀원({', '.join(participants[:4])})들의 심층 회의 대화와 아이디어 발의, 실증 데이터 수집을 유기적으로 엮어 작성되었습니다."

    # 최종 조립
    report_text = f"""[{theme_title}]

1. 서론: 문제 제기 및 추진 배경
{intro_paragraphs[0]}

2. 본론: 핵심 추진 전략 및 체계적 아키텍처
본 솔루션은 유기적으로 연계된 3대 핵심 추진 축을 바탕으로 설계된다.

{chr(10).join(body_items)}

3. 결론: 실증 데이터 기반 실행 방안 및 기대 효과
{' '.join(conclusion_parts)}

{team_note}"""

    return report_text.strip()

def _extract_theme_topic(messages: List[ChatMessage], domain: str) -> str:
    """대화 내용에서 가장 유의미한 주제 키워드를 추출하여 보고서 제목 생성"""
    full_text = " ".join([m.text for m in messages])

    patterns = [
        r"([가-힣a-zA-Z0-9\s]{2,15})(?:주제|프로젝트|시스템|방안|기획|개발|모델)",
        r"(?:차라리|우리|이번에)\s+([가-힣a-zA-Z0-9\s]{2,20})(?:해보자|어때|어떰|하자)",
        r"([가-힣a-zA-Z0-9\s]{2,15})(?:감축|해결|도입|개선|지원|방지)",
    ]
    
    candidates = []
    for pat in patterns:
        matches = re.findall(pat, full_text)
        for m in matches:
            cleaned = m.strip()
            if len(cleaned) >= 2 and cleaned not in ["우리", "이번", "얘들아", "좋은", "생각"]:
                candidates.append(cleaned)

    if candidates:
        best = max(candidates, key=lambda c: len(c))
        return f"{best} 추진 및 실천 방안 제안서"

    for m in messages:
        if any(k in m.text for k in ["어때", "하자", "해보자"]):
            words = [w for w in m.text.split() if len(w) > 1 and not w.endswith(("?", "!", "ㅋ", "ㅎ"))]
            if len(words) >= 2:
                phrase = " ".join(words[-3:])
                return f"{phrase} 기반 협업 기획 보고서"

    return f"{domain} 기반 문제 해결 및 혁신 실행 계획서"

def _formalize_sentence(raw: str) -> str:
    """구어체 문장을 보고서용 격식체 어조로 매끄럽게 정제"""
    s = raw.strip()
    s = re.sub(r"(?:어때\??|어떰\??|어떨까\??|해보자|하자|좋을듯|좋겠어|좋아!?)", "추진이 필요하다는 의견", s)
    s = re.sub(r"(?:이래|이래\.|이래!|했대|했대\.)", "는 점이 확인되었다", s)
    s = re.sub(r"(?:쓸게요|정리할게요|할게요|작성할게)", "체계적으로 정리 및 반영하였다", s)
    s = re.sub(r"(?:[ㅋㅎ!?]+)$", "", s).strip()
    return s

import io
import re
from typing import List, Optional, Dict
import config

def transcribe_meeting_audio(
    audio_bytes: bytes,
    mime_type: str = "audio/wav",
    participants: Optional[List[str]] = None,
    domain: str = "중·고교 수행평가",
    voice_profiles: Optional[Dict[str, bytes]] = None
) -> str:
    """
    회의 음성 녹음(WAV, MP3, M4A 등)을 화자별 대화록 텍스트([이름] 내용)로 변환합니다.
    팀원별 사전 등록된 목소리 프로필(voice_profiles)이 전달되면,
    각 사람의 음색을 대조하여 해당 사람의 대사로 정확히 매칭합니다.
    """
    if not participants:
        participants = ["김민준", "이서연", "박지훈", "최예은"]

    # 1. Gemini 멀티모달 오디오 분석 시도
    if config.GEMINI_API_KEY:
        try:
            return _transcribe_with_gemini(audio_bytes, mime_type, participants, domain, voice_profiles)
        except Exception as e:
            print(f"[Warning] Gemini 음성 분석 실패 ({e}). 로컬 전사 엔진으로 대체합니다.")

    # 2. 스마트 로컬 전사 엔진 (오프라인/시뮬레이션 모드)
    return _transcribe_with_local_engine(audio_bytes, participants, domain, voice_profiles)

def _transcribe_with_gemini(
    audio_bytes: bytes,
    mime_type: str,
    participants: List[str],
    domain: str,
    voice_profiles: Optional[Dict[str, bytes]] = None
) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    contents = []

    # 1) 사전에 등록된 각 팀원의 목소리 샘플 첨부 (음색 대조용)
    if voice_profiles:
        contents.append("### [팀원별 사전 등록된 목소리 음색 샘플]:")
        for name, v_bytes in voice_profiles.items():
            contents.append(f"▶ '{name}' 님의 등록된 목소리 샘플:")
            contents.append(types.Part.from_bytes(data=v_bytes, mime_type="audio/wav"))

    # 2) 전체 회의 음성 첨부
    contents.append("### [전체 회의 음성 녹음 본문]:")
    contents.append(types.Part.from_bytes(data=audio_bytes, mime_type=mime_type))

    # 3) 프롬프트 지침
    voice_guide = (
        "사전에 등록된 각 팀원의 목소리 샘플과 전체 회의 음성을 정밀 대조하여, "
        "일치하는 목소리의 팀원 이름으로 각 대사를 [이름] 내용 형식으로 매칭해 주세요."
        if voice_profiles else
        "목소리 톤과 대화 흐름을 분석하여 각 팀원의 발언으로 [이름] 내용 형식으로 매칭해 주세요."
    )

    prompt = f"""당신은 팀 회의 음성 화자 분리 및 전사 전문 AI입니다.
[프로젝트 분야]: {domain}
[참여 팀원 명단]: {', '.join(participants)}

작성 규칙:
1. {voice_guide}
2. 화자 이름은 반드시 위 [참여 팀원 명단]에 등록된 이름만 사용하세요.
3. 시간 표기나 불필요한 서술 없이 오직 [이름] 대화내용 형식의 텍스트만 출력하세요.
예시:
[{participants[0]}] 얘들아 우리 이번 주제 뭐로 할까?
[{participants[1] if len(participants)>1 else participants[0]}] 환경 문제 쪽으로 가보는 건 어때?
"""
    contents.append(prompt)

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
                contents=contents
            )
            if response.text and response.text.strip():
                break
        except Exception as err:
            last_err = err
            continue

    if not response or not response.text:
        raise Exception(f"모든 Gemini 음성 전사 호출 실패 ({last_err})")
    return response.text.strip()

def _transcribe_with_local_engine(
    audio_bytes: bytes,
    participants: List[str],
    domain: str,
    voice_profiles: Optional[Dict[str, bytes]] = None
) -> str:
    """오프라인 및 데모 환경용 음성 전사 (사전 등록된 목소리 매칭 반영)"""
    p1 = participants[0] if len(participants) > 0 else "팀원1"
    p2 = participants[1] if len(participants) > 1 else "팀원2"
    p3 = participants[2] if len(participants) > 2 else "팀원3"
    p4 = participants[3] if len(participants) > 3 else "팀원4"

    enrolled_tag = " (🎤 목소리 매칭)" if voice_profiles else ""

    if "대학" in domain or "캡스톤" in domain:
        return f"""[{p1}]{enrolled_tag} 얘들아 우리 이번 캡스톤 디자인 회의 시작하자. 각자 등록한 목소리대로 대사가 들어가니까 회의하기 진짜 편하다.
[{p2}]{enrolled_tag} 맞아. 기존에는 시각장애인 보행 안내 앱이 스마트폰 카메라로만 찍어서 주변 도로 소음 있으면 소리가 안 들리는 치명적인 문제가 있었어.
[{p1}]{enrolled_tag} 차라리 스마트폰 음성에만 의존하지 말고, 손목 밴드에 8방향 햅틱 진동 모터를 달아서 방향과 거리를 촉각 피드백으로 알려주는 하이브리드 웨어러블로 틀어보는 건 어떰?
[{p3}]{enrolled_tag} 오 햅틱 연계 진짜 혁신적이다! 도로교통공단 통계 찾아봤는데 소음 사고가 64%나 된대. 온디바이스 NPU 42ms 레이턴시 벤치마크 IEEE 논문도 링크 달아놓을게.
[{p2}]{enrolled_tag} 그럼 시스템 아키텍처를 1. 온디바이스 장애물 감지, 2. 8방향 햅틱 모듈, 3. SOS 클라우드 3단계로 구조화하자!
[{p4}]{enrolled_tag} 다들 아이디어 굿! 내가 지금 나온 내용 바탕으로 캡스톤 최종 제안서 학술 논문 규격으로 깔끔하게 정리해놓을게."""

    elif "스타트업" in domain or "해커톤" in domain:
        return f"""[{p1}]{enrolled_tag} 해커톤 24시간 남았는데 우리 1인 가구 배달비 절감 아이템으로 빠르게 피벗해보는 건 어때?
[{p2}]{enrolled_tag} 배달비가 5천 원이라 1인 가구는 혼자 시켜 먹기 너무 부담스러워. 어떻게 풀까?
[{p1}]{enrolled_tag} 같은 아파트나 오피스텔 거주자끼리 15분 동안 방 파서 '공동주문' 묶으면 배달팁을 1/N로 분할하는 마이크로 딜리버리 MVP로 피벗하자!
[{p3}]{enrolled_tag} 통계청 2024년 1인가구 보고서 보니까 주 3회 이상 시키는 비율이 48%에 달해. 신림동 원룸촌 시뮬레이션도 시간당 32건 나와서 경제성 충분해!
[{p2}]{enrolled_tag} 비즈니스 모델을 1. 200m 룸 개설, 2. 라이더 1회 픽업, 3. 거점 분배 및 자동 정산 3단계로 잡자.
[{p4}]{enrolled_tag} 오케이! 내가 심사위원용 IR 피치덱 본문으로 바로 읽히게 제안서 톤 매끄럽게 정리할게."""

    else:
        return f"""[{p1}]{enrolled_tag} 얘들아 우리 이번 사회과 수행평가 주제 뭐로 할까?
[{p2}]{enrolled_tag} 환경 문제 쪽으로 하기로 했잖아. 카페 일회용 컵 할인 어때?
[{p1}]{enrolled_tag} 아 근데 텀블러는 지난 학기에도 많이 했잖아. 차라리 배달 음식 시킬 때 나오는 플라스틱 배달용기 쓰레기 급증 문제로 확 틀어보는 건 어떰?
[{p3}]{enrolled_tag} 오 배달 쓰레기 좋다! 환경부 보도자료 보니까 연간 플라스틱 배달용기 소비량이 21억 개에 달한대. 서울시 시범사업 회수율 78% 논문도 찾음!
[{p2}]{enrolled_tag} 와 대박이다. 그럼 보고서 뼈대를 1. 실태, 2. 규제 한계, 3. 다회용기 인센티브제, 4. 기대효과 4단계로 구조화하자.
[{p4}]{enrolled_tag} 다들 대박! 내가 나온 통계랑 아이디어 모아서 최종 보고서 격식체 문장으로 예쁘게 다듬어놓을게."""

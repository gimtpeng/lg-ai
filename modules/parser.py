import re
from typing import List, Tuple, Optional
from modules.models import ChatMessage

# 시스템/비인간 제외 키워드 블랙리스트
SYSTEM_KEYWORDS = {
    "안내", "시스템", "공지", "알림", "채팅방", "카카오톡", "오전", "오후",
    "사진", "동영상", "음성메시지", "이모티콘", "파일", "초대", "퇴장", "삭제된",
    "관리자", "조원", "bot", "notice", "system"
}

def parse_chat_log(raw_text: str, allowed_participants: Optional[List[str]] = None) -> List[ChatMessage]:
    """
    메신저 대화 로그(.txt)를 파싱하여 ChatMessage 리스트로 변환합니다.
    allowed_participants가 주어지면 오직 해당 명단에 있는 실제 사람의 발화만 인식합니다.
    """
    messages: List[ChatMessage] = []
    lines = raw_text.strip().splitlines()

    # 허용 명단 정규화 (앞뒤 공백 제거)
    valid_names = [p.strip() for p in allowed_participants if p.strip()] if allowed_participants else []

    # 정규식 패턴들
    pat_kakao_pc = re.compile(r"^\[([^\]]+)\]\s+\[([^\]]+)\]\s+(.*)$")
    pat_kakao_mo = re.compile(r"^(\d{4}[^\d]+\d{1,2}[^\d]+\d{1,2}[^\d]+[오전|오후].*?),\s*([^:]+)\s*:\s*(.*)$")
    pat_simple = re.compile(r"^([^:]{2,15})\s*:\s*(.*)$")

    current_msg = None

    for idx, line in enumerate(lines, 1):
        line_clean = line.strip()
        if not line_clean:
            continue

        # 구분선이나 안내문 건너뛰기
        if line_clean.startswith("---------------") or line_clean.startswith("================="):
            continue

        speaker = None
        timestamp = ""
        text = ""

        # 패턴 1 검사: [이름] [시간] 내용
        m1 = pat_kakao_pc.match(line_clean)
        if m1:
            candidate = m1.group(1).strip()
            # 시간 문자열이 이름 위치에 잘못 들어간 경우 필터링
            if not any(k in candidate for k in ["오전", "오후", ":", "년", "월"]):
                speaker = candidate
                timestamp = m1.group(2).strip()
                text = m1.group(3).strip()

        # 패턴 2 검사: 카카오톡 모바일
        if not speaker:
            m2 = pat_kakao_mo.match(line_clean)
            if m2:
                speaker = m2.group(2).strip()
                timestamp = m2.group(1).strip()
                text = m2.group(3).strip()

        # 패턴 3 검사: 이름 : 내용
        if not speaker:
            m3 = pat_simple.match(line_clean)
            if m3:
                candidate = m3.group(1).strip()
                # 불필요한 시스템 접두사 배제
                if not any(k in candidate.lower() for k in SYSTEM_KEYWORDS):
                    speaker = candidate
                    timestamp = ""
                    text = m3.group(2).strip()

        # 허용된 팀원 명단(allowed_participants)이 지정된 경우 엄격 검증
        if valid_names:
            matched_name = None
            if speaker:
                for vn in valid_names:
                    if vn == speaker or vn in speaker:
                        matched_name = vn
                        break

            # 패턴에 안 걸렸더라도 줄 처음에 '민준: 내용' 등으로 시작하는지 직접 검사
            if not matched_name:
                for vn in valid_names:
                    if line_clean.startswith(f"[{vn}]") or line_clean.startswith(f"{vn}:") or line_clean.startswith(f"{vn} :"):
                        matched_name = vn
                        text = re.sub(rf"^(\[{vn}\]|{vn}\s*:)\s*", "", line_clean)
                        break

            if matched_name:
                current_msg = ChatMessage(
                    speaker=matched_name,
                    timestamp=timestamp,
                    text=text,
                    line_number=idx
                )
                messages.append(current_msg)
                continue
            else:
                # 명단 외의 발화(시스템 메시지나 이전 메시지의 줄바꿈 연속 내용)
                if current_msg is not None:
                    current_msg.text += f"\n{line_clean}"
                continue

        # 명단이 주어지지 않은 경우 기본 필터링 (블랙리스트 제외)
        if speaker and not any(k in speaker.lower() for k in SYSTEM_KEYWORDS):
            current_msg = ChatMessage(
                speaker=speaker,
                timestamp=timestamp,
                text=text,
                line_number=idx
            )
            messages.append(current_msg)
            continue

        if current_msg is not None:
            current_msg.text += f"\n{line_clean}"

    return messages

def parse_report_text(raw_text: str) -> List[Tuple[str, str]]:
    """
    보고서 텍스트를 섹션명과 문장 단위 리스트 [(섹션, 문장), ...]로 분리합니다.
    """
    results: List[Tuple[str, str]] = []
    lines = raw_text.strip().splitlines()
    current_section = "본문"

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        if (
            re.match(r"^(\d+[\.\)]|\[|#|\*|\b서론\b|\b본론\b|\b결론\b)", line_clean)
            and len(line_clean) < 50
            and not line_clean.endswith(".")
        ):
            current_section = line_clean
            continue

        sentences = re.split(r"(?<=[.!?])\s+(?=[가-힣A-Z0-9])", line_clean)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 8:
                results.append((current_section, s_clean))

    return results

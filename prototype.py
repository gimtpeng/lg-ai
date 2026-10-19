# ==============================================================
# 💡 Idea-Tracer AI - 기본 문법 프로토타입
# --------------------------------------------------------------
# 외부 라이브러리 / AI API 없이 파이썬 기본 문법만으로
# "글자 수 평가" vs "역할 기반 기여도 평가" 를 비교해 보는 버전
#
# 사용하는 기본 문법: 변수, 문자열, 리스트, 딕셔너리,
#                    for / if, 함수(def), 파일 읽기(open)
#
# 실행 방법:  python prototype.py
# ==============================================================


# --------------------------------------------------------------
# 1. 샘플 대화 데이터 (파일이 없을 때 사용)
# --------------------------------------------------------------
SAMPLE_CHAT = """[김민준] [오후 2:10] 얘들아 우리 이번 사회과 수행평가 주제 뭐로 할까?
[이서연] [오후 2:11] 환경 문제 쪽으로 하기로 했잖아. 카페 일회용 컵이나 텀블러 할인 어때?
[김민준] [오후 2:13] 아 근데 카페 텀블러는 지난 학기에도 다른 조가 많이 했잖아. 차라리 배달 용기 쓰레기 문제로 확 틀어보는 건 어떰?
[박지훈] [오후 2:15] 오 배달 쓰레기 좋다! 통계 찾아볼게.
[박지훈] [오후 2:18] 환경부 2023년 보도자료 찾았음! 연간 배달용기 약 21억 개래 링크: https://me.go.kr/news/202305
[이서연] [오후 2:20] 그럼 보고서 뼈대를 이렇게 4단계로 잡자: 1. 실태 2. 한계 3. 인센티브 방안 4. 기대효과
[김민준] [오후 2:22] 다회용기 쓸 때 그린포인트로 캐시백 주는 인센티브 아이디어 어때?
[박지훈] [오후 2:24] 시범사업 논문 보니까 회수율이 78%래. 링크: https://kci.go.kr/article/view?id=20230911
[최예은] [오후 2:45] 지훈이 통계랑 민준이 주제 합쳐서 첫 문장을 격식체로 다듬어서 작성했어.
[최예은] [오후 2:50] 서연이 목차 바탕으로 제언 파트 문장 매끄럽게 정리했어! 확인해줘!"""


# --------------------------------------------------------------
# 2. 역할별 감지 키워드 (AI 대신 키워드 규칙 사용)
# --------------------------------------------------------------
# ※ 위에서부터 순서대로 검사하고, 메시지 하나에는 역할 하나만 붙인다.
#   (예: "지훈이 통계로 문장 다듬었어" → 팩트체커가 아니라 문장 연마사)
ROLE_KEYWORDS = {
    "✍️ 문장 연마사": ["다듬", "격식", "매끄럽게 정리", "작성했"],
    "📐 구조 설계자": ["목차", "뼈대", "개요", "잡자"],
    "🔍 팩트체커": ["통계", "논문", "출처", "링크", "http"],
    "💡 아이디어 개척자": ["차라리", "어때", "어떰", "바꾸자", "틀어", "듯"],
}

# 역할별 가중치 (아이디어를 처음 낸 사람에게 더 높은 점수)
ROLE_WEIGHTS = {
    "💡 아이디어 개척자": 3,
    "📐 구조 설계자": 2,
    "🔍 팩트체커": 2,
    "✍️ 문장 연마사": 1,
}


# --------------------------------------------------------------
# 3. 함수 정의
# --------------------------------------------------------------
def load_chat(path):
    """대화 파일을 읽어서 문자열로 돌려준다. 실패하면 샘플 사용."""
    try:
        f = open(path, "r", encoding="utf-8")
        text = f.read()
        f.close()
        print("📂 파일을 불러왔습니다:", path)
        return text
    except FileNotFoundError:
        print("📂 파일이 없어 내장 샘플 대화를 사용합니다.")
        return SAMPLE_CHAT


def parse_chat(text):
    """'[이름] [시간] 내용' 형식을 (이름, 내용) 리스트로 바꾼다."""
    messages = []
    for line in text.split("\n"):
        line = line.strip()
        if line == "":
            continue

        if line.startswith("["):
            name_end = line.find("]")
            name = line[1:name_end]

            rest = line[name_end + 1:].strip()
            if rest.startswith("["):              # 시간 부분 건너뛰기
                rest = rest[rest.find("]") + 1:].strip()

            messages.append({"name": name, "text": rest})
        elif len(messages) > 0:
            # 줄바꿈으로 이어진 메시지는 앞 메시지에 붙인다
            messages[-1]["text"] += " " + line
    return messages


def detect_role(message_text):
    """메시지 하나에서 가장 먼저 감지된 역할을 돌려준다. 없으면 None."""
    for role in ROLE_KEYWORDS:
        for keyword in ROLE_KEYWORDS[role]:
            if keyword in message_text:
                return role
    return None


def analyze(messages):
    """팀원별 글자 수, 역할 횟수, 가중 점수를 계산한다."""
    result = {}
    seeds = []                                     # 아이디어 씨앗 기록

    for msg in messages:
        name = msg["name"]
        text = msg["text"]

        if name not in result:
            result[name] = {"chars": 0, "score": 0, "roles": {}}

        result[name]["chars"] += len(text)

        role = detect_role(text)
        if role is None:
            continue

        result[name]["roles"][role] = result[name]["roles"].get(role, 0) + 1
        result[name]["score"] += ROLE_WEIGHTS[role]

        if role == "💡 아이디어 개척자":
            seeds.append((name, text))

    return result, seeds


def to_percent(values):
    """{이름: 값} 딕셔너리를 {이름: 비율%} 로 바꾼다."""
    total = 0
    for name in values:
        total += values[name]

    percents = {}
    for name in values:
        if total == 0:
            percents[name] = 0
        else:
            percents[name] = round(values[name] / total * 100, 1)
    return percents


def make_bar(percent):
    """퍼센트를 ■ 막대 그래프 문자열로 바꾼다."""
    count = int(percent / 5)
    return "■" * count + "□" * (20 - count)


def main_role(roles):
    """가장 많이 감지된 역할을 대표 캐릭터로 고른다."""
    best_role = "🙂 조용한 참여자"
    best_count = 0
    for role in roles:
        if roles[role] > best_count:
            best_role = role
            best_count = roles[role]
    return best_role


# --------------------------------------------------------------
# 4. 결과 출력
# --------------------------------------------------------------
def print_report(result, seeds):
    char_values = {}
    score_values = {}
    for name in result:
        char_values[name] = result[name]["chars"]
        score_values[name] = result[name]["score"]

    char_pct = to_percent(char_values)
    score_pct = to_percent(score_values)

    print()
    print("=" * 60)
    print("   💡 Idea-Tracer AI 프로토타입 분석 결과")
    print("=" * 60)

    # (1) 아이디어 씨앗
    print("\n🌱 [아이디어 씨앗 발견]")
    number = 1
    for seed in seeds:
        short = seed[1][:40] + ("..." if len(seed[1]) > 40 else "")
        print(f"  {number}. {seed[0]}: \"{short}\"")
        number += 1

    # (2) 캐릭터 카드
    print("\n🎭 [협업 캐릭터 카드]")
    for name in result:
        roles = result[name]["roles"]
        print(f"\n  👤 {name}  →  {main_role(roles)}")
        for role in roles:
            print(f"      - {role}: {roles[role]}회")

    # (3) 기존 방식 vs Idea-Tracer 방식
    print("\n📊 [기여도 비교: 글자 수 방식 vs Idea-Tracer 방식]")
    for name in result:
        gap = round(score_pct[name] - char_pct[name], 1)
        sign = "+" if gap >= 0 else ""
        print(f"\n  {name}")
        print(f"    글자 수   {make_bar(char_pct[name])} {char_pct[name]}%")
        print(f"    역할 기반 {make_bar(score_pct[name])} {score_pct[name]}%  ({sign}{gap}%p)")

    # (4) 숨은 기여자
    hidden = ""
    biggest_gap = 0
    for name in result:
        gap = score_pct[name] - char_pct[name]
        if gap > biggest_gap:
            biggest_gap = gap
            hidden = name

    print("\n" + "=" * 60)
    if hidden != "":
        print(f"🏆 숨은 기여자: {hidden} (재평가 +{round(biggest_gap, 1)}%p)")
    print("=" * 60)


# --------------------------------------------------------------
# 5. 프로그램 시작
# --------------------------------------------------------------
if __name__ == "__main__":
    chat_text = load_chat("data/samples/sample_chat_eco.txt")
    messages = parse_chat(chat_text)
    result, seeds = analyze(messages)
    print_report(result, seeds)

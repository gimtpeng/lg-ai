from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    speaker: str
    timestamp: str = ""
    text: str
    line_number: int = 0

class EvolutionStep(BaseModel):
    step_num: int
    actor: str
    role_type: str  # '💡 씨앗 발의', '📐 구조 설계', '🔍 팩트 검증', '✍️ 문장 윤문'
    detail: str
    source_message: str = ""

class IdeaGenealogy(BaseModel):
    id: str
    report_sentence: str
    section: str = ""
    seed_author: str
    seed_concept: str
    seed_raw_message: str
    evolution_steps: List[EvolutionStep] = Field(default_factory=list)
    final_writer: str
    contribution_split: Dict[str, float] = Field(default_factory=dict)
    insight_comment: str = ""

class PersonaProfile(BaseModel):
    name: str
    primary_role: str        # '💡 아이디어 개척자', '📐 구조 설계자', '🔍 팩트체커', '✍️ 문장 연마사'
    role_english: str       # 'Pioneer', 'Architect', 'Critic', 'Polisher'
    badge_title: str        # 예: '우리 조의 브레인', '설계 마스터', '팩트 저격수', '황금 손잡이'
    avatar_path: str = ""   # 아바타 이미지 경로 (예: static/avatars/pioneer.png)
    summary_quote: str      # 핵심 평가 리포트 문구
    story_explanation: str = "" # 친절한 줄글 스토리텔링 해설 (왜 이 역할인지, 어떤 기여를 했는지 말로 설명)
    detailed_evidence: List[str] = Field(default_factory=list) # AI 감지 근거
    # 능력치 지표 (0~100)
    stat_pioneer: int = 50
    stat_architect: int = 50
    stat_factcheck: int = 50
    stat_polisher: int = 50
    stat_collaboration: int = 50
    # 공정 기여도 지수
    weighted_contribution_pct: float = 0.0 # AI 인과관계 기반 기여도 (%)
    traditional_typing_pct: float = 0.0    # 기존 단순 타이핑/글자수 비율 (%)
    hidden_contribution_gap: float = 0.0   # 숨은 기여도 격차 (+ : 재평가된 인재, - : 숟가락/단순 타이핑)

class ProjectAnalysisReport(BaseModel):
    title: str = "수행평가 협업 분석 리포트"
    project_domain: str = "중·고교 수행평가"
    summary: str = ""
    total_messages: int = 0
    total_sentences: int = 0
    participants: List[str] = Field(default_factory=list)
    genealogies: List[IdeaGenealogy] = Field(default_factory=list)
    personas: Dict[str, PersonaProfile] = Field(default_factory=dict)
    group_dynamics_review: str = ""
    domain_specific_feedback: Dict[str, str] = Field(default_factory=dict)

from enum import StrEnum


class Priority(StrEnum):
    URGENT = "urgent"
    IMPORTANT = "important"
    NORMAL = "normal"
    LOW = "low"


class Intent(StrEnum):
    PERSONAL_URGENT = "personal_urgent"
    PERSONAL_CASUAL = "personal_casual"
    WORK = "work"
    DELIVERY_LOGISTICS = "delivery_logistics"
    APPOINTMENT = "appointment"
    SALES_MARKETING = "sales_marketing"
    SCAM_SUSPECTED = "scam_suspected"
    WRONG_NUMBER = "wrong_number"
    OTHER = "other"


class Action(StrEnum):
    CONTINUE = "continue"
    TAKE_MESSAGE = "take_message"
    ESCALATE = "escalate"
    END_CALL = "end_call"


class CallMode(StrEnum):
    AWAY = "away"
    SCREEN_UNKNOWN = "screen_unknown"


class Language(StrEnum):
    EN_IN = "en-IN"
    HI_IN = "hi-IN"
    TE_IN = "te-IN"
    AUTO = "auto"


class SessionEndReason(StrEnum):
    CALLER_HANGUP = "caller_hangup"
    AGENT_END = "agent_end"
    ERROR = "error"
    ESCALATED = "escalated"

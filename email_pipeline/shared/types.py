from typing import TypedDict, Optional

class AgentState(TypedDict):
    """
    Shared state definition used throughout the LangGraph pipeline.

    Attributes:
        record (dict): The full email record from the database, including fields like
                       id, subject, body, user_email, etc.
        category (Optional[str]): The email classification label (e.g., "refund", "shipping confirmation").
    """
    record: dict
    category: Optional[str]

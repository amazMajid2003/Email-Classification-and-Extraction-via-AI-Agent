from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from typing import Dict
from shared.types import AgentState
from prompts.templates import CLASSIFICATION_TEMPLATE

# --------------------------------------------------
# 🧠 Setup: Classification Chain using GPT-4o-mini
# --------------------------------------------------

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1)
parser = StrOutputParser()

classification_prompt = PromptTemplate.from_template(CLASSIFICATION_TEMPLATE)
classification_chain = classification_prompt | llm | parser


# --------------------------------------------------
# 🔎 Node: Email Classification
# --------------------------------------------------

def classify_node(state: AgentState) -> dict:
    """
    LangGraph node: Classify an incoming email based on its sender, subject, and body.

    This uses an OpenAI prompt to categorize the email into one of:
    promos, refund, return confirmation, order update, shipping update, etc.

    Args:
        state (AgentState): Current pipeline state containing full email record.

    Returns:
        dict: A dictionary with a single key: 'category', indicating the classification result.
    """
    email_record = state["record"]

    try:
        classification_input = {
            "from_field": email_record.get("from", ""),
            "subject": email_record.get("subject", ""),
            "body": email_record.get("msg", "")
        }

        category = classification_chain.invoke(classification_input).strip().lower()
        print(f"📂 Email classified as: {category}")
        return {"category": category}

    except Exception as e:
        print(f"❌ Classification error: {e}")
        return {"category": "unknown"}

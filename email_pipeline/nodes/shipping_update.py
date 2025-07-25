import json
import re
from LLM.extractor import query_openai
from prompts.templates import SHIPPING_UPDATE_PROMPT_TEMPLATE
from supabase_client import supabase
from shared.types import AgentState


def extract_shipping_update_node(state: AgentState) -> dict:
    """
    LangGraph node: Extract shipping progress update (delivered, delayed, etc.)
    from email and apply updates to `order_details` table in Supabase.

    Matching logic (in order):
    - Match by user_id + order_id + tracking_num
    - Fallback to user_id + tracking_num
    - Skip update if no match found
    """

    def clean_field(value):
        """Sanitize values: convert 'null' → None, strip whitespace, trim datetime to date only."""
        if isinstance(value, str):
            value = value.strip()
            if value.lower() == "null":
                return None
            if re.match(r"^\d{4}-\d{2}-\d{2}", value):
                return value[:10]
        return value

    email_record = state["record"]
    user_id = email_record.get("user_id")

    # Generate the prompt and get extracted data
    prompt = SHIPPING_UPDATE_PROMPT_TEMPLATE.format(
        subject=email_record.get("subject", ""),
        body=email_record.get("msg", "")
    )
    extracted = query_openai(prompt)
    if not extracted:
        return {}

    shipping_info = extracted.get("order_info", {}) or {}
    order_id = (shipping_info.get("order_id") or "").strip() or None
    tracking_number = (shipping_info.get("tracking_num") or "").strip() or None

    if not user_id or not tracking_number:
        print("❌ Skipping update — missing user_id or tracking number.")
        return {}

    matching_rows = []
    try:
        # Step 1: Best match — user_id + order_id + tracking_num
        if order_id:
            response = supabase.table("order_details").select("*") \
                .eq("user_id", user_id) \
                .eq("order_id", order_id) \
                .eq("tracking_num", tracking_number) \
                .execute()
            matching_rows = response.data or []

        # Step 2: Fallback match — user_id + tracking_num
        if not matching_rows:
            response = supabase.table("order_details").select("*") \
                .eq("user_id", user_id) \
                .eq("tracking_num", tracking_number) \
                .execute()
            matching_rows = response.data or []

        if not matching_rows:
            print(f"❌ No match found for tracking: {tracking_number}, order: {order_id}")
            return {}

        print(f"✅ Found {len(matching_rows)} matching row(s). Applying update...")

        # Exclude keys that should never be overwritten
        immutable_fields = {"order_id", "user_id", "item_desc", "item_sku"}
        update_payload = {
            key: clean_field(value)
            for key, value in shipping_info.items()
            if key not in immutable_fields and clean_field(value) is not None
        }

        for row in matching_rows:
            update_query = supabase.table("order_details").update(update_payload) \
                .eq("user_id", user_id) \
                .eq("tracking_num", tracking_number) \
                .eq("entry_id", row["entry_id"])

            if order_id:
                update_query = update_query.eq("order_id", order_id)

            update_response = update_query.execute()
            if update_response.data:
                print(f"✅ Updated entry_id={row['entry_id']}")
            else:
                print(f"⚠️ No data returned for entry_id={row['entry_id']}")

    except Exception as e:
        print(f"❌ Shipping update failed: {e}")

    return {}

import json
from typing import Dict
from LLM.extractor import query_openai, match_item_desc_via_gpt
from parser.email_parser import parse_item_details
from prompts.templates import SHIPPING_PROMPT_TEMPLATE
from supabase_client import supabase
from shared.types import AgentState


def extract_shipping_node(state: AgentState) -> dict:
    """
    LangGraph node: Extract shipping confirmation details from email and update the database.

    This function:
    - Parses shipping email using GPT
    - Matches each item to the original order using item_desc, color, size, sku
    - Falls back to GPT semantic matching if no direct DB match is found
    - Updates matching rows with tracking, delivery, carrier, and shipping fields
    """
    email_record = state["record"]

    # Step 1: Send prompt to OpenAI
    prompt = SHIPPING_PROMPT_TEMPLATE.format(
        subject=email_record.get("subject", ""),
        body=email_record.get("msg", "")
    )
    extracted = query_openai(prompt)
    if not extracted:
        return {}

    order_info = extracted.get("order_info", {}) or {}
    items = extracted.get("items", []) or []

    for item in items:
        user_id = email_record.get("user_id")
        order_id = (order_info.get("order_id") or "").strip()

        # Normalize item description
        raw_desc = item.get("item_desc", "").strip()
        base_desc, parsed_color, parsed_size = parse_item_details(raw_desc)

        color = item.get("item_color") or parsed_color
        size = item.get("item_size") or parsed_size
        item_sku = (item.get("item_sku") or "").strip()

        if not all([user_id, order_id, base_desc]):
            continue  # Cannot update without these keys

        try:
            # Step 2: Attempt DB match by user/order/item_desc
            query = supabase.table("order_details").select("*") \
                .eq("order_id", order_id) \
                .eq("item_desc", base_desc) \
                .eq("user_id", user_id)

            def flexible_filter(q, field, value):
                if value:
                    return q.filter(field, "ilike", f"%{value}%")
                return q

            query = flexible_filter(query, "item_color", color)
            query = flexible_filter(query, "item_size", size)
            query = flexible_filter(query, "item_sku", item_sku)

            response = query.execute()
            matched_rows = response.data or []

            # Step 3: If no match, use GPT fallback
            if not matched_rows:
                fallback_query = supabase.table("order_details").select("*") \
                    .eq("order_id", order_id).eq("user_id", user_id)
                fallback_response = fallback_query.execute()
                fallback_candidates = fallback_response.data or []

                best_match = match_item_desc_via_gpt(base_desc, fallback_candidates)
                if best_match:
                    matched_rows = [best_match]

            if not matched_rows:
                continue  # Still no match, skip update

            # Step 4: Prepare update payload
            shipping_fields = [
                "item_discount", "item_shipping", "item_tax", "shipping_method", "tracking_num",
                "expected_deliv_date", "actual_deliv_date", "carrier", "status"
            ]
            update_data = {field: item.get(field) for field in shipping_fields}
            update_data["shipping_address"] = order_info.get("shipping_address")
            update_data["zip_code"] = order_info.get("zip_code")

            # Skip empty update
            if all(value is None for value in update_data.values()):
                continue

            # Step 5: Apply updates to matched rows
            for row in matched_rows:
                update_query = supabase.table("order_details").update(update_data) \
                    .eq("entry_id", row["entry_id"])
                update_response = update_query.execute()

                if update_response.data:
                    print(f"✅ Shipping info updated for entry_id={row['entry_id']}")

        except Exception as e:
            print(f"❌ Error updating shipping info for order_id={order_id}: {e}")

    return {}

import json
from shared.types import AgentState
from LLM.extractor import query_openai
from parser.email_parser import parse_item_details
from prompts.templates import PROMPT_TEMPLATE
from supabase_client import supabase


def extract_order_node(state: AgentState) -> dict:
    """
    LangGraph node: Extract order details and individual item data from an order confirmation email.

    - Uses GPT to parse structured order info
    - Normalizes product attributes (desc, color, size)
    - Inserts cleaned item records into Supabase `order_details`

    Args:
        state (AgentState): Contains the full email record.

    Returns:
        dict: Empty dict (used for chaining, no intermediate output needed here)
    """
    email_record = state["record"]

    # ------------------------------------------
    # 🧠 Step 1: Generate prompt and call OpenAI
    # ------------------------------------------
    prompt = PROMPT_TEMPLATE.format(
        subject=email_record.get("subject", ""),
        body=email_record.get("msg", "")
    )

    extracted = query_openai(prompt)
    if not extracted:
        return {}

    # ------------------------------------------
    # 📦 Step 2: Extract top-level order fields
    # ------------------------------------------
    order_field_names = [
        "retailer", "order_id", "order_date", "order_total", "tax_total",
        "shipping_total", "discount_total", "shipping_address", "zip_code", "archive_flag"
    ]

    item_field_names = [
        "item_desc", "item_price", "item_sku", "item_qty", "item_color", "item_size",
        "item_discount", "image_name", "item_tax", "item_shipping", "shipping_method",
        "tracking_num", "expected_deliv_date", "status", "carrier", "actual_deliv_date"
    ]

    raw_order_info = extracted.get("order_info", {}) or {}
    order_info = {field: raw_order_info.get(field, None) for field in order_field_names}

    # ------------------------------------------
    # 🧾 Step 3: Normalize and enrich each item
    # ------------------------------------------
    order_rows = []
    for item in extracted.get("items", []) or []:
        item_data = {field: item.get(field, None) for field in item_field_names}

        # Normalize item description (split out base/size/color)
        raw_description = (item.get("item_desc") or "").strip()
        base_desc, parsed_color, parsed_size = parse_item_details(raw_description)

        item_data["item_desc"] = base_desc
        item_data["item_color"] = item.get("item_color") or parsed_color or None
        item_data["item_size"] = item.get("item_size") or parsed_size or None
        item_data["item_sku"] = item_data.get("item_sku") or ""

        # Combine all data into a single row
        row = {
            "user_email": email_record.get("user_email"),
            "user_id": email_record.get("user_id"),
            **order_info,
            **item_data
        }
        order_rows.append(row)

    # ------------------------------------------
    # 💾 Step 4: Insert rows into Supabase
    # ------------------------------------------
    try:
        if order_rows:
            print(f"✅ Inserting {len(order_rows)} order items into DB...")
            supabase.table("order_details").insert(order_rows).execute()
    except Exception as e:
        print(f"❌ DB insert error: {e}")

    return {}

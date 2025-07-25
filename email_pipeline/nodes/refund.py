import json
from LLM.extractor import query_openai, match_item_desc_via_gpt_returns
from prompts.templates import REFUND_PROMPT_TEMPLATE
from supabase_client import supabase
from shared.types import AgentState


def extract_refund_node(state: AgentState) -> dict:
    """
    LangGraph node: Extract refund details and synchronize them with the `returns_refunds` table.

    Uses OpenAI to parse refund-related data and follows a fallback update strategy:
    - Attempt to match existing DB rows by return_id + order_id
    - If no match, fall back to return_id or order_id alone
    - Within each match step, match by item_desc, color, and size
    - If no match, fallback to GPT-based semantic matching
    - If still no match, insert as a new refund row

    Returns:
        dict: Contains return_info and items for downstream use.
    """
    email_record = state["record"]
    print("📨 Parsing refund email via OpenAI...")

    # Step 1: Format prompt and extract
    prompt = REFUND_PROMPT_TEMPLATE.format(
        subject=email_record.get("subject", ""),
        body=email_record.get("msg", "")
    )
    extracted = query_openai(prompt)

    if not extracted:
        print("❌ No data extracted from OpenAI.")
        return {}

    return_info = extracted.get("return_info", {}) or {}
    items = extracted.get("items", []) or []

    print("📦 Parsed Refund Summary:")
    print(json.dumps(return_info, indent=2))

    rows_to_insert = []

    # Step 2: Iterate over each item for update/insert
    for idx, item in enumerate(items, 1):
        print(f"\n🔹 Item {idx}: {json.dumps(item, indent=2)}")

        # Merge top-level and item-level fields
        merged_item_data = {**return_info, **item}
        merged_item_data["return_id"] = merged_item_data.get("return_id") or ""
        merged_item_data["order_id"] = merged_item_data.get("order_id") or ""
        merged_item_data["user_email"] = merged_item_data.get("user_email") or ""

        return_id = merged_item_data["return_id"]
        order_id = merged_item_data["order_id"]
        item_desc = merged_item_data.get("return_item_desc")

        print(f"🧪 Sanity → return_id: '{return_id}', order_id: '{order_id}'")

        # Step 2.1: Match candidates from DB
        def get_candidate_rows(match_fields: list[str]) -> list[dict]:
            query = supabase.table("returns_refunds").select("*")
            for field in match_fields:
                value = merged_item_data.get(field)
                if value:
                    query = query.filter(field, "ilike", f"%{value}%")
            return query.execute().data or []

        def match_existing_row(candidates: list[dict]) -> dict | None:
            for row in candidates:
                match = all(
                    not merged_item_data.get(f) or merged_item_data.get(f).lower() in (row.get(f) or "").lower()
                    for f in ["return_item_desc", "return_item_color", "return_item_size"]
                )
                if match:
                    print("✅ Field-based match found.")
                    return row

            return match_item_desc_via_gpt_returns(item_desc, candidates)

        # Step 2.2: Apply fallback logic (3 levels)
        matched_row = None
        if return_id and order_id:
            print("🤖 Trying GPT fallback match return id and order id")
            matched_row = match_existing_row(get_candidate_rows(["return_id", "order_id"]))
        if not matched_row and return_id:
            print("🤖 Trying GPT fallback match return id only")
            matched_row = match_existing_row(get_candidate_rows(["return_id"]))
        if not matched_row and order_id:
            print("🤖 Trying GPT fallback match order id only")
            matched_row = match_existing_row(get_candidate_rows(["order_id"]))

        # Step 3: Clean keys and perform update or insert
        cleaned = {
            k: v for k, v in merged_item_data.items()
            if v is not None and (k != "return_item_desc" or str(v).strip() != "")
        }

        if matched_row:
            print("🛠️ Updating existing matched row...")

            # Don't overwrite key fields if already present
            if matched_row.get("return_id"):
                cleaned.pop("return_id", None)
            if matched_row.get("order_id"):
                cleaned.pop("order_id", None)
            if matched_row.get("return_item_desc"):
                cleaned.pop("return_item_desc", None)

            update_query = supabase.table("returns_refunds").update(cleaned)
            for key in [
                "return_id", "order_id", "return_item_desc",
                "return_item_sku", "return_item_size", "return_item_color"
            ]:
                if matched_row.get(key):
                    update_query = update_query.eq(key, matched_row[key])

            update_response = update_query.execute()
            if update_response.data:
                print("✅ Row updated.")
            else:
                print("⚠️ Update ran but returned no data.")

        else:
            print("🆕 No match found. Inserting as new row.")
            rows_to_insert.append(cleaned)

    # Step 4: Insert unmatched items
    if rows_to_insert:
        print(f"📥 Inserting {len(rows_to_insert)} new refund row(s).")
        supabase.table("returns_refunds").insert(rows_to_insert).execute()
    else:
        print("📭 Nothing to insert.")

    return {
        "return_info": return_info,
        "items": items
    }

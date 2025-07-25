import json
from LLM.extractor import query_openai, match_item_desc_via_gpt_returns
from prompts.templates import RETURN_UPDATE_PROMPT_TEMPLATE
from supabase_client import supabase
from shared.types import AgentState


def extract_return_update_node(state: AgentState) -> dict:
    """
    LangGraph node: Extract return progress update from an email and sync to Supabase.

    Matching strategy:
    - Try matching using return_id + order_id
    - Fallback to return_id or order_id individually
    - Within each fallback, match by item_desc, color, and size
    - If no match, use GPT fallback
    - If still no match, insert a new row
    """
    email_record = state["record"]
    print("📨 Extracting return update from email...")

    # Step 1: Format the prompt and call OpenAI
    prompt = RETURN_UPDATE_PROMPT_TEMPLATE.format(
        subject=email_record.get("subject", ""),
        body=email_record.get("msg", "")
    )
    extracted = query_openai(prompt)

    if not extracted:
        print("❌ No data extracted from OpenAI.")
        return {}

    return_info = extracted.get("return_info", {}) or {}
    items = extracted.get("items", []) or []

    print("📦 Return Update Summary Extracted")
    print(json.dumps(return_info, indent=2))

    rows_to_insert = []

    for idx, item in enumerate(items, 1):
        merged_item_data = {**return_info, **item}
        merged_item_data["return_id"] = merged_item_data.get("return_id") or ""
        merged_item_data["order_id"] = merged_item_data.get("order_id") or ""
        merged_item_data["user_email"] = merged_item_data.get("user_email") or ""

        return_id = merged_item_data["return_id"]
        order_id = merged_item_data["order_id"]
        item_desc = merged_item_data.get("return_item_desc", "")

        print(f"\n🔹 Item {idx} — {item_desc}")

        # Step 2: Search for matching DB row
        def fetch_candidates(fields: list[str]) -> list[dict]:
            query = supabase.table("returns_refunds").select("*")
            for field in fields:
                value = merged_item_data.get(field)
                if value:
                    query = query.filter(field, "ilike", f"%{value}%")
            return query.execute().data or []

        def match_best_row(candidates: list[dict]) -> dict | None:
            for row in candidates:
                match = all(
                    not merged_item_data.get(f) or merged_item_data.get(f).lower() in (row.get(f) or "").lower()
                    for f in ["return_item_desc", "return_item_color", "return_item_size"]
                )
                if match:
                    print("✅ Field-based match found.")
                    return row

            return match_item_desc_via_gpt_returns(item_desc, candidates)

        matched_row = None
        if return_id and order_id:
            print("🤖 Trying GPT fallback match return id and order id")
            matched_row = match_best_row(fetch_candidates(["return_id", "order_id"]))
        if not matched_row and return_id:
            print("🤖 Trying GPT fallback match return id only")
            matched_row = match_best_row(fetch_candidates(["return_id"]))
        if not matched_row and order_id:
            print("🤖 Trying GPT fallback match order id only")
            matched_row = match_best_row(fetch_candidates(["order_id"]))

        # Step 3: Prepare final payload
        cleaned = {
            k: v for k, v in merged_item_data.items()
            if v is not None and (k != "return_item_desc" or str(v).strip() != "")
        }

        if matched_row:
            print("🛠️ Updating existing return row...")

            # Avoid overwriting return_id/order_id/item_desc if they exist
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
                print("✅ Row updated successfully.")
            else:
                print("⚠️ Update executed but returned no data.")
        else:
            print("🆕 No match found. Will insert new record.")
            rows_to_insert.append(cleaned)

    if rows_to_insert:
        print(f"📥 Inserting {len(rows_to_insert)} new row(s)...")
        print(json.dumps(rows_to_insert, indent=2))
        supabase.table("returns_refunds").insert(rows_to_insert).execute()
    else:
        print("📭 No rows to insert.")

    return {
        "return_info": return_info,
        "items": items
    }

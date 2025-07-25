import json
from LLM.extractor import query_openai, match_item_desc_via_gpt_returns
from prompts.templates import RETURN_CONFIRMATION_PROMPT_TEMPLATE
from supabase_client import supabase
from shared.types import AgentState


def extract_return_confirmation_node(state: AgentState) -> dict:
    """
    LangGraph node: Extract return confirmation details from email and sync with Supabase.

    Fallback logic:
    - Try return_id + order_id match
    - Fallback to return_id or order_id
    - Match by item_desc, color, and size
    - Use GPT fallback if no DB match
    - Insert new row if no match

    Ensures critical fields (return_id, order_id, user_email) are non-null.
    Only updates fields that are empty or missing in DB.
    """
    email_record = state["record"]
    print("📨 Extracting return confirmation from email...")

    # Step 1: Generate prompt & query OpenAI
    prompt = RETURN_CONFIRMATION_PROMPT_TEMPLATE.format(
        subject=email_record.get("subject", ""),
        body=email_record.get("msg", "")
    )
    extracted = query_openai(prompt)

    if not extracted:
        print("❌ No data extracted from OpenAI.")
        return {}

    return_info = extracted.get("return_info", {}) or {}
    items = extracted.get("items", []) or []

    print("📦 Return Summary Extracted")
    print(json.dumps(return_info, indent=2))

    rows_to_insert = []

    # Step 2: Handle each return item individually
    for idx, item in enumerate(items, 1):
        merged_item_data = {**return_info, **item}
        merged_item_data["return_id"] = merged_item_data.get("return_id") or ""
        merged_item_data["order_id"] = merged_item_data.get("order_id") or ""
        merged_item_data["user_email"] = merged_item_data.get("user_email") or ""

        return_id = merged_item_data["return_id"]
        order_id = merged_item_data["order_id"]
        item_desc = merged_item_data.get("return_item_desc", "")

        print(f"\n🔹 Item {idx} — {item_desc}")

        # Step 2.1: Fetch potential DB matches
        def fetch_candidate_rows(fields: list[str]) -> list[dict]:
            query = supabase.table("returns_refunds").select("*")
            for field in fields:
                val = merged_item_data.get(field)
                if val:
                    query = query.filter(field, "ilike", f"%{val}%")
            return query.execute().data or []

        def match_row(candidates: list[dict]) -> dict | None:
            # First try exact-ish field match
            for row in candidates:
                match = all(
                    not merged_item_data.get(field) or merged_item_data.get(field).lower() in (row.get(field) or "").lower()
                    for field in ["return_item_desc", "return_item_color", "return_item_size"]
                )
                if match:
                    print("✅ Field-based match found.")
                    return row

            return match_item_desc_via_gpt_returns(item_desc, candidates)

        # Step 2.2: Fallback match logic
        matched_row = None
        if return_id and order_id:
            print("🤖 Trying GPT fallback match return id and order id")
            matched_row = match_row(fetch_candidate_rows(["return_id", "order_id"]))
        if not matched_row and return_id:
            print("🤖 Trying GPT fallback match return id only")
            matched_row = match_row(fetch_candidate_rows(["return_id"]))
        if not matched_row and order_id:
            print("🤖 Trying GPT fallback match order id only")
            matched_row = match_row(fetch_candidate_rows(["order_id"]))

        # Step 3: Prepare cleaned fields for DB insert/update
        cleaned = {
            k: v for k, v in merged_item_data.items()
            if v is not None and (k != "return_item_desc" or str(v).strip() != "")
        }

        if matched_row:
            print("🛠️ Updating existing refund row...")
            # Avoid overwriting key identifiers if already present
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

            response = update_query.execute()
            if response.data:
                print("✅ Row updated successfully.")
            else:
                print("⚠️ Update ran but returned no data.")
        else:
            print("🆕 No match found. Will insert new record.")
            rows_to_insert.append(cleaned)

    # Step 4: Perform insert for unmatched rows
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

"""
📄 prompts/templates.py

This module contains all the prompt templates used to extract structured data from emails.
Each prompt follows a strict schema and is used in different LangGraph nodes.
"""

# --------------------------------------------------
# 🛒 Order Extraction Prompt (Initial Order Email)
# --------------------------------------------------

PROMPT_TEMPLATE = """Extract order details from this email into JSON. 
Order details go in the order_info object, and each purchased item goes into the items array.

Return this structure:
{{
  "order_info": {{
    "retailer": "string",
    "order_id": "string",
    "order_date": "YYYY-MM-DD",
    "order_total": float,
    "tax_total": float,
    "shipping_total": float,
    "discount_total": float,
    "shipping_address": "string",
    "zip_code": "string",
    "archive_flag": bool
  }},
  "items": [
    {{
      "item_desc": "string",
      "item_price": float,
      "item_sku": "string",
      "item_qty": integer,
      "item_color": "string",
      "item_size": "string",
      "item_discount": float,
      "image_name": "string",
      "item_tax": float,
      "item_shipping": float,
      "shipping_method": "string",
      "tracking_num": "string",
      "expected_deliv_date": "YYYY-MM-DD",
      "status": "string",
      "carrier": "string",
      "actual_deliv_date": "YYYY-MM-DD"
    }}
  ]
}}

Rules:
1. Use null for unknown values
2. Format dates as YYYY-MM-DD
3. Maintain numeric types for prices/quantities
4. Never add comments or explanations
5. Status should be: confirmed, processed, delivered, returned, etc.
6. Handle discounts carefully:
   - item_discount: Apply to individual items when available
   - discount_total: Use for order-level discounts when present
7. Each image_name should contain the item image URL or best value found in an <img> tag or hyperlink.
8. Don't include any escape character in extraction like in shipping address etc.
10. Extract information from structured or semi-structured text (tables, lists, bullet points, etc.) and emails with or without HTML.

Email Subject: {subject}
Email Content:
{body}
"""

# --------------------------------------------------
# 💰 Refund Confirmation Prompt
# --------------------------------------------------

REFUND_PROMPT_TEMPLATE = """Extract refund details from this email into JSON format. 

Return this structure:
{{
  "return_info": {{
    "created_at": "YYYY-MM-DD",
    "retailer": "string",
    "return_id": "string",
    "return_method": "string",
    "return_tracking_num": "string",
    "return_carrier": "string",
    "return_confirmation": "Yes",
    "return_dropoff_deadline": "YYYY-MM-DD",
    "return_deadline": "YYYY-MM-DD",
    "exp_refund_amt": float,
    "refund_method": "string",
    "refund_status": "string",
    "exp_refund_date": "YYYY-MM-DD",
    "act_refund_date": "YYYY-MM-DD",
    "refund_amt": float,
    "order_id": "string",
    "qr_label": "string",
    "user_email": "string",
    "status": "Initiated | Approved | In Transit"
  }},
  "items": [
    {{
      "return_item_desc": "string",
      "return_item_sku": "string",
      "return_item_qty": integer,
      "return_item_size": "string",
      "return_item_color": "string",
      "return_reason": "string",
      "return_condition": "string",
      "item_amt": float,
      "ship_amt": float,
      "taxes_amt": float,
      "other_amt": float
    }}
  ]
}}

Guidelines:
1. Use null if a value is not present or cannot be found.
2. Dates must be in the format YYYY-MM-DD.
3. Numeric fields must be properly typed.
4. Only return the JSON object—no comments or extra text.
5. This prompt is for emails confirming a refund.
6. Choose the most appropriate return_status: Initiated, Approved, or In Transit.

Email Subject: {subject}
Email Content:
{body}
"""

# --------------------------------------------------
# 🚚 Shipping Update Prompt (Post-Shipment Email)
# --------------------------------------------------

SHIPPING_UPDATE_PROMPT_TEMPLATE = """Extract delivery details from this email into JSON format. 
Focus on identifying the expected and actual delivery dates, along with relevant shipping info.

Return this structure:
{{
  "order_info": {{
    "order_id": "string",
    "shipping_method": "string",
    "tracking_num": "string",
    "expected_deliv_date": "YYYY-MM-DD",
    "actual_deliv_date": "YYYY-MM-DD",
    "status": "string",
    "carrier": "string",
    "shipping_address": "string",
    "zip_code": "string"
  }}
}}

Extraction Instructions:
1. Use null for any value that is unknown or not present.
2. Format both delivery dates strictly as YYYY-MM-DD.
3. For **expected delivery date**, look for phrases like:
   - "expected delivery date is", "arriving by", "estimated arrival", "should arrive", "delivery window", etc.
4. For **actual delivery date**, look for:
   - "delivered on", "your package was delivered", "delivered:", "shipment completed on", etc.
5. Only extract one value for each date field — the most clearly stated one.
6. Status should be one of: confirmed, shipped, out for delivery, delivered, returned, etc.
7. Do not add explanations, color, or other attributes outside this schema.
8. Carrier Extraction:
    - Look for phrases near tracking numbers or shipping sections like:
      "Carrier: USPS", "Delivered via FedEx", "Tracking via UPS"
    - Extract just the carrier name: "UPS", "FedEx", "DHL", "USPS"
Email Subject: {subject}
Email Content:
{body}
"""

# --------------------------------------------------
# 📦 Shipping Confirmation Prompt (Initial Shipping Email)
# --------------------------------------------------

SHIPPING_PROMPT_TEMPLATE = """Extract order details from this email into JSON. 
Order details go in the order_info object, and each purchased item goes into the items array.

Return this structure:
{{
  "order_info": {{
    "retailer": "string",
    "order_id": "string",
    "shipping_address": "string",
    "zip_code": "string"
  }},
  "items": [
    {{
      "item_desc": "string",
      "item_price": float,
      "item_sku": "string",
      "item_qty": integer,
      "item_color": "string",
      "item_size": "string",
      "item_discount": float,
      "image_name": "string",
      "item_tax": float,
      "item_shipping": float,
      "shipping_method": "string",
      "tracking_num": "string",
      "expected_deliv_date": "YYYY-MM-DD",
      "status": "string",
      "carrier": "string",
      "actual_deliv_date": "YYYY-MM-DD"
    }}
  ]
}}

Rules:
1. Use null for unknown values.
2. Format all dates as YYYY-MM-DD.
3. Maintain correct numeric types for prices and quantities.
4. Never add comments, extra text, or explanations.
5. Status must be one of: confirmed, processed, shipped, out for delivery, delivered, returned.
6. Don't include any escape character in extraction like in shipping address etc.
7. For tracking number:
   - Look for lines like: 
     "Your tracking number is 1Z12345E0205271688", 
     "Tracking ID: 9400 1000 0000 0000 0000 00", 
     "Track your package using: FX1234567890".
   - Extract the most relevant and clearly tied tracking number (10–30 characters).
8. For shipping method:
   - Look for: "Shipping Method: Overnight", "Delivery Option: 2-Day", etc.
   - Extract values like: "Standard", "Overnight", "2-Day".
9. For carrier:
    - Look near tracking numbers for: "Carrier: USPS", "Delivered via FedEx", etc.
    - Extract just the carrier name like: "UPS", "FedEx", "DHL", "USPS".

Email Subject: {subject}
Email Content:
{body}
"""

# --------------------------------------------------
# 🔁 Return Confirmation Prompt
# --------------------------------------------------

RETURN_CONFIRMATION_PROMPT_TEMPLATE = """Extract return confirmation details from this email into JSON format.

Return this structure:
{{
  "return_info": {{
    "created_at": "YYYY-MM-DD",
    "retailer": "string",
    "return_id": "string",
    "return_method": "string",
    "return_tracking_num": "string",
    "return_carrier": "string",
    "return_confirmation": "Yes",
    "return_dropoff_deadline": "YYYY-MM-DD",
    "return_deadline": "YYYY-MM-DD",
    "exp_refund_amt": float,
    "refund_method": "string",
    "refund_status": "string",
    "exp_refund_date": "YYYY-MM-DD",
    "act_refund_date": "YYYY-MM-DD",
    "refund_amt": float,
    "order_id": "string",
    "qr_label": "string",
    "user_email": "string",
    "status": "Initiated | Approved | In Transit"
  }},
  "items": [
    {{
      "return_item_desc": "string",
      "return_item_sku": "string",
      "return_item_qty": integer,
      "return_item_size": "string",
      "return_item_color": "string",
      "return_reason": "string",
      "return_condition": "string",
      "item_amt": float,
      "ship_amt": float,
      "taxes_amt": float,
      "other_amt": float
    }}
  ]
}}

Guidelines:
1. Use null if a value is not present or cannot be found.
2. Dates must be in the format YYYY-MM-DD.
3. Numeric fields must be properly typed.
4. Only return the JSON object—no comments or extra text.
5. This prompt is for emails confirming a return has been requested, approved, or started.
6. Choose the most appropriate return_status: Initiated, Approved, or In Transit.

Email Subject: {subject}
Email Content:
{body}
"""

# --------------------------------------------------
# 🔁 Return Update Prompt (Post-return Email)
# --------------------------------------------------

RETURN_UPDATE_PROMPT_TEMPLATE = """Extract return update details from this email into JSON format.

Return this structure:
{{
  "return_info": {{
    "created_at": "YYYY-MM-DD",
    "retailer": "string",
    "return_id": "string",
    "return_method": "string",
    "return_tracking_num": "string",
    "return_carrier": "string",
    "return_confirmation": "Yes",
    "return_dropoff_deadline": "YYYY-MM-DD",
    "return_deadline": "YYYY-MM-DD",
    "exp_refund_amt": float,
    "refund_method": "string",
    "refund_status": "string",
    "exp_refund_date": "YYYY-MM-DD",
    "act_refund_date": "YYYY-MM-DD",
    "refund_amt": float,
    "order_id": "string",
    "qr_label": "string",
    "user_email": "string",
    "status": "Received | Inspected | Rejected | Processing Refund"
  }},
  "items": [
    {{
      "return_item_desc": "string",
      "return_item_sku": "string",
      "return_item_qty": integer,
      "return_item_size": "string",
      "return_item_color": "string",
      "return_reason": "string",
      "return_condition": "string",
      "item_amt": float,
      "ship_amt": float,
      "taxes_amt": float,
      "other_amt": float
    }}
  ]
}}

Guidelines:
1. Use null if a value is not present or cannot be found.
2. Dates must be in the format YYYY-MM-DD.
3. Numeric fields must be correctly typed.
4. Only return the JSON object—no extra text or commentary.
5. This prompt is used for emails indicating progress after a return was confirmed (e.g., item received, refund processing).
6. Choose the most appropriate status: Received, Inspected, Rejected, Processing Refund.

Email Subject: {subject}
Email Content:
{body}
"""

# --------------------------------------------------
# 📊 Email Classification Prompt
# --------------------------------------------------

CLASSIFICATION_TEMPLATE = """
You are an email classifier. Classify each email into exactly one of the following categories:
promos, goods receipt, retailer order confirmation, retailer shipping confirmation, services receipt, shipping update, return confirmation, return update, refund, retailer order update.

Definitions:
- promos: Promotional offers, discounts, advertisements, or sales emails. These do NOT confirm any order, payment, or shipment.
- goods receipt: Proof of payment for physical goods that were delivered to the customer. These typically include detailed itemized lists, total price paid, **and an invoice number**. A price or order summary alone is NOT sufficient. Do not classify an email as goods receipt unless it clearly shows the purchase was completed and invoiced.
- retailer order confirmation: Notification from a retailer that an order has been placed or is being prepared. These emails confirm the order but do NOT mention that it has shipped or include tracking information.
- retailer shipping confirmation: Notification from a retailer that item(s) have been handed off to a carrier. This is the **first** shipping alert. It typically includes tracking number or carrier info and uses language like “your package has shipped”, “we’ve shipped your item”, or “on its way”. It does NOT include delivery progress like "in transit" or "out for delivery".
- services receipt: Confirmation of payment for **non-physical services** such as rides (e.g., Uber, Lyft), bookings, event tickets, or food/restaurant delivery (e.g., DoorDash, Uber Eats).  
  ⚠️ All restaurant orders, food delivery, and cab or rideshare receipts — even itemized ones — belong to `services receipt`.
  ⚠️ Emails from restaurants that mention **order confirmation**, **order received**, or similar — even if they do not show a receipt — are still classified as `services receipt`.
- shipping update: Any **post-shipment** email that reports the **status or progress of the shipment**. These updates can include phrases like:  
  “in transit”, “delivered”, “arriving today/tomorrow”, “out for delivery”, “running late”, “rescheduled”, “delayed”, “held at facility”, etc.  
  Shipping updates may include tracking number, order ID, item list, and even **price info**, but those do NOT make it a goods receipt or shipping confirmation. The presence of **shipping status language** is what defines this category.
- retailer order update: Any **non-shipping** update from a **retailer** about an order that is not the initial order confirmation or shipping confirmation. Examples: item delayed, out of stock, backordered, or delivery date changed.
- return confirmation: The retailer's acknowledgment that a return request has been received and processing has begun. This is the **first positive response** to a return request, typically including:
  - Return authorization/approval
  - Return instructions (label, QR code, or drop-off details)
  - Items eligible for return
  - May include estimated refund amount
  ⚠️ Key indicator: Language confirming the return request is accepted (e.g., "Your return has been approved", "We've accepted your return request, "Return has been registered" etc").
- return update: **Shipping-related updates** about the physical return package ONLY. Must include:
  - "We've received your return package"
  - "Your return is in transit"
  - Carrier tracking updates for the return

Rules:
- 🚗 All rideshare or cab receipts (Uber, Lyft, etc.) = services receipt.
- 🍕 All restaurant orders or food delivery receipts (DoorDash, Uber Eats, etc.) = services receipt — even if itemized.
- 🍽️ **Restaurant emails that say “your order is confirmed” or “we’ve received your order”** should still be classified as `services receipt`, even if they look like an order confirmation.
- A receipt for physical goods is **goods receipt** only if it includes **an invoice number** and confirms the item was delivered.
- Do NOT classify emails with just price details or item lists as goods receipt — especially if they mention shipment progress.
- Shipping updates must contain **shipping status language**. These can be sent by **either the retailer or the carrier**.
- Retailer shipping confirmation is the **initial shipping notice** from the retailer. It introduces the shipment and often includes tracking info.
- Shipping update is any **follow-up** email that shows the shipment's progress (even if it repeats order info or tracking details).
- Return confirmation = return initiated or accepted.
- Return update = progress on return after confirmation.
- Refund = confirmation that a refund has been issued.
- Retailer order update, order confirmation, and shipping confirmation must be from the **retailer**, not a shipping provider. Use sender domain to help determine this (e.g., `@amazon.com`, `@target.com`, not `@ups.com`, `@fedex.com`).

Examples:
From: Amazon <shipment-tracking@amazon.com>  
Subject: Your Amazon order has shipped  
Email Content: Your package is on the way with tracking number 12345.  
Category: retailer shipping confirmation

From: FedEx <notifications@fedex.com>  
Subject: Your package is out for delivery  
Email Content: Your package will arrive today between 3–5 PM.  
Category: shipping update

From: Amazon <updates@amazon.com>  
Subject: Running late: Order #998877  
Email Content: We’re sorry — your order is delayed. New expected delivery: Friday.  
Category: shipping update

From: Apple <no-reply@apple.com>  
Subject: Receipt for your order  
Email Content: This is your receipt for the iPhone 14 you ordered. Invoice #456789.  
Category: goods receipt

From: Walmart <orders@walmart.com>  
Subject: Backorder notice for item #2345  
Email Content: One or more items in your order have been backordered. Estimated ship date has changed.  
Category: retailer order update

From: Target <orders@target.com>  
Subject: Order confirmation #AB123  
Email Content: Thanks for your order! We’re preparing your items now.  
Category: retailer order confirmation

From: UPS <tracking@ups.com>  
Subject: We've received your shipment  
Email Content: Your shipment from Amazon has been picked up and is on the way.  
Category: shipping update

From: Uber <noreply@uber.com>  
Subject: Your Uber receipt  
Email Content: Thanks for riding with us. Total charge: $12.55  
Category: services receipt

From: DoorDash <no-reply@doordash.com>  
Subject: Your food has been delivered  
Email Content: Thanks for your order. Pepperoni Pizza, Garlic Knots. Total: $21.80  
Category: services receipt

From: Chipotle <noreply@chipotle.com>  
Subject: We’ve received your order!  
Email Content: Your burrito bowl is confirmed. Ready for pickup at 6:30 PM.  
Category: services receipt

From: Amazon <refunds@amazon.com>  
Subject: Refund issued  
Email Content: We’ve issued your refund of $29.99 to your original payment method.  
Category: refund

Now classify this email:
From: {from_field}  
Subject: {subject}  
Email Content: {body}  
Only write the category name exactly as listed above (no explanation).  
Category:
"""

# --------------------------------------------------
# 🤖 GPT Matching Fallback Prompt
# --------------------------------------------------

FALLBACK_MATCH_PROMPT = """
You are helping to identify whether a product description from a shipping email matches any item from a list of known order items.

Extracted Description:
"{short_desc}"

Known Items (list of dictionaries):
{candidates}

Instructions:
- Your task is to return the dictionary of the single best-matching item, if one exists.
- Match by **meaning**, not just exact text.
- The extracted description may be abbreviated or formatted differently.
- Match even if the wording differs but the meaning is the same.
- Use semantic reasoning. For example:
  - "5Pkt" = "5 Pocket"
  - "Blk" = "Black"
  - "*Warpstreme" = "Warpstreme"
  - "Slim-Fit" = "Slim Fit"
  - "Reg" = "Regular"
  - Ignore case, punctuation, word order differences, and asterisks.
- Focus on matching core product identity: name, style, fit, fabric, size, and color.
- If no known item matches the extracted description at all, return nothing.

Output Format:
Return ONLY the matching dictionary from the list. If no match is found, return `null`.
"""

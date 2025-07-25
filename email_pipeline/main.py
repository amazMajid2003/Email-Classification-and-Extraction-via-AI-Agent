import os
import time
import asyncio
from dotenv import load_dotenv
from typing import Optional
from parser.email_parser import clean_email_html
from realtime import AsyncRealtimeClient, RealtimeSubscribeStates
from supabase_client import supabase
from workflow.graph import workflow  # LangGraph workflow

# Load environment variables
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_KEY")


def get_realtime_url(database_url: str) -> str:
    """
    Convert Supabase project URL to Realtime WebSocket-compatible URL.
    """
    return f"wss://{database_url.split('//')[1]}/realtime/v1"


async def load_test_pipeline(batch_size: int = 50):
    """
    Process the latest `batch_size` emails sequentially to test pipeline accuracy/performance.
    """
    print(f"\n🚀 Running load test on {batch_size} recent emails...")

    try:
        response = supabase.table("email_extracts") \
            .select("*") \
            .order("id", desc=True) \
            .limit(batch_size) \
            .execute()

        emails = response.data
        if not emails:
            print("⚠️ No emails found.")
            return

        durations = []
        for index, email in enumerate(emails, 1):
            email_id = email["id"]
            email["msg"] = clean_email_html(email["msg"])
            start = time.perf_counter()

            try:
                await workflow.ainvoke(
                    {"record": email},
                    {"configurable": {"thread_id": str(email_id)}}
                )
                elapsed = time.perf_counter() - start
                durations.append(elapsed)
            except Exception:
                print(f"❌ Failed to process email ID {email_id}")

        if durations:
            print("\n📊 Load Test Results")
            print(f"Total: {len(durations)} | Avg: {sum(durations)/len(durations):.2f}s | "
                  f"Min: {min(durations):.2f}s | Max: {max(durations):.2f}s")

    except Exception as e:
        print(f"❌ Load test error: {e}")


async def load_test_pipeline_parallel(batch_size: int = 50, concurrency: int = 5):
    """
    Parallel load test to simulate high-throughput pipeline execution.
    """
    print(f"\n🚀 Parallel load test: {batch_size} emails @ concurrency {concurrency}")

    try:
        response = supabase.table("email_extracts") \
            .select("*") \
            .order("id", desc=True) \
            .limit(batch_size) \
            .execute()

        emails = response.data
        if not emails:
            print("⚠️ No emails found.")
            return

        semaphore = asyncio.Semaphore(concurrency)
        durations = []

        async def process(email: dict, index: int):
            async with semaphore:
                email_id = email["id"]
                start = time.perf_counter()
                try:
                    await workflow.ainvoke(
                        {"record": email},
                        {"configurable": {"thread_id": str(email_id)}}
                    )
                    durations.append(time.perf_counter() - start)
                except Exception:
                    print(f"❌ Failed email ID {email_id}")

        await asyncio.gather(*[
            process(email, i + 1) for i, email in enumerate(emails)
        ])

        if durations:
            print("\n📊 Parallel Load Test Results")
            print(f"Total: {len(durations)} | Avg: {sum(durations)/len(durations):.2f}s | "
                  f"Min: {min(durations):.2f}s | Max: {max(durations):.2f}s")

    except Exception as e:
        print(f"❌ Parallel test error: {e}")


async def handle_realtime_event(payload: dict):
    """
    Callback for new email insert from Supabase Realtime.
    Triggers the LangGraph workflow.
    """
    email = payload["data"]["record"]
    email_id = email["id"]

    start = time.perf_counter()
    try:
        await workflow.ainvoke(
            {"record": email},
            {"configurable": {"thread_id": str(email_id)}}
        )
        print(f"📩 Processed realtime email ID {email_id} in {time.perf_counter() - start:.2f}s")
    except Exception:
        print(f"🔥 Realtime processing failed for email ID {email_id}")


async def main():
    """
    Entry point: Connects to Supabase Realtime and listens for new inserts.
    """
    realtime_url = get_realtime_url(SUPABASE_URL)
    client = AsyncRealtimeClient(realtime_url, SUPABASE_ANON_KEY)
    channel = client.channel("realtime:public:email_extracts")

    def on_insert(payload, ref=None):
        asyncio.create_task(handle_realtime_event(payload))

    def on_subscribe(status: RealtimeSubscribeStates, err: Optional[Exception]):
        print(f"🟢 Realtime Subscribed" if not err else f"🔴 Subscribe failed: {err}")

    channel.on_postgres_changes(
        event="INSERT",
        schema="public",
        table="email_extracts",
        callback=on_insert
    )

    await channel.subscribe(on_subscribe)
    await client.connect()

    print("✅ Pipeline is now listening for new emails...")
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())

import sys, asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    import aiosqlite
    print("aiosqlite imported", flush=True)
    async with aiosqlite.connect(":memory:") as db:
        print("connected", flush=True)
        await db.execute("CREATE TABLE t (id INTEGER)")
        print("table created", flush=True)
    print("DONE", flush=True)

asyncio.run(main())

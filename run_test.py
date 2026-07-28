import asyncio

from apps.api.test_intelligence import test_pg_lexical_adapter


async def main():
    try:
        await test_pg_lexical_adapter()
        print("SUCCESS")
    except Exception:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

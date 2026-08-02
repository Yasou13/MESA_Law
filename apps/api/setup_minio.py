import asyncio

from apps.api.core.storage import storage_service


async def main():
    await storage_service.create_bucket_if_not_exists()
    print("Bucket created successfully!")


if __name__ == "__main__":
    asyncio.run(main())

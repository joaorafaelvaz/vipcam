"""Seed initial camera records into the database."""

import asyncio
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


async def main():
    from app.db.session import async_session, engine
    from app.models.camera import Camera

    cameras = []

    # Read cameras from environment variables
    i = 1
    while True:
        name = os.getenv(f"CAMERA_{i}_NAME")
        url = os.getenv(f"CAMERA_{i}_URL")
        if not name or not url:
            break
        cameras.append(
            {
                "name": name,
                "rtsp_url": url,
                "location": os.getenv(f"CAMERA_{i}_LOCATION", ""),
                "fps_target": int(os.getenv(f"CAMERA_{i}_FPS", "5")),
            }
        )
        i += 1

    if not cameras:
        # Default demo cameras
        cameras = [
            {
                "name": "Salao Principal",
                "rtsp_url": "rtsp://admin:senha@192.168.0.101:554/onvif1",
                "location": "Unidade Centro - Salao",
                "fps_target": 5,
            },
            {
                "name": "Recepcao",
                "rtsp_url": "rtsp://admin:senha@192.168.0.102:554/onvif1",
                "location": "Unidade Centro - Recepcao",
                "fps_target": 3,
            },
        ]

    async with async_session() as session:
        for cam_data in cameras:
            camera = Camera(**cam_data)
            session.add(camera)
            print(f"  Added camera: {cam_data['name']}")
        await session.commit()

    await engine.dispose()
    print(f"\nSeeded {len(cameras)} cameras successfully.")


if __name__ == "__main__":
    asyncio.run(main())

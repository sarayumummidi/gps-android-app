import subprocess
import os
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

app = FastAPI(title="GPS Remote Control API")

PACKAGE_NAME = "com.pupil_labs.gps_alpha_lab"
RECEIVER_NAME = f"{PACKAGE_NAME}/.GpsRemoteReceiver"

# Use full path to ADB if not in PATH
ADB_PATH = os.path.expanduser("~/Library/Android/sdk/platform-tools/adb")

# Default device (set to None to auto-select when only one device, or specify device ID)
# Example device IDs: "emulator-5554", "adb-ZY22HHX45Q-2737J7"
DEFAULT_DEVICE = None


class ADBResponse(BaseModel):
    success: bool
    message: str
    device: str | None = None
    output: str | None = None


def get_connected_devices() -> list[dict]:
    """Get list of connected devices with their details."""
    result = subprocess.run(
        [ADB_PATH, "devices", "-l"],
        capture_output=True,
        text=True,
        timeout=5
    )

    devices = []
    lines = result.stdout.strip().split("\n")[1:]  # Skip header

    for line in lines:
        if line.strip() and " device " in line and "attached" not in line:
            # Split on " device " to get the full device ID (handles IDs with spaces like "(2)")
            parts = line.split(" device ")
            device_id = parts[0].strip()

            # Extract model name if available
            model = "unknown"
            if len(parts) > 1:
                for part in parts[1].split():
                    if part.startswith("model:"):
                        model = part.replace("model:", "")
                        break

            devices.append({"id": device_id, "model": model})

    return devices


def send_adb_broadcast(action: str, device: str | None = None) -> ADBResponse:
    """Send an ADB broadcast intent to the GPS app."""
    full_action = f"{PACKAGE_NAME}.{action}"

    # Determine which device to use
    target_device = device or DEFAULT_DEVICE

    if target_device is None:
        # Check how many devices are connected
        devices = get_connected_devices()
        if len(devices) == 0:
            raise HTTPException(status_code=400, detail="No Android devices connected")
        elif len(devices) > 1:
            device_list = ", ".join([f"{d['id']} ({d['model']})" for d in devices])
            raise HTTPException(
                status_code=400,
                detail=f"Multiple devices connected. Please specify device parameter. Available: {device_list}"
            )
        else:
            target_device = devices[0]["id"]

    cmd = [
        ADB_PATH, "-s", target_device, "shell", "am", "broadcast",
        "-a", full_action,
        "-n", RECEIVER_NAME
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            return ADBResponse(
                success=True,
                message=f"Broadcast sent: {action}",
                device=target_device,
                output=result.stdout.strip()
            )
        else:
            return ADBResponse(
                success=False,
                message=f"ADB command failed",
                device=target_device,
                output=result.stderr.strip()
            )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="ADB command timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ADB not found. Make sure Android SDK is installed")


@app.get("/")
def root():
    """Health check endpoint."""
    return {"status": "running", "service": "GPS Remote Control API"}


@app.post("/gps/start", response_model=ADBResponse)
def start_gps(device: str | None = Query(None, description="Device ID (e.g., emulator-5554)")):
    """Start GPS recording on the Android device."""
    return send_adb_broadcast("START_GPS", device)


@app.post("/gps/stop", response_model=ADBResponse)
def stop_gps(device: str | None = Query(None, description="Device ID (e.g., emulator-5554)")):
    """Stop GPS recording on the Android device."""
    return send_adb_broadcast("STOP_GPS", device)


@app.post("/gps/toggle", response_model=ADBResponse)
def toggle_gps(device: str | None = Query(None, description="Device ID (e.g., emulator-5554)")):
    """Toggle GPS recording (same as start - it toggles automatically)."""
    return send_adb_broadcast("START_GPS", device)


@app.post("/gps/event", response_model=ADBResponse)
def send_event(device: str | None = Query(None, description="Device ID (e.g., emulator-5554)")):
    """Send a marker event to the GPS app."""
    return send_adb_broadcast("SEND_EVENT", device)


@app.get("/devices")
def list_devices():
    """List all connected Android devices."""
    try:
        devices = get_connected_devices()
        return {
            "connected": len(devices) > 0,
            "device_count": len(devices),
            "devices": devices,
            "default_device": DEFAULT_DEVICE
        }
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="ADB not found")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="ADB command timed out")


@app.post("/devices/set-default")
def set_default_device(device_id: str = Query(..., description="Device ID to set as default")):
    """Set the default device for GPS commands."""
    global DEFAULT_DEVICE

    devices = get_connected_devices()
    device_ids = [d["id"] for d in devices]

    if device_id not in device_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Device '{device_id}' not found. Available: {device_ids}"
        )

    DEFAULT_DEVICE = device_id
    return {"message": f"Default device set to: {device_id}", "default_device": DEFAULT_DEVICE}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

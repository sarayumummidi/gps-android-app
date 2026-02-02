# GPS Remote Control API

This guide explains how to control the GPS Alpha Lab Android app remotely via terminal commands and how to run latency tests.

## Prerequisites

1. **ADB (Android Debug Bridge)** installed and in your PATH
2. **Python 3.10+** with dependencies installed
3. Android device connected via USB with USB debugging enabled
4. GPS Alpha Lab app installed on the device

### Install Python Dependencies

```bash
cd gps-api
pip install -r requirements.txt
```

---

## Method 1: Direct ADB Commands

You can send commands directly to the Android app using ADB broadcast intents without running the API server.

### Start Recording

```bash
adb shell am broadcast -a com.pupil_labs.gps_alpha_lab.START_GPS -n com.pupil_labs.gps_alpha_lab/.GpsRemoteReceiver
```

### Stop Recording

```bash
adb shell am broadcast -a com.pupil_labs.gps_alpha_lab.STOP_GPS -n com.pupil_labs.gps_alpha_lab/.GpsRemoteReceiver
```

### Send Event Marker

```bash
adb shell am broadcast -a com.pupil_labs.gps_alpha_lab.SEND_EVENT -n com.pupil_labs.gps_alpha_lab/.GpsRemoteReceiver
```

### With Multiple Devices Connected

If you have multiple devices connected, specify the device with `-s`:

```bash
# List connected devices
adb devices

# Send command to specific device
adb -s <device_id> shell am broadcast -a com.pupil_labs.gps_alpha_lab.START_GPS -n com.pupil_labs.gps_alpha_lab/.GpsRemoteReceiver
```

---

## Method 2: REST API

Run the FastAPI server to control the app via HTTP requests.

### Start the API Server

```bash
cd gps-api
python main.py
```

The server runs on `http://localhost:8000` by default.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/gps/start` | POST | Start GPS recording |
| `/gps/stop` | POST | Stop GPS recording |
| `/gps/event` | POST | Send event marker |
| `/gps/toggle` | POST | Toggle recording on/off |
| `/devices` | GET | List connected devices |
| `/devices/set-default` | POST | Set default device |
| `/health` | GET | Check API health |

### Using curl

```bash
# Start recording
curl -X POST http://localhost:8000/gps/start

# Stop recording
curl -X POST http://localhost:8000/gps/stop

# Send event marker
curl -X POST http://localhost:8000/gps/event

# Toggle recording
curl -X POST http://localhost:8000/gps/toggle

# List connected devices
curl http://localhost:8000/devices

# Specify a device
curl -X POST "http://localhost:8000/gps/start?device=emulator-5554"
```

### Interactive API Docs

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## Latency Testing

The `latency_test.py` script measures round-trip latency for API calls.

### Basic Usage

```bash
python latency_test.py
```

### Command-Line Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--url` | `-u` | `http://localhost:8000` | Base URL of the API server |
| `--device` | `-d` | Auto-detect | Target device ID |
| `--iterations` | `-n` | `10` | Number of test iterations per endpoint |
| `--delay` | | `0.1` | Delay between calls (seconds) |
| `--endpoints` | `-e` | `start stop event` | Endpoints to test |
| `--verbose` | `-v` | `False` | Print each measurement |
| `--output` | `-o` | None | Save results to CSV file |
| `--warmup` | `-w` | `3` | Warmup calls before measuring |

### Examples

```bash
# Run 50 iterations with verbose output
python latency_test.py --iterations 50 --verbose

# Test against a remote server
python latency_test.py --url http://192.168.1.100:8000

# Test specific endpoints only
python latency_test.py --endpoints start stop

# Test all endpoints including health and toggle
python latency_test.py --endpoints start stop event toggle health

# Save results to CSV
python latency_test.py --iterations 100 --output results.csv

# Full example with all options
python latency_test.py \
  --url http://localhost:8000 \
  --device emulator-5554 \
  --iterations 50 \
  --delay 0.2 \
  --endpoints start stop event \
  --warmup 5 \
  --verbose \
  --output latency_results.csv
```

### Output Metrics

For each endpoint tested, the script reports:
- **Mean**: Average latency in milliseconds
- **Std Dev**: Standard deviation
- **Min/Max**: Minimum and maximum latency
- **Median**: Middle value of all measurements

### Sample Output

```
=== Latency Test Results ===

Endpoint: start
  Samples: 10
  Mean: 45.23 ms
  Std Dev: 5.12 ms
  Min: 38.45 ms
  Max: 55.67 ms
  Median: 44.89 ms

Endpoint: stop
  Samples: 10
  Mean: 43.87 ms
  ...
```

---

## Troubleshooting

### "No devices connected"
- Ensure USB debugging is enabled on your device
- Run `adb devices` to verify connection
- Try `adb kill-server && adb start-server`

### "App not installed"
- Install the GPS Alpha Lab app on the device
- Verify package name: `adb shell pm list packages | grep gps_alpha_lab`

### API server won't start
- Check if port 8000 is already in use
- Install dependencies: `pip install -r requirements.txt`

### High latency results
- Ensure device is connected via USB (not WiFi debugging)
- Close other ADB-heavy applications
- Increase warmup iterations with `--warmup 10`

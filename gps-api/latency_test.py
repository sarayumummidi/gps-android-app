#!/usr/bin/env python3
"""
Latency Test Script for GPS Remote Control API

Measures round-trip latency for start, stop, and event marker API calls.
Uses time.perf_counter() for high-precision timing (nanosecond resolution).
"""

import argparse
import statistics
import time
from dataclasses import dataclass

import requests


@dataclass
class LatencyResult:
    """Stores latency measurements for a single endpoint."""
    endpoint: str
    latencies_ms: list[float]

    @property
    def mean(self) -> float:
        return statistics.mean(self.latencies_ms)

    @property
    def stdev(self) -> float:
        return statistics.stdev(self.latencies_ms) if len(self.latencies_ms) > 1 else 0.0

    @property
    def min(self) -> float:
        return min(self.latencies_ms)

    @property
    def max(self) -> float:
        return max(self.latencies_ms)

    @property
    def median(self) -> float:
        return statistics.median(self.latencies_ms)


def measure_latency(url: str, method: str = "POST", params: dict = None) -> tuple[float, bool, str]:
    """
    Measure the latency of a single API call.

    Returns:
        tuple: (latency_ms, success, response_text)
    """
    start = time.perf_counter()
    try:
        if method.upper() == "POST":
            response = requests.post(url, params=params, timeout=30)
        else:
            response = requests.get(url, params=params, timeout=30)
        end = time.perf_counter()

        latency_ms = (end - start) * 1000  # Convert to milliseconds
        success = response.status_code == 200
        return latency_ms, success, response.text
    except requests.RequestException as e:
        end = time.perf_counter()
        latency_ms = (end - start) * 1000
        return latency_ms, False, str(e)


def run_latency_test(
    base_url: str,
    endpoint: str,
    method: str = "POST",
    iterations: int = 10, # change this number to get more iterations
    device: str = None,
    delay_between_calls: float = 0.1,
    verbose: bool = False
) -> LatencyResult:
    """
    Run multiple latency measurements for an endpoint.

    Args:
        base_url: Base API URL (e.g., http://localhost:8000)
        endpoint: API endpoint (e.g., /gps/start)
        method: HTTP method
        iterations: Number of measurements to take
        device: Optional device ID
        delay_between_calls: Seconds to wait between calls
        verbose: Print each measurement

    Returns:
        LatencyResult with all measurements
    """
    url = f"{base_url.rstrip('/')}{endpoint}"
    params = {"device": device} if device else None
    latencies = []

    print(f"\nTesting {endpoint}...")

    for i in range(iterations):
        latency_ms, success, response = measure_latency(url, method, params)
        latencies.append(latency_ms)

        if verbose:
            status = "OK" if success else "FAIL"
            print(f"  [{i+1}/{iterations}] {latency_ms:.3f} ms ({status})")

        if not success and verbose:
            print(f"    Response: {response[:200]}")

        if i < iterations - 1:
            time.sleep(delay_between_calls)

    return LatencyResult(endpoint=endpoint, latencies_ms=latencies)


def print_results(results: list[LatencyResult], output_csv: str = None):
    """Print formatted results and optionally save to CSV."""
    print("\n" + "=" * 70)
    print("LATENCY TEST RESULTS")
    print("=" * 70)

    csv_lines = ["endpoint,mean_ms,stdev_ms,min_ms,max_ms,median_ms,samples"]

    for result in results:
        print(f"\n{result.endpoint}")
        print("-" * 40)
        print(f"  Mean:    {result.mean:8.3f} ms")
        print(f"  Stdev:   {result.stdev:8.3f} ms")
        print(f"  Min:     {result.min:8.3f} ms")
        print(f"  Max:     {result.max:8.3f} ms")
        print(f"  Median:  {result.median:8.3f} ms")
        print(f"  Samples: {len(result.latencies_ms)}")

        csv_lines.append(
            f"{result.endpoint},{result.mean:.3f},{result.stdev:.3f},"
            f"{result.min:.3f},{result.max:.3f},{result.median:.3f},{len(result.latencies_ms)}"
        )

    # Print all raw latencies for analysis
    print("\n" + "=" * 70)
    print("RAW LATENCIES (ms)")
    print("=" * 70)
    for result in results:
        print(f"\n{result.endpoint}:")
        print("  " + ", ".join(f"{l:.3f}" for l in result.latencies_ms))

    if output_csv:
        with open(output_csv, "w") as f:
            f.write("\n".join(csv_lines))
        print(f"\nResults saved to: {output_csv}")


def main():
    parser = argparse.ArgumentParser(
        description="Measure API latency for GPS Remote Control endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python latency_test.py
  python latency_test.py --iterations 50 --verbose
  python latency_test.py --url http://192.168.1.100:8000 --device emulator-5554
  python latency_test.py --endpoints start event --iterations 100
        """
    )
    parser.add_argument(
        "--url", "-u",
        default="http://localhost:8000",
        help="Base URL of the API (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--device", "-d",
        default=None,
        help="Device ID to use (optional, auto-selects if only one connected)"
    )
    parser.add_argument(
        "--iterations", "-n",
        type=int,
        default=10,
        help="Number of iterations per endpoint (default: 10)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between calls in seconds (default: 0.1)"
    )
    parser.add_argument(
        "--endpoints", "-e",
        nargs="+",
        choices=["start", "stop", "event", "toggle", "health"],
        default=["start", "stop", "event"],
        help="Endpoints to test (default: start stop event)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print each measurement"
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Save results to CSV file"
    )
    parser.add_argument(
        "--warmup", "-w",
        type=int,
        default=3,
        help="Number of warmup calls before measuring (default: 3)"
    )

    args = parser.parse_args()

    # Map endpoint names to paths
    endpoint_map = {
        "start": "/gps/start",
        "stop": "/gps/stop",
        "event": "/gps/event",
        "toggle": "/gps/toggle",
        "health": "/",
    }

    method_map = {
        "start": "POST",
        "stop": "POST",
        "event": "POST",
        "toggle": "POST",
        "health": "GET",
    }

    print("=" * 70)
    print("GPS API LATENCY TEST")
    print("=" * 70)
    print(f"API URL:    {args.url}")
    print(f"Device:     {args.device or 'auto-select'}")
    print(f"Iterations: {args.iterations}")
    print(f"Delay:      {args.delay}s")
    print(f"Warmup:     {args.warmup} calls")
    print(f"Endpoints:  {', '.join(args.endpoints)}")

    # Check API connectivity
    print("\nChecking API connectivity...")
    try:
        response = requests.get(f"{args.url}/", timeout=5)
        if response.status_code == 200:
            print("  API is reachable")
        else:
            print(f"  Warning: API returned status {response.status_code}")
    except requests.RequestException as e:
        print(f"  ERROR: Cannot connect to API: {e}")
        return 1

    # Warmup phase
    if args.warmup > 0:
        print(f"\nWarmup phase ({args.warmup} calls per endpoint)...")
        for name in args.endpoints:
            endpoint = endpoint_map[name]
            method = method_map[name]
            url = f"{args.url.rstrip('/')}{endpoint}"
            params = {"device": args.device} if args.device else None

            for _ in range(args.warmup):
                try:
                    if method == "POST":
                        requests.post(url, params=params, timeout=30)
                    else:
                        requests.get(url, params=params, timeout=30)
                except requests.RequestException:
                    pass
                time.sleep(0.05)

    # Run tests
    results = []
    for name in args.endpoints:
        endpoint = endpoint_map[name]
        method = method_map[name]

        result = run_latency_test(
            base_url=args.url,
            endpoint=endpoint,
            method=method,
            iterations=args.iterations,
            device=args.device,
            delay_between_calls=args.delay,
            verbose=args.verbose
        )
        results.append(result)

    # Print results
    print_results(results, args.output)

    return 0


if __name__ == "__main__":
    exit(main())

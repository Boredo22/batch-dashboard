#!/usr/bin/env python3
"""
Test script for SSE (Server-Sent Events) endpoint.
Run this to verify the SSE stream is working correctly.

Usage:
    python test_sse.py [--host HOST] [--port PORT] [--duration SECONDS]
"""

import argparse
import json
import time
import sys

def test_sse_endpoint(host='localhost', port=5000, duration=10):
    """Test the SSE endpoint by connecting and receiving events."""
    import urllib.request
    import urllib.error

    url = f'http://{host}:{port}/api/system/status/stream'
    print(f"Connecting to SSE endpoint: {url}")
    print(f"Will listen for {duration} seconds...\n")

    try:
        request = urllib.request.Request(url)
        request.add_header('Accept', 'text/event-stream')
        request.add_header('Cache-Control', 'no-cache')

        start_time = time.time()
        event_count = 0

        with urllib.request.urlopen(request, timeout=duration + 5) as response:
            print(f"Connected! Status: {response.status}")
            print(f"Headers: {dict(response.headers)}\n")
            print("-" * 60)

            buffer = ""
            while time.time() - start_time < duration:
                try:
                    chunk = response.read(1024).decode('utf-8')
                    if not chunk:
                        break

                    buffer += chunk

                    # Process complete SSE events
                    while '\n\n' in buffer:
                        event, buffer = buffer.split('\n\n', 1)

                        if event.startswith('data: '):
                            data_str = event[6:]  # Remove 'data: ' prefix
                            try:
                                data = json.loads(data_str)
                                event_count += 1
                                print(f"\n[Event #{event_count}] Received at {time.strftime('%H:%M:%S')}")
                                print(f"  Success: {data.get('success')}")
                                print(f"  Timestamp: {data.get('timestamp')}")
                                print(f"  Relays: {len(data.get('relays', []))} items")
                                print(f"  Pumps: {len(data.get('pumps', []))} items")
                                print(f"  Flow Meters: {len(data.get('flow_meters', []))} items")
                                print(f"  EC Value: {data.get('ec_value')}")
                                print(f"  pH Value: {data.get('ph_value')}")

                                # Show first pump status as example
                                pumps = data.get('pumps', [])
                                if pumps:
                                    pump = pumps[0]
                                    print(f"  Sample Pump: {pump.get('name')} - dispensing: {pump.get('is_dispensing')}")

                            except json.JSONDecodeError as e:
                                print(f"  [JSON Error] {e}")
                                print(f"  Raw data: {data_str[:200]}...")

                except Exception as e:
                    if "timed out" not in str(e).lower():
                        print(f"Read error: {e}")
                    break

        print("-" * 60)
        print(f"\nTest complete!")
        print(f"  Duration: {time.time() - start_time:.1f} seconds")
        print(f"  Events received: {event_count}")
        print(f"  Average rate: {event_count / (time.time() - start_time):.2f} events/second")

        return event_count > 0

    except urllib.error.URLError as e:
        print(f"Connection failed: {e}")
        print("\nMake sure the Flask server is running:")
        print(f"  cd batch-dashboard && python app.py")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_rest_endpoint(host='localhost', port=5000):
    """Quick test of the REST status endpoint for comparison."""
    import urllib.request
    import urllib.error

    url = f'http://{host}:{port}/api/system/status'
    print(f"\nTesting REST endpoint: {url}")

    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
            print(f"  Status: {response.status}")
            print(f"  Success: {data.get('success')}")
            print(f"  Timestamp: {data.get('timestamp')}")
            return True
    except Exception as e:
        print(f"  REST endpoint failed: {e}")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Test SSE endpoint')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=5000, help='Server port')
    parser.add_argument('--duration', type=int, default=10, help='Test duration in seconds')
    args = parser.parse_args()

    print("=" * 60)
    print("SSE Endpoint Test")
    print("=" * 60)

    # First test REST endpoint
    rest_ok = test_rest_endpoint(args.host, args.port)

    if rest_ok:
        print()
        # Then test SSE endpoint
        sse_ok = test_sse_endpoint(args.host, args.port, args.duration)

        if sse_ok:
            print("\n✓ SSE endpoint is working correctly!")
            sys.exit(0)
        else:
            print("\n✗ SSE endpoint test failed")
            sys.exit(1)
    else:
        print("\n✗ Server is not responding")
        sys.exit(1)

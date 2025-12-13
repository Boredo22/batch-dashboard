Get current system status summary.

```bash
echo "=== Backend Status ==="
curl -s http://localhost:5000/api/status | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f\"System Ready: {data.get('status', {}).get('system_ready', 'Unknown')}\")
    print(f\"Timestamp: {data.get('timestamp', 'Unknown')}\")

    relays = data.get('relays', [])
    active_relays = [r for r in relays if r.get('state')]
    print(f\"Active Relays: {len(active_relays)}/{len(relays)}\")
    for r in active_relays:
        print(f\"  - {r.get('name', r.get('id'))}: ON\")

    jobs = {
        'Fill': data.get('active_fill_job'),
        'Mix': data.get('active_mix_job'),
        'Send': data.get('active_send_job')
    }
    active_jobs = {k: v for k, v in jobs.items() if v}
    print(f\"Active Jobs: {len(active_jobs)}\")
    for name, job in active_jobs.items():
        print(f\"  - {name}: {job.get('status')} ({job.get('progress_percent', 0):.0f}%)\")

    print(f\"EC/pH Monitoring: {'Active' if data.get('ec_ph_monitoring') else 'Inactive'}\")
    if data.get('ec_ph_monitoring'):
        print(f\"  EC: {data.get('ec_value', 0):.2f} | pH: {data.get('ph_value', 0):.2f}\")
except Exception as e:
    print(f'Error parsing status: {e}')
"

echo ""
echo "=== Process Status ==="
ps aux | grep -E "(python.*app|node.*vite)" | grep -v grep || echo "No backend/frontend processes found"
```
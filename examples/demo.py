"""Run against the local server: python examples/demo.py [base-url]."""

import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def main(base):
    def call(path, method="GET", payload=None):
        data = json.dumps(payload).encode() if payload is not None else None
        headers = {"Content-Type": "application/json"} if data is not None else {}
        with urlopen(Request(base + path, data=data, headers=headers, method=method), timeout=5) as response:
            raw = response.read()
            return json.loads(raw) if raw else None

    print("TEXT ANALYZER")
    print(json.dumps(call("/api/v1/analyze", "POST", {"text": "Python builds APIs. Python makes data useful.", "top_n": 3}), indent=2))
    print("STUDENT RECORDS")
    student = call("/api/v1/students", "POST", {"name": "Demo Student", "country": "Demo", "skills": ["SQL"]})
    path = f"/api/v1/students/{student['id']}"
    try:
        call(path, "PATCH", {"skills": ["SQL", "Python"]})
        updated = call(path)
        assert updated["skills"] == ["SQL", "Python"]
        print(json.dumps(updated, indent=2))
    finally:
        call(path, "DELETE")
    print("Demo student deleted.")
    print("COUNTRIES INSIGHTS (fictional data by default)")
    print(json.dumps(call("/api/v1/countries/stats?top_n=3"), indent=2))


if __name__ == "__main__":
    try:
        main((sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5050").rstrip("/"))
    except (HTTPError, URLError) as error:
        raise SystemExit(f"Demo failed: {error}. Start the local Flask server as shown in README.md.")

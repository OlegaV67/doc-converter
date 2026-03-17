"""
Script to generate and add license keys to the server.

Usage:
    python generate_keys.py --count 10 --server https://your-app.railway.app --admin-token YOUR_TOKEN

Each key looks like: XXXX-XXXX-XXXX-XXXX
"""

import argparse
import secrets
import string
import requests


def generate_key() -> str:
    alphabet = string.ascii_uppercase + string.digits
    segments = ["".join(secrets.choice(alphabet) for _ in range(4)) for _ in range(4)]
    return "-".join(segments)


def add_key(server: str, admin_token: str, key: str) -> bool:
    resp = requests.post(
        f"{server}/admin/add-key",
        json={"key": key},
        headers={"x-admin-token": admin_token},
        timeout=10,
    )
    if resp.status_code == 200:
        return True
    print(f"  Error for {key}: {resp.status_code} {resp.text}")
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--server", required=True)
    parser.add_argument("--admin-token", required=True)
    parser.add_argument("--output", default="keys.txt", help="Save keys to file")
    args = parser.parse_args()

    keys = [generate_key() for _ in range(args.count)]
    added = []

    for key in keys:
        print(f"Adding {key} ... ", end="", flush=True)
        if add_key(args.server, args.admin_token, key):
            print("OK")
            added.append(key)
        else:
            print("FAILED")

    if added:
        with open(args.output, "a") as f:
            for k in added:
                f.write(k + "\n")
        print(f"\n{len(added)} keys saved to {args.output}")


if __name__ == "__main__":
    main()

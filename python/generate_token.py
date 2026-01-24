"""
SentinAL: JWT Token Generator
==============================
Utility script to generate JWT tokens for testing.

Usage:
    python generate_token.py --user test_user --expires 60

Author: SentinAL Security Team
Date: 2026-01-23
"""

import argparse
from datetime import timedelta
from auth import create_access_token


def main():
    parser = argparse.ArgumentParser(
        description='Generate JWT token for SentinAL API testing'
    )
    parser.add_argument(
        '--user',
        type=str,
        default='test_user',
        help='User ID to encode in token (default: test_user)'
    )
    parser.add_argument(
        '--expires',
        type=int,
        default=30,
        help='Token expiration time in minutes (default: 30)'
    )
    
    args = parser.parse_args()
    
    # Generate token
    token = create_access_token(
        data={"sub": args.user},
        expires_delta=timedelta(minutes=args.expires)
    )
    
    print("\n" + "="*70)
    print("JWT TOKEN GENERATED")
    print("="*70)
    print(f"\nUser ID: {args.user}")
    print(f"Expires in: {args.expires} minutes")
    print(f"\nToken:\n{token}")
    print("\n" + "="*70)
    print("\nUsage:")
    print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/analyze/77')
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

"""One-time, local-only helper: run this on your own machine (not in CI) to
complete the OAuth consent flow for a platform and save its token file.

Usage:
    python -m src.oauth_bootstrap youtube
"""

import sys

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] != "youtube":
        print("Usage: python -m src.oauth_bootstrap youtube")
        sys.exit(1)

    from src.platforms import youtube

    youtube.bootstrap_token()
    print("Saved YouTube token. You can now run this platform from CI using that token file as a secret.")


if __name__ == "__main__":
    main()

"""
One-command setup: initializes the database, downloads public policy PDFs,
and builds the vector store.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from data.init_db import init_database
from data.generate_policies import generate_all_policies
from utils.vector_store import build_vector_store


def main():
    print("=" * 50)
    print("  TechCorp Customer Support AI — Setup")
    print("=" * 50)

    if not os.getenv("OPENAI_API_KEY"):
        print("\n⚠️  OPENAI_API_KEY not set.")
        print("   Create a .env file with: OPENAI_API_KEY=your-key")
        print("   Or export it: export OPENAI_API_KEY=your-key\n")
        sys.exit(1)

    print("\n[1/3] Initializing SQLite database...")
    init_database()

    print("\n[2/3] Downloading public policy PDF documents...")
    generate_all_policies()

    print("\n[3/3] Building vector store from policy PDFs...")
    build_vector_store()

    print("\n" + "=" * 50)
    print("  Setup complete! Run the app with:")
    print("    streamlit run app.py")
    print("=" * 50)


if __name__ == "__main__":
    main()

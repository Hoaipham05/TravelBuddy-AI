"""
agent_cli.py – CLI chat trực tiếp (không qua API/queue).
Dùng để test local khi không cần Redis.

Chạy: python agent_cli.py
"""
from __future__ import annotations
import sys
import os
import logging

# Đưa thư mục gốc vào path
sys.path.insert(0, os.path.dirname(__file__))

from colorama import Fore, Style, init as colorama_init
from dotenv import load_dotenv

load_dotenv()
colorama_init(autoreset=True)
logging.basicConfig(level=logging.WARNING)


def _banner():
    print(f"""
{Fore.CYAN}{'═' * 62}
{Fore.YELLOW}  ✈️  TravelBuddy v2 — Trợ lý Du lịch Thông minh
{Fore.WHITE}  LangGraph · LiteLLM · SearXNG + DuckDuckGo · Redis Ready
{Fore.CYAN}{'═' * 62}
{Fore.WHITE}  Provider: {os.getenv('LLM_PROVIDER','groq').upper()} / {os.getenv('GROQ_MODEL','qwen/qwen3-32b')}
  Gõ 'quit' để thoát | 'reset' để hội thoại mới
{Fore.CYAN}{'─' * 62}{Style.RESET_ALL}""")


def main():
    _banner()

    from src.agent.graph import run_agent
    history = []

    while True:
        try:
            user_input = input(Fore.GREEN + "\nBạn: " + Style.RESET_ALL).strip()
        except (EOFError, KeyboardInterrupt):
            print(Fore.YELLOW + "\nTạm biệt! ✈️")
            sys.exit(0)

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q", "thoát"):
            print(Fore.YELLOW + "\nTạm biệt! Chúc chuyến đi vui! 🌏")
            break
        if user_input.lower() == "reset":
            history = []
            print(Fore.CYAN + "\n🔄 Hội thoại mới!\n")
            continue

        print(Fore.MAGENTA + "\n🤔 TravelBuddy đang suy nghĩ…" + Style.RESET_ALL)

        try:
            answer, history = run_agent(user_input, history)
            print(Fore.CYAN + "\nTravelBuddy: " + Style.RESET_ALL + answer)
        except Exception as exc:
            print(Fore.RED + f"\n❌ Lỗi: {exc}\n   Gõ 'reset' để thử lại.")

        print(Fore.CYAN + "─" * 62 + Style.RESET_ALL)


if __name__ == "__main__":
    main()

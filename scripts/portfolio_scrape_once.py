#!/usr/bin/env python3
"""
One-off portfolio scraper (no Flask).

Uses the same scheduler scraping logic, then exits.
"""

from portfolio_scraper import (
    SOLANA_ADDRESSES,
    EVM_ADDRESSES,
    SCRAPE_INTERVAL_MINUTES,
    CHROME_DEBUG_PORT,
    PortfolioScheduler,
)


def main() -> None:
    print("\n" + "=" * 70)
    print("   UNIFIED PORTFOLIO SCRAPER - ONE-OFF MODE")
    print("=" * 70)
    print(f"   Solana wallets: {len(SOLANA_ADDRESSES)}")
    print(f"   EVM wallets:    {len(EVM_ADDRESSES)}")
    print()

    scheduler = PortfolioScheduler(
        solana_addresses=SOLANA_ADDRESSES,
        evm_addresses=EVM_ADDRESSES,
        scrape_interval_minutes=SCRAPE_INTERVAL_MINUTES,
        chrome_debug_port=CHROME_DEBUG_PORT,
    )

    try:
        scheduler.scrape_and_cache()
    finally:
        if scheduler.jupiter_scraper:
            scheduler.jupiter_scraper.cleanup()
        if scheduler.debank_scraper:
            scheduler.debank_scraper.cleanup()


if __name__ == "__main__":
    main()

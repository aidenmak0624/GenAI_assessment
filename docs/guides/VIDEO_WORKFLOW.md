# Demo Workflow

This is the exact flow used by the recorded demo in `scripts/record_demo_video.js`.

## Part 1: Core Functionality

1. Ask: `Summarize Best Buy's return policy for most products.`
   Expected:
   - Routed to `RAG Agent (Policy Documents)`
   - Mentions the `15 / 30 / 45 day` windows
   - `Show sources` cites `bestbuy_return_exchange_policy.pdf`

2. Ask: `How many Premium tier customers do we have?`
   Expected:
   - Routed to `SQL Agent (Customer Database)`
   - Returns `11 Premium tier customers`
   - `Show sources` includes the generated SQL against `customers`

3. Ask: `Based on Best Buy's return policy, would Ema still qualify for a refund on her SmartDesk Hub?`
   Expected:
   - Routed to `Hybrid (SQL + RAG Synthesis)`
   - Explains Ema's June 15, 2023 order is outside the documented return window
   - `Show sources` combines SQL facts and Best Buy policy evidence

## Part 2: John's Workflow

4. Upload:
   - `demo_assets/upload_pdfs/single/beaconshield_device_protection_policy.pdf`

5. Ask: `Summarize the BeaconShield device protection policy.`
   Expected:
   - Routed to `RAG Agent (Policy Documents)`
   - Mentions `BeaconShield Standard`, `BeaconShield Plus`, `24 months`, and `2 business hours`
   - `Show sources` cites `beaconshield_device_protection_policy.pdf`

6. Ask: `Give me a quick overview of customer Ema Johnson's profile and past support ticket details.`
   Expected:
   - Routed to `SQL Agent (Customer Database)`
   - Summarizes Ema's membership plus her ticket/order context
   - `Show sources` includes the SQL trace

## Closing Note

End the demo by stating that the same backend is also exposed through the FastMCP server for MCP-compatible clients.

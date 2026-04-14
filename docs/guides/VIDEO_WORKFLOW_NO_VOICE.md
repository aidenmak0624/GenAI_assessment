# Silent Demo Workflow

Use short caption cards between scenes.

## Caption Cards

1. `Part 1: Core functionality`
2. `RAG over public policy PDFs`
3. `Natural-language SQL over customer data`
4. `Hybrid reasoning across SQL + policy documents`
5. `Part 2: John's workflow`
6. `Upload a new PDF and query it immediately`
7. `Customer lookup from the SQL database`
8. `FastMCP integration for external clients`

## On-Screen Steps

1. Ask `Summarize Best Buy's return policy for most products.` and open `Show sources`.
2. Ask `How many Premium tier customers do we have?` and open `Show sources`.
3. Ask `Based on Best Buy's return policy, would Ema still qualify for a refund on her SmartDesk Hub?` and open `Show sources`.
4. Upload `demo_assets/upload_pdfs/single/beaconshield_device_protection_policy.pdf`.
5. Ask `Summarize the BeaconShield device protection policy.` and open `Show sources`.
6. Ask `Give me a quick overview of customer Ema Johnson's profile and past support ticket details.` and open `Show sources`.

## Result

This silent flow demonstrates:
- policy RAG
- SQL retrieval
- hybrid reasoning
- live PDF upload and re-index
- MCP readiness

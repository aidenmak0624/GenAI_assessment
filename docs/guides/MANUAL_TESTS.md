# Manual Test Checklist

## Setup

1. Start the app with `streamlit run app.py`.
2. Enter `OPENAI_API_KEY`.
3. Click `Full Setup`.

## Core Checks

1. Ask `Summarize Best Buy's return policy for most products.`
   Verify:
   - RAG route
   - 15/30/45-day summary
   - sources are hidden by default and expandable

2. Ask `How many Premium tier customers do we have?`
   Verify:
   - SQL route
   - answer is `11`
   - SQL trace appears under `Show sources`

3. Ask `Based on Best Buy's return policy, would Ema still qualify for a refund on her SmartDesk Hub?`
   Verify:
   - Hybrid route
   - answer says she is outside the return window
   - source block combines customer facts and policy evidence

## Upload Check

1. Upload `demo_assets/upload_pdfs/single/beaconshield_device_protection_policy.pdf`.
2. Wait for `Vector store updated with new documents!`
3. Ask `Summarize the BeaconShield device protection policy.`
   Verify:
   - RAG route
   - BeaconShield coverage details appear
   - source references point at the uploaded PDF

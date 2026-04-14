# Demo Assets

This directory contains stable, upload-ready files for manual demos and interview recordings.

## Upload Packs

- [Single upload demo PDF](/Users/chinweimak/Documents/gitpushplace/TCS/demo_assets/upload_pdfs/single/beaconshield_device_protection_policy.pdf)
- [Standard mock upload pack](/Users/chinweimak/Documents/gitpushplace/TCS/demo_assets/upload_pdfs/standard/UPLOAD_TEST_QUERIES.md)
- [Conflict-focused mock upload pack](/Users/chinweimak/Documents/gitpushplace/TCS/demo_assets/upload_pdfs/conflicts/UPLOAD_TEST_QUERIES.md)

## Purpose

- `upload_pdfs/single/`: simplest one-file upload demo for RAG verification
- `upload_pdfs/standard/`: clean mock policies with distinct terms for normal upload testing
- `upload_pdfs/conflicts/`: intentionally overlapping policies for citation and conflict-resolution testing

## Notes

- These files are separate from `docs/`, which is reserved for the seeded public policy corpus used by default setup.
- Runtime logs, Playwright artifacts, and temporary screenshots belong in `output/` and are ignored for Git.

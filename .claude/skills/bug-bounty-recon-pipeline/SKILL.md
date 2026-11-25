---
name: bug-bounty-recon-pipeline
description: Build an automated, continuously-running reconnaissance pipeline for bug bounty programs — subdomain enumeration, service fingerprinting, and change detection. Use when starting or scaling bug bounty recon.
---

# Bug Bounty Recon Pipeline

Stand up an automated recon pipeline that surfaces new attack surface as it appears.

## When to Use

- You are starting a bug bounty program and need a repeatable recon workflow
- You want to detect changes (new subdomains, ports, endpoints) over time

## Pipeline Stages

### 1. Scope Ingestion

- Parse program scope from the policy page; store exact in-scope patterns (`*.example.com` vs `example.com`)
- Reject anything out of scope at query time, not by memory

### 2. Subdomain Enumeration

- Passive: certificate transparency logs (crt.sh), amass passive, subfinder with multiple sources
- Active: amass active, DNS bruteforce (puredns), permutations (gotator)
- Resolve and probe live hosts (httpx): status, title, tech stack, CDN

### 3. Content Discovery

- URL collection: waybackurls, gau, katana crawl
- Pattern match for high-value endpoints: API keys, login portals, admin panels, GraphQL, `.git`, `.env` (report-worthy without reading contents)
- Screenshot everything (gowitness / axiom) for manual review

### 4. Port and Service Scan

- `nmap -sV` top ports on in-scope IPs, plus full range on interesting hosts
- Tag non-HTTP services (RDP, SMB, databases) for targeted testing

### 5. Change Detection

- Re-run stages on a schedule (daily/weekly)
- Diff outputs; alert on new subdomains, new ports, new endpoints, changed tech stacks
- Store everything in version-controlled or timestamped directories

## Tooling Notes

- Run from VPS/VPN only where program policy permits automated scanning
- Rate-limit aggressively; many programs ban aggressive automation
- Containers (e.g., via axiom/nuclei-templates) keep tool versions consistent

## Output

A prioritized target list: new/changed assets, annotated with observed technologies and suspected entry points.

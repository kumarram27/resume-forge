---
# ── Identity ──────────────────────────────────────────────────────────────
name: Alex Rivera
title: Senior Software Engineer
email: alex.rivera@example.com
phone: "+1 (415) 555-0192"
location: San Francisco, CA

# Labeled contact links (optional - add as many as you like)
links:
  - text: Portfolio
    url: https://alexrivera.dev
  - text: LinkedIn
    url: https://linkedin.com/in/alexrivera
  - text: GitHub
    url: https://github.com/alexrivera

# ── Template / theming ─────────────────────────────────────────────────────
template: modern
accent_color: "#2563eb"
font: inter          # inter | georgia | source-sans
---

# Summary

Versatile senior engineer with 8 years of experience designing and shipping
distributed systems at scale. Passionate about developer tooling, platform
reliability, and mentoring early-career engineers. Proven track record of
reducing infrastructure costs while improving system throughput.

# Experience

## Stripe
**Staff Software Engineer**
January 2022 – Present
_San Francisco, CA_

- Led architecture and rollout of an internal feature-flag platform serving
  400 million flag evaluations per day with sub-millisecond p99 latency.
- Reduced CI pipeline duration by 42 % by introducing remote build caching
  and parallelised test sharding across 1,200 daily builds.
- Mentored a cohort of 6 new-grad engineers through the company's onboarding
  program; 4 were promoted to L3 within 18 months.
- Collaborated with product and data science to design an A/B testing
  framework that increased experiment velocity by 3×.

## Cloudflare
**Software Engineer II**
June 2019 – December 2021
_Remote_

- Built a real-time log aggregation pipeline (Kafka → ClickHouse) that
  ingested 2 TB of edge logs per hour with end-to-end latency under 5 s.
- Owned the on-call rotation for the Workers KV storage layer; drove MTTR
  from 47 min to 12 min over two quarters through better runbooks and alerts.
- Designed a tenant-isolation model for multi-region deployments that passed
  SOC 2 Type II audit with zero findings.
- Contributed 14 accepted patches to the open-source `pingora` Rust HTTP
  framework.

# Education

## University of California, Berkeley
**Bachelor of Science in Electrical Engineering and Computer Sciences**
August 2015 – May 2019
GPA: 3.82

- Dean's List - six consecutive semesters
- Teaching assistant for CS 162 (Operating Systems), Spring 2018 & 2019

# Skills

**Languages:** Rust, Go, Python, TypeScript, SQL
**Platforms:** Kubernetes, AWS (ECS, RDS, S3, Lambda), Cloudflare Workers
**Data & Messaging:** Kafka, ClickHouse, PostgreSQL, Redis, Elasticsearch
**Observability:** Prometheus, Grafana, OpenTelemetry, Datadog
**Practices:** System design, SRE, CI/CD, code review, technical writing

# Projects

## Flagsmith OSS Contributions
- GitHub: [Repository](https://github.com/Flagsmith/flagsmith)
**Tech:** Python, Django, React, PostgreSQL

- Added multi-environment flag inheritance, reducing configuration drift
  across staging and production environments.
- Implemented a streaming SDK endpoint (SSE) reducing flag-change propagation
  time from 60 s (polling) to under 500 ms.

## resume-forge
- GitHub: [Repository](https://github.com/alexrivera/resume-forge)
**Tech:** Python, WeasyPrint, Jinja2, GitHub Actions

A GitHub Action that converts a Markdown resume into a polished PDF and
commits it back to the repository automatically on every push.

- Supports configurable templates, accent colours, and font families.
- Generates versioned PDF snapshots keyed by commit SHA and timestamp.

# Certifications

## AWS Certified Solutions Architect - Professional
**Amazon Web Services**
March 2023
[https://aws.amazon.com/certification/](https://aws.amazon.com/certification/)

## Certified Kubernetes Administrator (CKA)
**Cloud Native Computing Foundation**
November 2021

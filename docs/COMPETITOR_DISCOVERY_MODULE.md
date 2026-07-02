# Competitor Discovery Module

## Overview

The Competitor Discovery Module is a backend feature within the VoxIntel multi-tenant SaaS platform that automates competitor identification based on industry and location.

The module combines search engine results, LLM-based extraction, official website verification, blacklist filtering, and duplicate detection to produce a structured list of validated competitors.

This module serves as the foundation for future competitor intelligence features such as analytics, monitoring, AI insights, and automated reporting.

---

## Problem Statement

Identifying competitors manually is time-consuming and often produces inconsistent results. Search results frequently contain:

* Directory websites
* Review platforms
* Government organizations
* Social media pages
* Duplicate company listings
* Invalid website URLs

These issues reduce data quality and make competitor research inefficient.

The Competitor Discovery Module automates competitor discovery and website validation to provide reliable competitor data.

---

## Objectives

* Discover competitors based on industry and location.
* Extract only relevant organizations.
* Verify official company websites.
* Exclude directories, aggregators, and social platforms.
* Remove duplicate records.
* Return structured competitor information.

---

## Architecture and Workflow

The Competitor Discovery Module follows a multi-stage workflow that combines search engine results, LLM-based extraction, website verification, duplicate detection, and structured response generation.

```text
            ┌──────────────────────────────┐
            │ 1. User Input                │
            │ Industry, Country, State,    │
            │ District                     │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 2. Query Builder             │
            │ District → State → Country   │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 3. Serper Search API         │
            │ Competitor Discovery Search  │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 4. Search Result Collection  │
            │ Titles + URLs + Snippets     │
            │ (Serper Results)             │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 5. Groq LLM                  │
            │ Competitor Extraction        │
            │ Organization Identification  │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 6. Company Validation        │
            │ Parse & Clean Results        │
            │ Remove Invalid Entries       │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 7. Serper Search API         │
            │ Official Website Lookup      │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 8. Website Verification      │
            │ Blacklist Filtering          │
            │ Domain Matching              │
            │ Fallback Validation          │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 9. Duplicate Detection       │
            │ seen_companies               │
            │ seen_websites                │
            └──────────────┬───────────────┘
                        │
                        ▼
            ┌──────────────────────────────┐
            │ 10. Response Generation      │
            │ Structured JSON Response     │
            └──────────────────────────────┘
```


### Core Processing Flow

The module performs two separate Serper searches:

**First Serper Search**

* Discover competitor organizations.
* Collect search context.

**Groq Processing**

* Extract valid competitors from search results.

**Second Serper Search**

* Verify official company websites.

```text
Serper → Groq → Serper → Validation → Response
```

### Query Strategy

Location-aware search queries are generated using:

```text
District → State → Country
```

This ensures local competitors are prioritized before expanding the search scope.

---

## Components Implemented

### Competitor Discovery API

Endpoint:

```text
POST /api/v1/competitors/discover
```

Accepts industry and location inputs and returns validated competitor data.

---

### Search Query Builder

Generates location-aware search queries using the district, state, and country fallback strategy.

---

### Competitor Search Agent

Integrates with the Serper Search API to collect search result titles, URLs, and snippets.

---

### Groq-Based Competitor Extraction

Uses the `llama-3.3-70b-versatile` model to extract valid competitor organizations from aggregated search results.

---

### Prompt Engineering

Custom prompt rules improve extraction quality by:

* Prioritizing local competitors
* Applying industry-specific filtering
* Excluding government organizations
* Excluding directories and aggregators
* Enforcing location relevance

---

### Website Verification Engine

Verifies official company websites using:

* Serper Search API
* Domain normalization
* Blacklist filtering
* Company-domain matching
* Fallback website selection

---

### Domain Validation

Website validation uses:

* `OFFICIAL_WEBSITE_BLACKLIST`
* `IGNORE_WORDS`
* Matching score
* Required score threshold

Only trusted and relevant domains are accepted.

---

### Duplicate Detection

Duplicate removal is implemented using:

```text
seen_companies
seen_websites
```

This ensures unique company records and website URLs.

---

## Files Implemented

### app/agents/web_search_agent.py

Core agent responsible for:

* Query generation
* Serper integration
* Groq extraction
* Website verification
* Blacklist filtering

### app/service/website_url_service.py

Contains the competitor discovery workflow, validation logic, duplicate detection, and response generation.

### app/routes/website_url_routes.py

Implements the FastAPI endpoint for competitor discovery.

### app/schemas/website_url_schema.py

Defines request and response schemas using Pydantic.

### test_groq.py

Used to validate Serper search and Groq extraction.

### app/service/test_competitor_service.py

Used to test the complete competitor discovery workflow.

---

## Challenges Faced

* Incorrect company extraction
* Government organizations appearing in results
* Invalid website URLs
* Directory websites being selected as official websites
* Duplicate competitor entries
* Location relevance issues
* Domain matching accuracy

---

## Solutions Implemented

* Prompt refinement
* Industry-specific filtering
* Location-based filtering
* Website blacklist filtering
* Domain scoring mechanism
* Official website verification
* Fallback search strategy
* Duplicate detection and removal

---

## Future Enhancements

* Competitor CRUD operations
* Tenant-specific competitor storage
* Competitor analytics
* Competitor monitoring
* AI-generated competitor insights
* Automated competitor reports

---

## Conclusion

The Competitor Discovery Module successfully automates competitor identification using search engine data, Groq-based extraction, official website verification, blacklist filtering, and duplicate detection.

By returning validated competitor names and official website URLs, the module provides a reliable foundation for competitor intelligence capabilities within the VoxIntel platform.

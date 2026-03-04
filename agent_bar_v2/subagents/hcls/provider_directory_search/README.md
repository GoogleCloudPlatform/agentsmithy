# Provider Directory Search Agent

A healthcare provider directory search agent built that helps users find practitioners, facilities, and organizations by name, specialty, location, or relationship.

## Overview

Users can ask natural-language questions like:

- *"Find a cardiologist near the Texas Medical Center"*
- *"Are there any psychologists near Logan Square?"*
- *"Where can I find a pharmacy near the Field Museum?"*
- *"Find an organization named Mercy"*
- *"What doctors work at Houston Methodist Hospital?"*

The agent interprets the query, calls the appropriate search tool(s), and returns formatted results.

## Project Structure

```
provider_directory_search/
├── README.md          # This file
├── pyproject.toml     # Project metadata & dependencies
├── requirements.txt   # Pip-installable dependency list
├── __init__.py        # Exports root_agent
├── agent.py           # ADK Agent definition (model, tools, instruction)
├── prompt.py          # System instruction / persona
├── tools.py           # Search tool functions exposed to the agent
└── data.py            # Synthetic provider directory dataset
```

## Data Model

The directory contains three entity types that are linked by ID-based relationships.

### Practitioners

Individual clinicians — physicians (MD/DO), nurse practitioners (NP), and physician assistants (PA-C).

| Field | Description |
|---|---|
| `npi` | Unique National Provider Identifier |
| `first_name`, `last_name`, `prefix` | Name (e.g. "Dr. Sarah Chen") |
| `credentials` | Degree / certification (e.g. "MD", "PsyD", "NP") |
| `specialty` | Primary specialty (e.g. "Cardiology") |
| `subspecialties` | List of subspecialties |
| `gender` | Male / Female |
| `languages` | Languages spoken |
| `phone`, `address` | Contact info with lat/lng coordinates |
| `accepting_new_patients` | Boolean |
| `telehealth_available` | Boolean |
| `organization_ids` | Affiliated organization IDs |
| `facility_ids` | Facilities where they practice |

### Facilities

Physical locations where care is delivered — hospitals, clinics, pharmacies, urgent care centers, etc.

| Field | Description |
|---|---|
| `id` / `npi` | Unique identifiers |
| `name` | Facility name |
| `type` | `hospital`, `clinic`, `pharmacy`, `urgent_care`, `community_health_center`, etc. |
| `organization_id` | Parent organization (nullable) |
| `address` | Street address with lat/lng |
| `services` | List of services offered (e.g. `emergency`, `pharmacy`, `laboratory`) |
| `hours` | Operating hours |

### Organizations

Parent entities that own or manage facilities — hospital systems, medical groups, specialty groups.

| Field | Description |
|---|---|
| `id` / `npi` | Unique identifiers |
| `name` | Organization name |
| `type` | `hospital_system`, `medical_group`, `community_health_center`, `specialty_group` |
| `address` | Headquarters address with lat/lng |
| `phone`, `website` | Contact info |

### Relationships

```
Organization  1──*  Facility  *──*  Practitioner
     │                                    │
     └──────────── * ─────────────────────┘
```

- A **practitioner** can belong to one or more **organizations** and practice at one or more **facilities**.
- A **facility** belongs to at most one **organization**.

## Search Tools

The agent has access to eight tools, each a Python function with typed parameters.

| Tool | What it does |
|---|---|
| `search_practitioners` | Filter practitioners by name, specialty, city, ZIP, new-patient status, telehealth, language, gender |
| `find_nearby_practitioners` | Geospatial search — find practitioners within N miles of a lat/lng point |
| `search_facilities` | Filter facilities by name, type, city, ZIP, service |
| `find_nearby_facilities` | Geospatial search — find facilities within N miles of a lat/lng point |
| `search_organizations` | Filter organizations by name, type, city |
| `get_provider_details` | Look up any entity (practitioner, facility, or org) by NPI |
| `find_practitioners_at_facility` | List all practitioners who practice at a named facility |
| `find_practitioners_in_organization` | List all practitioners affiliated with a named organization |

All text filters are case-insensitive substring matches. Multiple filters combine with AND logic. Geospatial search uses the [haversine formula](https://en.wikipedia.org/wiki/Haversine_formula) for distance.

## Dataset Coverage

The synthetic dataset covers two metro areas:

| Metro | Organizations | Facilities | Practitioners |
|---|---|---|---|
| Greater Houston, TX | 8 | 15 | 40 |
| Greater Chicago, IL | 3 | 8 | 10 |
| **Total** | **11** | **23** | **50** |

Specialties represented: Family Medicine, Internal Medicine, Cardiology, Orthopedic Surgery, Pediatrics, OB/GYN, Dermatology, Psychiatry, Psychology, Neurology, Endocrinology, Oncology, Pulmonology, Gastroenterology, Ophthalmology, Emergency Medicine.


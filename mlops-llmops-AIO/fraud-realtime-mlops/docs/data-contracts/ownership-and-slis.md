# Contract Ownership and SLIs

## Ownership model
- payment gateway team owns card authorization event production
- auth team owns login event production
- fraud platform owns feature request contract
- fraud analytics / model platform owns fraud outcome label contract

## Contract SLIs
### Availability
Can consumers parse and process events successfully?

### Freshness
Are events arriving within expected lateness bounds?

### Completeness
Are required fields present at expected rates?

### Validity
Do fields conform to enum/type/range constraints?

## Example SLOs
- card auth contract parse success: >= 99.99%
- fraud-critical required-field completeness: >= 99.95%
- online contract freshness lag: <= 60 sec p95
- label contract completeness by training cutoff: >= 98%

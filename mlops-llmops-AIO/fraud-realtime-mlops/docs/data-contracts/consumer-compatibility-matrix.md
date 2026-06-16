# Consumer Compatibility Matrix

| Contract | Producer | Primary Consumers | Compatibility Risk | Release Gate |
|---|---|---|---|---|
| `card_auth_event/v1` | payment gateway | stream enrichers, raw lake, replay tools | high | contract test + replay |
| `card_auth_event/v2` | payment gateway v2 | stream enrichers, feature pipelines, fraud scoring prep | critical | contract test + stage replay + shadow |
| `login_event/v1` | auth service | failed-login features, ATO scoring, fraud enrichers | medium | contract test + feature freshness check |
| `fraud_request_contract/v1` | feature assembly service | SageMaker fraud endpoint | critical | contract test + local smoke + replay |
| `fraud_outcome/v1` | chargeback/manual review systems | training label join, monitoring, backtests | critical | label completeness validation |

## Operating note
A contract with `critical` compatibility risk must have a named owner and explicit rollback plan for producer-side releases.

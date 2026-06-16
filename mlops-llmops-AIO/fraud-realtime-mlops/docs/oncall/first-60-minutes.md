# On-Call: First 60 Minutes for Fraud Serving Incidents

## 0-5 Minutes
- acknowledge page
- assign incident commander
- identify endpoint, region, environment, and blast radius
- freeze active releases if potentially related

## 5-15 Minutes
- gather metrics: 5xx, latency, invocation count, feature freshness, approval rate proxy
- determine whether issue is infra, feature, model, or threshold config
- open the most relevant runbook

## 15-30 Minutes
- execute mitigation: rollback, fallback mode, or capacity adjustment
- notify fraud ops of current operating mode
- record exact config/model versions involved

## 30-60 Minutes
- validate recovery against dashboards and queue depth
- ensure no hidden downstream backlog remains
- create incident follow-up issue with owner and next review time

# Cost semantics

The monitor keeps monetary categories separate:

| Category | Meaning |
| --- | --- |
| API_EQUIVALENT | Local estimate from reviewed public API rates |
| PROVIDER_REPORTED_USAGE_VALUE | Dollar-denominated quota value reported by a provider |
| BILLED | Authoritative invoice or billing evidence only |
| SUBSCRIPTION_FEE | Explicit fixed plan fee |
| UNKNOWN | Evidence is insufficient |

API-equivalent values are indicative estimates calculated from reviewed public API rates. They are not subscription charges or invoices.

Valuation quality is exact, bounded, estimated, or unknown. Missing pricing conditions never silently select a favorable rate. A defensible range is shown when two documented rates bound the result.

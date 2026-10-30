# Validation flow

This page describes the implemented processing sequence in the demo. It is a local file-processing workflow; it does not connect to a portal or external system.

## Process

```mermaid
flowchart TD
    A[Input Excel workbook] --> B[Locate header and read rows]
    B --> C[Normalise values where safe]
    C --> D[Required and field-level rules]
    D --> E[Cross-field consistency rules]
    E --> F[Duplicate supplier ID and PAN checks]
    F --> G[Accepted or rejected row result]
    G --> H[Results workbook]
    G --> I[Issue-level CSV]
    G --> J[Accepted-row CSV]
```

## Row decision

- A row with one or more **errors** is rejected.
- A row with warnings but no errors remains accepted and carries the warning into the report.
- A workbook-level structural problem, such as a missing required header or duplicate header, stops the run rather than producing misleading row results.

## Output handling

All output files are written to the chosen local output directory. The source workbook is read, not modified. The accepted-row CSV is an example export for a hypothetical next step; it is not transmitted to another system.

## Important boundary

The validator checks whether values conform to the demo's defined rules. It does not establish that a supplier, PAN or GSTIN is genuine, registered or authorised.

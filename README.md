# PostVerify NG | Built on Nigeria's Postcode (NDAPS)

**Instant Tier-3 Bank KYC, Electricity DisCo Customer Enumeration & Digital Proof-of-Address Infrastructure powered by the NIPOST Digital Postcode API (`api.postcode.gov.ng/v1`).**

Built for the **3MTT × NIPOST "Built on Nigeria's Postcode" Pitch Series**.

## Key Features
- **Live NIPOST NDAPS v1 Integration**: Real-time HTTP GET calls to `/v1/lookup` and `/v1/search/autocomplete` using `X-API-Key` and `X-Publishable-Key`.
- **5-Segment National Postcode Hierarchy Decoder**: Instant breakdown of the 11-character Nigerian Digital Alphanumeric Postcode (`State` → `LGA` → `Postcode District` → `Facility/Area` → `Building Unit`).
- **Interactive Leaflet Building Pin & Geofence Map**: Automatically flies to verified building coordinates and renders a 50m KYC geofence or flags 420km remote GPS spoofing attempts.
- **Official Printable Digital Proof-of-Address Certificate**: Generates a cryptographic SHA-256 verification ID (`PVNG-...`), dynamic verification QR code, and print-ready PDF layout.

## Deployment
- **Vercel**: Configured via `vercel.json`
- **Render**: Configured via `Procfile` and `render.yaml`

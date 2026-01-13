# RTR Endpoint Configuration

## Overview

The RTR system sends mitigation actions to the ePEM (Enhanced Policy Enforcement Manager) endpoint, which is automatically selected based on the `CURRENT_DOMAIN` environment variable.

## Environment Variables

### Required Variables

- **CURRENT_DOMAIN** - Specifies the active domain (Options: `CNIT` or `UPC`)
- **EPEM_CNIT** - ePEM endpoint URL for CNIT domain
- **EPEM_UPC** - ePEM endpoint URL for UPC domain
- **DOC_CNIT** - DOC endpoint URL for CNIT domain (used by ePEM configuration)
- **DOC_UPC** - DOC endpoint URL for UPC domain (used by ePEM configuration)

### Example Configuration

```env
CURRENT_DOMAIN = "CNIT"

# CNIT TESTBED
EPEM_CNIT = "http://192.168.130.233:5002"
DOC_CNIT = "http://192.168.130.62:8001"

# UPC TESTBED
EPEM_UPC = "http://10.19.2.20:5002"
DOC_UPC = "http://10.19.2.19:8001"
```

## Endpoint Selection Logic

The system automatically selects the ePEM endpoint based on `CURRENT_DOMAIN`:

1. If `CURRENT_DOMAIN = "CNIT"` → Uses `EPEM_CNIT`
2. If `CURRENT_DOMAIN = "UPC"` → Uses `EPEM_UPC`
3. If `CURRENT_DOMAIN` is not set → Defaults to `EPEM_CNIT`

## Mitigation Action Flow

```
┌─────────────┐
│  RTR API    │
└──────┬──────┘
       │
       │ 1. Create playbook
       │
       ▼
┌──────────────────┐
│ playbook_creator │
└──────┬───────────┘
       │
       │ 2. Send to ePEM
       │
       ▼
┌─────────────────┐
│  ePEM Endpoint  │ ◄── Selected based on CURRENT_DOMAIN
└──────┬──────────┘
       │
       │ 3. ePEM forwards to DOC
       │
       ▼
┌─────────────────┐
│  DOC (Domain    │
│  Orchestration  │
│  Controller)    │
└─────────────────┘
```

## Status Codes

The system tracks different status codes based on ePEM responses:

### Success States
- **sent_to_epem** - Successfully sent to ePEM (200, 201, 202)
  - HTTP 200: Action processed and sent to DOC
  - HTTP 201: Action created at ePEM
  - HTTP 202: Action accepted and queued

### Error States
- **epem_rejected** - ePEM rejected the request (HTTP 400)
- **epem_unauthorized** - Authentication failed (HTTP 401)
- **epem_not_found** - Endpoint not found (HTTP 404)
- **epem_server_error** - ePEM server error (HTTP 5xx)
- **epem_unexpected_response** - Unexpected response code
- **epem_timeout** - Request timed out after 10 seconds
- **epem_connection_error** - Failed to connect to ePEM
- **epem_error** - General error during sending

## API Startup Configuration

During startup, the RTR API automatically configures the ePEM endpoint with the DOC information:

```python
@rtr_api.on_event("startup")
async def startup_event():
    # Loads configuration
    config_loader = get_config_loader()
    
    # Configures ePEM with DOC endpoint info
    configure_epem_doc_endpoint()
```

This ensures ePEM knows where to forward mitigation actions for enforcement.

## Switching Domains

To switch between CNIT and UPC domains:

1. Update the `.env` file:
   ```env
   CURRENT_DOMAIN = "UPC"  # Change from "CNIT" to "UPC"
   ```

2. Restart the Docker container:
   ```bash
   docker-compose restart rtr-api
   ```

3. Or reload via API (doesn't change CURRENT_DOMAIN, only reloads action mappings):
   ```bash
   curl -X POST "http://localhost:8000/api/reload-config" \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Multidomain Actions

When a mitigation action includes multiple domains in `target_domain` (e.g., `["CNIT", "UPC"]`), the system:

1. Logs all involved domains
2. Sends the action to the ePEM endpoint for the current domain
3. ePEM coordinates the multidomain mitigation

Example log output:
```
Multidomain mitigation action detected for domains: ['CNIT', 'UPC']
 - Domain involved: CNIT
 - Domain involved: UPC
Sending request to ePEM endpoint: http://192.168.130.233:5002/v2/horse/rtr_request
```

## Troubleshooting

### ePEM Not Responding

If ePEM is not available, you'll see error status:
- **epem_timeout** or **epem_connection_error**

**Solution:** 
1. Check ePEM service is running
2. Verify network connectivity
3. Check the endpoint URL in `.env` is correct

### Wrong Endpoint Selected

If the wrong ePEM is being used:

1. Check `CURRENT_DOMAIN` in `.env`
2. Verify the correct `EPEM_CNIT` or `EPEM_UPC` URL
3. Restart the container to apply changes

### Authentication Errors (401)

If you get `epem_unauthorized`:

1. Check ePEM authentication requirements
2. Verify credentials if required
3. Contact ePEM administrator

## Implementation Files

- **mitigation_regex_control.py** - Implements endpoint selection and sending logic
- **IBI-RTR_api.py** - Handles API startup and ePEM configuration
- **.env** - Contains endpoint configuration
- **docker-compose.yml** - Passes environment variables to container

## Related Documentation

- [RTR Configuration System](./README.md) - Action mapping configuration
- [Docker Compose Configuration](../docker-compose.yml) - Container setup

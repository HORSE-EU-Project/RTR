# RTR Configuration System

This directory contains configuration files for the RTR (Reliability, Trustworthiness & Resilience) system.

## Configuration Files

### mitigation_ansible_map.json

Maps mitigation action names to their corresponding Ansible playbook paths.

**Structure:**
```json
{
  "action_name_to_playbook": {
    "ACTION_NAME": "path/to/playbook.yaml",
    ...
  },
  "metadata": {
    "version": "1.0",
    "description": "Mapping description",
    "last_updated": "YYYY-MM-DD"
  }
}
```

**Supported Action Names:**
- `DNS_RATE_LIMIT` / `DNS_RATE_LIMITING` - DNS rate limiting
- `DNS_SERV_DISABLE` / `DNS_SERVICE_DISABLE` - Disable DNS service
- `DNS_SERV_ENABLE` - Enable DNS service
- `DNS_SERVICE_HANDOVER` - DNS service handover
- `DNS_FIREWALL_SPOOFING_DETECTION` - DNS firewall spoofing detection
- `BLOCK_POD_ADDRESS` / `BLOCK_POD_ADDRESSES` / `BLOCK_IP_ADDRESSES` - Block IP addresses
- `API_RATE_LIMITING` / `API_RATE_LIMIT` - API rate limiting
- `BLOCK_UES_MULTIDOMAIN` - Block UEs in multidomain scenarios
- `TEST` / `TEST_2` - Test playbooks

## Usage

### Loading Configuration at Startup

The configuration is automatically loaded when the RTR API starts:

```python
from config_loader import get_config_loader

config_loader = get_config_loader()
mappings = config_loader.get_all_action_mappings()
```

### Getting Playbook for an Action

```python
from config_loader import get_playbook_for_action

try:
    playbook_path = get_playbook_for_action("DNS_RATE_LIMIT")
    print(f"Playbook: {playbook_path}")
except ValueError as e:
    print(f"Error: {e}")
```

### Reloading Configuration (Without Restarting Docker)

You can reload the configuration dynamically using the API endpoint:

**Endpoint:** `POST /api/reload-config`

**Authentication:** Required (Bearer token)

**Example using curl:**
```bash
curl -X POST "http://localhost:8000/api/reload-config" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Example Response:**
```json
{
  "status": "success",
  "message": "Configurations reloaded successfully",
  "mitigation_ansible_map": {
    "previous_count": 15,
    "current_count": 15,
    "actions": ["DNS_RATE_LIMIT", "DNS_SERV_DISABLE", ...]
  }
}
```

### Viewing Current Action Mappings

**Endpoint:** `GET /api/config/actions`

**Authentication:** Required (Bearer token)

**Example using curl:**
```bash
curl -X GET "http://localhost:8000/api/config/actions" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Example Response:**
```json
{
  "total_mappings": 15,
  "action_mappings": {
    "DNS_RATE_LIMIT": "ansible_playbooks/dns_rate_limiting.yaml",
    "DNS_SERV_DISABLE": "ansible_playbooks/dns_service_disable.yaml",
    ...
  }
}
```

## Adding New Action Mappings

1. Edit `mitigation_ansible_map.json` in this directory
2. Add your new action mapping to the `action_name_to_playbook` object:
   ```json
   "NEW_ACTION_NAME": "ansible_playbooks/your_playbook.yaml"
   ```
3. Update the `last_updated` field in `metadata`
4. Reload the configuration using the API endpoint (or restart the container)

**Note:** Action names are case-insensitive. They will be automatically converted to uppercase.

## Error Handling

When an action name is not found in the configuration:

- **ValueError** is raised with a detailed message listing all available actions
- API returns **HTTP 404** with error details
- The error message includes all supported action names for easy troubleshooting

Example error message:
```
No playbook mapping found for action 'INVALID_ACTION'. 
Available actions (case insensitive): API_RATE_LIMIT, API_RATE_LIMITING, 
BLOCK_IP_ADDRESSES, BLOCK_POD_ADDRESS, ...
```

## Configuration Loader Module

The `config_loader.py` module provides:

- **ConfigLoader**: Singleton class managing all configurations
- **get_config_loader()**: Get the singleton instance
- **get_playbook_for_action(action_name)**: Look up playbook path by action name
- **reload_configurations()**: Reload all configuration files

### Thread Safety

The ConfigLoader uses thread locking to ensure thread-safe singleton initialization and configuration reloading in concurrent environments.

## Best Practices

1. **Always validate changes** - Test new action mappings in a development environment first
2. **Keep metadata updated** - Update version and last_updated fields when modifying the config
3. **Use consistent naming** - Follow the existing naming convention (UPPERCASE_WITH_UNDERSCORES)
4. **Document changes** - Add comments in commits explaining why mappings were added/changed
5. **Reload after changes** - Use the reload endpoint to apply changes without downtime

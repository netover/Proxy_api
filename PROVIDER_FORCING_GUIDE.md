# Provider Activation/Deactivation and Forcing Guide

## Overview
This guide documents the new provider activation/deactivation and "Force this" functionality implemented in the LLM Proxy API system.

## Features Added

### 1. Provider Activation/Deactivation
- **Enabled Toggle**: Each provider can be individually enabled or disabled
- **Configuration Preservation**: Disabled providers retain their configuration but are not used for requests
- **Automatic Cleanup**: When a forced provider is disabled, its forced status is automatically removed

### 2. Force Provider Functionality
- **Exclusive Routing**: When a provider is marked as "forced", all requests use that provider exclusively
- **Bypass Logic**: Forced providers bypass normal priority-based selection and health checks
- **Single Provider Limit**: Only one provider can be forced at a time (enforced by validation)

## Backend Changes

### Configuration Schema
```yaml
providers:
  - name: "openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models: ["gpt-3.5-turbo", "gpt-4"]
    enabled: true          # New field
    forced: false          # New field
    priority: 1
    timeout: 30
```

### API Endpoints Updated
- `/v1/models` - Now includes `enabled` and `forced` fields
- `/health` - Now includes `enabled` and `forced` fields in provider details
- `/providers` - Now includes `enabled` and `forced` fields
- `/metrics` - Now includes `enabled` and `forced` fields

### Routing Logic
The request routing now follows this priority:
1. **Check for forced provider**: If a provider is forced and supports the model, use it exclusively
2. **Normal selection**: If no forced provider, use enabled providers sorted by priority
3. **Health checks**: Forced providers bypass health checks, others must be healthy/degraded

## Frontend Changes

### Configuration Interface
- **Enabled Toggle**: Checkbox to enable/disable each provider
- **Force Radio Button**: Radio button to select which provider to force
- **Tooltips**: Hover tooltips explain the functionality
- **Visual Indicators**: 
  - Forced providers have a blue border
  - Disabled providers are grayed out
  - Forced providers show "[FORCED]" in dashboard

### Dashboard Updates
- Provider status cards now show forced status
- Visual indicators for enabled/disabled state

## Usage Examples

### Configuration File
```yaml
providers:
  - name: "openai"
    type: "openai"
    api_key_env: "OPENAI_API_KEY"
    base_url: "https://api.openai.com/v1"
    models: ["gpt-3.5-turbo", "gpt-4"]
    enabled: true
    forced: true  # This will be the only provider used
    priority: 1
  
  - name: "anthropic"
    type: "anthropic"
    api_key_env: "ANTHROPIC_API_KEY"
    base_url: "https://api.anthropic.com"
    models: ["claude-3-haiku"]
    enabled: true
    forced: false
    priority: 2
```

### API Usage
```bash
# Get provider status including forced/enabled
curl -H "X-API-Key: your-key" http://localhost:8000/v1/providers

# Response includes:
# {
#   "providers": [
#     {
#       "name": "openai",
#       "type": "openai",
#       "enabled": true,
#       "forced": true,
#       "models": ["gpt-3.5-turbo", "gpt-4"],
#       ...
#     }
#   ]
# }
```

## Validation Rules

1. **Forced Provider Uniqueness**: Only one provider can have `forced: true`
2. **Enabled Constraint**: Forced providers must also be enabled
3. **Auto-cleanup**: Disabling a forced provider automatically unsets the forced flag
4. **Model Support**: Forced providers must support the requested model

## Testing

Run the comprehensive test suite:
```bash
python test_provider_forcing.py
```

The test covers:
- Configuration loading with new fields
- Setting and unsetting forced providers
- Provider activation/deactivation
- Validation rules
- Routing behavior with forced providers

## Migration

Existing configurations will automatically work as:
- `enabled` defaults to `true` for backward compatibility
- `forced` defaults to `false` for backward compatibility
- No breaking changes to existing API responses

## Security Considerations

- Forced providers still require valid API keys
- Configuration changes require authentication
- No additional security risks introduced

## Performance Impact

- **Minimal**: Forced provider check adds negligible latency
- **Caching**: Provider selection results are cached
- **Bypass**: Forced providers skip health checks for better performance
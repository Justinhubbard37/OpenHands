# OpenHands Repository Skills

## Project Structure

- `openhands/app_server/` - App Server API endpoints and services
- `openhands/app_server/app_conversation/` - Conversation management services
  - `app_conversation_models.py` - Pydantic models for conversations
  - `live_status_app_conversation_service.py` - Main service for conversation lifecycle
  - `app_conversation_router.py` - FastAPI router for conversation endpoints
- `tests/unit/app_server/` - Unit tests for app server components

## SDK Dependencies

The project uses three SDK packages from `software-agent-sdk`:
- `openhands-sdk` - Core SDK functionality
- `openhands-agent-server` - Agent server models and client
- `openhands-tools` - Tool definitions

To test against an unmerged SDK PR:
1. Update `pyproject.toml` to use git-based dependencies with the PR commit SHA
2. Run `poetry lock` and `poetry install`

Example:
```toml
openhands-sdk = { git = "https://github.com/OpenHands/software-agent-sdk.git", subdirectory = "openhands-sdk", rev = "<commit-sha>" }
```

## Key Models

- `PluginSpec` - Specification for loading plugins (source, ref, parameters)
- `AppConversationStartRequest` - Request to start a new conversation
- `StartConversationRequest` - SDK model passed to agent server

## Testing

Run tests with:
```bash
poetry run python -m pytest tests/unit/app_server/ -v
```

# TODO: Implement Config Attribute in main.py

## Tasks
- [x] Change all `app.state.config` references to `app.config` for consistency
- [x] Remove `hasattr(app.state, 'config')` checks since config is guaranteed in lifespan
- [x] Update health_check endpoint to use app.config
- [x] Update list_providers endpoint to use app.config
- [x] Update chat_completions endpoint to use app.config
- [x] Update completions endpoint to use app.config
- [x] Update embeddings endpoint to use app.config
- [x] Update list_models endpoint to use app.config
- [x] Test the changes to ensure config is properly accessible

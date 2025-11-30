# Production Configuration

## Claude Models - Production IDs

This application uses **production-ready model IDs with exact snapshot dates** as recommended by Anthropic documentation.

### Current Models (Nov 2025)

#### Active Models:
1. **Claude Sonnet 4.5** - `claude-sonnet-4-5-20250929`
   - Release: Sept 29, 2025
   - Best for: Coding, agents, orchestration
   - Context: 200K (1M preview)
   - Default model

2. **Claude Haiku 4.5** - `claude-haiku-4-5-20251015`
   - Release: Oct 15, 2025
   - Best for: Fast execution, sub-agents
   - Performance: 90% of Sonnet at 20% cost
   - Context: 200K

3. **Claude Opus 4.1** - `claude-opus-4-1-20250805`
   - Release: Aug 2025
   - Best for: Deep thinking, code review
   - Use case: Safety net for critical reviews
   - Context: 200K

4. **Legacy Models**: Claude 4, Claude 3.7, Claude 3.5, Claude 3 Haiku

### Why Snapshot IDs?

Per Anthropic documentation:
- ✅ **Production**: Use exact snapshots (e.g., `claude-sonnet-4-5-20250929`)
- ⚠️ **Development**: Aliases work but auto-update (e.g., `claude-sonnet-4-5`)

**Reason**: Aliases migrate to newest snapshots within ~1 week of new releases, which can cause unexpected behavior changes in production.

### Model Selection Strategy

#### For DevOps Agent Tasks:
1. **Complex orchestration**: Sonnet 4.5 (main orchestrator)
2. **Fast parallel execution**: Haiku 4.5 (sub-agents)
3. **Critical review**: Opus 4.1 (final validation)

#### Cost Optimization:
- Sonnet 4.5: $3/$15 per 1M tokens
- Haiku 4.5: $1/$5 per 1M tokens (80% cheaper)
- Use Haiku for simple tasks, Sonnet for complex ones

### Configuration Files

#### Frontend:
`apps/frontend/src/components/AgentChatManus.tsx`
```typescript
const [selectedModel, setSelectedModel] = useState('claude-sonnet-4-5-20250929')
```

#### Backend:
`apps/backend-python/app/config.py`
```python
CLAUDE_MODEL: str = "claude-sonnet-4-5-20250929"
```

### Future Updates

When new model snapshots are released:
1. Test with new snapshot ID
2. Update config files
3. Update this documentation
4. Deploy with exact dates

### References
- [Claude Models Overview](https://platform.claude.com/docs/en/about-claude/models/overview)
- [Migration Guide](https://platform.claude.com/docs/en/about-claude/models/migrating-to-claude-4)

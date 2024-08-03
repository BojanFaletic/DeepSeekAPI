from openai.types.completion import CompletionUsage

class DS_CompletionUsage(CompletionUsage):
    prompt_cache_hit_tokens : int
    """Number of tokens in the prompt that were served from the cache."""

    prompt_cache_miss_tokens : int
    """Number of tokens in the prompt that were not served from the cache."""
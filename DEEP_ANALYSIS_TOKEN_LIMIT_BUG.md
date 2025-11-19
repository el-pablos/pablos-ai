# Deep Analysis: Token Limit Bug Causing Null Content Responses

## Executive Summary

The chatbot was experiencing consistent failures when responding to certain user messages, particularly "lu bisa apa aja sebagai chatbot?" and requests to count from 1 to 1 million. The root cause was identified as an API bug in the MegaLLM service where hitting the token limit causes the API to return `null` content instead of truncated text.

## Problem Description

### Symptoms
- Bot responds with error message: "Waduh, gue lagi error nih. Coba lagi ya! 😅"
- Errors occur on specific types of requests that generate longer responses
- Pattern shows consistent failures on the same user queries

### Error Logs
```
2025-11-19 21:42:29,926 - WARNING - API hit token limit and returned null content
2025-11-19 21:42:29,927 - WARNING - Content is None or empty from primary
2025-11-19 21:42:29,927 - ERROR - Unexpected response format or null content from primary
Full response: {
  'id': '', 
  'object': 'chat.completion', 
  'created': 1763588549, 
  'model': 'openai-gpt-oss-20b', 
  'choices': [{
    'index': 0, 
    'message': {'role': 'assistant', 'content': None}, 
    'finish_reason': 'length'
  }], 
  'usage': {
    'completion_tokens': 399, 
    'prompt_tokens': 785, 
    'total_tokens': 1184
  }
}
```

## Root Cause Analysis

### Key Findings

1. **Token Limit Too Low**: `MAX_TOKENS` was set to 400, which is insufficient for many responses

2. **API Bug**: The MegaLLM API has a bug where:
   - When generation hits the token limit (`finish_reason: 'length'`)
   - It returns `completion_tokens: 399` (one less than the limit)
   - **Instead of returning the truncated text, it returns `content: null`**
   - This is non-standard behavior - OpenAI's API returns truncated content

3. **Consistent Pattern**: Analysis of multiple failed requests shows:
   ```
   Request 1: completion_tokens: 399, content: null, finish_reason: 'length'
   Request 2: completion_tokens: 399, content: null, finish_reason: 'length'
   Request 3: completion_tokens: 399, content: null, finish_reason: 'length'
   ```
   All failures show exactly 399 tokens generated with null content.

4. **Prompt Length Correlation**: Failed requests had varying prompt lengths:
   - 785 tokens → 399 completion tokens → FAIL
   - 792 tokens → 399 completion tokens → FAIL
   - 849 tokens → 399 completion tokens → FAIL
   - 995 tokens → 399 completion tokens → FAIL
   
   The API consistently generates up to the limit and then returns null.

### Why Certain Requests Failed

**"lu bisa apa aja sebagai chatbot?"** - This question asks the bot to list its capabilities, which naturally generates a long, detailed response that exceeds 400 tokens.

**"coba 1 - 1juta bisa?"** - Asking to count to 1 million would generate an extremely long response, immediately hitting the token limit.

## Solution Implemented

### Primary Fix: Increase MAX_TOKENS

Changed `.env` configuration:
```diff
- MAX_TOKENS=400
+ MAX_TOKENS=1500
```

**Rationale:**
- 400 tokens ≈ 300 words (too short for detailed responses)
- 1500 tokens ≈ 1125 words (sufficient for most conversational responses)
- Provides 3.75x more room for generation
- Reduces likelihood of hitting the limit
- Still reasonable for API costs and response times

### Why This Fixes the Issue

1. **More Generation Room**: With 1500 tokens, the API can generate complete responses without hitting the limit
2. **Avoids API Bug**: By not hitting the token limit, we avoid triggering the null content bug
3. **Better User Experience**: Users get complete, coherent responses instead of errors
4. **Handles Edge Cases**: Even for longer responses, the bot has room to generate meaningful content

### Alternative Solutions Considered

1. **Retry with Shorter Prompt**: Could truncate conversation history when hitting limit
   - Rejected: Loses context, complex to implement
   
2. **Fallback Response**: Return a generic message when hitting limit
   - Rejected: Poor user experience, doesn't solve the problem

3. **Multiple Chunks**: Split long responses into multiple messages
   - Rejected: API returns null, so there's no content to split

4. **Contact API Provider**: Report the bug to MegaLLM
   - Recommended: Should still be done, but need immediate fix

## Testing Plan

1. **Restart the bot** with new MAX_TOKENS setting
2. **Test previously failing queries**:
   - "lu bisa apa aja sebagai chatbot?"
   - "coba 1 - 1juta bisa?"
   - Other queries that generated long responses
3. **Monitor logs** for:
   - No more `completion_tokens: 399` with null content
   - Successful responses with varying token counts
   - `finish_reason: 'stop'` instead of `'length'`
4. **Verify response quality**: Ensure responses are complete and coherent

## Expected Outcomes

- ✅ No more null content errors
- ✅ Complete responses to capability questions
- ✅ Better handling of requests that generate longer responses
- ✅ Improved user experience with fewer error messages

## Monitoring

After deployment, monitor for:
1. **Token usage patterns**: Check if 1500 is sufficient or needs adjustment
2. **API costs**: Higher max_tokens may increase costs slightly
3. **Response times**: Longer generation may take more time
4. **Finish reasons**: Should see more `'stop'` and fewer `'length'`

## Long-term Recommendations

1. **Report API Bug**: Contact MegaLLM support about null content on token limit
2. **Dynamic Token Adjustment**: Consider adjusting max_tokens based on prompt length
3. **Response Streaming**: Implement streaming for very long responses
4. **Conversation Pruning**: Automatically trim old messages when context gets too long

## Files Changed

- `.env`: Increased MAX_TOKENS from 400 to 1500

## Related Issues

- FIX_ALTERNATING_ERROR_PATTERN.md: History management fix
- Previous null content handling improvements in app/ai_client.py


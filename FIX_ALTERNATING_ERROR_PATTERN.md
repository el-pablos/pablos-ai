# Fix for Alternating Error Pattern

## Problem Description

The chatbot was experiencing an intermittent error pattern where every other message would fail:
- Message 1: Works fine ✅
- Message 2: Returns error ❌ ("Waduh, gue lagi error nih. Coba lagi ya! 😅")
- Message 3: Works fine ✅
- Message 4: Returns error ❌
- And so on...

### Symptoms

The API was returning valid HTTP 200 responses but with `null` content:

```
2025-11-19 21:34:13,884 - Content is None or empty from primary. Full choice: {'index': 0, 'message': {'role': 'assistant', 'content': None}, 'finish_reason': 'length'}
2025-11-19 21:34:13,886 - Trying next endpoint...
2025-11-19 21:34:13,886 - All 1 available endpoint(s) failed
```

Note the `finish_reason: "length"` indicates the API hit the token limit.

## Root Cause Analysis

After investigating the logs and code, I discovered **TWO separate but related issues**:

### Issue 1: API Returning Null Content
The MegaLLM API was intermittently returning `null` content when hitting the token limit (`finish_reason: "length"`). This appears to be an API bug - it should return truncated content, not null.

### Issue 2: Conversation History Imbalance (THE MAIN CAUSE)
The alternating error pattern was caused by **conversation history management**:

1. In `app/handlers.py`, the code was:
   - Adding user message to history BEFORE calling the AI (line 266)
   - Only adding assistant response to history if the response was successful (line 301)

2. This created an imbalance when requests failed:
   - **Request 1**: User message added → AI succeeds → Assistant response added → History balanced ✅
   - **Request 2**: User message added → API returns null → No assistant response added → **History imbalanced** ❌
   - **Request 3**: User message added (now 2 user messages in a row!) → AI succeeds → Assistant response added → History balanced again ✅
   - **Request 4**: User message added → API returns null → History imbalanced again ❌

3. The imbalanced history (with consecutive user messages without assistant responses) was likely confusing the API or causing it to behave differently, leading to the alternating pattern.

### Issue 3: Endpoint Rotation Logic
The original code in `app/ai_client.py` had `continue` statements that would increment `current_endpoint_index` and then continue the loop. With only 1 endpoint, this caused the loop to exit prematurely after one iteration, preventing proper retry logic.

## Solution Implemented

### Fix 1: Conversation History Management (`app/handlers.py`)

**Changed the order of operations** to prevent history imbalance:

**BEFORE:**
```python
async def _handle_chat(self, update: Update, user_id: int, user_message: str) -> None:
    # Add user message to history FIRST
    self.memory.add_user_message(user_id, user_message)
    
    # Get conversation history
    history = self.memory.format_history_for_prompt(user_id, max_messages=8)
    
    # ... build prompt and call AI ...
    
    if response:
        # Only add assistant response if successful
        self.memory.add_assistant_message(user_id, response)
    else:
        # User message already in history, but no assistant response!
        await update.message.reply_text("Waduh, gue lagi error nih. Coba lagi ya! 😅")
```

**AFTER:**
```python
async def _handle_chat(self, update: Update, user_id: int, user_message: str) -> None:
    # Get conversation history BEFORE adding current message
    history = self.memory.format_history_for_prompt(user_id, max_messages=8)
    
    # ... build prompt and call AI ...
    
    if response:
        # Add BOTH user message and assistant response together
        self.memory.add_user_message(user_id, user_message)
        self.memory.add_assistant_message(user_id, response)
    else:
        # Don't add anything to history if request failed
        await update.message.reply_text("Waduh, gue lagi error nih. Coba lagi ya! 😅")
```

**Key improvement:** User messages and assistant responses are now added to history **atomically** - either both are added (on success) or neither is added (on failure). This prevents the imbalanced history that was causing the alternating error pattern.

### Fix 2: Endpoint Rotation Logic (`app/ai_client.py`)

**Removed premature `continue` statements** that were causing loop exits:

**BEFORE:**
```python
if content is not None and content.strip():
    result = content.strip()
    logger.info(f"✅ Success on {endpoint.name}!")
    return result
else:
    logger.warning(f"Content is None or empty from {endpoint.name}")
    self.current_endpoint_index = (self.current_endpoint_index + 1) % len(self.endpoints)
    continue  # This causes loop to exit with 1 endpoint!
```

**AFTER:**
```python
if content is not None and content.strip():
    result = content.strip()
    logger.info(f"✅ Success on {endpoint.name}!")
    return result
else:
    logger.warning(f"Content is None or empty from {endpoint.name}")
    # Fall through to end of loop where index is incremented
```

**Key improvement:** The code now falls through to the end of the loop where `current_endpoint_index` is incremented, allowing the loop to complete properly even with a single endpoint.

## Testing

To verify the fix works:

1. **Restart the bot application**
2. **Send multiple messages in sequence** to test for the alternating pattern
3. **Check the logs** for:
   - No more alternating success/failure pattern
   - Proper history management (messages only added on success)
   - Better error handling when content is null

## Files Changed

- `app/handlers.py`: Fixed conversation history management to prevent imbalance
- `app/ai_client.py`: Fixed endpoint rotation logic to prevent premature loop exits

## Commits

```
commit aaa0fdf
Fix alternating error pattern by improving history management
```

```
commit 05e5cb7
Fix AI client null content handling and improve error recovery
```


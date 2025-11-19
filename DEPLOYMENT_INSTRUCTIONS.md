# Deployment Instructions - Critical Bug Fix

## 🚨 CRITICAL: Manual Configuration Update Required

The fix for the null content bug requires you to **manually update your `.env` file** on the server.

### Step 1: Update .env File

SSH into your server and edit the `.env` file:

```bash
nano .env
```

Find this line:
```
MAX_TOKENS=400
```

Change it to:
```
MAX_TOKENS=1500
```

Save and exit (Ctrl+X, then Y, then Enter).

### Step 2: Restart the Bot

After updating `.env`, restart the bot to apply the changes:

```bash
# If using PM2:
pm2 restart pablos-ai

# If running directly:
# Stop the current process (Ctrl+C) and restart:
python3 -m app.main
```

### Step 3: Verify the Fix

Test the bot with previously failing queries:

1. Send: **"lu bisa apa aja sebagai chatbot?"**
   - Should now get a complete response listing capabilities
   - No more error messages

2. Send: **"coba 1 - 1juta bisa?"**
   - Should get a response (though it won't actually count to 1 million)
   - No more error messages

3. Monitor the logs:
   ```bash
   tail -f pablos_bot.log
   ```
   
   Look for:
   - ✅ `✅ Success on primary!` messages
   - ✅ `finish_reason: 'stop'` instead of `'length'`
   - ✅ No more `Content is None or empty` warnings
   - ✅ No more `completion_tokens: 399` with null content

## What Was Fixed

### The Problem
The MegaLLM API has a bug where it returns `null` content when hitting the token limit, instead of returning truncated text like standard OpenAI-compatible APIs.

**Symptoms:**
- Bot responded with: "Waduh, gue lagi error nih. Coba lagi ya! 😅"
- Errors on queries that generate longer responses
- Logs showed: `completion_tokens: 399, content: null, finish_reason: 'length'`

### The Solution
Increased `MAX_TOKENS` from 400 to 1500:
- 400 tokens ≈ 300 words (too short)
- 1500 tokens ≈ 1125 words (sufficient for detailed responses)
- Provides 3.75x more room for generation
- Avoids hitting the limit and triggering the API bug

### Why This Works
By increasing the token limit, the API can generate complete responses without hitting the limit. This avoids triggering the bug where the API returns null content.

## Files Changed (Already Pushed to GitHub)

✅ **Commit b61a300**: "Fix null content bug by increasing MAX_TOKENS from 400 to 1500"
- `.env.example`: Updated with new MAX_TOKENS value and comments
- `DEEP_ANALYSIS_TOKEN_LIMIT_BUG.md`: Comprehensive analysis document
- `FIX_ALTERNATING_ERROR_PATTERN.md`: Previous fix documentation

✅ **Commit aaa0fdf**: "Fix alternating error pattern by improving history management"
- `app/handlers.py`: Fixed conversation history management
- `app/ai_client.py`: Fixed endpoint rotation logic

## Expected Results

After deploying this fix:

1. **No more null content errors** - The bot should handle all queries successfully
2. **Complete responses** - Users get full, coherent answers instead of errors
3. **Better user experience** - Fewer "Waduh, gue lagi error nih" messages
4. **Stable operation** - No more alternating success/failure patterns

## Monitoring

After deployment, check the logs for:

```bash
# Check for successful responses
tail -100 pablos_bot.log | grep "✅ Success"

# Check for any remaining errors
tail -100 pablos_bot.log | grep "ERROR"

# Check token usage patterns
tail -100 pablos_bot.log | grep "completion_tokens"
```

## Troubleshooting

If you still see errors after updating:

1. **Verify .env was updated**: `cat .env | grep MAX_TOKENS`
   - Should show: `MAX_TOKENS=1500`

2. **Verify bot restarted**: Check the logs for startup messages
   - Should show: `Max tokens: 1500`

3. **Check for other issues**: Look at the full error logs
   - `tail -200 pablos_bot.log`

## Support

If issues persist after following these steps, check:
- `DEEP_ANALYSIS_TOKEN_LIMIT_BUG.md` for detailed analysis
- `FIX_ALTERNATING_ERROR_PATTERN.md` for history management fix details
- Application logs for specific error messages

## Summary

✅ **Code changes**: Already pushed to GitHub (commits b61a300 and aaa0fdf)
⚠️ **Manual action required**: Update `.env` file with `MAX_TOKENS=1500`
🔄 **Restart required**: Restart the bot after updating `.env`
✅ **Testing**: Verify with previously failing queries
📊 **Monitoring**: Check logs for successful responses


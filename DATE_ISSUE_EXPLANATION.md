# Why Hardcoded Dates Cause Problems

## The IMAP "SINCE" Search

When the script searches Gmail, it uses IMAP's `SINCE` command:
```python
criteria = ["SINCE", SINCE_DATE]  # e.g., ["SINCE", "31-Dec-2024"]
```

**IMAP `SINCE` means: "Find emails on or AFTER this date"**

## Example Scenarios

### Scenario 1: Hardcoded Date in the Past
```python
# Original code (example)
SINCE_DATE = "31-Dec-2024"  # Hardcoded date
```

**What happens:**
- ✅ **Dec 31, 2024**: Script runs, searches for emails since Dec 31, 2024 → Works fine
- ✅ **Jan 1, 2025**: Script runs, searches for emails since Dec 31, 2024 → Still works! Finds emails from Jan 1
- ✅ **Jan 15, 2025**: Script runs, searches for emails since Dec 31, 2024 → Still works, but...

**The Problem:**
- The script searches through **ALL emails from Dec 31, 2024 to today**
- As time passes, it searches through MORE and MORE emails (inefficient)
- After 30+ days, it's searching through thousands of old emails unnecessarily
- **Performance degrades over time**

### Scenario 2: Hardcoded Date Too Old
```python
SINCE_DATE = "01-Jan-2024"  # Very old date
```

**What happens:**
- Script searches through **an entire year of emails** every time it runs
- Very slow, may hit Gmail rate limits
- Unnecessary processing

### Scenario 3: Hardcoded Date in the Future (Worst Case)
```python
SINCE_DATE = "28-Jul-2025"  # Future date
```

**What happens:**
- If today is Jan 15, 2025, it searches for emails since July 28, 2025
- **Finds ZERO emails** because that date hasn't happened yet
- Script appears to work but downloads nothing

## Why It "Stopped Working" After Dec 31

The most likely scenarios:

### Theory 1: Date Was Set to Future Date
If the code had:
```python
SINCE_DATE = "31-Dec-2024"  # or similar
```
And someone manually changed it to:
```python
SINCE_DATE = "01-Jan-2025"  # thinking it needed updating
```
But if today was still Dec 31, 2024, it would search for future emails and find nothing.

### Theory 2: Year Rollover Bug
Some date parsing might have issues with year changes:
- Date format: `"31-Dec-2024"` 
- When year changes to 2025, parsing might fail
- Or the date comparison logic might break

### Theory 3: Manual Update Required
The most common issue:
- Date was hardcoded to something like `"15-Dec-2024"`
- After Dec 31, the script still worked but was inefficient
- Someone noticed it wasn't finding recent emails
- Realized the date needed manual updating
- **This is a maintenance burden**

## The Solution: Dynamic Date

### Before (Hardcoded - BAD):
```python
SINCE_DATE = "31-Dec-2024"  # ❌ Never changes, needs manual updates
```

### After (Dynamic - GOOD):
```python
# Always looks back 30 days from TODAY
days_back = 30
default_since = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")
SINCE_DATE = os.getenv("IMAP_SINCE", default_since)
```

**What this does:**
- ✅ **Jan 1, 2025**: Searches since Dec 2, 2024 (30 days back)
- ✅ **Jan 15, 2025**: Searches since Dec 16, 2024 (30 days back)
- ✅ **Feb 1, 2025**: Searches since Jan 2, 2025 (30 days back)
- ✅ **Always current** - no manual updates needed
- ✅ **Efficient** - only searches last 30 days

## Real-World Example

### Timeline with Hardcoded Date:
```
Dec 15, 2024: SINCE_DATE = "15-Nov-2024" → Searches 30 days ✅
Dec 31, 2024: SINCE_DATE = "15-Nov-2024" → Searches 46 days ⚠️ (slower)
Jan 15, 2025: SINCE_DATE = "15-Nov-2024" → Searches 61 days ❌ (very slow)
Feb 1, 2025:  SINCE_DATE = "15-Nov-2024" → Searches 78 days ❌ (too slow, may fail)
```

### Timeline with Dynamic Date:
```
Dec 15, 2024: Searches since Nov 15, 2024 (30 days) ✅
Dec 31, 2024: Searches since Dec 1, 2024 (30 days) ✅
Jan 15, 2025: Searches since Dec 16, 2024 (30 days) ✅
Feb 1, 2025:  Searches since Jan 2, 2025 (30 days) ✅
```

## Why This Matters

1. **Performance**: Searching 30 days is fast, searching 6 months is slow
2. **Reliability**: Less likely to hit Gmail rate limits
3. **Maintenance**: No manual date updates required
4. **Correctness**: Always gets recent emails, never misses new ones

## Bottom Line

The hardcoded date didn't necessarily "break" after Dec 31, but it:
- Required manual maintenance
- Got slower over time
- Could have been set incorrectly
- Was a maintenance burden

The dynamic date solution:
- ✅ Always works correctly
- ✅ Always efficient (30 days)
- ✅ No maintenance needed
- ✅ Self-updating



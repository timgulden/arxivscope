# For New Chats: React Frontend Rebuild

> **Quick start guide for new conversations working on the React frontend rebuild**

---

## **What You Need to Type**

**When starting a new conversation to work on the React frontend rebuild, type exactly this:**

```
Please read docscope-platform/services/docscope/react/FOR_NEW_CHATS.md to get up to speed on the React frontend rebuild task.
```

**That's it. One prompt.**

The chat will:
1. Read `FOR_NEW_CHATS.md`
2. Follow the instructions inside to read `CONTEXT_SUMMARY.md`, `REBUILD_PLAN.md`, and `STATE_MANAGEMENT_STRATEGY.md`
3. Understand the task and be ready to work

**Optional (but recommended)**: After the chat confirms it has read everything, you can ask:
```
Please confirm you understand the approach, functional programming principles, interceptor pattern, and state management strategy.
```

But this is optional - the chat should already understand these things from reading the documents.

---

## **What You Need to Know**

### **The Situation**
- ✅ React frontend code was lost during migration (submodule not bundled)
- ✅ Need to rebuild from scratch using Dash code (`docscope/components/`) as reference
- ✅ React project is initialized (Vite + React + TypeScript) but empty
- ✅ Legacy Dash frontend (`docscope/`) provides functionality reference

### **The Approach**
1. **Logic Layer First**: Implement pure functions with tests before any UI code
2. **Functional Programming**: All business logic must be pure functions (no side effects)
3. **Interceptor Pattern**: Use interceptors for cross-cutting concerns (logging, validation, error handling)
4. **State Management**: Single source of truth in logic layer (see `STATE_MANAGEMENT_STRATEGY.md`)

### **Key Documents**
- **`CONTEXT_SUMMARY.md`** - System overview, current environment, architecture
- **`REBUILD_PLAN.md`** - Complete phased rebuild plan (Logic → Testing → UI)
- **`STATE_MANAGEMENT_STRATEGY.md`** - State management architecture and patterns
- **`embedding-enrichment/DESIGN_PRINCIPLES.md`** - Core design principles
- **`docs/ARCHITECTURE/interceptor101.md`** - Interceptor pattern specification
- **`docs/ARCHITECTURE/FUNCTIONAL_PROGRAMMING_GUIDE.md`** - Functional programming guide

### **Dash Code Reference** (`docscope/components/`)
- `view_management_fp.py` - View state management (pure functions)
- `data_fetching_fp.py` - Data fetching (pure functions)
- `interceptor_orchestrator.py` - Interceptor pattern implementation
- `component_contracts_fp.py` - Component contracts

---

## **Current Status**

- ✅ Planning: Complete (`REBUILD_PLAN.md`, `STATE_MANAGEMENT_STRATEGY.md`)
- ⏳ Logic Layer: Not yet implemented (Phase 1)
- ⏳ Testing: Not yet implemented (Phase 2)
- ⏳ UI Layer: Not yet implemented (Phase 3)

**Next Step**: Begin Phase 1 - Logic Layer Foundation

---

## **Quick Context Check**

After reading the documents, you should understand:

- ✅ **What**: Rebuilding React frontend from scratch
- ✅ **Why**: React code was lost (submodule not bundled)
- ✅ **How**: Logic layer first with tests, then UI
- ✅ **Principles**: Functional programming (pure functions) + Interceptor pattern
- ✅ **State**: Single source of truth in logic layer
- ✅ **Reference**: Dash code in `docscope/components/` provides functionality reference

---

*This document is designed to quickly get new chats up to speed. The actual detailed plans are in `REBUILD_PLAN.md` and `STATE_MANAGEMENT_STRATEGY.md`.*


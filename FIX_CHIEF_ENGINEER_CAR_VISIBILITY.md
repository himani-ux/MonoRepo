# Fix: CHIEF ENGINEER CAR Visibility After MARK_COMPLETED

## Problem Statement
When a SECOND ENGINEER marked a CAR as COMPLETED (triggering MARK_COMPLETED action), the CAR status changed to `PENDING_CE_REVIEW`, but the CAR was **not visible** in the CHIEF ENGINEER's CAR list.

## Root Cause Analysis

### Issue 1: Missing Reviewer Assignment
**Location:** [psc-backend/apps/car/views.py](psc-backend/apps/car/views.py#L1044-L1070) - `CARWorkflowView.post()`

When `MARK_COMPLETED` action was executed:
- ✅ CAR status changed: `IN_PROGRESS` → `PENDING_CE_REVIEW`
- ❌ **But** `deficiency.reviewer_crew_id` remained **NULL**

The workflow code has a `determine_reviewer()` function ([workflow.py L61](psc-backend/apps/inspection/workflow.py#L61)) that automatically determines the correct reviewer based on the owner's rank:
- **SECOND ENGINEER (2E) owner** → Routes to **CHIEF ENGINEER (CE)** reviewer
- **CHIEF ENGINEER (CE) owner** → Routes to **MASTER** reviewer  
- **CHIEF OFFICER (CO) owner** → Routes to **MASTER** reviewer

But this function was **never called** during the MARK_COMPLETED action.

### Issue 2: CAR List Filtering Logic
**Location:** [psc-backend/apps/car/views.py](psc-backend/apps/car/views.py#L190-L206) - `CARListView.get_queryset()`

The CAR list filtering for VESSEL_CREW users only showed:
```python
queryset = queryset.filter(
    deficiency__assigned_crew_id=user.crew_id  # Only owns CARs
)
```

Since `reviewer_crew_id` was NULL, the CHIEF ENGINEER (even though qualified as a reviewer) didn't appear in the filter.

## Solution Implemented

### Change 1: Auto-Assign Reviewer on PENDING_CE_REVIEW
**File:** [psc-backend/apps/car/views.py](psc-backend/apps/car/views.py\#L1098-L1122)

Added code after CAR is saved to automatically assign the reviewer when transitioning to `PENDING_CE_REVIEW`:

```python
# Auto-assign reviewer when transitioning to PENDING_CE_REVIEW (MARK_COMPLETED action)
if target_status == CARStatus.PENDING_CE_REVIEW and car.deficiency:
    from apps.inspection.workflow import determine_reviewer
    
    deficiency = car.deficiency
    
    # Only auto-assign if no reviewer is already set
    if not deficiency.reviewer_crew_id:
        reviewer_crew, reviewer_rank_cat = determine_reviewer(
            deficiency.owner_rank,
            str(deficiency.inspection.vessel_id),
        )
        if reviewer_crew:
            deficiency.reviewer_crew_id = reviewer_crew.id
            deficiency.reviewer_rank = get_rank_name_by_id(reviewer_crew.rank_name)
            deficiency.reviewer_name = reviewer_crew.full_name
            deficiency.save(update_fields=['reviewer_crew_id', 'reviewer_rank', 'reviewer_name'])
```

### Change 2: Update CAR List Filter for Reviewers
**File:** [psc-backend/apps/car/views.py](psc-backend/apps/car/views.py#L190-L217)

Updated the VESSEL_CREW filtering to show CARs where user is either the **owner OR the reviewer**:

```python
if user.role == RoleCodes.VESSEL_CREW:
    from apps.inspection.deficiency_models import Deficiency
    from django.db.models import Q

    # Show CARs if user is either the owner OR the reviewer
    matching_defs = Deficiency.objects.filter(
        Q(assigned_crew_id=user.crew_id) |  # Owner
        Q(reviewer_crew_id=user.crew_id)     # Reviewer
    )
    
    queryset = queryset.filter(
        deficiency__in=matching_defs
    )
```

## Data Flow After Fix

```
1. SECOND ENGINEER clicks MARK_COMPLETED
   ↓
2. CARWorkflowView.post() processes MARK_COMPLETED action
   ↓
3. Car status: IN_PROGRESS → PENDING_CE_REVIEW
   Car.save()
   ↓
4. Auto-assign reviewer logic triggers:
   - determine_reviewer(SECOND_ENGINEER_RANK, vessel_id)
   - Returns CHIEF_ENGINEER crew record
   - Sets deficiency.reviewer_crew_id = CHIEF_ENGINEER.id
   - Saves deficiency
   ↓
5. CHIEF ENGINEER opens CAR list:
   - CARListView filters with: assigned_crew_id OR reviewer_crew_id
   - Matches CHIEF_ENGINEER.crew_id in reviewer_crew_id field
   ✅ CAR now visible with PENDING_CE_REVIEW status
   ↓
6. CHIEF ENGINEER can see APPROVE_AND_FORWARD and RETURN_FOR_REWORK buttons
```

## Database Changes
No schema changes required. The fix uses existing fields:
- `deficiency.reviewer_crew_id` (already exists, was just NULL)
- `deficiency.reviewer_rank` (already exists for display)
- `deficiency.reviewer_name` (already exists for display)

## Testing Checklist
- [ ] Create deficiency with SECOND ENGINEER as owner
- [ ] Auto-CAR created in ALLOTTED status
- [ ] SECOND ENGINEER sees CAR in their list
- [ ] SECOND ENGINEER clicks START_WORK → status = IN_PROGRESS
- [ ] SECOND ENGINEER clicks MARK_COMPLETED
- [ ] ✅ CAR status → PENDING_CE_REVIEW
- [ ] ✅ deficiency.reviewer_crew_id set to CHIEF_ENGINEER
- [ ] ✅ CAR visible in CHIEF ENGINEER's list
- [ ] ✅ CHIEF ENGINEER can see APPROVE_AND_FORWARD and RETURN_FOR_REWORK buttons

## Related Code
- Workflow definition: [workflow.py L175-195](psc-backend/apps/inspection/workflow.py#L175-L195)
- Reviewer routing: [workflow.py L61-118](psc-backend/apps/inspection/workflow.py#L61-L118) 
- Available actions: [workflow.py L350-367](psc-backend/apps/inspection/workflow.py#L350-L367)

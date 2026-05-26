# VIMS Safety Module User Guide

 

This guide is for the Safety module rollout without the Incident workflow.

The available Safety areas are:

- Near Miss
- Safety Committee Meeting
- Safety Officer Inspection
- Safety dashboard, search, notifications, and PDF reports

The Incident section is not part of this deployment. If a serious accident, injury, pollution event, fire, grounding, collision, or other formal incident occurs, follow the company's current incident reporting procedure outside this Safety rollout.

## Common Words Used in the Module

| Word | Meaning |
|---|---|
| Near Miss | An unsafe event that could have caused harm, damage, pollution, or injury, but did not. |
| SCM | Safety Committee Meeting. This is the vessel safety meeting record. |
| SOI | Safety Officer Inspection. This is the vessel safety inspection process. |
| Finding | A safety issue found during an inspection or meeting. |
| Corrective action | The action needed to correct a finding. |
| DPA | Designated Person Ashore. Shore-side safety authority. |
| FM | Fleet Manager. Shore-side fleet authority. |
| Master | Vessel Master. Final onboard sign-off authority. |
| CO | Chief Officer. Usually prepares or hosts vessel safety work. |
| SO | Safety Officer. Usually the CO, or another assigned officer when allowed. |

## Who Does What

| User | Main Responsibility |
|---|---|
| Any crew member | Report a Near Miss. |
| Master | Sign off Safety Committee Meetings and approve SOI closure where required. |
| CO / Safety Officer | Prepare SCM records and carry out SOI work. |
| DPA | Review Near Misses, issue circular/alert for high-priority learning, approve SOI applicability changes, review fleet safety status. |
| FM | Review fleet safety status and high-priority Near Miss closure where required. |
| Office reviewer | Review signed SCM records and add office comments. |

## Safety Module Home

The Safety area gives users a single place to:

- report Near Misses
- create and sign Safety Committee Meetings
- create and close Safety Officer Inspections
- review open findings
- download or print PDF reports
- view safety status and pending actions

Each user only sees actions allowed for their role.

## Near Miss Workflow

### Purpose

Near Miss reporting helps the company learn from unsafe situations before they become accidents.

Examples:

- A loose ladder pin was found before someone climbed the ladder.
- A mooring line snap-back risk was noticed before an injury occurred.
- A spill risk was noticed and controlled before pollution happened.
- A person almost slipped, but recovered without injury.

### Step 1: Crew Reports the Near Miss

Who can do this:

- Any crew member.

The reporter fills:

- vessel
- date and time of occurrence
- what happened
- severity
- event type
- loss type
- immediate action taken
- suggestion to prevent recurrence
- optional evidence or photo, where available

The system records the reporter from login. The reporter should not type another person's name.

### Step 2: Reporter Identity Is Protected

Reporter identity is protected to encourage honest reporting.

Visible to:

- DPA
- FM
- the reporter themselves

Hidden from:

- Master
- CO
- CE
- HOD
- other vessel users

For restricted users, the reporter appears as:

`Anonymous Reporter`

### Step 3: Vessel Review

The vessel-side reviewer checks whether the report is clear enough.

The reviewer may:

- send it forward for office triage
- send it back for correction if important information is missing

### Step 4: DPA Triage

The DPA reviews the Near Miss and marks it as:

- LOW priority
- HIGH priority

LOW priority means the case can be closed with a simple review and closure note.

HIGH priority means more learning is needed before closure.

### Step 5: LOW Priority Closure

LOW priority Near Misses can be closed after:

- DPA triage is complete
- closure note is entered
- typed name/signature is captured
- required role approval is given

Authorized closers may include Master, DPA, FM, or assigned PIC depending on permission.

### Step 6: HIGH Priority Handling

HIGH priority Near Misses require:

- fact or causal analysis
- preventive measures
- fleet learning
- circular/alert action
- closure by DPA or FM

### Step 7: Issue Circular / Alert

For important learning, the DPA can open the Circular module with title and body prefilled from the Near Miss learning.

The DPA then completes the remaining circular details and publishes it using the normal Circular process.

### Step 8: PDF Report

The Near Miss PDF shows:

- Near Miss reference
- vessel
- dates
- what happened
- severity and priority
- immediate action
- preventive measure or suggestion
- fleet learning, if any
- closure details
- signatures
- reporter name only if the viewer is allowed to see it

## Safety Committee Meeting Workflow

### Purpose

The Safety Committee Meeting records what the vessel safety committee discussed, what was decided, and what actions were assigned.

Both Regular and Ad-Hoc meetings use the same form.

### Regular Meeting

Used for the normal vessel safety meeting cycle.

Who can host:

- Master
- CO

### Ad-Hoc Meeting

Used when an extra meeting is needed.

Examples:

- urgent safety concern
- important circular or alert
- repeated Near Miss trend
- significant SOI finding
- office instruction

Who can host:

- Master
- CO

### Step 1: Create the Meeting

The host selects:

- Regular Meeting
- Ad-Hoc Meeting

The form includes:

- meeting date and time
- location or vessel position
- meeting sections
- attendance
- safety topics
- circular or safety alert review
- SOI observations
- findings and corrective measures
- minutes and decisions

### Step 2: Complete Sections 1 to 9

The vessel completes the meeting record.

Important sections include:

- previous meeting review
- safety practice
- circular or safety alert discussion
- environment
- health
- crew welfare
- SOI findings and corrective measures
- minutes of meeting

For repeatable fields such as Q&S topics or findings, only filled rows are printed in the PDF.

### Step 3: Attendance and Signatures

The meeting records:

- who attended
- work/rest-hour warning status where available
- attendee signatures
- CO signature where required
- Master final sign-off

WRH warnings must be acknowledged, but they do not stop meeting creation.

### Step 4: Master Sign-Off

The Master performs final onboard sign-off.

Before sign-off, the system checks:

- required sections are complete
- required decisions/actions are filled
- attendance warnings are acknowledged
- required signatures are captured
- overdue SOI blockers are cleared where applicable

After Master sign-off, the vessel-side meeting is closed.

### Step 5: Office Review

After the meeting is signed by the Master, office users review it.

Office review includes:

- office comments
- review status

The office review appears as Section 10 in the SCM PDF.

### Step 6: PDF / Print

The SCM PDF is the meeting minutes record.

It includes:

- meeting details
- attendance
- closed items since last SCM
- sections 1 to 10
- SOI observations
- findings and corrective measures
- meeting minutes
- decisions/actions
- signatures

The PDF should not show developer notes, internal project notes, or document-control text.

## Safety Officer Inspection Workflow

### Purpose

SOI is used to inspect vessel safety areas and record findings.

The inspection is paper-first:

- the checklist is downloaded and printed
- the inspection is carried out on paper
- findings are entered into VIMS
- the signed paper checklist is kept onboard as per company filing procedure

The system does not require uploading a scan of the paper checklist.

### Step 1: Create SOI

Who can create:

- Safety Officer
- assigned alternate where allowed

The user selects:

- vessel
- inspection areas
- assistant, if applicable
- trainee, if applicable

### Step 2: Download Checklist

The system generates a checklist with a unique checklist ID.

The user downloads or prints:

- PDF checklist, or
- Excel checklist, if available

The checklist ID must be used later when entering findings.

### Step 3: Carry Out Inspection on Paper

The Safety Officer and assistant carry out the inspection onboard.

They:

- check the selected areas
- mark items on paper
- note any findings
- sign the paper checklist

The paper checklist remains the inspection working record.

### Step 4: Register Findings in VIMS

After the inspection, findings are entered into VIMS.

For each finding, enter:

- checklist unique ID
- area/item
- finding title
- description
- severity
- proposed action
- photo if required
- responsible person, if applicable

High-severity findings may require a photo.

### Step 5: Submit Findings

When findings are entered, the SOI can be submitted.

The system tracks:

- open findings
- pending closure findings
- reopened findings
- closed findings

### Step 6: Closure and Approval

Findings are closed only after the required action and approval.

The Master may approve closure where required.

If DPA reopens a finding, it returns to the vessel for correction and then goes back for closure again.

### Section 12 Rule

Section 12 is a cross-cutting safety and culture section.

It should be covered once per inspection cycle.

If Section 12 has already been covered in the current cycle, the system may show:

`Section 12 has already been covered in this cycle.`

This avoids duplicate Section 12 inspections in the same period.

## SOI Findings in SCM

Open SOI findings are shown in the Safety Committee Meeting so the committee can discuss them.

The SCM should record:

- what was discussed
- what action is required
- who owns the action
- expected completion date, where applicable

This helps carry important SOI findings into the vessel safety meeting.

## Circulars and Safety Alerts in SCM

Circulars and safety alerts are discussion inputs for the meeting.

The meeting should record:

- whether the latest circular or safety alert was received
- circular/alert serial number
- whether it was discussed
- any action required onboard

Circulars are not a separate SCM approval workflow.

If a circular or alert requires follow-up, the follow-up should be recorded as an SCM action item.

## Dashboard and Notifications

The dashboard helps users see:

- open Near Misses
- pending SCM actions
- SOI compliance status
- open SOI findings
- overdue or pending items

Notifications may appear for:

- Near Miss review
- Near Miss triage
- SOI finding closure
- SCM sign-off
- office review
- overdue safety actions

Users should treat notifications as their daily action list.

## PDF and Print Guidance

PDFs are used as formal records.

Users can generate PDFs for:

- Near Miss
- SCM
- SOI summary

PDFs should show only production information, such as:

- vessel
- reference number
- dates
- facts/details
- decisions
- actions
- signatures
- closure information

PDFs should not show:

- developer notes
- internal rule IDs
- internal project wording
- document-control/debug sections
- technical implementation details

## What Users Should Check Before Final Submission

### Near Miss

- Description is clear.
- Occurred date/time is correct.
- Immediate action is entered.
- Suggestion or preventive measure is entered.
- Evidence/photo is attached when needed.

### SCM

- Attendance is correct.
- Required sections are complete.
- Decisions/actions are entered.
- Findings have corrective measures.
- Attendees and CO have signed where required.
- Master sign-off is complete.
- Office comments are added after vessel sign-off.

### SOI

- Correct areas were selected.
- Checklist was downloaded and printed.
- Checklist unique ID matches.
- Findings are entered clearly.
- Required photos are attached.
- Closure approval is complete.

## Simple Lifecycle Summary

### Near Miss

Crew reports Near Miss
-> Vessel review
-> DPA triage
-> LOW closure or HIGH analysis/fleet learning
-> closure
-> PDF record

### Safety Committee Meeting

Master/CO creates meeting
-> sections and attendance completed
-> attendees/CO sign
-> Master signs off
-> office adds Section 10 review
-> PDF minutes generated

### Safety Officer Inspection

Safety Officer creates SOI
-> downloads checklist
-> carries out paper inspection
-> enters findings in VIMS
-> submits findings
-> Master/office closure approval
-> SOI summary PDF generated

## Important Notes

- Incident workflow is not included in this deployment.
- Reporter identity in Near Miss is protected.
- SOI remains paper-first.
- SCM Regular and Ad-Hoc meetings can be hosted by Master or CO.
- Master final sign-off is required for SCM.
- Office review is added after vessel-side SCM sign-off.
- PDFs are official records and should be printed or shared as required by company procedure.

MASTER INSPECTION WORK INSTRUCTION

Document purpose

This work instruction explains how a Vessel Master should use the Inspection module in VIMS.
It is written in simple language and can be copied directly into a Word file.

Based on current application logic in this repository as of 17 April 2026.

1. Scope

This instruction is for users logged in with the role:

- VESSEL_MASTER

It covers the Master's work in these areas:

- creating inspection records
- adding deficiencies
- reviewing linked CAR work
- submitting the inspection
- registering PSC follow-up
- downloading CAR reports

2. Simple meaning of common words

- Inspection: the main record for a PSC, RightShip, or Audit visit
- Deficiency: a non-conformity or issue found during the inspection
- CAR: Corrective Action Report created by the system for each deficiency
- PIC: office reviewer
- DPA: final office closer for the inspection
- Follow-up: later reinspection update recorded against the same PSC inspection

3. Main screens used by Master

- Dashboard: summary of vessel inspection and CAR activity
- Inspections: create, open, edit, submit, and follow inspections
- Inspection Detail: review reports, deficiencies, and activity history
- CARs: work on corrective actions, evidence, and workflow
- Deficiencies: review vessel deficiency workflow status
- Notifications: check office comments and returns
- Sync: upload pending work when internet is available

4. Master permissions in the current system

The Vessel Master can:

- create PSC inspections
- create RightShip inspections
- create Audit inspections
- edit inspection records while they are in DRAFT status
- delete draft inspections if no deficiencies have been added
- add deficiencies to an inspection
- work on vessel-side CAR steps
- submit CARs to PIC when the CAR is ready
- submit the inspection for office review
- register PSC follow-up on the same inspection

The Vessel Master cannot:

- do PIC review of an inspection
- do DPA closure of an inspection
- close an inspection after PIC review

5. End to end work flow for Master

5.1 Open the Inspection module

1. Log in with your Vessel Master account.
2. Open the Inspections screen from the menu.
3. Review the list of inspections for your vessel.

Useful list actions:

- filter by inspection type
- filter by status
- search by vessel or port
- filter detention cases
- export Excel if needed

5.2 Create a new inspection

1. Open Inspections.
2. Click New Inspection.
3. Fill the inspection details.
4. Attach the inspection report.
5. Click Create Draft.

Important rules while creating:

- Only Vessel Master can create PSC or RightShip inspections.
- Inspection date cannot be in the future.
- Port or Place is required.
- You must state whether deficiencies were reported: YES or NO.
- For PSC inspection, PSC subtype is required.
- For PSC inspection, MOU is required.

Inspection types available to Master:

- PSC
- RS
- AUDIT

Common fields to complete:

- inspection type
- PSC subtype, if inspection type is PSC
- inspection date
- port or place
- country or state, if available
- MOU, if inspection type is PSC
- authority
- inspector name
- detention yes or no
- detention reason, if detention is yes
- deficiencies reported yes or no

5.3 Upload the inspection report

The system requires at least one report before the inspection can be submitted.

Current report upload rules for the main inspection report:

- allowed file types: PDF, JPG, JPEG
- maximum file size: 3 MB

Good practice:

- upload the report during draft creation itself
- if upload fails, open the inspection later and upload again before submission

5.4 Review the draft inspection

After draft creation, open the Inspection Detail screen and review:

- vessel and inspection summary
- inspection reports
- deficiency section
- activity history

If "Deficiencies Reported" is NO:

- the system will not let you add deficiencies
- edit the inspection first and change the value to YES if deficiencies need to be recorded

5.5 Add deficiencies

When deficiencies are reported:

1. Open the inspection.
2. Click Add Deficiency.
3. Select the deficiency code.
4. Enter the deficiency description.
5. Select the action code, if required.
6. Assign crew or target date if needed.
7. Save the deficiency.

Important system behavior:

- every new deficiency automatically creates one linked CAR
- you do not create the CAR manually

5.6 Review and work on the linked CAR

From the deficiency or CAR list, open the related CAR and complete the vessel-side work.

The CAR detail can include:

- root cause summary
- corrective actions
- evidence files
- activity history
- workflow buttons

Master can edit CARs in vessel-side statuses such as:

- ALLOTTED
- IN_PROGRESS
- PENDING_CE_REVIEW
- PENDING_MASTER_REVIEW
- RETURNED_FOR_REWORK

Master can upload evidence during these working stages:

- ALLOTTED
- IN_PROGRESS
- RETURNED_FOR_REWORK

Typical CAR flow for Master:

1. Open the CAR.
2. Enter or review corrective action details.
3. Upload evidence files as needed.
4. Move the CAR to the next status using the available workflow button.
5. If office returns the CAR for rework, update it and send again.

Current CAR transition points relevant to Master:

- ALLOTTED to IN_PROGRESS
- IN_PROGRESS to PENDING_CE_REVIEW
- PENDING_CE_REVIEW to PENDING_MASTER_REVIEW
- PENDING_CE_REVIEW back to IN_PROGRESS if rework is needed
- PENDING_MASTER_REVIEW to SUBMITTED_TO_PIC
- PENDING_MASTER_REVIEW back to IN_PROGRESS if rework is needed

Note:

- the exact buttons shown depend on current CAR status and system permissions
- if a button is missing, the record is usually not yet at the correct stage

5.7 Bulk submit ready deficiencies to office

The inspection detail page may show a bulk submit option for Master.

Use this when:

- the deficiency is already approved on vessel side
- the linked CAR is in PENDING_MASTER_REVIEW

Steps:

1. Open the inspection.
2. In the deficiency section, select the ready items.
3. Click Submit Selected.
4. Confirm the submission.

5.8 Submit the inspection

When all inspection data is complete:

1. Open the draft inspection.
2. Review the reports and deficiencies.
3. Click the submit action when available.

The system will block submission if:

- the inspection is not in DRAFT status
- no inspection report is attached
- any deficiency does not have a linked CAR

After successful submission:

- inspection status becomes SUBMITTED
- office reviewers can continue the inspection review

5.9 Respond after office review

After submission, office users may:

- review the inspection
- review CARs
- return CARs for rework

Master should then:

1. open Notifications, Deficiencies, or CARs
2. read office comments
3. correct the returned item
4. resubmit the CAR when the action becomes available

5.10 Register PSC follow-up

Follow-up is only for PSC inspections and only for Vessel Master.

Use this when the same PSC inspection needs reinspection updates.

Steps:

1. Open the PSC inspection.
2. Click Register Follow-up.
3. Select the deficiencies to update.
4. enter the reinspection date
5. update the action code for each selected deficiency
6. add notes if needed
7. optionally attach up to three follow-up report PDFs
8. confirm and submit

Current follow-up rules:

- only PSC inspections are allowed
- only Vessel Master can register follow-up
- reinspection date cannot be in the future
- reinspection date cannot be before the original inspection date
- at least one deficiency update is required
- follow-up report PDFs are optional
- up to three follow-up report PDFs can be attached
- if any follow-up report PDF is uploaded, description is mandatory
- follow-up report attachments must be PDF only
- each follow-up report PDF maximum size is 5 MB

What happens after follow-up submission:

- selected deficiency action codes are updated
- follow-up report PDFs are stored under the same inspection
- activity history records the follow-up event

5.11 Download all CARs for one inspection

If the inspection has linked CARs:

1. Open the inspection.
2. Click Download All CARs.
3. Choose Internal Report or External Report.

System behavior:

- if only one CAR exists, download is a PDF
- if more than one CAR exists, download is a ZIP file

6. Daily working checklist for Master

Use this quick sequence for normal work:

1. Open Dashboard and check pending work.
2. Open Inspections and create or update the draft inspection.
3. Upload the inspection report.
4. Add deficiencies if any issue was found.
5. Open related CARs and complete vessel-side actions.
6. Submit ready CARs to PIC.
7. Submit the inspection when all requirements are complete.
8. Monitor Notifications for office comments or rework.
9. Use Register Follow-up when PSC reinspection is required.
10. Use Sync Now when internet is available.

7. Common reasons why Master cannot proceed

Problem: New Inspection button is visible but PSC or RS cannot be created

- check that the login role is VESSEL_MASTER

Problem: Add Deficiency button is missing

- check whether "Deficiencies Reported" is set to NO
- edit the inspection and change it to YES if needed

Problem: Inspection cannot be edited

- Vessel Master can edit only while the inspection is in DRAFT status

Problem: Inspection cannot be deleted

- only draft inspections can be deleted
- if deficiencies already exist, delete is not available

Problem: Inspection cannot be submitted

- attach at least one inspection report
- confirm the inspection is still in DRAFT status
- confirm every deficiency has a linked CAR

Problem: Follow-up option is not available

- follow-up is only for PSC inspections
- follow-up is only for Vessel Master

Problem: Follow-up report upload fails

- only PDF is allowed
- file must be 5 MB or smaller
- description is required when file is attached

Problem: CAR workflow button is missing

- the CAR may be in a different status
- the action may belong to Chief Engineer, PIC, or DPA
- some actions appear only after the previous step is completed

8. Good practice for Master

- create the inspection as soon as the inspection visit is completed
- upload the report before starting submission work
- write clear deficiency descriptions
- ensure each deficiency has the correct action code
- check linked CARs before submitting the inspection
- review notifications daily
- use follow-up only for PSC same-inspection reinspection updates

9. Final note

If a button mentioned in this work instruction is not visible, it usually means one of these:

- your role does not have that permission
- the inspection or CAR is not in the correct status
- a required field or file is still missing
- the action belongs to office side, not Master side

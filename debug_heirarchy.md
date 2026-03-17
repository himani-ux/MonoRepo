####Heirarchial workflow

1. When CAR is assigned to SECOND ENGINEER 
    a. Access to buttons ---> START_FOR_WORK, MARK_COMPLETED
    b. ON_CLICKING ---------> START_FOR_WORK          ---------------> status   ---> IN PROGRESS
    c. MARK_COMPLETED button appears when START_FOR_WORK button is clicked and when MARK_COMPLETED is clicked status changes to PENDING CE REVIEW 
    d. The CAR is assigned to CHIEF_ENGINEER for review and button APPROVE_AND_FORWARD and RETURN_FOR_REWORK appears for chief engineer
    e. After clicking on APPROVE_AND_FORWARD by CHIEF_ENGINEER the status changes to PENDING_MASTER_REVIEW
    f. The CAR is assigned to MASTER for review and button SUBMIT_TO_PIC and RETURN_FOR_REWORK appears for master
    g. After clicking on SUBMIT_TO_PIC by MASTER the status changes to SUBMITTED_TO_PIC
    Clicking on  RETURN_FOR_REWORK button makes the status IN PROGRESS and returns to SECOND ENGINEER or owner

2. When CAR is assigned to CHIEF ENGINEER OR CHIEF OFFICER
   a. Access to buttons ---> START_FOR_WORK, MARK_COMPLETED
   b. ON_CLICKING ---------> START_FOR_WORK          ---------------> status   ---> IN PROGRESS
   c. MARK_COMPLETED button appears when START_FOR_WORK button is clicked and when MARK_COMPLETED is clicked status changes to PENDING_MASTER_REVIEW
   d. The CAR is assigned to MASTER for review and button SUBMIT_TO_PIC and RETURN_FOR_REWORK appears for master
   e. After clicking on SUBMIT_TO_PIC by MASTER the status changes to SUBMITTED_TO_PIC
   Clicking on  RETURN_FOR_REWORK button makes the status IN PROGRESS and returns to SECOND ENGINEER or owner

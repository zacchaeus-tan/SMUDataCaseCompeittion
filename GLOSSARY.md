# OneRecord

OneRecord is Lives Group's single front door for creating master records in SAP B1, plus the regional sales view
built on those clean records. General MDM and SAP terms (Business Partner, Item, Cost Center, business entity,
approval chain) follow Appendix A of the case brief.

## Setup requests

**Setup request**:
A request to create a new Customer, Item, Vendor or Cost centre record in SAP B1.
_Avoid_: request (on its own), MDM request, ticket

**Requestor**:
The person who raises a setup request, such as a Product Manager, Regional Sales or Procurement officer.
_Avoid_: submitter, user

**Approver**:
A person who signs off the part of a setup request they are responsible for: BU Head, Finance, Quality/Regulatory or
Business Support.
_Avoid_: reviewer, checker

**Final check**:
The MDM Analyst's last approval, after every approver has signed off and before the record goes into SAP B1.
_Avoid_: MDM approval, final approval

**Time to SAP**:
The time from submitting a setup request to the record existing in SAP B1, quoted as a median.
_Avoid_: cycle time, turnaround, lead time

**Duplicate**:
Two or more records that describe the same real customer, item or vendor, whatever their names.
_Avoid_: double, copy, near-match

## Customer purchases

**Order**:
A customer purchase order for Product A, B or C. Only orders count towards volumes and growth.
_Avoid_: purchase request, PO request, sale

**Enquiry**:
A customer email asking about products, prices or stock that is not an order. Follow-ups are grouped with enquiries.
_Avoid_: lead, request

**Growth**:
The year-on-year change in units ordered, Apr–Sep 2026 against Apr–Sep 2025, counting orders only.
_Avoid_: sales growth (unqualified), increase

**Regional view**:
Order volumes and growth for Products A, B and C across the five countries, from one clean record per customer.
_Avoid_: dashboard, report

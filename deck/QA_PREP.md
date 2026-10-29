# Q&A cheat sheet (5 min, free-for-all)

Rule for all four of us: answer in two sentences, then offer the slide or the live app. If you don't know, say
"we'd check that in the pilot" rather than guess.

## Business case and impact

**1. Where does the S$205k a year come from?**
Mostly sales, not staff time: about S$103k of gross profit kept from customers dropping off and S$83k from
cross-sell, plus S$12k from new accounts going live sooner and S$7.5k of staff time. All counted at a 30% gross margin,
and every rate is adjustable on the app's Business case page. → *Appendix C*

**2. Is 4–6 days to SAP realistic?**
We replayed the same 150 past setup requests with parallel approvals, keeping each approver's historical waiting
time. Even if reminders changed nothing, parallel approvals and the smart form alone give about 6 days; 4 days is with
reminders working. → *Business case page in the app*

**3. Your data is synthetic. Why trust any of these numbers?**
We don't ask you to: that's why the ask is a 4-week pilot with SPD, on real SAP data, with two targets (≤5 days to
SAP, ≥90% through the form). We roll out to QTS and QTG only if the pilot hits them. → *Slide 22*

**4. What if the pilot misses its target?**
Then we don't scale yet. The audit log shows exactly where each setup request waited, so we fix that step (rules,
reminders, a missing approver) and rerun, before spending on Phase 2 or 3.

## Adoption

**5. What stops people from just emailing MDM like before?**
Emails to the MDM mailbox get an automatic reply with the form link, and after go-live MDM only actions setup
requests that came through the form. Approvers don't need to change habits at all: the card comes to them in Teams.
→ *Slide 20*

**6. Will approvers really respond faster?**
Today 62% of the time is waiting for approvers to notice an email. A Teams card, a reminder at 9 AM in their own time
zone and escalation after 4 days remove the "didn't see it" delay; parallel approvals remove the queue.

## Method

**7. How do you know the duplicate threshold is right?**
It was tuned on our synthetic duplicates (41 of 41 found, 0 false matches, 3% of new customers warned), so the first
pilot task is re-checking it on real SAP data. A "possible match" only warns; going ahead just needs a reason that
every approver can see. → *Appendix A*

**8. Why not a proper machine-learning forecast?**
12–18 months of history is too short to train one well, and someone would have to retrain it. Our model uses events
the business already knows (dengue season, December budget push, Lunar New Year), so it has few parameters and still
beats the 6-month average: 11.1% vs 13.7% error. → *Appendix B*

**9. How does the email sorter decide order vs enquiry?**
Rules first, then an AI prompt for the unclear ones, then a person for anything still unsure. Only orders count
towards growth; setup requests are passed to the people who raise them.

## Technology and governance

**10. Why not write straight into SAP B1?**
The import file already removes Priya's retyping at almost no risk. A live connection needs an SAP partner and
testing, so it's Phase 3, and only if volumes justify it. → *Slide 6*

**11. How are bank details protected?**
They sit in a separate restricted list that only Finance, MDM and the requestor can see; approval cards carry a link,
never the values. Every step is written to an audit log that is only ever added to. → *Appendix E*

**12. What does IT actually have to do?**
About two days, once: set up the Teams site and permissions. Standard connectors only, so no premium licence; after
that the MDM team edits rules, fields and approvers itself.

**13. You demoed a Streamlit app. Is that what Lives Group gets?**
No. The workflow runs as a Power App with Power Automate in Teams (that's the video). The Streamlit app is our
working copy of the same rules; in production the regional view moves to Power BI inside Teams in Phase 2.

**14. How would you add a new data domain, like price lists?**
Rules, fields and approvers are rows in lists, so a new domain is new rows plus a form screen, not a new system. It's
on the Phase 3 list.

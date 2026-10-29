# OneRecord finals pitch script

**15 minutes pitch + 5 minutes Q&A.** About 2,000 spoken words in total.

| Section | Speaker | Slides | Target |
|---|---|---|---|
| 1 · The problem | Megan | 1–7 | 3:40 |
| 2 · OneRecord: what the form does | Zacchaeus | 8–15 | 4:00 |
| 3 · The dashboard: what it does | Darryl | 16–21 | 4:10 |
| 4 · Making it real | Chloe | 22–27 | 3:40 |
| | | **Total** | **15:30** |

No live demo: both demos are videos (slides 10 and 13). **The total is now about 30 s over 15:00**, so the cuts below are no longer optional: rehearse with them.

**How to read this**
- `[CLICK]` means the clicker presses once: either the next animation or the next slide. The speaker says a quiet "next" or nods.
- **Clicker:** someone else clicks for Megan (slides 1–7, **TBC**). From slide 8 onwards, Megan clicks.
- Slide numbers are the shared deck's current ones, assuming one of the two "Roadmap, and our ask" slides (26 and 27) is deleted.
- **To fit 15:00** (about 35 s to find): say slide 7 in one line (saves about 15 s); Zacchaeus says slide 15's three numbers in one breath (about 10 s); Chloe covers only the top three risks on slide 25 (about 10 s). Never cut the business case or the Ask.

---

## 1 · The problem: Megan (3:40)

### Slide 1 · Title (0:10)
Good afternoon. We're OneRecord. Our promise in one line: clean records in, better decisions out.
`[CLICK]`

### Slide 2 · Executive summary (0:30)
Here's our whole pitch in thirty seconds. Today it takes 18.8 days to get one record into SAP, and duplicate
customers make the regional sales view wrong. Our answer is OneRecord: one front door for setup requests, built on
the Microsoft 365 that Lives Group already pays for. Clean data then powers a regional view that already finds
S$431k a quarter at risk. It pays back in about 3.4 months, and our ask is a 4-week pilot with SPD. Let's start
with the problem.
`[CLICK]`

### Slide 3 · Divider 01 (0:05)
*(Move straight on.)*
`[CLICK]`

### Slide 4 · Amy's 18 days (0:50)
This is Amy, the product manager from your brief. She needs one item code.
`[CLICK]` On day 0 she copies an old email and leaves the QA field blank, because she isn't sure. On day 2 MDM
notices the gap. On day 7 she replies from a trip. Then three approvers sign, one after another. On day 18 her
sales order fails: the item still isn't in SAP.
`[CLICK]` The brief asks us to fix exactly this, and to find sales growth across five countries.
`[CLICK]` And it isn't a one-off. Across 150 past setup requests, the median is 18.8 days, 41% bounce back at least
once, and 62% of the time is spent just waiting for an approver to notice an email.
`[CLICK]`

### Slide 5 · Five pain points, one root cause (1:00)
`[CLICK]` The brief lists five groups of pain points. Data quality, speed, audit, flexibility and forecasting.
Quick question: how many emails reached your SMU Outlook today? Twenty? Thirty? Wei Jie's inbox looks the same. His
four-day delay isn't him being slow. It's email.
`[CLICK]` Our reading is that all five share one root cause: bad data gets in at the setup request, the moment
someone emails MDM. Duplicates then split one hospital into several customers, and the regional sales view is
wrong. So we fix the front door first, then put the clean data to work.
`[CLICK]`

### Slide 6 · Why OneRecord on Microsoft 365 (0:40)
We compared our options.
`[CLICK]` A better email template costs almost nothing, but nothing enforces it. A custom portal, or off-the-shelf
MDM software, would fix it, but needs developers or an integrator, and months.
`[CLICK]` Our pick is to build on Microsoft 365. About S$58k in year one, around ten weeks, and IT needs only about
two days.
`[CLICK]` It's already licensed, the MDM team can change it themselves, and it fixes data where it enters.
`[CLICK]`

### Slide 7 · Not in version 1 (0:25)
`[CLICK]` We also chose what *not* to build. The two that matter most: no direct write into SAP yet, because an
import file removes the retyping at almost no risk. And no automatic merging of duplicates, because a merge touches
open orders and invoices, so a person confirms. Happy to go through the rest in Q&A.

> **Hand-off:** "Zacchaeus will now show you OneRecord."

`[CLICK]`

---

## 2 · OneRecord: Zacchaeus (3:40)

*From here on, Megan clicks.*

### Slide 8 · Divider 02 (0:05)
Let's replay Amy's request, this time through OneRecord.
`[CLICK]`

### Slide 9 · One front door (0:30)
`[CLICK]` OneRecord is one front door for all four kinds of setup request: customer, item, vendor and cost centre.
`[CLICK]` Behind it are six things. A smart form that shows only the fields that apply. A duplicate check while you
type. Approvals in Teams, in parallel. Reminders, then escalation. An audit log with locked bank details. And an
SAP import file, so Priya stops retyping.
`[CLICK]` The rules behind all of it are lists the MDM team edits themselves.
`[CLICK]`

### Slide 10 · Amy raises her item request (0:50)
*Video, about 38 s, no sound. Click 1 starts it. Click 2 and 3 as each step happens on screen.*

This is our working prototype. Watch Amy raise the same item request.
1. `[CLICK]` *(video starts)* She picks Item, and only the item fields appear. Submit stays off until the request is
   complete, so nothing half-filled reaches an approver.
2. `[CLICK]` *(as "Is this regulated?" is set to Not sure)* Amy wasn't sure about regulatory sign-off. Now she just
   says "Not sure", and Quality/Regulatory is added to the approvers for her. No guessing.
3. `[CLICK]` *(as she types the name)* And as she types, OneRecord warns her: this looks like item A-1001, which is
   already in SAP. The duplicate is stopped before it reaches anyone. The check compares names the way a person
   would, so "NUH" and "National University Hospital" match. A similar name only warns; the same registration
   number blocks.

This is our web copy. The same form runs in Teams, as you'll see in a moment.
`[CLICK]` *(slide 11 is hidden, so this goes straight to slide 12)*

### Slide 12 · Approvers sign off at the same time (0:35)
`[CLICK]` Amy submits.
`[CLICK]` Every approver gets their card at the same time, instead of one after another.
`[CLICK]` Priya from MDM approves last, and the flow writes the SAP import file.
`[CLICK]` If someone doesn't answer, they get a reminder at 9 AM in their own time zone, then it's escalated after
four days. Amy can see who it's waiting on.
`[CLICK]` And for audit: every approval is logged with who and when. Bank details sit in a locked list, so they
never appear on the card.
`[CLICK]`

### Slide 13 · Watch: approvals to SAP (1:20)
`[CLICK]` *(the video starts)* Here's the rest of the journey.
`[CLICK]` *(as the BU Head approves)* The approver sees the card, with Approve, Request changes or Reject.
`[CLICK]` *(when the demo clock jumps)* We skip ahead four days, and the reminders and escalation fire on their own.
`[CLICK]` *(on Amy's My requests)* Amy sees exactly who it's still waiting on.
`[CLICK]` *(on Priya's screen)* Priya gives the final check, downloads the SAP import file, and marks it created.
Amy is told it's live.
`[CLICK]`

### Slide 14 · Marcus's new team (0:20)
One more persona from the brief. Marcus's team was just added to Lives Group.
`[CLICK]` In OneRecord his business unit is one row.
`[CLICK]` Fields and approvers are rows too, so a new regulatory step doesn't need IT.
`[CLICK]` And if nobody is set up yet, his request goes to MDM instead of stalling.
`[CLICK]` Before, his first requests sat untouched for two weeks.
`[CLICK]`

### Slide 15 · What the form delivers (0:20)
In short: setup requests reach SAP in 4 to 6 days instead of 18.8. The form caught all 41 duplicates in our data
while people typed. And it stays quiet when it should: only 3% of genuinely new customers get a warning.

> **Hand-off:** "Now that the data coming in is clean, Darryl will show what it unlocks."

`[CLICK]`

---

## 3 · The dashboard: Darryl (4:10)

*Slides 18 to 21 open on the full app page; your first click zooms in. After that, each click brings in one callout
and its screenshot. Talk about what the dashboard does; use a number only as evidence that a feature works.*

### Slide 16 · Divider 03 (0:05)
With clean data now entering the system, I will show what that data makes possible.
`[CLICK]`

### Slide 17 · Duplicates double the money at risk (0:40)
Before I walk through the dashboard, it is worth showing why clean master data matters commercially.
`[CLICK]` This is our customer analysis, run on Lives Group's SAP records as they stand today. It raises 56 drop-off
alerts: customers who appear to be ordering much less. However, 29 of those are false alarms, because the same
customer exists under more than one record.
`[CLICK]` Once OneRecord merges those duplicates, the same analysis returns 27 genuine alerts.
`[CLICK]` In value terms, the raw data suggests S$852,000 a quarter at risk. The true figure is S$431,000. In other
words, half of what the sales team would be chasing is not real.
`[CLICK]`

### Slide 18 · Dashboard view (0:45)
*Opens on the full Overview page.*

This is the Overview page: the regional view the brief asks for, and the first page a regional lead such as Daniel
would open. Every figure on it can be filtered by country and by period.
`[CLICK]` *(zooms in)* On the left is growth by country and product. Each cell compares units ordered this year with
the same period last year: the darker the green, the stronger the growth; the darker the red, the sharper the decline.
`[CLICK]` On the right are the three highest-priority actions for the quarter. Each one links directly to the evidence
behind it, so a manager can check the reasoning before acting on it.
`[CLICK]` Below that, actual orders are plotted against our forecast model, with a likely range for the next six
months.
`[CLICK]`

### Slide 19 · Country deep-dive (0:50)
*Opens on the full Country deep-dive page.*

For more detail, the Country deep-dive page breaks the regional view down further.
`[CLICK]` *(zooms in)* The headline figures cover all five countries: units, order value, active customers, and the
fastest-growing market, each compared with last year.
`[CLICK]` Growth is defined the same way across the dashboard: units ordered from April to September 2026, against the
same months in 2025, so seasonal effects cancel out. Only customer purchase orders are counted; enquiries and setup
requests are excluded.
`[CLICK]` A manager can then select any country from this dropdown, to see its monthly sales by product and its ten
largest customers.
`[CLICK]` Finally, monthly units by country for each product line, with written takeaways that update automatically as
the data changes.
`[CLICK]`

### Slide 20 · Who to call, and what counts (0:50)
*Opens on the full Customers page.*

The Customers page turns these insights into a work list for the sales team.
`[CLICK]` *(zooms in)* First, a call list ranked by value at risk. For each customer, it shows why the account was
flagged and the recommended next step.
`[CLICK]` Second, an early warning for larger customers who have gone unusually quiet, so that sales can step in
before they become a drop-off.
`[CLICK]` Third, cross-sell leads: customers who buy Product A but not Product B, where similar customers buy both.
`[CLICK]` Underneath all of this, an email sorter ensures that only genuine purchase orders count towards growth. Its
AI instructions are written in plain English, so the MDM team can adjust them without retraining a model.
`[CLICK]`

### Slide 21 · Forecasts that know the calendar (1:00)
*Opens on the full Forecasting page.*

The final page is forecasting. Lives Group currently uses a six-month moving average, which cannot anticipate
seasonal patterns.
`[CLICK]` *(zooms in)* Our model combines each country and product's own trend with calendar events the business
already knows: dengue season, the year-end hospital budget spend, the January slowdown, and public holidays such as
Lunar New Year.
`[CLICK]` We tested it on past data. From each month between April and September, we forecast one to three months
ahead and compared the result with actual orders. Forecast error fell from 13.7 per cent to 11.1 per cent.
`[CLICK]` Rather than a single number, the model provides a likely range. In testing, eight months out of ten fell
within it.
`[CLICK]` This feeds a stock plan for the next quarter. Where the model has been less accurate in the past, the series
is flagged for review rather than acted upon.
`[CLICK]` In Phase 2, an AI-generated action brief will be posted to Teams each month. It works only from summary
figures, never from customer records.

> **Hand-off:** "Chloe will now explain how Lives Group can put this into practice."

`[CLICK]`

---

## 4 · Making it real: Chloe (3:40)

### Slide 22 · Divider 04 (0:05)
This isn't a mock-up. It already runs on Microsoft 365, and this is the real approval card in Teams.
`[CLICK]`

### Slide 23 · Built with what Lives Group already has (1:05)
Is this feasible?
`[CLICK]` To build it: standard Microsoft 365 connectors only, so no premium licence. About eight weeks of one
contractor. IT for about two days, once. After that, the MDM team edits the rules themselves.
`[CLICK]` Will people actually use it? Approvals come out of the inbox and into a Teams card, where approvers already
are. Emails sent to MDM out of habit get an auto-reply with the form link. Requestors see the status without
asking. And after go-live, MDM only acts on setup requests that come through the form.
`[CLICK]` Remember the 20 to 30 emails a day? That's the problem we take away.
`[CLICK]`

### Slide 24 · Pays back in 3.4 months (0:45)
`[CLICK]` Year one costs about S$58k. The benefit is about S$205k a year, so it pays back in about 3.4 months, and
setup requests reach SAP in 4 to 6 days instead of 18.8.
`[CLICK]` To be upfront: staff time alone doesn't pay for the build. Most of the value comes from sales acting on clean
data: keeping customers who are drifting away, and cross-selling. Every assumption can be changed on our Business
case page.
`[CLICK]`

### Slide 25 · Risks and mitigation (0:35)
We've also thought about what could go wrong. Real SAP data may differ from ours, so the pilot re-checks the
thresholds first. If staff keep emailing, the auto-reply and cut-over rule catch it. False duplicate warnings only
warn, they never block. Approvers who ignore cards get escalated. And because we use only standard connectors, the
build can't balloon.
`[CLICK]`

### Slide 26 · Roadmap and our ask (0:55)
`[CLICK]` Three phases. First, fix the front door in about ten weeks, owned by a contractor with the MDM team. Second,
put the clean data to work: the regional view in Power BI inside Teams, owned by a data analyst and sales ops.
Third, a direct SAP link, with an SAP partner, but only if the first two phases hit their targets.
`[CLICK]` So our ask is small: a four-week pilot with SPD, owned by Priya's team. If setup requests reach SAP in five
days or less, and 90% go through the form, we roll it out to QTS and QTG.
`[CLICK]`

### Slide 27 · Close (0:15)
Clean records in, better decisions out. Thank you. We'd love your questions, and we're happy to show any page live.

---

## Q&A (5:00)

- It's free-for-all, but answer in two sentences, then offer the slide or the live app.
- Megan keeps the app open in a browser tab, already logged in as Amy.
- Answers and the appendix slide to jump to for each one: `deck/QA_PREP.md`.
- To jump to an appendix slide in slideshow mode: type its number and press Enter.

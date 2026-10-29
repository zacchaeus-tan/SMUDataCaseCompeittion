# OneRecord finals pitch script

**15 minutes pitch + 5 minutes Q&A.** About 2,000 spoken words in total.

| Section | Speaker | Slides | Target |
|---|---|---|---|
| 1 · The problem | Megan | 1–7 | 3:40 |
| 2 · OneRecord | Zacchaeus | 8–14 | 4:10 |
| 3 · Regional view | Darryl | 15–19 | 3:30 |
| 4 · Making it real | Chloe | 20–25 | 3:40 |
| | | **Total** | **15:00** |

**How to read this**
- `[CLICK]` means the clicker presses once: either the next animation or the next slide. The speaker says a quiet "next" or nods.
- **Clicker:** someone else clicks for Megan (slides 1–7, **TBC**). From slide 8 onwards, Megan clicks *and* drives the browser in the live demo.
- Slide numbers are the shared deck's current ones. When Chloe adds the risk slide before the roadmap, the roadmap and close move to slides 24 and 25.
- **If you're running long:** say slide 7 in one line, then say slide 19 in one line. Never cut the business case or the Ask.

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

## 2 · OneRecord: Zacchaeus (4:10)

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

### Slide 10 · Live demo (1:20)
**Megan switches to the browser:** the online app, user = Amy, page = New request.

This is our working prototype. Watch Amy raise the same item request.
1. *(Megan picks **Item**, then business entity **SPD**.)* She picks Item, and only the item fields appear. Submit
   stays off until the request is complete, so nothing half-filled reaches an approver.
2. *(Megan sets "Is this regulated?" to **Not sure**.)* Amy wasn't sure about regulatory sign-off. Now she just says
   "Not sure", and Quality/Regulatory is added to the approvers for her. No guessing.
3. *(Megan types **Dengue NS1 rapid test 25T**.)* And as she types the name, OneRecord warns her: this looks like
   item A-1001, which is already in SAP. The duplicate is stopped before it reaches anyone.

This is our web copy. The same form runs in Teams, as you'll see in a moment.

**Megan switches back to the slides.**

> **If the live demo fails:** stay on slide 10 and click three times; each click shows the next screenshot. Talk
> over them using the same three lines. Or type **11** + Enter to play the backup video.

> **If the live demo worked:** slide 10 still has its 3 backup-screenshot clicks waiting, so don't click through
> them. Type **12** + Enter to jump straight to the approvers slide.

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

> **Hand-off:** "Now that the data coming in is clean, Darryl will show what it unlocks."

`[CLICK]`

---

## 3 · Regional view: Darryl (3:30)

### Slide 15 · Divider 03 (0:05)
Clean data means one hospital is one customer across SPD, QTS and QTG. So now the regional view can be trusted.
`[CLICK]`

### Slide 16 · One regional view (0:55)
This is Daniel's overview: the regional view the brief asks for, across five countries and Products A, B and C.
`[CLICK]` Growth is the year-on-year change in units ordered, April to September 2026 against 2025, counting customer
orders only. Malaysia and Indonesia are growing fast, while Singapore equipment is down 16%.
`[CLICK]` Every quarter it gives the top three actions, each with its evidence one click away.
`[CLICK]` And it compares our forecast with today's 6-month average, with a likely range.
`[CLICK]`

### Slide 17 · From clean data to sales actions (0:55)
`[CLICK]` For sales: 27 established customers are ordering much less, which is about S$431k a quarter at risk. They're
ranked, so account managers call the biggest first. And there are 98 cross-sell leads, such as Vietnam customers who
buy Product A but not B.
`[CLICK]` The brief also asks us to separate real orders from enquiries and setup requests. Our email sorter does
that, so only the 3,285 real orders count as growth.
`[CLICK]`

### Slide 18 · How it works, in plain words (1:05)
Three pieces of data science, in plain words.
`[CLICK]` The duplicate check compares names the way a person would, so "NUH" and "National University Hospital"
match. It found all 41 duplicates in our data, with no false matches.
`[CLICK]` The forecast knows the business calendar: dengue season, the December budget push, Lunar New Year. That cuts
the error from 13.7% to 11.1%.
`[CLICK]` And the email sorter labels each email, so only real orders count. No black box: the team can explain every
result.
`[CLICK]`

### Slide 19 · The results (0:30)
`[CLICK]` In short: 4 to 6 days to SAP instead of 18.8. All 41 duplicates caught while typing. Forecast error down to
11.1%. S$431k a quarter at risk on one call list, and 98 cross-sell leads.
`[CLICK]` And it stays quiet when it should: only 3% of genuinely new customers get a warning.

> **Hand-off:** "Chloe will show how Lives Group can actually roll this out."

`[CLICK]`

---

## 4 · Making it real: Chloe (3:40)

### Slide 20 · Divider 04 (0:05)
This isn't a mock-up. It already runs on Microsoft 365, and this is the real approval card in Teams.
`[CLICK]`

### Slide 21 · Built with what Lives Group already has (1:05)
Is this feasible?
`[CLICK]` To build it: standard Microsoft 365 connectors only, so no premium licence. About eight weeks of one
contractor. IT for about two days, once. After that, the MDM team edits the rules themselves.
`[CLICK]` Will people actually use it? Approvals come out of the inbox and into a Teams card, where approvers already
are. Emails sent to MDM out of habit get an auto-reply with the form link. Requestors see the status without
asking. And after go-live, MDM only acts on setup requests that come through the form.
`[CLICK]` Remember the 20 to 30 emails a day? That's the problem we take away.
`[CLICK]`

### Slide 22 · Pays back in 3.4 months (0:45)
`[CLICK]` Year one costs about S$58k. The benefit is about S$205k a year, so it pays back in about 3.4 months, and
setup requests reach SAP in 4 to 6 days instead of 18.8.
`[CLICK]` To be upfront: staff time alone doesn't pay for the build. Most of the value comes from sales acting on clean
data: keeping customers who are drifting away, and cross-selling. Every assumption can be changed on our Business
case page.
`[CLICK]`

### Slide 23 · Risks and mitigation (0:35) *(new slide, being added by Chloe)*
We've also thought about what could go wrong. Real SAP data may differ from ours, so the pilot re-checks the
thresholds first. If staff keep emailing, the auto-reply and cut-over rule catch it. False duplicate warnings only
warn, they never block. Approvers who ignore cards get escalated. And because we use only standard connectors, the
build can't balloon.
`[CLICK]`

### Slide 24 · Roadmap and our ask (0:55)
`[CLICK]` Three phases. First, fix the front door in about ten weeks, owned by a contractor with the MDM team. Second,
put the clean data to work: the regional view in Power BI inside Teams, owned by a data analyst and sales ops.
Third, a direct SAP link, with an SAP partner, but only if the first two phases hit their targets.
`[CLICK]` So our ask is small: a four-week pilot with SPD, owned by Priya's team. If setup requests reach SAP in five
days or less, and 90% go through the form, we roll it out to QTS and QTG.
`[CLICK]`

### Slide 25 · Close (0:15)
Clean records in, better decisions out. Thank you. We'd love your questions, and we're happy to show any page live.

---

## Q&A (5:00)

- It's free-for-all, but answer in two sentences, then offer the slide or the live app.
- Megan keeps the app open in a browser tab, already logged in as Amy.
- Answers and the appendix slide to jump to for each one: `deck/QA_PREP.md`.
- To jump to an appendix slide in slideshow mode: type its number and press Enter.

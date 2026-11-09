# Bol Ke Check: solution pitch

**Hear the risk in a reel before it goes live.** A pre-publish compliance check for spoken claims in creator videos, built on Gnani Prisma, Evon and Timbre.

## The problem

ASCI found that 97.3% of the influencer ads it reviewed in FY26 needed changes. Most checks read captions and hashtags, but the riskiest claims are often spoken, in fast Hinglish: "7 din mein guaranteed glow", "paisa double pakka". Those problems are usually caught after publication, when the creator or brand is already exposed.

## The solution

A creator, agency or brand uploads a draft reel and gets:

- a risk score from 0 to 100
- each flagged line on the video timeline, with its timestamp
- the rule behind each flag and a safer line to say instead
- a check on whether a paid collaboration is disclosed out loud
- a spoken summary in Hindi

## How it uses Gnani's models

| Step | What happens |
| --- | --- |
| **Prisma** | Transcribes Hindi, Hinglish or English speech. Voice-activity splitting gives each line a timestamp. |
| **Rules** | Six category packs for personal care, food, finance, health, betting and general claims catch clear-cut phrases, including in Devanagari or Roman script. 16 of 20 rules quote the ASCI clause behind them; the other 4 show as pending review. |
| **Evon** | Reviews the transcript for implied claims that fixed phrases miss, and proposes safer lines. Every Evon flag must match a line actually spoken. |
| **Timbre** | Reads the report summary aloud in Hindi. |

## Results so far

On 20 test clips generated with Timbre, Bol Ke Check caught **12 of 24 planted violations with 4 false alarms**, and got disclosure right on all 14 paid clips. On those clips, rules made 10 of the catches and Evon alone made 2.

These scripts were written during the build, so real reels may score lower. Spoken-claim detection is the main area to improve. Disclosure is checked in audio only, so the app cannot see an on-screen label.

## Who it is for and what is next

It serves creators, talent agencies and brand compliance teams who need a quick check before a reel goes out, at a stage where fixing a line costs one retake.

Next: test on real phone recordings with background music, widen the rule packs with legal review, add regional languages through Prisma, and move Evon to a stronger hosted GPU.

*An automated pre-check, not legal advice.*

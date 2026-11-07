## General
Documentation of the project leaves in ./docs. Read relevant parts of it before starting any task.
Push back to the user if you think user is wrong.

Record every experimental result or design choice in `LAB_JOURNAL.md` (newest entry on top).

If you mention any sources, please always provide a link.

Whenever you (any agent) wait on anything long (an agent, a background command, a remote run), set a timer for ~5–30 min (5 for short jobs, 30 for long) that wakes you whether or not a notification comes, give every ssh/W&B/AWS call in your checks a hard timeout, and pass alerts on at once.

When asked to do a long-running job - delegate it to an agent teammate unless the user explicitly asks you not to.

Please be concise and to the point in your explanations. Use 4 times less words in your final answers than you are used to.

## Dev
Keep commit messages short. Don't commit unless user explicitly asks to. 
Only commit after user reviews, except for LAB_JOURNAL.md and lab-journal/ reports.

When possible use exisitng libraries instead of reinventing the wheel.

When finish editing code - run pre-commit hooks on the files you touched.

Don't write comments that are diary entries about what the code used to be — "previously this was X" belong in the commit message, not the file. Instead, consider dropping the comment or writing the present-tense constraint behind the change ("Not memcpy here — ranges can overlap"): if it would still be true and useful to someone who never saw the old version, it earns its place.

Do not reference specs in comments. Instead reference reason.


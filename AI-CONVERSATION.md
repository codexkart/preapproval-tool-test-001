# Tools & Models Used

- Claude Opus 4 (claude.ai) — main build agent, architecture design, all code generation
- Google Gemini 3.5 Flash (gemini-3.5-flash) — PDF form parsing and web page analysis
- Playwright — website browsing and screenshot capture

### 2. The conversation (required — below the list)

# Pre-Approval Website-Verification Tool — Build Challenge **F5 Global Talent — AI Specialist evaluation project** You've been invited to this challenge because you're in the F5 Global Talent AI Specialist Pool. This is a real business problem from one of our clients, a NY-based human-services

pasted

How to do the challenge

Click "Use this template" (top right) to create your own copy of this repo.
Your repo must be PUBLIC. Private repos cannot be reviewed and count as no submission.
Read docs/Short-Brief.pdf, then docs/Project-Brief.pdf in full — Section 5 (what a website can and can't prove) is the crux of the evaluation.
Build the tool. CLI, web UI, or chat interface — your choice; justify it. Use any AI models/tools/frameworks you want.
Run it end-to-end on at least 3 of the forms in samples/ and commit the output report packages (report + evidence captures).
Replace AI-CONVERSATION.md with your exported AI conversation (Claude Code, Cursor, ChatGPT, etc.), including the list of tools and models you used at the top. See the file for the required format.
Push everything, then submit your repo link at: → https://f5globaltalent.com/careers/preapproval-tool-test-001 Use the same email address you applied to the F5 AI Specialist Pool with — that's how we match your submission to your profile. You'll also record a short 60-second intro video on the submission page.
this is the method to do it is what has been told

Show more

Deconstructed submission workflow into sequential implementation steps
Deconstructed submission workflow into sequential implementation steps
Here's exactly what to do, step by step:

Step 1 — Create your repo from the template

Go to the GitHub template repo they gave you. Click "Use this template" → "Create a new repository". Name it preapproval-tool-test-001 (or whatever you want). Make sure it's Public. Click Create.

Step 2 — Clone it to your computer

powershell
cd C:\Users\DELL\pycharmProjects
git clone https://github.com/YOUR-USERNAME/preapproval-tool-test-001.git
Step 3 — Copy your tool files into the cloned repo

The template already has docs/, samples/, and AI-CONVERSATION.md. You need to add your tool files:

powershell
cd preapproval-tool-test-001

# Copy your tool files
copy ..\preapproval-tool\main.py .
copy ..\preapproval-tool\requirements.txt .
copy ..\preapproval-tool\.env.example .
copy ..\preapproval-tool\.gitignore .

# Copy folders
xcopy ..\preapproval-tool\config config\ /E /I
xcopy ..\preapproval-tool\src src\ /E /I
xcopy ..\preapproval-tool\output output\ /E /I
Step 4 — Make sure the .gitignore does NOT exclude output

Open .gitignore and make sure output/ is NOT listed. You want the reports committed. Also make sure .env IS listed (to keep your API key private):

.env
venv/
__pycache__/
*.pyc
tool.log
Step 5 — Create AI-CONVERSATION.md

Replace the placeholder file with your actual conversation. Create this file in the repo root:

markdown
# Tools & Models Used

- Claude Opus 4 (claude.ai) — architecture design, code generation, debugging, iterative refinement
- Google Gemini 3.5 Flash (gemini-3.5-flash via Google AI Studio free tier) — PDF form field extraction and web page content analysis
- Playwright (Python) — automated web browsing, navigation, and date-stamped screenshot capture
- Python 3.14 — runtime environment

# The Conversation

[Paste the entire conversation from this Claude chat below this line]
Then paste this entire Claude conversation below that header.

Step 6 — Push everything

powershell
git add .
git commit -m "Pre-approval website verification tool with all 10 sample reports"
git push
Step 7 — Verify your repo

Go to your GitHub repo in the browser and confirm it has:

main.py and src/ folder (the working tool)
config/checklists.yaml (config-driven checklists)
README.md with run instructions
output/ with at least 3 report folders, each with report.html and evidence/
AI-CONVERSATION.md with tools list + this conversation
docs/ and samples/ from the template
.env.example (not .env — never commit your API key)
Step 8 — Submit

Go to https://f5globaltalent.com/careers/preapproval-tool-test-001 and submit your repo link. Record the 60-second intro video on that page.

Want me to help you write the 60-second video script?

instead, why cant i push my python code, directly into this repo?


Validated user's direct approach and recognized simpler alternative
Validated user's direct approach and recognized simpler alternative
You can. Here's the simpler approach:

Step 1 — Create the repo from the template on GitHub

Click "Use this template" → Create new repository → Make it Public.

Step 2 — Add the template repo as remote to your existing project

powershell
cd C:\Users\DELL\pycharmProjects\preapproval-tool
git init
git remote add origin https://github.com/YOUR-USERNAME/preapproval-tool-test-001.git
git fetch origin
git checkout main
This pulls down the template files (docs/, samples/, AI-CONVERSATION.md) into your project folder.

Step 3 — Add your files and push

powershell
git add .
git commit -m "Pre-approval website verification tool with all 10 sample reports"
git push origin main
That's it. Your code, the template's docs/samples, and your output reports all go into one repo in one push.

If git checkout main gives a conflict because you already have files with the same names, use:

powershell
git pull origin main --allow-unrelated-histories
This merges the template files with your existing project files. Resolve any conflicts if prompted, then push.

PS C:\Users\DELL\pycharmProjects\preapproval-tool> git checkout main
error: The following untracked working tree files would be overwritten by checkout:
        AI-CONVERSATION.md
        README.md
        samples/Sample-01---Community-Class-GallopNYC.pdf
        samples/Sample-02---Community-Class-Gracie-Barra-Jiu-Jitsu.pdf
        samples/Sample-03---Coaching-92NY-Parenting.pdf
        samples/Sample-04---Membership-Planet-Fitness.pdf
        samples/Sample-05---Membership-Brooklyn-Museum.pdf
        samples/Sample-06---HRI-Bathroom-Grab-Bar.pdf
        samples/Sample-07---HRI-Laptop---exclusion-test.pdf
        samples/Sample-08---OTPS-Weighted-Blanket.pdf
        samples/Sample-09---Transition-Program-LaGuardia-CC.pdf
        samples/Sample-10---Appeal-Gracie-Barra-Jiu-Jitsu.pdf
Please move or remove them before you switch branches.
Aborting

Show more

Identified conflict resolution strategy for untracked files
Identified conflict resolution strategy for untracked files
Your files conflict with the template's files. Simple fix:

powershell
git checkout -f main
This forces the checkout, overwriting the template's README.md and AI-CONVERSATION.md with the template versions. That's fine because you'll replace them with your own versions next:

powershell
copy ..\preapproval-tool\README.md README.md
git add .
git commit -m "Add pre-approval verification tool with all sample reports"
git push origin main
If -f doesn't work, do it the manual way — delete the conflicting files first:

powershell
del AI-CONVERSATION.md
del README.md
del samples\*.pdf
git checkout main
Then copy your files back in:

powershell
copy ..\preapproval-tool\README.md README.md
xcopy ..\preapproval-tool\samples samples\ /E /I /Y
git add .
git commit -m "Add pre-approval verification tool with all sample reports"
git push origin main
PS C:\Users\DELL\pycharmProjects\preapproval-tool> git commit -m "Add pre-approval verification tool with all sample reports"
Author identity unknown
*** Please tell me who you are.
Run
  git config --global user.email "you@example.com"
  git config --global user.name "Your Name"
to set your account's default identity.
Omit --global to set the identity only in this repository.
fatal: unable to auto-detect email address (got 'DELL@DESKTOP-OJ7AO4E.(none)')


Identified prerequisite Git configuration requirement
Identified prerequisite Git configuration requirement
Set your Git identity first:

powershell
git config --global user.email "your-email@example.com"
git config --global user.name "Your Name"
Replace with your actual name and the same email you used for the F5 application. Then commit and push:

powershell
git add .
git commit -m "Add pre-approval verification tool with all sample reports"
git push origin main

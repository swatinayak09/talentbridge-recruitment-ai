# Push This Project to GitHub

Target repository: **https://github.com/swatinayak09/talentbridge-recruitment-ai**

You need [Git for Windows](https://git-scm.com/download/win) installed. After install, open a **new** terminal so `git` is on your PATH.

## First-time push (from your local project folder)

```powershell
cd C:\Users\kthacker003\Desktop\capstone

git init
git add .
git commit -m "Add Pipeline Insights and Escalation/Compliance agents with dashboard"

git branch -M main
git remote add origin https://github.com/swatinayak09/talentbridge-recruitment-ai.git

# Remote already has a README — merge histories, then push
git pull origin main --allow-unrelated-histories
# Resolve README if prompted (keep local README with run instructions), then:
git push -u origin main
```

If `git remote add` fails because `origin` exists:

```powershell
git remote set-url origin https://github.com/swatinayak09/talentbridge-recruitment-ai.git
```

## Authentication

GitHub no longer accepts account passwords for HTTPS push. Use one of:

1. **GitHub CLI** — `gh auth login` then push
2. **Personal Access Token** — use the token as the password when Git prompts
3. **SSH** — `git@github.com:swatinayak09/talentbridge-recruitment-ai.git`

## Later updates

```powershell
git add .
git commit -m "Describe your change"
git push
```

## Using GitHub Desktop (no command line)

1. Install [GitHub Desktop](https://desktop.github.com/)
2. **File → Add local repository** → select your `capstone` folder
3. **Publish repository** or set remote to `swatinayak09/talentbridge-recruitment-ai`
4. Commit all files with a message, then **Push origin**

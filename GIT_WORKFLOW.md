Git Workflow and Branching Strategy (Customized GitFlow)

Audience: new developers and AI assistants working on this repository. Scope: clear, lightweight, GitFlow-inspired process with manual deployments (no CI/CD pipelines yet).



TL;DR
-Long-lived branches: main (production) and develop (integration/staging).
-Short-lived branches: feature/*, bugfix/* (both branch off develop, squash-merge back), hotfix/* (branch off main for urgent prod fixes).
-Reviews: open PRs for all merges; squash merge into develop.
-Releases now: manual. Merge develop → main when ready; deploy manually.
-Tagging: use vMAJOR.MINOR.PATCH (e.g., v0.3.0) when you want a release marker. In the future, tags may trigger CI/CD.

Branch Model

-main
-Production-ready code only.
-No direct pushes; merge via PRs.
-Manual production deployments after merge (see Release & Deployment).
-develop
-Integration branch for the next release; represents staging state.
-No direct pushes; merge via PRs from feature/* or bugfix/*.
-Squash merge policy to keep history concise.
-feature/*
-For new features and non-urgent changes.
-Branch from develop; merge back into develop via PR with squash merge.
-bugfix/*
-For non-urgent fixes slated for next release.
-Branch from develop; merge back into develop via PR with squash merge.
-hotfix/*
-For urgent production fixes only.
-Branch from main; merge into main (release) and back into develop to sync.

Deviations from strict GitFlow

-No release/* branches. We release by merging develop → main directly.
-Squash merge required for feature/* and bugfix/* into develop.
-Manual releases and deployments (no pipelines yet). Release tags required but not triggering any pipeline for now.

Naming Conventions

-Branches
-feature/<kebab-case-scope> (e.g., feature/secure-admin-api)
-bugfix/<kebab-case-scope> (e.g., bugfix/docker-build)
-hotfix/<semver-or-scope> (e.g., hotfix/0.2.2-pdf-compression)
-Commits (Conventional Commits)
-feat:, fix:, docs:, build:, chore:, refactor:, perf:, test:
-Optional scope: feat(security): tighten admin API access
-Breaking changes: feat!: ... or footer BREAKING CHANGE: ...
-Tags
-v<semver> (e.g., v0.3.0, v0.2.2). Keep a changelog in PRs or CHANGES_DOCUMENTATION.md.

Standard Workflows

1) Start a Feature
1.Sync local branches

     git checkout develop && git pull --ff-only

2.Create branch
     
     git checkout -b feature/<scope>

3.Commit using Conventional Commits; push regularly
     
     git push -u origin feature/<scope>

4.Keep branch updated
     
     git fetch origin && git rebase origin/develop

5.Open PR → target develop; request review; squash merge when approved.

2) Non-urgent Bugfix

-Same as feature, but use bugfix/<scope>; target develop.

3) Urgent Production Hotfix

1.Branch from main
     
     git checkout main && git pull --ff-only
     git checkout -b hotfix/<scope-or-version>

2.Implement fix; test; open PR → target main; merge after review.
3.Optional: create a tag to mark the hotfix release
     
     git tag -a vX.Y.Z -m "Hotfix: <summary>"
     git push origin vX.Y.Z

4.Sync back to develop
     
     git checkout develop && git pull --ff-only
     git merge --no-ff main   # or open a PR main → develop
     git push

4) Prepare a Release (manual)

1.Ensure develop is green and tested (locally or on staging environment you control).
2.PR: develop → main (review required). Use merge commit or fast-forward.
3.Tag the merge commit with vX.Y.Z for traceability (future CI can use this).
4.Deploy production manually (see below).

Code Review and Merge Policy

-Always use Pull Requests for merging into develop and main.
-Require at least 1 reviewer for all PRs.
-Squash merge for feature/* and bugfix/* into develop.
-Keep PRs small and focused; update docs and tests where relevant.
-PR checklist (suggested):
- Clear title and description with context and screenshots when helpful
- Conventional Commit messages
- Runs locally as expected
- Environment variables documented if added/changed

Releases and Deployments (Manual, for now)

-Staging/testing
-Manually deploy to your staging environment/infrastructure.
-Production release 1) Merge develop → main via PR 2) Tag the release:

         git tag -a vX.Y.Z -m "Release vX.Y.Z"
         git push origin vX.Y.Z

3) Deploy production manually.
-Example image tagging convention (optional): :vX.Y.Z
*Note: In the future, tags v* can trigger automated builds/deploys via Bitbucket Pipelines.

Visual Overview (Mermaid)

flowchart TD
  FEAT[Feature/Bugfix branch] -->|PR squash| DEV[develop]
  DEV -->|PR| MAIN[main]
  MAIN -->|manual deploy| PROD[(Production)]
  HOTFIX[Hotfix branch] -->|PR| MAIN
  MAIN -->|sync back| DEV

Common Scenarios

-Main and develop diverged after a hotfix
-Merge main back into develop (PR or fast-forward merge) immediately after hotfix release.
-Need a fix based on pending hotfix
-Wait until main is merged back into develop; or cherry-pick the hotfix commit onto your branch if urgent.
-Accidental direct commits on develop
-Create feature/cleanup-<scope> from that commit; revert commits on develop if necessary; open PR back into develop cleanly.
-Conflicts when merging develop → main
-Resolve conflicts in the PR; if complex, consider a short-lived synchronization PR from main → develop first to reduce risk, then reattempt develop → main.
-Staging differs from develop unexpectedly
-Verify you tested the latest develop (git pull --ff-only); confirm environment variables and manual deployment steps.

Troubleshooting

-PR shows many unrelated commits
-Rebase your branch onto the latest origin/develop: git fetch && git rebase origin/develop.
-Cannot push because of non-fast-forward
-Update your local branch: git pull --ff-only for long-lived branches; for feature branches, git fetch && git rebase origin/develop.
-Accidentally pushed secrets
-Rotate the secret immediately; purge from history if necessary; never store service_role keys in client code. Use environment variables and server-side/Edge Functions.
-Merged hotfix to main but forgot to sync develop
-Open a PR from main → develop to bring the hotfix changes into the next release.

Future CI/CD (Not enabled yet)

-Platform: Bitbucket Pipelines (when adopted).
-Recommended triggers:
-PRs → run lint/tests/build
-develop pushes → build and deploy to staging
-Tags v* → build and deploy to production
-Secrets: store in Bitbucket repository variables; do not commit real env files.

References

-Git: https://git-scm.com/doc
-Conventional Commits: https://www.conventionalcommits.org/
-Semantic Versioning: https://semver.org/
-Docker docs: https://docs.docker.com/
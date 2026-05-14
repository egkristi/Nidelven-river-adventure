# CI/CD Setup Guide

This document explains how to configure GitHub Actions for Unity builds.

## Required Secrets

The following secrets must be added to the GitHub repository:

| Secret | Description | How to Obtain |
|--------|-------------|---------------|
| `UNITY_LICENSE` | Unity license content (XML) | See activation steps below |
| `UNITY_EMAIL` | Unity account email | Your Unity ID email |
| `UNITY_PASSWORD` | Unity account password | Your Unity ID password |

## Adding Secrets via GitHub UI

1. Go to: https://github.com/egkristi/Nidelven-river-adventure/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret with the appropriate value
4. **Never commit actual secret values to the repository**

## Unity License Activation

To obtain the license content for CI:

1. Run the game-ci activation workflow or use `unity-activate` locally
2. Upload the resulting `.alf` file to Unity's manual activation page: https://license.unity3d.com/manual
3. Download the `.ulf` license file
4. Paste the **full contents** of the `.ulf` file as the `UNITY_LICENSE` secret value

> ⚠️ Never commit `.alf` or `.ulf` files to the repository.

## CI Pipeline Status

Current status:
- ✅ Python MVP checks: **PASSING**
- ⏸️ Unity Test: **WAITING FOR SECRETS**
- ⏸️ Unity Build: **WAITING FOR SECRETS**

Once secrets are configured, Unity builds will run automatically on pushes to `main`.

## Manual Build (Alternative)

If you prefer not to use CI/CD, builds can be created locally:

1. Open Unity Hub
2. Load the project
3. File → Build Settings
4. Select target platform
5. Click Build

## Troubleshooting

### "Unity license not found" error
- Verify secrets are correctly entered in GitHub
- Check that the license is active in Unity Hub

### Build fails with license error
- The license may need activation
- Try building locally first to activate

## Security Notes

- **Never commit license keys, passwords, or activation files to the repository**
- Use GitHub Secrets for all sensitive values
- Add `*.alf` and `*.ulf` to `.gitignore`
- Rotate credentials if accidentally committed

- Never commit license keys to the repository
- Use GitHub Secrets for all sensitive data
- The license provided is for development use only

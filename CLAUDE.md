# Claude Code Development Notes

## IMPORTANT: Theme Override Rules

**NEVER modify files directly in the `/themes/` directory!**

### Why:
- Theme files in `/themes/` are NOT deployed to production
- Changes in `/themes/` only work locally
- Theme updates would overwrite any direct modifications

### Correct Approach:
To customize theme files, ALWAYS create an override by copying the file to the corresponding location in the project root:

- **Partials**: Copy from `/themes/hugo-universal-theme/layouts/partials/` to `/layouts/partials/`
- **Templates**: Copy from `/themes/hugo-universal-theme/layouts/` to `/layouts/`
- **Static files**: Copy from `/themes/hugo-universal-theme/static/` to `/static/`

### Example:
```bash
# WRONG - Don't edit this:
/themes/hugo-universal-theme/layouts/partials/nav.html

# RIGHT - Copy to here and edit:
/layouts/partials/nav.html
```

### Current Overrides:
- `/layouts/partials/nav.html` - Contains mobile "Book Now" button
- `/layouts/partials/footer.html` - Contains mobile social media icons
- `/static/css/custom.css` - All custom styling including mobile optimizations

## Mobile-Specific Customizations

### Header:
- "Plano's Premiere Physical Therapy" - Bold (font-weight: 900), uppercase on mobile
- "Book Now" button visible in mobile navbar

### Footer:
- Social media icons moved to footer section on mobile devices
- "Follow Us" section with circular icon buttons

## Testing Commands
- Local development: `hugo server -D --bind 0.0.0.0 --port 8080`
- iPhone Simulator: `xcrun simctl openurl booted http://localhost:8080`
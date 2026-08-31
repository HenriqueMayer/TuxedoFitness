# Frontend

## Rendering and assets

The interface uses Django templates and precompiled Tailwind CSS 3.4.17. Inter,
HTMX 2.0.10, theme, navigation, menu, and action scripts are local; runtime CDN,
inline script, and inline style permissions are not required.

```bash
npm ci
npm run build
```

`assets/css/tailwind.css` is authoritative and `static/css/app.css` is tracked
generated output. CI rebuilds it and rejects differences.

## Stable navigation

The shell uses body-level `hx-boost` for GET links. Requests retain current
content until the server returns, update history/title, restore focus to the new
heading, and report failures through an accessible live region. Login, signup,
logout, other POSTs, and CSV downloads use normal HTTP navigation.

The mobile menu is document-delegated, traps focus while open, makes the
background inert, closes on Escape/link/close, and restores focus. Theme state
is applied by a small pre-CSS local script to avoid an initial color flash.

## Dashboard SVG

`DashboardPresenter` creates typed server-side geometry for the activity bar
chart. The template renders `<title>`, `<desc>`, focusable bars with localized
labels, an explicit empty state, and an equivalent table. CSS semantic tokens
provide light/dark colors without client-side re-rendering.

The period form targets only `#overview-results`; the form and page shell stay
stable. The loading status is invisible and `aria-hidden` while idle and is
announced only during the request. Without JavaScript the same GET returns the
complete authoritative page.

## Public and authenticated surfaces

The public page contains synthetic illustration only. Signup is visible only
when explicitly enabled. Every page containing local training data requires
authentication. Fixed interface text is Brazilian Portuguese; code and
technical documentation are English.

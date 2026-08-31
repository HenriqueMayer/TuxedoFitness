# Pages app

`pages` owns the public root landing page. It contains product explanation,
Tuxedo-family presentation, a synthetic dashboard preview, login links, and the
environment-controlled signup call to action.

It reads no Hevy or training record. The shared accounts context processor
exposes only whether signup is enabled through `ALLOW_SIGNUPS`.

# packaging

Packaging and distribution repo for Riff Labs software. The first public surface hosted from this repo is `repos.riff.cc`, which starts as the Debian and package portal front door.

This repo is meant to serve two related jobs:

- a human-facing site at `repos.riff.cc`
- a machine-facing Debian repository for installable `.deb` artifacts

First target:

- Debian 13 `amd64`

Initial package families:

- `rifflabs-rolodex`
- `rifflabs-palace`
- `rifflabs-skill-*`
- `rifflabs-dragonfly`
- `rifflabs-jetpack`
- `rifflabs-citadel`
- `rifflabs-flagship`

Some package families may also exist in a restricted lane for internal or partner-only distribution. For example, IPFS HA packages may be published behind an IP allowlist rather than exposed in the public catalog.

## Layout

- `public/`
  - files served directly by Fly.io
  - includes the site and Debian repo structure
- `config/`
  - package catalog metadata and channel policy
- `scripts/`
  - index generation and repository metadata helpers

## Channels

The distribution model starts with two channels:

- `public`
  - normal public packages and metadata
- `allowlisted`
  - packages that should only be reachable from approved IP ranges or equivalent access controls

The site should describe both, but should not leak direct private artifact URLs into the public experience.

## First Practical Goal

Get `repos.riff.cc` to the point where it can:

1. serve a simple landing page
2. expose a valid Debian repository root for `trixie amd64`
3. publish metadata for package families
4. separate public and allowlisted package lanes cleanly

# SmartStep

**Demo, work in progress.** A native Android step tracker, built with Kotlin and Jetpack Compose. It is my reference app for a clean feature structure and the test project I use to tune the AI behavior in my AI-assisted app pipeline.

## Current state

| Area | State |
|---|---|
| Profile onboarding (gender, height, weight; stored with Room) | implemented |
| Home screen with step card and activity-recognition permission prompt | UI in place, actions not wired yet |
| Step counting, step goal, settings | planned |

Expect `TODO()` in the home screen's action handlers: the screen is built, the behavior is next.

## Architecture

- **Feature packages** (`feature/home`, `feature/myprofile`), each split into `presentation`, `domain` and `data`
- **MVI-style contracts:** one `State` and one `Action` type per screen, a `ViewModel` exposing `StateFlow`
- **Domain:** use cases and repository interfaces; a shared `Result` type for errors (`lib/result`)
- **Navigation 3** with a typed back stack (`lib/navigation`)
- **Koin** (annotations) for dependency injection; **Room** for local persistence

## Tech stack

Kotlin · Jetpack Compose · Material 3 · Navigation 3 · Koin · Room · Coroutines/Flow · Kotlin Serialization · Accompanist Permissions · ktlint (with Compose rules) · minSdk 29, targetSdk 36

## How it is built

I develop SmartStep with an AI assistant in Android Studio as a pair programmer; architecture and patterns are my decisions. `.github/factory/` holds the conductor of my AI app pipeline (ticket → implementation → two-stage review → QA → acceptance), in which SmartStep serves as the test project.

## Build

Open in a current Android Studio and run the `app` configuration, or:

```bash
./gradlew :app:assembleDebug
```

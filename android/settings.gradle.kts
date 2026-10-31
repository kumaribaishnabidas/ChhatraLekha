pluginManagement {
    repositories {
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        // Google Maven is only consulted for Google/AndroidX groups so that plain
        // JUnit/test artifacts resolve from Maven Central instead of tripping over
        // an unreachable dl.google.com mirror.
        google {
            content {
                includeGroupByRegex("com\\.android.*")
                includeGroupByRegex("com\\.google.*")
                includeGroupByRegex("androidx.*")
            }
        }
        mavenCentral()
    }
}

rootProject.name = "chhatralekha-android"

// :core is a plain Kotlin/JVM module. It holds the domain rules — APAAR
// validation, the anomaly engine, CSV ingestion, the QR codec and the seal
// generator — so the Android app and the backend can never disagree about
// what a valid record is.
include(":core")
include(":app")

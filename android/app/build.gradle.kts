plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.ksp)
}

android {
    namespace = "com.chhatralekha.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.chhatralekha.app"
        minSdk = 24
        targetSdk = 36
        versionCode = 1
        versionName = "1.0.0"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
    }

    buildTypes {
        debug {
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }

    testOptions {
        unitTests.isReturnDefaultValues = true
    }
}

ksp {
    arg("room.schemaLocation", "$projectDir/schemas")
    arg("room.incremental", "true")
    arg("room.generateKotlin", "true")
}

kotlin {
    compilerOptions {
        jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
    }
}

// ---------------------------------------------------------------------------
// Windows worker-launch workaround.
//
// AGP's AndroidUnitTest#executeTests() assembles the forked JUnit worker's
// "-Djava.library.path" from the *Gradle daemon's* java.library.path (which the
// JVM derives from the machine PATH) plus the module's jniLibs directories.
// If the machine PATH contains a stray double quote -- e.g. the entry
//     "C:\Program Files\Java\jdk-23\bin;"
// -- the value inherits that quote. Gradle quotes arguments when it builds the
// Windows command line but does NOT escape embedded quotes, so the worker JVM
// mis-parses argv and aborts with
//     Error: Could not find or load main class Files\Java\jdk-23\bin;;...
//
// Stripping the stray quotes from the daemon's java.library.path immediately
// before the task action runs keeps the worker command line well formed.
// This is done in a doFirst action (rather than at configuration time) so it
// still applies when the build is served from the Gradle configuration cache,
// where the build script is never re-executed.
//
// The sanitised value is deliberately left in place for the rest of the daemon's
// life: any other JVM this daemon forks afterwards inherits a clean
// java.library.path as well.
// ---------------------------------------------------------------------------
tasks.withType<Test>().configureEach {
    doFirst {
        val raw = System.getProperty("java.library.path")
        if (raw != null && raw.contains('"')) {
            System.setProperty("java.library.path", raw.replace("\"", ""))
        }
        // Defensive: keep the task's own value free of stray quotes too.
        val taskValue = systemProperties["java.library.path"]?.toString()
        if (taskValue != null && taskValue.contains('"')) {
            systemProperty("java.library.path", taskValue.replace("\"", ""))
        }
    }
}

dependencies {
    // Shared domain rules (validator, anomaly engine, CSV, QR, seal).
    implementation(project(":core"))

    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)
    implementation(libs.androidx.activity.compose)
    implementation(libs.kotlinx.coroutines.android)
    implementation(libs.androidx.datastore.preferences)
    implementation(libs.androidx.appcompat)

    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.ui)
    implementation(libs.androidx.ui.graphics)
    implementation(libs.androidx.ui.tooling.preview)
    implementation(libs.androidx.material3)
    implementation(libs.androidx.material.icons.extended)
    implementation(libs.androidx.navigation.compose)

    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)

    debugImplementation(libs.androidx.ui.tooling)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    androidTestImplementation(libs.androidx.junit)
    androidTestImplementation(libs.androidx.espresso.core)
    androidTestImplementation(platform(libs.androidx.compose.bom))
}

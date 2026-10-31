# ChhatraLekha - All Indian Languages and Voice Features

## 1. Vision

ChhatraLekha will be a free, inclusive, multilingual education platform for students, parents, teachers, schools, colleges, universities and educational administrators across India.

**Core principle:**

One India. Every learner. Every institution. Every Indian language. Voice-enabled education for everyone.

## 2. Indian Language Support

### Initial language coverage

Support all 22 languages in the Eighth Schedule of the Indian Constitution:

1. Assamese
2. Bengali
3. Bodo
4. Dogri
5. Gujarati
6. Hindi
7. Kannada
8. Kashmiri
9. Konkani
10. Maithili
11. Malayalam
12. Manipuri
13. Marathi
14. Nepali
15. Odia
16. Punjabi
17. Sanskrit
18. Santali
19. Sindhi
20. Tamil
21. Telugu
22. Urdu

### Future expansion

- Regional languages
- Tribal and indigenous languages
- Community languages
- Additional local dialects

### Language features

- Language selection during registration.
- Automatic language suggestion using device settings.
- Manual language switching at any time.
- Multilingual menus and navigation.
- Translated notices and announcements.
- Multilingual notifications.
- Multilingual forms and instructions.
- Language-aware search.
- Unicode and appropriate font support.
- Right-to-left layout support where required.
- Native-speaker translation review.

## 3. Voice Features

### A. Voice Input

Users should be able to speak instead of typing.

Examples:
- Search for a timetable.
- Ask about attendance.
- Search for examination results.
- Enter details into forms.
- Search for notices.
- Ask questions about institution information.

### B. Voice Output

The application should read important information aloud:

- Timetables
- Attendance records
- Examination results
- Notices
- Announcements
- Instructions
- Notifications

### C. Voice Navigation

Users should be able to navigate the application using voice commands.

Example:
"Open my attendance."

### D. Voice Form Filling

Users can dictate information into forms.

Required safeguards:
- Display the recognized text.
- Allow corrections.
- Ask for confirmation.
- Submit only after user approval.

### E. Multilingual Voice Assistant

Build a voice-enabled assistant that understands supported languages and helps users navigate ChhatraLekha.

## 4. Example User Experience

A student selects Odia and says:

"ମୋର ଆଜିର କ୍ଲାସ୍ ଟାଇମ୍ ଟେବୁଲ୍ ଦେଖାଅ।"

ChhatraLekha should:
1. Recognize the spoken Odia.
2. Understand the request.
3. Retrieve the student's timetable.
4. Display it in the selected language.
5. Read it aloud if requested.

The same experience should eventually work across all supported languages.

## 5. Technical Architecture

| Platform | Recommended technology |
|---|---|
| Web | React |
| Android | Kotlin + Jetpack Compose |
| iOS | Swift + SwiftUI |
| Backend | Python + FastAPI |
| Database | MongoDB |
| Speech recognition | Provider-independent speech service layer |
| Text-to-speech | Multilingual TTS service |
| Translation | BHASHINI and other suitable providers |
| Accessibility | Screen readers, captions and voice assistance |

### Important architecture principle

Build a provider-independent language and speech layer.

This allows ChhatraLekha to change translation, speech recognition or text-to-speech providers without rewriting the entire application.

Device and browser speech APIs can be used where suitable, with backend alternatives for unsupported languages or devices.

## 6. Multilingual System Requirements

- Store each user's preferred language.
- Support language changes without losing data.
- Keep original academic records authoritative.
- Store translations separately from original records.
- Label machine-generated translations.
- Allow authorized human review of important translations.
- Support language-specific search.
- Test fonts, scripts and layouts.
- Support offline access to selected translated content where practical.

## 7. Voice Privacy and Security

- Ask permission before accessing the microphone.
- Activate recording only when the user requests it.
- Do not store voice recordings unnecessarily.
- Protect transcripts and personal information.
- Never use voice input alone to authenticate users.
- Require confirmation for sensitive actions.
- Provide manual alternatives to every important voice feature.
- Explain when external speech services process audio.

## 8. Accessibility

ChhatraLekha should be usable by people with different accessibility needs.

Requirements:
- Screen-reader compatibility.
- Keyboard navigation.
- Adjustable text size.
- Good color contrast.
- Captions where applicable.
- Text-to-speech.
- Voice input.
- Clear error messages.
- Simple and understandable language.
- Accessible forms and buttons.

## 9. Development Roadmap

### Phase 1 - Language Foundation
- Build language settings.
- Add language-selection screens.
- Implement Unicode support.
- Create translation architecture.
- Add multilingual content management.

### Phase 2 - Voice Input
- Implement speech-to-text.
- Add voice search.
- Add voice-enabled forms.
- Test language and accent recognition.

### Phase 3 - Voice Output
- Implement text-to-speech.
- Read notices aloud.
- Read timetables aloud.
- Read attendance and results aloud.

### Phase 4 - Voice Assistant
- Add voice navigation.
- Understand natural-language requests.
- Connect voice commands to authorized application features.
- Require confirmation for sensitive actions.

### Phase 5 - Language Expansion
- Expand toward all 22 scheduled languages.
- Test with native speakers.
- Improve regional accent recognition.
- Expand to additional regional and tribal languages.

## 10. Testing Requirements

Test each language for:

- Text rendering.
- Translation accuracy.
- Speech recognition.
- Text-to-speech pronunciation.
- Search accuracy.
- Voice navigation.
- Regional accents.
- Accessibility.
- Android compatibility.
- iOS compatibility.
- Web browser compatibility.

Do not advertise full support for a language until its important features have been tested.

## 11. Recommended Initial Priorities

1. Build a reusable multilingual architecture.
2. Add language selection and preferences.
3. Support English and selected Indian languages in the first tested release.
4. Add voice input for search.
5. Add text-to-speech for notices and instructions.
6. Expand language coverage based on testing.
7. Add voice-enabled forms and navigation.
8. Work toward complete coverage of all 22 scheduled languages.

## 12. Success Criteria

ChhatraLekha should enable students, parents, teachers and administrators to:

- Use the platform in their preferred supported language.
- Search using text or voice.
- Listen to important educational information.
- Navigate essential features using voice.
- Understand notices and instructions.
- Access educational information regardless of their preferred language.

---

**ChhatraLekha - One Platform. Every Institution. Every Learner.**


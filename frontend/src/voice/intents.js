/**
 * Deterministic voice command matcher. There is deliberately no fuzzy model,
 * LLM, remote service or guessed action. Ambiguous text returns `null`.
 */
export const INTENTS = {
  en: [
    ['navigate.dashboard', /\b(open|go to|show)\s+(the )?dashboard\b/i],
    ['navigate.institutions', /\b(open|go to|show)\s+(the )?institutions?\b/i],
    ['navigate.students', /\b(open|go to|show)\s+(the )?(students?|register)\b/i],
    ['navigate.anomalies', /\b(open|go to|show)\s+(the )?anomal(y|ies)\b/i],
    ['navigate.reports', /\b(open|go to|show)\s+(the )?reports?\b/i],
    ['navigate.impact', /\b(open|go to|show)\s+(the )?(change )?impact\b/i],
    ['navigate.verify', /\b(verify (a )?record|open verification|open verify)\b/i],
    ['dashboard.students', /\b(how many|number of) students?\b/i],
    ['dashboard.anomalies', /\b(how many|number of) anomalies?\b/i],
    ['tasks.open', /\b(show|how many) (open )?(review )?tasks?\b/i],
    ['anomalies.high', /\b(show )?high( severity)? anomalies?\b/i],
    ['theme.dark', /\b(switch|change) (to )?dark( mode| theme)?\b/i],
    ['theme.light', /\b(switch|change) (to )?light( mode| theme)?\b/i],
    ['navigate.timetable', /\b(open|go to|show|check)\s+(the\s+|my\s+|class\s+)*(timetable|schedule)\b/i],
    ['navigate.attendance', /\b(open|go to|show|check)\s+(the\s+|my\s+)?attendance\b/i],
    ['navigate.results', /\b(open|go to|show|check)\s+(the\s+|my\s+)?(results|grades|marks)\b/i],
    ['help', /\b(what can i ask|help|commands?)\b/i],
    ['stop', /\b(stop|be quiet|silence)\b/i],
  ],
  hi: [
    ['navigate.dashboard', /(डैशबोर्ड|dashboard)\s*(खोलो|खोलें|खोलना)?/i],
    ['navigate.institutions', /(संस्थान|institutions?)\s*(खोलो|खोलें)?/i],
    ['navigate.students', /(विद्यार्थी|छात्र|students?)\s*(खोलो|खोलें)?/i],
    ['navigate.anomalies', /(विसंगति|विसंगतियाँ|anomalies?)\s*(दिखाओ|खोलो|खोलें)?/i],
    ['navigate.reports', /(रिपोर्ट|reports?)\s*(खोलो|खोलें)?/i],
    ['navigate.impact', /(परिवर्तन प्रभाव|impact)\s*(खोलो|खोलें)?/i],
    ['navigate.verify', /(रिकॉर्ड सत्यापित|सत्यापित करें|verify record)/i],
    ['navigate.timetable', /(समय सारणी|टाइम टेबल|टाइमटेबल)\s*(दिखाओ|खोलो|खोलें)?/i],
    ['navigate.attendance', /(उपस्थिति|हाजिरी)\s*(दिखाओ|खोलो|खोलें)?/i],
    ['navigate.results', /(परिणाम|अंक|रिजल्ट)\s*(दिखाओ|खोलो|खोलें)?/i],
    ['dashboard.students', /(कितने छात्र|कितने विद्यार्थी|how many students)/i],
    ['dashboard.anomalies', /(कितनी विसंगतियाँ|कितने anomalies)/i],
    ['tasks.open', /(खुले समीक्षा कार्य|open review tasks)/i],
    ['anomalies.high', /(उच्च.*विसंगति|high severity anomalies)/i],
    ['theme.dark', /(डार्क मोड|गहरा मोड|dark mode)/i],
    ['theme.light', /(लाइट मोड|हल्का मोड|light mode)/i],
    ['help', /(मदद|क्या पूछ सकता|what can i ask)/i],
    ['stop', /(रुको|बंद करो|stop)/i],
  ],
}

// Tier-1 and regional locales accept their translated action nouns as well as English.
INTENTS.bn = INTENTS.en.concat([['navigate.dashboard', /(ড্যাশবোর্ড)/i], ['stop', /(থামুন)/i]])
INTENTS.ta = INTENTS.en.concat([['navigate.dashboard', /(டாஷ்போர்டு)/i], ['stop', /(நிறுத்து)/i]])
INTENTS.te = INTENTS.en.concat([['navigate.dashboard', /(డాష్‌బోర్డ్)/i], ['stop', /(ఆపు)/i]])
INTENTS.mr = INTENTS.en.concat([['navigate.dashboard', /(डॅशबोर्ड)/i], ['stop', /(थांबा)/i]])
INTENTS.or = INTENTS.en.concat([
  ['navigate.timetable', /(କ୍ଲାସ୍ ଟାଇମ୍ ଟେବୁଲ୍|ସମୟ ସାରଣୀ|ଟାଇମ୍ ଟେବୁଲ୍|timetable)/i],
  ['navigate.attendance', /(ଉପସ୍ଥାନ|ହାଜିରା|attendance)/i],
  ['navigate.results', /(ଫଳାଫଳ|ନମ୍ବର|results)/i],
  ['navigate.dashboard', /(ଡ୍ୟାସବୋର୍ଡ|dashboard)/i],
  ['navigate.students', /(ଛାତ୍ର|ଛାତ୍ରୀ|ବିଦ୍ୟାର୍ଥୀ)/i],
  ['stop', /(ରୁହ|ବନ୍ଦ କର|stop)/i],
  ['help', /(ସାହାଯ୍ୟ|help)/i],
])

export function normaliseSpeech(value) {
  return String(value || '').toLocaleLowerCase().normalize('NFKC').replace(/\s+/g, ' ').trim()
}

export function matchIntent(text, language = 'en') {
  const commands = INTENTS[language] || INTENTS.en
  const matches = commands.filter(([, pattern]) => pattern.test(normaliseSpeech(text))).map(([intent]) => intent)
  return matches.length === 1 ? matches[0] : null
}

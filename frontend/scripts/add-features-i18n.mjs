import { readFile, writeFile } from 'node:fs/promises'

const additions = {
  en: {
    nav: {
      wallet: "Wallet",
      institutionDashboard: "Institution"
    },
    wallet: {
      title: "Academic identity and wallet",
      lead: "Your verifiable academic ID, credential archive, and privacy consent controls.",
      idCard: "Digital student ID",
      credentials: "Verifiable credentials",
      consent: "Privacy and consent",
      ocrUpload: "Upload document for OCR",
      ocrPrompt: "Select a marksheet or certificate to extract fields and submit for review.",
      ocrExtracting: "Extracting academic data...",
      ocrSubmit: "Submit for approval",
      ocrReviewNotice: "Decision support only. An authorized administrator must review and approve before a credential is valid.",
      toggleApaar: "Toggle APAAR ID visibility",
      downloadCertificate: "Download certificate PDF",
      qrNotice: "Scan to verify opaque token. No personal data is embedded in this QR code."
    },
    institution: {
      title: "Institution dashboard",
      lead: "Enrolment intake status, quota compliance, and academic record review queue.",
      reviewQueue: "Review queue",
      pendingReviews: "Pending approvals",
      approve: "Approve record",
      dismiss: "Dismiss finding",
      noTasks: "No pending review tasks."
    },
    demo: {
      title: "Guided interactive demo",
      switchRole: "Switch persona",
      roleAicte: "AICTE Admin",
      roleInstitution: "Institution Admin",
      roleStudent: "Student",
      roleVerifier: "Verifier"
    }
  },
  hi: {
    nav: {
      wallet: "वॉलेट",
      institutionDashboard: "संस्थान"
    },
    wallet: {
      title: "शैक्षणिक पहचान और वॉलेट",
      lead: "आपकी सत्यापन योग्य शैक्षणिक आईडी, क्रेडेंशियल संग्रह, और गोपनीयता सहमति नियंत्रण।",
      idCard: "डिजिटल छात्र आईडी",
      credentials: "सत्यापन योग्य क्रेडेंशियल",
      consent: "गोपनीयता और सहमति",
      ocrUpload: "ओसीआर के लिए दस्तावेज़ अपलोड करें",
      ocrPrompt: "फ़ील्ड निकालने और समीक्षा के लिए सबमिट करने हेतु अंकतालिका या प्रमाणपत्र चुनें।",
      ocrExtracting: "शैक्षणिक डेटा निकाला जा रहा है...",
      ocrSubmit: "मंजूरी के लिए सबमिट करें",
      ocrReviewNotice: "केवल निर्णय समर्थन। क्रेडेंशियल मान्य होने से पहले एक अधिकृत व्यवस्थापक को समीक्षा और अनुमोदन करना होगा।",
      toggleApaar: "APAAR आईडी दृश्यता टॉगल करें",
      downloadCertificate: "प्रमाणपत्र पीडीएफ डाउनलोड करें",
      qrNotice: "अपारदर्शी टोकन सत्यापित करने के लिए स्कैन करें। इस क्यूआर कोड में कोई व्यक्तिगत डेटा शामिल नहीं है।"
    },
    institution: {
      title: "संस्थान डैशबोर्ड",
      lead: "नामांकन स्थिति, कोटा अनुपालन, और शैक्षणिक रिकॉर्ड समीक्षा कतार।",
      reviewQueue: "समीक्षा कतार",
      pendingReviews: "लंबित अनुमोदन",
      approve: "रिकॉर्ड स्वीकृत करें",
      dismiss: "निष्कर्ष खारिज करें",
      noTasks: "कोई लंबित समीक्षा कार्य नहीं है।"
    },
    demo: {
      title: "निर्देशित इंटरैक्टिव डेमो",
      switchRole: "भूमिका बदलें",
      roleAicte: "एआईसीटीई व्यवस्थापक",
      roleInstitution: "संस्थान व्यवस्थापक",
      roleStudent: "छात्र",
      roleVerifier: "सत्यापनकर्ता"
    }
  },
  bn: {
    nav: {
      wallet: "ওয়ালেট",
      institutionDashboard: "প্রতিষ্ঠান"
    },
    wallet: {
      title: "শিক্ষাগত পরিচয় এবং ওয়ালেট",
      lead: "আপনার যাচাইযোগ্য শিক্ষাগত আইডি, প্রশংসাপত্র সংরক্ষণাগার এবং গোপনীয়তা সম্মতি নিয়ন্ত্রণ।",
      idCard: "ডিজিটাল শিক্ষার্থী আইডি",
      credentials: "যাচাইযোগ্য প্রশংসাপত্র",
      consent: "গোপনীয়তা এবং সম্মতি",
      ocrUpload: "ওসিআরের জন্য নথি আপলোড করুন",
      ocrPrompt: "ফিল্ড বের করতে এবং পর্যালোচনার জন্য জমা দিতে একটি মার্কশিট বা সার্টিফিকেট নির্বাচন করুন।",
      ocrExtracting: "শিক্ষাগত তথ্য নিষ্কাশন করা হচ্ছে...",
      ocrSubmit: "অনুমোদনের জন্য জমা দিন",
      ocrReviewNotice: "শুধুমাত্র সিদ্ধান্ত সমর্থন। একটি প্রশংসাপত্র বৈধ হওয়ার আগে একজন অনুমোদিত প্রশাসককে অবশ্যই পর্যালোচনা এবং অনুমোদন করতে হবে।",
      toggleApaar: "APAAR আইডি দৃশ্যমানতা টগল করুন",
      downloadCertificate: "সার্টিফিকেট পিডিএফ ডাউনলোড করুন",
      qrNotice: "অস্বচ্ছ টোকেন যাচাই করতে স্ক্যান করুন। এই কিউআর কোডে কোনো ব্যক্তিগত ডেটা নেই।"
    },
    institution: {
      title: "প্রতিষ্ঠান ড্যাশবোর্ড",
      lead: "ভর্তি গ্রহণের স্থিতি, কোটা সম্মতি এবং শিক্ষাগত রেকর্ড পর্যালোচনা সারি।",
      reviewQueue: "পর্যালোচনা সারি",
      pendingReviews: "মুলতুবি অনুমোদন",
      approve: "রেকর্ড অনুমোদন করুন",
      dismiss: "ফলাফল খারিজ করুন",
      noTasks: "কোনো মুলতুবি পর্যালোচনা কাজ নেই।"
    },
    demo: {
      title: "নির্দেশিত ইন্টারেক্টিভ ডেমো",
      switchRole: "ভূমিকা পরিবর্তন করুন",
      roleAicte: "এআইসিটিই প্রশাসক",
      roleInstitution: "প্রতিষ্ঠান প্রশাসক",
      roleStudent: "শিক্ষার্থী",
      roleVerifier: "যাচাইকারী"
    }
  },
  te: {
    nav: {
      wallet: "వాలెట్",
      institutionDashboard: "సంస్థ"
    },
    wallet: {
      title: "విద్యా గుర్తింపు మరియు వాలెట్",
      lead: "మీ ధృవీకరించదగిన విద్యా ID, ఆధారాల ఆర్కైవ్ మరియు గోప్యతా సమ్మతి నియంత్రణలు.",
      idCard: "డిజిటల్ విద్యార్థి ID",
      credentials: "ధృవీకరించదగిన ఆధారాలు",
      consent: "గోప్యత మరియు సమ్మతి",
      ocrUpload: "OCR కోసం పత్రాన్ని అప్‌లోడ్ చేయండి",
      ocrPrompt: "ఫీల్డ్‌లను సంగ్రహించడానికి మరియు సమీక్ష కోసం సమర్పించడానికి మార్కుల జాబితా లేదా ధృవీకరణ పత్రాన్ని ఎంచుకోండి.",
      ocrExtracting: "విద్యా డేటాను సంగ్రహిస్తోంది...",
      ocrSubmit: "ఆమోదం కోసం సమర్పించండి",
      ocrReviewNotice: "కేవలం నిర్ణయ మద్దతు మాత్రమే. ఆధారాలు చెల్లుబాటు అయ్యే ముందు అధికారిక నిర్వాహకుడు సమీక్షించి ఆమోదించాలి.",
      toggleApaar: "APAAR ID దృశ్యమానతను మార్చండి",
      downloadCertificate: "సర్టిఫికేట్ PDFని డౌన్‌లోడ్ చేయండి",
      qrNotice: "టోకెన్‌ను ధృవీకరించడానికి స్కాన్ చేయండి. ఈ QR కోడ్‌లో వ్యక్తిగత డేటా ఏదీ లేదు."
    },
    institution: {
      title: "సంస్థ డాష్‌బోర్డ్",
      lead: "చేరికల స్థితి, కోటా సమ్మతి మరియు విద్యా రికార్డుల సమీక్ష క్రమం.",
      reviewQueue: "సమీక్ష క్రమం",
      pendingReviews: "పెండింగ్ ఆమోదాలు",
      approve: "రికార్డును ఆమోదించండి",
      dismiss: "తీర్పును విస్మరించండి",
      noTasks: "పెండింగ్ సమీక్ష పనులు లేవు."
    },
    demo: {
      title: "మార్గదర్శక ఇంటరాక్టివ్ డెమో",
      switchRole: "పాత్రను మార్చండి",
      roleAicte: "AICTE అడ్మిన్",
      roleInstitution: "సంస్థ అడ్మిన్",
      roleStudent: "విద్యార్థి",
      roleVerifier: "ధృవీకరణకర్త"
    }
  },
  ta: {
    nav: {
      wallet: "வாலட்",
      institutionDashboard: "நிறுவனம்"
    },
    wallet: {
      title: "கல்வி அடையாளம் மற்றும் பணப்பை",
      lead: "உங்கள் சரிபார்க்கக்கூடிய கல்வி ஐடி, சான்றிதழ் காப்பகம் மற்றும் தனியுரிமை ஒப்புதல் கட்டுப்பாடுகள்.",
      idCard: "டிஜிட்டல் மாணவர் ஐடி",
      credentials: "சரிபார்க்கக்கூடிய சான்றிதழ்கள்",
      consent: "தனியுரிமை மற்றும் ஒப்புதல்",
      ocrUpload: "OCR க்கான ஆவணத்தைப் பதிவேற்றவும்",
      ocrPrompt: "மதிப்பெண் பட்டியல் அல்லது சான்றிதழைத் தேர்ந்தெடுத்து மதிப்பாய்வுக்குச் சமர்ப்பிக்கவும்.",
      ocrExtracting: "கல்வித் தரவு பிரித்தெடுக்கப்படுகிறது...",
      ocrSubmit: "ஒப்புதலுக்குச் சமர்ப்பிக்கவும்",
      ocrReviewNotice: "முடிவு ஆதரவு மட்டுமே. சான்றிதழ் செல்லுபடியாகும் முன் அங்கீகரிக்கப்பட்ட நிர்வாகி மறுஆய்வு செய்து அங்கீகரிக்க வேண்டும்.",
      toggleApaar: "APAAR ஐடி தெரிவுநிலையை மாற்றவும்",
      downloadCertificate: "சான்றிதழ் PDF ஐப் பதிவிறக்கவும்",
      qrNotice: "டோக்கனைச் சரிபார்க்க ஸ்கேன் செய்யவும். இந்த QR குறியீட்டில் தனிப்பட்ட தரவு எதுவும் இல்லை."
    },
    institution: {
      title: "நிறுவன டாஷ்போர்டு",
      lead: "சேர்க்கை நிலை, ஒதுக்கீட்டு இணக்கம் மற்றும் கல்விப் பதிவு மறுஆய்வு வரிசை.",
      reviewQueue: "மறுஆய்வு வரிசை",
      pendingReviews: "நிலுவையில் உள்ள ஒப்புதல்கள்",
      approve: "பதிவை அங்கீகரிக்கவும்",
      dismiss: "முடிவைத் தள்ளுபடி செய்யவும்",
      noTasks: "நிலுவையில் உள்ள மறுஆய்வுப் பணிகள் எதுவும் இல்லை."
    },
    demo: {
      title: "வழிகாட்டப்பட்ட மாதிரி செயல்விளக்கம்",
      switchRole: "பொறுப்பை மாற்றவும்",
      roleAicte: "AICTE நிர்வாகி",
      roleInstitution: "நிறுவன நிர்வாகி",
      roleStudent: "மாணவர்",
      roleVerifier: "சரிபார்ப்பாளர்"
    }
  },
  mr: {
    nav: {
      wallet: "वॉलेट",
      institutionDashboard: "संस्था"
    },
    wallet: {
      title: "शैक्षणिक ओळख आणि वॉलेट",
      lead: "तुमचे पडताळणीयोग्य शैक्षणिक आयडी, प्रमाणपत्र संग्रह आणि गोपनीयता संमती नियंत्रणे.",
      idCard: "डिजिटल विद्यार्थी आयडी",
      credentials: "पडताळणीयोग्य प्रमाणपत्रे",
      consent: "गोपनीयता आणि संमती",
      ocrUpload: "ओसीआरसाठी दस्तऐवज अपलोड करा",
      ocrPrompt: "तपशील काढण्यासाठी आणि पुनरावलोकनासाठी सादर करण्यासाठी गुणपत्रिका किंवा प्रमाणपत्र निवडा.",
      ocrExtracting: "शैक्षणिक डेटा काढला जात आहे...",
      ocrSubmit: "मंजुरीसाठी सबमिट करा",
      ocrReviewNotice: "केवळ निर्णय समर्थन. प्रमाणपत्र वैध होण्यापूर्वी अधिकृत प्रशासकाने पुनरावलोकन आणि मंजुरी दिली पाहिजे.",
      toggleApaar: "APAAR आयडी दृश्यमानता बदला",
      downloadCertificate: "प्रमाणपत्र पीडीएफ डाउनलोड करा",
      qrNotice: "अस्पष्ट टोकन पडताळण्यासाठी स्कॅन करा. या क्यूआर कोडमध्ये कोणताही वैयक्तिक डेटा नाही."
    },
    institution: {
      title: "संस्था डॅशबोर्ड",
      lead: "प्रवेश स्थिती, कोटा अनुपालन आणि शैक्षणिक नोंद पुनरावलोकन रांग.",
      reviewQueue: "पुनरावलोकन रांग",
      pendingReviews: "प्रलंबित मंजुरी",
      approve: "नोंद मंजूर करा",
      dismiss: "निष्कर्ष फेटाळा",
      noTasks: "कोणतीही प्रलंबित पुनरावलोकन कार्ये नाहीत."
    },
    demo: {
      title: "मार्गदर्शित परस्परसंवादी डेमो",
      switchRole: "भूमिका बदला",
      roleAicte: "एआयसीटीई प्रशासक",
      roleInstitution: "संस्था प्रशासक",
      roleStudent: "विद्यार्थी",
      roleVerifier: "पडताळणीकर्ता"
    }
  },
  gu: {
    nav: {
      wallet: "વોલેટ",
      institutionDashboard: "સંસ્થા"
    },
    wallet: {
      title: "શૈક્ષણિક ઓળખ અને વોલેટ",
      lead: "તમારું ચકાસણી યોગ્ય શૈક્ષણિક આઈડી, ઓળખપત્ર સંગ્રહ અને ગોપનીયતા સંમતિ નિયંત્રણો.",
      idCard: "ડિજિટલ વિદ્યાર્થી આઈડી",
      credentials: "ચકાસણી યોગ્ય ઓળખપત્રો",
      consent: "ગોપનીયતા અને સંમતિ",
      ocrUpload: "OCR માટે દસ્તાવેજ અપલોડ કરો",
      ocrPrompt: "વિગતો મેળવવા અને સમીક્ષા માટે સબમિટ કરવા માટે માર્કશીટ અથવા પ્રમાણપત્ર પસંદ કરો.",
      ocrExtracting: "શૈક્ષણિક ડેટા મેળવવામાં આવી રહ્યો છે...",
      ocrSubmit: "મંજૂરી માટે સબમિટ કરો",
      ocrReviewNotice: "માત્ર નિર્ણય આધાર. ક્રેડેન્શિયલ માન્ય થાય તે પહેલાં અધિકૃત સંચાલકે સમીક્ષા અને મંજૂરી આપવી આવશ્યક છે.",
      toggleApaar: "APAAR ID દૃશ્યતા બદલો",
      downloadCertificate: "પ્રમાણપત્ર પીડીએફ ડાઉનલોડ કરો",
      qrNotice: "ટોકન ચકાસવા માટે સ્કેન કરો. આ ક્યૂઆર કોડમાં કોઈ વ્યક્તિગત ડેટા નથી."
    },
    institution: {
      title: "સંસ્થા ડેશબોર્ડ",
      lead: "પ્રવેશ સ્થિતિ, ક્વોટા પાલન અને શૈક્ષણિક રેકોર્ડ સમીક્ષા કતાર.",
      reviewQueue: "સમીક્ષા કતાર",
      pendingReviews: "બાકી મંજૂરીઓ",
      approve: "રેકોર્ડ મંજૂર કરો",
      dismiss: "તારણ રદ કરો",
      noTasks: "કોઈ બાકી સમીક્ષા કાર્યો નથી."
    },
    demo: {
      title: "માર્ગદર્શિત ઇન્ટરેક્ટિવ ડેમો",
      switchRole: "ભૂમિકા બદલો",
      roleAicte: "AICTE એડમિન",
      roleInstitution: "સંસ્થા એડમિન",
      roleStudent: "વિદ્યાર્થી",
      roleVerifier: "ચકાસણીકર્તા"
    }
  },
  kn: {
    nav: {
      wallet: "ವಾಲೆಟ್",
      institutionDashboard: "ಸಂಸ್ಥೆ"
    },
    wallet: {
      title: "ಶೈಕ್ಷಣಿಕ ಗುರುತು ಮತ್ತು ವಾಲೆಟ್",
      lead: "ನಿಮ್ಮ ಪರಿಶೀಲಿಸಬಹುದಾದ ಶೈಕ್ಷಣಿಕ ಐಡಿ, ರುಜುವಾತು ಆರ್ಕೈವ್ ಮತ್ತು ಗೌಪ್ಯತೆ ಸಮ್ಮತಿ ನಿಯಂತ್ರಣಗಳು.",
      idCard: "ಡಿಜಿಟಲ್ ವಿದ್ಯಾರ್ಥಿ ಐಡಿ",
      credentials: "ಪರಿಶೀಲಿಸಬಹುದಾದ ರುಜುವಾತುಗಳು",
      consent: "ಗೌಪ್ಯತೆ ಮತ್ತು ಸಮ್ಮತಿ",
      ocrUpload: "OCR ಗಾಗಿ ದಾಖಲೆಯನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ",
      ocrPrompt: "ವಿವರಗಳನ್ನು ಹೊರತೆಗೆಯಲು ಮತ್ತು ಪರಿಶೀಲನೆಗೆ ಸಲ್ಲಿಸಲು ಅಂಕಪಟ್ಟಿ ಅಥವಾ ಪ್ರಮಾಣಪತ್ರವನ್ನು ಆಯ್ಕೆಮಾಡಿ.",
      ocrExtracting: "ಶೈಕ್ಷಣಿಕ ಡೇಟಾವನ್ನು ಪಡೆಯಲಾಗುತ್ತಿದೆ...",
      ocrSubmit: "ಅನುಮೋದನೆಗಾಗಿ ಸಲ್ಲಿಸಿ",
      ocrReviewNotice: "ಕೇವಲ ನಿರ್ಧಾರ ಬೆಂಬಲ ಮಾತ್ರ. ರುಜುವಾತು ಮಾನ್ಯವಾಗುವ ಮೊದಲು ಅಧಿಕೃತ ನಿರ್ವಾಹಕರು ಪರಿಶೀಲಿಸಿ ಅನುಮೋದಿಸಬೇಕು.",
      toggleApaar: "APAAR ID ಗೋಚರತೆಯನ್ನು ಬದಲಿಸಿ",
      downloadCertificate: "ಪ್ರಮಾಣಪತ್ರ PDF ಡೌನ್‌ಲೋಡ್ ಮಾಡಿ",
      qrNotice: "ಟೋಕನ್ ಪರಿಶೀಲಿಸಲು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ. ಈ ಕ್ಯೂಆರ್ ಕೋಡ್‌ನಲ್ಲಿ ಯಾವುದೇ ವೈಯಕ್ತಿಕ ಡೇಟಾ ಇಲ್ಲ."
    },
    institution: {
      title: "ಸಂಸ್ಥೆಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್",
      lead: "ದಾಖಲಾತಿ ಸ್ಥಿತಿ, ಕೋಟಾ ಅನುಸರಣೆ ಮತ್ತು ಶೈಕ್ಷಣಿಕ ದಾಖಲೆ ಪರಿಶೀಲನಾ ಸಾಲು.",
      reviewQueue: "ಪರಿಶೀಲನಾ ಸಾಲು",
      pendingReviews: "ಬಾಕಿ ಉಳಿದಿರುವ ಅನುಮೋದನೆಗಳು",
      approve: "ದಾಖಲೆಯನ್ನು ಅನುಮೋದಿಸಿ",
      dismiss: "ಫಲಿತಾಂಶವನ್ನು ತಿರಸ್ಕರಿಸಿ",
      noTasks: "ಯಾವುದೇ ಬಾಕಿ ಪರಿಶೀಲನಾ ಕಾರ್ಯಗಳಿಲ್ಲ."
    },
    demo: {
      title: "ಮಾರ್ಗದರ್ಶಿ ಸಂವಾದಾತ್ಮಕ ಡೆಮೊ",
      switchRole: "ಪಾತ್ರವನ್ನು ಬದಲಾಯಿಸಿ",
      roleAicte: "AICTE ನಿರ್ವಾಹಕರು",
      roleInstitution: "ಸಂಸ್ಥೆಯ ನಿರ್ವಾಹಕರು",
      roleStudent: "ವಿದ್ಯಾರ್ಥಿ",
      roleVerifier: "ಪರಿಶೀಲಕರು"
    }
  },
  ml: {
    nav: {
      wallet: "വാലറ്റ്",
      institutionDashboard: "സ്ഥാപനം"
    },
    wallet: {
      title: "വിദ്യാഭ്യാസ ഐഡന്റിറ്റിയും വാലറ്റും",
      lead: "നിങ്ങളുടെ പരിശോധിക്കാവുന്ന അക്കാദമിക് ഐഡി, സർട്ടിഫിക്കറ്റ് ശേഖരം, സ്വകാര്യതാ സമ്മത നിയന്ത്രണങ്ങൾ.",
      idCard: "ഡിജിറ്റൽ വിദ്യാർത്ഥി ഐഡി",
      credentials: "പരിശോധിക്കാവുന്ന സർട്ടിഫിക്കറ്റുകൾ",
      consent: "സ്വകാര്യതയും സമ്മതവും",
      ocrUpload: "OCR നായി രേഖ അപ്‌ലോഡ് ചെയ്യുക",
      ocrPrompt: "വിവരങ്ങൾ ശേഖരിക്കാനും അവലോകനത്തിനായി സമർപ്പിക്കാനും മാർക്ക്‌ഷീറ്റോ സർട്ടിഫിക്കറ്റോ തിരഞ്ഞെടുക്കുക.",
      ocrExtracting: "വിദ്യാഭ്യാസ ഡാറ്റ വേർതിരിച്ചെടുക്കുന്നു...",
      ocrSubmit: "അംഗീകാരത്തിനായി സമർപ്പിക്കുക",
      ocrReviewNotice: "തീരുമാന പിന്തുണ മാത്രം. ഒരു സർട്ടിഫിക്കറ്റ് സാധുവാകുന്നതിന് മുമ്പ് അംഗീകൃത അഡ്മിനിസ്ട്രേറ്റർ പരിശോധിച്ച് അംഗീകരിക്കണം.",
      toggleApaar: "APAAR ഐഡി ദൃശ്യപരത മാറ്റുക",
      downloadCertificate: "സർട്ടിഫിക്കറ്റ് PDF ഡൗൺലോഡ് ചെയ്യുക",
      qrNotice: "ടോക്കൺ സ്ഥിരീകരിക്കാൻ സ്കാൻ ചെയ്യുക. ഈ ക്യുആർ കോഡിൽ വ്യക്തിഗത വിവരങ്ങളൊന്നുമില്ല."
    },
    institution: {
      title: "സ്ഥാപന ഡാഷ്‌ബോർഡ്",
      lead: "പ്രവേശന നില, ക്വാട്ട പാലിക്കൽ, അക്കാദമിക് റെക്കോർഡ് അവലോകന നിര.",
      reviewQueue: "അവലോകന നിര",
      pendingReviews: "തീർച്ചപ്പെടുത്താത്ത അംഗീകാരങ്ങൾ",
      approve: "റെക്കോർഡ് അംഗീകരിക്കുക",
      dismiss: "കണ്ടെത്തൽ തള്ളിക്കളയുക",
      noTasks: "തീർച്ചപ്പെടുത്താത്ത അവലോകന ജോലികളൊന്നുമില്ല."
    },
    demo: {
      title: "മാർഗ്ഗനിർദ്ദേശമുള്ള ഇന്ററാക്ടീവ് ഡെമോ",
      switchRole: "സ്ഥാനം മാറ്റുക",
      roleAicte: "AICTE അഡ്മിൻ",
      roleInstitution: "സ്ഥാപന അഡ്മിൻ",
      roleStudent: "വിദ്യാർത്ഥി",
      roleVerifier: "പരിശോധകൻ"
    }
  },
  or: {
    nav: {
      wallet: "ୱାଲେଟ୍",
      institutionDashboard: "ଅନୁଷ୍ଠାନ"
    },
    wallet: {
      title: "ଶିକ୍ଷାଗତ ପରିଚୟ ଏବଂ ୱାଲେଟ୍",
      lead: "ଆପଣଙ୍କର ଯାଞ୍ଚଯୋଗ୍ୟ ଶିକ୍ଷାଗତ ID, ପ୍ରମାଣପତ୍ର ଅଭିଲେଖାଗାର, ଏବଂ ଗୋପନୀୟତା ସମ୍ମତି ନିୟନ୍ତ୍ରଣ।",
      idCard: "ଡିଜିଟାଲ୍ ଛାତ୍ର ID",
      credentials: "ଯାଞ୍ଚଯୋଗ୍ୟ ପ୍ରମାଣପତ୍ର",
      consent: "ଗୋପନୀୟତା ଏବଂ ସମ୍ମତି",
      ocrUpload: "OCR ପାଇଁ ଡକ୍ୟୁମେଣ୍ଟ୍ ଅପଲୋଡ୍ କରନ୍ତୁ",
      ocrPrompt: "ବିବରଣୀ ବାହାର କରିବା ଏବଂ ସମୀକ୍ଷା ପାଇଁ ଦାଖଲ କରିବାକୁ ଏକ ମାର୍କସିଟ୍ କିମ୍ବା ପ୍ରମାଣପତ୍ର ଚୟନ କରନ୍ତୁ।",
      ocrExtracting: "ଶିକ୍ଷାଗତ ତଥ୍ୟ ବାହାର କରାଯାଉଛି...",
      ocrSubmit: "ଅନୁମୋଦନ ପାଇଁ ଦାଖଲ କରନ୍ତୁ",
      ocrReviewNotice: "କେବଳ ନିଷ୍ପତ୍ତି ସହାୟତା। ପ୍ରମାଣପତ୍ର ବୈଧ ହେବା ପୂର୍ବରୁ ଜଣେ ଅଧିକୃତ ପ୍ରଶାସକ ସମୀକ୍ଷା ଏବଂ ଅନୁମୋଦନ କରିବା ଆବଶ୍ୟକ।",
      toggleApaar: "APAAR ID ଦୃଶ୍ୟମାନତା ପରିବର୍ତ୍ତନ କରନ୍ତୁ",
      downloadCertificate: "ପ୍ରମାଣପତ୍ର PDF ଡାଉନଲୋଡ୍ କରନ୍ତୁ",
      qrNotice: "ଟୋକନ୍ ଯାଞ୍ଚ କରିବାକୁ ସ୍କାନ୍ କରନ୍ତୁ। ଏହି QR କୋଡ୍‌ରେ କୌଣସି ବ୍ୟକ୍ତିଗତ ତଥ୍ୟ ନାହିଁ।"
    },
    institution: {
      title: "ଅନୁଷ୍ଠାନ ଡ୍ୟାସବୋର୍ଡ",
      lead: "ନାମଲେଖା ସ୍ଥିତି, କୋଟା ଅନୁପାଳନ, ଏବଂ ଶିକ୍ଷାଗତ ରେକର୍ଡ ସମୀକ୍ଷା ଧାଡ଼ି।",
      reviewQueue: "ସମୀକ୍ଷା ଧାଡ଼ି",
      pendingReviews: "ବକେୟା ଅନୁମୋଦନ",
      approve: "ରେକର୍ଡ ଅନୁମୋଦନ କରନ୍ତୁ",
      dismiss: "ଫଳାଫଳ ଖାରଜ କରନ୍ତୁ",
      noTasks: "କୌଣସି ବକେୟା ସମୀକ୍ଷା କାର୍ଯ୍ୟ ନାହିଁ।"
    },
    demo: {
      title: "ନିର୍ଦ୍ଦେଶିତ ଇଣ୍ଟରାକ୍ଟିଭ୍ ଡେମୋ",
      switchRole: "ଭୂମିକା ପରିବର୍ତ୍ତନ କରନ୍ତୁ",
      roleAicte: "AICTE ପ୍ରଶାସକ",
      roleInstitution: "ଅନୁଷ୍ଠାନ ପ୍ରଶାସକ",
      roleStudent: "ଛାତ୍ର",
      roleVerifier: "ଯାଞ୍ଚକାରୀ"
    }
  },
  pa: {
    nav: {
      wallet: "ਵਾਲਿਟ",
      institutionDashboard: "ਸੰਸਥਾ"
    },
    wallet: {
      title: "ਵਿਦਿਅਕ ਪਛਾਣ ਅਤੇ ਵਾਲਿਟ",
      lead: "ਤੁਹਾਡੀ ਪ੍ਰਮਾਣਿਤ ਵਿਦਿਅਕ ਆਈਡੀ, ਪ੍ਰਮਾਣ ਪੱਤਰ ਪੁਰਾਲੇਖ, ਅਤੇ ਗੋਪਨੀਯਤਾ ਸਹਿਮਤੀ ਨਿਯੰਤਰਣ।",
      idCard: "ਡਿਜੀਟਲ ਵਿਦਿਆਰਥੀ ਆਈਡੀ",
      credentials: "ਤਸਦੀਕ ਯੋਗ ਪ੍ਰਮਾਣ ਪੱਤਰ",
      consent: "ਗੋਪਨੀਯਤਾ ਅਤੇ ਸਹਿਮਤੀ",
      ocrUpload: "OCR ਲਈ ਦਸਤਾਵੇਜ਼ ਅੱਪਲੋਡ ਕਰੋ",
      ocrPrompt: "ਵੇਰਵੇ ਕੱਢਣ ਅਤੇ ਸਮੀਖਿਆ ਲਈ ਜਮ੍ਹਾ ਕਰਨ ਲਈ ਮਾਰਕਸ਼ੀਟ ਜਾਂ ਸਰਟੀਫਿਕੇਟ ਚੁਣੋ।",
      ocrExtracting: "ਵਿਦਿਅਕ ਡਾਟਾ ਕੱਢਿਆ ਜਾ ਰਿਹਾ ਹੈ...",
      ocrSubmit: "ਮਨਜ਼ੂਰੀ ਲਈ ਜਮ੍ਹਾਂ ਕਰੋ",
      ocrReviewNotice: "ਸਿਰਫ਼ ਫੈਸਲਾ ਸਮਰਥਨ। ਪ੍ਰਮਾਣ ਪੱਤਰ ਵੈਧ ਹੋਣ ਤੋਂ ਪਹਿਲਾਂ ਇੱਕ ਅਧਿਕਾਰਤ ਪ੍ਰਬੰਧਕ ਨੂੰ ਸਮੀਖਿਆ ਅਤੇ ਮਨਜ਼ੂਰੀ ਦੇਣੀ ਚਾਹੀਦੀ ਹੈ।",
      toggleApaar: "APAAR ID ਦ੍ਰਿਸ਼ਟੀ ਬਦਲੋ",
      downloadCertificate: "ਸਰਟੀਫਿਕੇਟ PDF ਡਾਊਨਲੋਡ ਕਰੋ",
      qrNotice: "ਟੋਕਨ ਦੀ ਪੁਸ਼ਟੀ ਕਰਨ ਲਈ ਸਕੈਨ ਕਰੋ। ਇਸ QR ਕੋਡ ਵਿੱਚ ਕੋਈ ਨਿੱਜੀ ਡਾਟਾ ਸ਼ਾਮਲ ਨਹੀਂ ਹੈ।"
    },
    institution: {
      title: "ਸੰਸਥਾ ਡੈਸ਼ਬੋਰਡ",
      lead: "ਦਾਖਲਾ ਸਥਿਤੀ, ਕੋਟਾ ਪਾਲਣਾ, ਅਤੇ ਅਕਾਦਮਿਕ ਰਿਕਾਰਡ ਸਮੀਖਿਆ ਕਤਾਰ।",
      reviewQueue: "ਸਮੀਖਿਆ ਕਤਾਰ",
      pendingReviews: "ਬਕਾਇਆ ਮਨਜ਼ੂਰੀਆਂ",
      approve: "ਰਿਕਾਰਡ ਮਨਜ਼ੂਰ ਕਰੋ",
      dismiss: "ਸਿੱਟਾ ਖਾਰਜ ਕਰੋ",
      noTasks: "ਕੋਈ ਬਕਾਇਆ ਸਮੀਖਿਆ ਕਾਰਜ ਨਹੀਂ ਹਨ।"
    },
    demo: {
      title: "ਨਿਰਦੇਸ਼ਿਤ ਇੰਟਰਐਕਟਿਵ ਡੈਮੋ",
      switchRole: "ਭੂਮਿਕਾ ਬਦਲੋ",
      roleAicte: "AICTE ਪ੍ਰਬੰਧਕ",
      roleInstitution: "ਸੰਸਥਾ ਪ੍ਰਬੰਧਕ",
      roleStudent: "ਵਿਦਿਆਰਥੀ",
      roleVerifier: "ਤਸਦੀਕਕਰਤਾ"
    }
  },
  as: {
    nav: {
      wallet: "ৱালেট",
      institutionDashboard: "প্ৰতিষ্ঠান"
    },
    wallet: {
      title: "শৈক্ষিক পৰিচয় আৰু ৱালেট",
      lead: "আপোনাৰ পৰীক্ষণযোগ্য শৈক্ষিক আইডি, প্ৰমাণপত্ৰ আৰ্কাইভ আৰু গোপনীয়তা সন্মতি নিয়ন্ত্ৰণ।",
      idCard: "ডিজিটেল শিক্ষাৰ্থী আইডি",
      credentials: "পৰীক্ষণযোগ্য প্ৰমাণপত্ৰসমূহ",
      consent: "গোপনীয়তা আৰু সন্মতি",
      ocrUpload: "OCR ৰ বাবে নথি আপল'ড কৰক",
      ocrPrompt: "তথ্য নিষ্কাষণ আৰু পুনৰীক্ষণৰ বাবে মাৰ্কশ্বীট বা প্ৰমাণপত্ৰ বাছক।",
      ocrExtracting: "শৈক্ষিক তথ্য সংগ্ৰহ কৰা হৈছে...",
      ocrSubmit: "অনুমোদনৰ বাবে দাখিল কৰক",
      ocrReviewNotice: "কেৱল সিদ্ধান্তৰ সহায়ক। প্ৰমাণপত্ৰ বৈধ হোৱাৰ পূৰ্বে কৰ্তৃত্বপ্ৰাপ্ত প্ৰশাসকে অনুমোদন জনাব লাগিব।",
      toggleApaar: "APAAR ID দৃশ্যমানতা সলনি কৰক",
      downloadCertificate: "প্ৰমাণপত্ৰ PDF ডাউনলোড কৰক",
      qrNotice: "টোকেন পৰীক্ষা কৰিবলৈ স্কেন কৰক। এই QR ক'ডত কোনো ব্যক্তিগত তথ্য নাই।"
    },
    institution: {
      title: "প্ৰতিষ্ঠান ডেচব'ৰ্ড",
      lead: "নামভৰ্তি স্থিতি, সংৰক্ষণ নীতি আৰু শৈক্ষিক তথ্য পুনৰীক্ষণ সূচী।",
      reviewQueue: "পুনৰীক্ষণ সূচী",
      pendingReviews: "বকেয়া অনুমোদন",
      approve: "তথ্য অনুমোদন কৰক",
      dismiss: "সিদ্ধান্ত খাৰিজ কৰক",
      noTasks: "কোনো পুনৰীক্ষণ কাৰ্য্য বাকী নাই।"
    },
    demo: {
      title: "নিৰ্দেশিত ইন্টাৰেক্টিভ ডেম'",
      switchRole: "ভূমিকা সলনি কৰক",
      roleAicte: "AICTE প্ৰশাসক",
      roleInstitution: "প্ৰতিষ্ঠান প্ৰশাসক",
      roleStudent: "শিক্ষাৰ্থী",
      roleVerifier: "পৰীক্ষক"
    }
  },
  ur: {
    nav: {
      wallet: "والیٹ",
      institutionDashboard: "ادارہ"
    },
    wallet: {
      title: "تعلیمی شناخت اور والیٹ",
      lead: "آپ کا قابل تصدیق تعلیمی شناختی کارڈ، اسناد کا ذخیرہ، اور رازداری کی رضامندی کے کنٹرول۔",
      idCard: "ڈیجیٹل طالب علم شناختی کارڈ",
      credentials: "قابل تصدیق اسناد",
      consent: "رازداری اور رضامندی",
      ocrUpload: "OCR کے لیے دستاویز اپ لوڈ کریں",
      ocrPrompt: "تفصیلات نکالنے اور جائزے کے لیے مارک شیٹ یا سند منتخب کریں۔",
      ocrExtracting: "تعلیمی ڈیٹا نکالا جا رہا ہے...",
      ocrSubmit: "منظوری کے لیے جمع کروائیں",
      ocrReviewNotice: "صرف فیصلہ سازی میں معاونت۔ سند درست ہونے سے پہلے مجاز منتظم کا جائزہ اور منظوری ضروری ہے۔",
      toggleApaar: "APAAR ID کی نمائش تبدیل کریں",
      downloadCertificate: "سند کی پی ڈی ایف ڈاؤن لوڈ کریں",
      qrNotice: "ٹوکن کی تصدیق کے لیے اسکین کریں۔ اس کیو آر کوڈ میں کوئی ذاتی معلومات نہیں ہیں۔"
    },
    institution: {
      title: "ادارے کا ڈیش بورڈ",
      lead: "اندراج کی حیثیت، کوٹہ کی تعمیل، اور تعلیمی ریکارڈ کے جائزے کی قطار۔",
      reviewQueue: "جائزے کی قطار",
      pendingReviews: "زیر التواء منظوریاں",
      approve: "ریکارڈ منظور کریں",
      dismiss: "نتیجہ خارج کریں",
      noTasks: "کوئی زیر التواء جائزہ کام نہیں ہے۔"
    },
    demo: {
      title: "رہنمائی پر مبنی انٹرایکٹو ڈیمو",
      switchRole: "کردار تبدیل کریں",
      roleAicte: "AICTE ایڈمن",
      roleInstitution: "ادارہ ایڈمن",
      roleStudent: "طالب علم",
      roleVerifier: "تصدیق کنندہ"
    }
  }
}

const localesDir = new URL('../src/i18n/locales/', import.meta.url)

for (const [lang, content] of Object.entries(additions)) {
  const filePath = new URL(`${lang}/common.json`, localesDir)
  const raw = await readFile(filePath, 'utf8')
  const data = JSON.parse(raw)
  data.nav.wallet = content.nav.wallet
  data.nav.institutionDashboard = content.nav.institutionDashboard
  data.wallet = content.wallet
  data.institution = content.institution
  data.demo = content.demo
  await writeFile(filePath, JSON.stringify(data, null, 2) + '\n', 'utf8')
  console.log(`Updated ${lang}/common.json with new feature keys.`)
}
